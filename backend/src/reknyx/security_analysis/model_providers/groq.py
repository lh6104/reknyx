"""Fixed-destination Groq adapter. No tools, redirects, retries or provider switching."""
from dataclasses import dataclass
import math
import ssl
import copy
import http.client
import json
import multiprocessing
from pathlib import Path
import tempfile

from reknyx.contracts import canonical_request,parse_json
from ..output_validation import SCHEMA

MODEL='openai/gpt-oss-120b'
ENDPOINT='https://api.groq.com/openai/v1/chat/completions'
OUTPUT_CAP=1024
PROMPT=Path(__file__).parents[1].joinpath('prompts/evidence_review_v2.txt').read_text()
WIRE_SCHEMA=copy.deepcopy(SCHEMA)
for field in ('basis_observation_ids','topics'):
    for constraint in ('minItems','maxItems','uniqueItems'):
        WIRE_SCHEMA['properties'][field].pop(constraint,None)

@dataclass(frozen=True)
class RequestOptions:
    model: str = MODEL
    temperature: float = 0.1
    reasoning_effort: str = 'low'
    max_output_tokens: int = OUTPUT_CAP

    def __post_init__(self):
        if self.model not in ('openai/gpt-oss-120b','openai/gpt-oss-20b'):
            raise ValueError('Unsupported Groq model; use a reviewed GPT-OSS model')
        if not math.isfinite(self.temperature) or not 0 <= self.temperature <= 2:
            raise ValueError('Temperature must be between 0 and 2')
        if self.reasoning_effort not in ('low','medium','high'):
            raise ValueError('Unsupported reasoning effort')
        if type(self.max_output_tokens) is not int or not 128 <= self.max_output_tokens <= 4096:
            raise ValueError('Output token limit must be 128–4096')


def options_for(settings):
    return RequestOptions(settings.groq_model,settings.groq_temperature,settings.groq_reasoning_effort,settings.groq_max_output_tokens)


class ProviderError(ValueError):
    def __init__(self,code,http_status=None):
        self.code,self.http_status=code,http_status
        super().__init__(code)

def project_observation(observation):
    projected={k:observation[k] for k in ('id','kind','source_tool')}
    facts=observation.get('facts',{})
    severity=facts.get('severity','unknown')
    transport=facts.get('transport','unknown')
    port=facts.get('port')
    projected['facts']={
        'severity':severity if severity in ('critical','high','medium','low','informational','unknown') else 'unknown',
        'transport':transport if transport in ('tcp','udp','unknown') else 'unknown',
        'port':port if type(port) is int and 1<=port<=65535 else None,
        'historical':facts.get('historical') if type(facts.get('historical')) is bool else True,
    }
    return projected


def payload(context,options=None):
    options=options or RequestOptions()
    # Only these static structural facts are sent, never scope, messages or raw bytes.
    projected={'observations':[project_observation(o) for o in context['observations']],'truncated':context['truncated']}
    return {'model':options.model,'messages':[{'role':'system','content':PROMPT},{'role':'user','content':canonical_request(projected).decode()}],
      'max_completion_tokens':options.max_output_tokens,'temperature':options.temperature,'reasoning_effort':options.reasoning_effort,'stream':False,
      'response_format':{'type':'json_schema','json_schema':{'name':'evidence_review_v2','strict':True,'schema':WIRE_SCHEMA}}}

def input_reservation(context,options=None):
    # UTF-8 byte upper bound plus conservative chat-format overhead; no tokenizer claim.
    return len(canonical_request(payload(context,options)))+1024

def _request(context,key,connection_factory=http.client.HTTPSConnection,options=None):
    connection=connection_factory('api.groq.com',timeout=8)
    try:
        connection.request('POST','/openai/v1/chat/completions',body=canonical_request(payload(context,options)),
                           headers={'Authorization':'Bearer '+key,'Content-Type':'application/json','User-Agent':'Reknyx/0.1'})
        response=connection.getresponse()
        if response.status!=200:
            raise ProviderError({400:'provider_bad_request',401:'provider_authentication_failed',403:'provider_forbidden',404:'provider_model_unavailable',429:'provider_rate_limited'}.get(response.status,'provider_unavailable'),response.status)
        raw=response.read(65537)
        if len(raw)>65536:raise ProviderError('provider_response_limit')
        data=parse_json(raw)
        choices=data.get('choices')
        if not isinstance(choices,list) or len(choices)!=1:raise ProviderError('invalid_model_output')
        choice=choices[0]
        if choice.get('finish_reason')!='stop':raise ProviderError('provider_incomplete')
        message=choice.get('message',{})
        if message.get('refusal'):raise ProviderError('provider_refused')
        content=message.get('content')
        if not isinstance(content,str):raise ProviderError('invalid_model_output')
        value=parse_json(content.encode())
        usage=data.get('usage',{})
        usage={k:usage.get(k) for k in ('prompt_tokens','completion_tokens')}
        if not all(type(n) is int and n>=0 for n in usage.values()):usage=None
        return {'http_status':200,'value':value,'usage':usage,'request_id':str(data.get('id',''))[:200] or None}
    except ProviderError:
        raise
    except ssl.SSLError:
        raise ProviderError('provider_tls_error') from None
    except TimeoutError:
        raise ProviderError('provider_timeout') from None
    except OSError:
        raise ProviderError('provider_unavailable') from None
    except (ValueError,TypeError,KeyError,AttributeError):
        raise ProviderError('invalid_model_output') from None
    finally:
        connection.close()

def _child(context,key,output,options):
    try:result={'result':_request(context,key,options=options)}
    except ProviderError as exc:result={'failure_code':exc.code,'http_status':exc.http_status}
    except Exception:result={'failure_code':'provider_unavailable'}
    Path(output).write_text(json.dumps(result))

def review(context,key,options=None):
    """One bounded request. Timeout retains an uncertain usage reservation."""
    with tempfile.TemporaryDirectory(prefix='reknyx-model-') as directory:
        output=str(Path(directory)/'result.json')
        process=multiprocessing.get_context('spawn').Process(target=_child,args=(context,key,output,options or RequestOptions()))
        process.start()
        process.join(12)
        if process.is_alive():
            process.kill();process.join()
            raise ProviderError('provider_timeout')
        path=Path(output)
        if process.exitcode!=0 or not path.is_file() or path.stat().st_size>65536:
            raise ProviderError('provider_unavailable')
        value=parse_json(path.read_bytes())
        if 'failure_code' in value:raise ProviderError(value['failure_code'],value.get('http_status'))
        return value['result']
