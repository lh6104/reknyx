import pytest
from reknyx.security_analysis.evidence_analysis import local_review,render_review
from reknyx.security_analysis.output_validation import validate_output


def test_empty_and_populated_local_reviews_are_explicit_and_grounded():
    for records in [[],[{'id':'source-1','kind':'service','source_tool':'nmap'}]]:
        context={'observations':records}
        value=local_review(context)
        assert value['outcome']=='ask'
        assert value['basis_observation_ids']==[o['id'] for o in records]
        assert 'review' in render_review(value,context).lower()

@pytest.mark.parametrize('change',[{'basis_observation_ids':['foreign']},{'outcome':'propose'},{'topics':['run_shell']},{'shell':'whoami'},{'basis_observation_ids':[]}])
def test_model_cannot_invent_references_or_execution_authority(change):
    context={'observations':[{'id':'source-1'}]}
    with pytest.raises(ValueError):validate_output({**local_review(context),**change},context)


def test_groq_request_is_fixed_bounded_and_strips_private_fields():
    from reknyx.security_analysis.model_providers.groq import _request,MODEL,input_reservation
    import json
    context={'observations':[{'id':'o1','kind':'service','source_tool':'nmap'}],'truncated':False,'private':'do not transmit'}
    calls=[]
    class Response:
        status=200
        def read(self,n):return json.dumps({'choices':[{'finish_reason':'stop','message':{'content':json.dumps(local_review(context))}}],'usage':{'prompt_tokens':50,'completion_tokens':20},'id':'test-request'}).encode()
    class Connection:
        def __init__(self,host,timeout):assert host=='api.groq.com' and timeout==8
        def request(self,method,path,body,headers):calls.append(json.loads(body));assert path=='/openai/v1/chat/completions'
        def getresponse(self):return Response()
        def close(self):pass
    result=_request(context,'test-only',Connection)
    assert len(calls)==1 and calls[0]['model']==MODEL
    assert 'private' not in json.dumps(calls)
    assert 'tools' not in calls[0] and calls[0]['max_completion_tokens']==1024
    assert result['usage']['completion_tokens']==20
    assert input_reservation(context)>len(json.dumps(calls[0]))

@pytest.mark.parametrize('status,finish,code',[(429,'stop','provider_rate_limited'),(500,'stop','provider_unavailable'),(200,'length','provider_incomplete'),(401,'stop','provider_authentication_failed'),(403,'stop','provider_forbidden'),(400,'stop','provider_bad_request')])
def test_groq_failures_are_explicit_without_retry(status,finish,code):
    import json
    from reknyx.security_analysis.model_providers.groq import _request,ProviderError
    attempts=[]
    class Response:
        def read(self,n):return json.dumps({'choices':[{'finish_reason':finish}]}).encode()
    Response.status=status
    class Connection:
        def __init__(self,*a,**kw):pass
        def request(self,*a,**kw):attempts.append(1)
        def getresponse(self):return Response()
        def close(self):pass
    with pytest.raises(ProviderError,match=code):_request({'observations':[],'truncated':False},'test',Connection)
    assert len(attempts)==1


def test_groq_model_options_are_explicit_bounded_and_recordable():
    from reknyx.security_analysis.model_providers.groq import RequestOptions,payload
    context={'observations':[],'truncated':False}
    value=payload(context,RequestOptions(model='openai/gpt-oss-20b',temperature=0.2,reasoning_effort='high',max_output_tokens=2048))
    assert value['model']=='openai/gpt-oss-20b' and value['temperature']==0.2
    assert value['reasoning_effort']=='high' and value['max_completion_tokens']==2048
    assert value['response_format']['json_schema']['strict'] is True
    for kwargs in [{'model':'unreviewed'},{'temperature':float('nan')},{'temperature':3},{'max_output_tokens':0},{'reasoning_effort':'max'}]:
        with pytest.raises(ValueError):RequestOptions(**kwargs)
