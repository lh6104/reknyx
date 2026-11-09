"""Paired retrieval diagnostics. Labels never enter search input; no model calls."""
from copy import deepcopy
import hashlib
import math
from pathlib import Path
from time import perf_counter

from sqlalchemy.exc import SQLAlchemyError
from reknyx.contracts import canonical_request
from reknyx.security_analysis import knowledge

VERSION = 'paired-retrieval-v1'


def score_ranking(retrieved, relevant, *, k):
    if (type(k) is not int or not 1 <= k <= 10
            or any(not isinstance(items,list) for items in (retrieved,relevant))
            or any(not isinstance(item,str) or not item for item in retrieved+relevant)
            or len(set(retrieved)) != len(retrieved) or len(set(relevant)) != len(relevant)):
        raise ValueError('invalid_ranking')
    top=retrieved[:k]; gold=set(relevant)
    if not gold:
        return {'recall':None,'reciprocal_rank':None,'ndcg':None,'empty_gold_correct':not top}
    rank=next((i for i,identifier in enumerate(top,1) if identifier in gold),None)
    dcg=sum(1/math.log2(i+1) for i,identifier in enumerate(top,1) if identifier in gold)
    ideal=sum(1/math.log2(i+1) for i in range(1,min(k,len(gold))+1))
    return {'recall':len(gold.intersection(top))/len(gold),
            'reciprocal_rank':1/rank if rank else 0.0,'ndcg':dcg/ideal,'empty_gold_correct':None}


def _dataset(value, snapshot, *, as_of, k):
    if (not isinstance(value,dict) or set(value)!={'version','provenance','label_status','cases'}
            or not isinstance(value['version'],str) or not 1 <= len(value['version']) <= 128
            or value['provenance']!='synthetic_fixture'
            or value['label_status']!='project_authored_not_independently_reviewed'
            or not isinstance(value['cases'],list) or not 1 <= len(value['cases']) <= 200):
        raise ValueError('invalid_retrieval_dataset')
    corpus={d['id'] for d in snapshot['documents']}
    seen=set()
    for case in value['cases']:
        if (not isinstance(case,dict) or set(case)!={'id','query','identifiers','relevant_ids'}
                or not isinstance(case['id'],str) or not 1 <= len(case['id']) <= 128
                or case['id'] in seen or not isinstance(case['query'],str) or len(case['query']) > 1000):
            raise ValueError('invalid_retrieval_case')
        seen.add(case['id'])
        for field in ('identifiers','relevant_ids'):
            items=case[field]
            if (not isinstance(items,list) or len(items)>32
                    or any(not isinstance(item,str) for item in items) or len(set(items))!=len(items)):
                raise ValueError('invalid_retrieval_labels')
        if not set(case['relevant_ids']) <= corpus or len(case['identifiers']) > k:
            raise ValueError('invalid_gold_or_limit')
        knowledge.exact_lookup(snapshot,case['identifiers'],as_of=as_of)
    return deepcopy(value)


def _summary(rows, cases):
    relevant=sum(bool(c['relevant_ids']) for c in cases)
    empty=len(cases)-relevant
    metrics={}
    for key,name in (('recall','recall_at_k'),('reciprocal_rank','mrr'),('ndcg','ndcg_at_k')):
        total=sum(row['scores'][key] or 0 for row in rows)
        metrics[name]={'sum':total,'denominator':relevant,'value':total/relevant if relevant else None}
    metrics['empty_gold_correct']={'numerator':sum(row['scores']['empty_gold_correct'] is True for row in rows),
                                   'denominator':empty}
    return {'coverage':{'numerator':len(rows),'denominator':len(cases)},
            'errors':sum(row['status']=='error' for row in rows),'metrics':metrics,'cases':rows}


def run_retrieval_benchmark(connection, snapshot, dataset, *, as_of, k=5, modes=('exact','exact_fts')):
    if type(k) is not int or not 1 <= k <= 10:
        raise ValueError('invalid_retrieval_limit')
    if (not isinstance(modes,tuple) or not modes or len(set(modes))!=len(modes)
            or any(mode not in ('exact','exact_fts') for mode in modes)):
        raise ValueError('invalid_retrieval_modes')
    # Validate snapshot identity and all labels before any SQL is attempted.
    knowledge.exact_lookup(snapshot,[],as_of=as_of)
    cases=_dataset(dataset,snapshot,as_of=as_of,k=k)['cases']
    arms={}
    for mode in modes:
        rows=[]
        for case in cases:
            start=perf_counter()
            row={'id':case['id'],'status':'ok','retrieved_ids':[],'error_code':None}
            try:
                if mode=='exact':
                    result=knowledge.exact_lookup(snapshot,case['identifiers'],as_of=as_of)
                else:
                    result=knowledge.retrieve_knowledge(connection,snapshot,case['query'],identifiers=case['identifiers'],as_of=as_of,limit=k)
                pack=knowledge.knowledge_pack(result,snapshot=snapshot)
                row['retrieved_ids']=[d['id'] for d in pack['references']][:k]
            except (ValueError,SQLAlchemyError):
                row.update(status='error',error_code='retrieval_failed')
            row['elapsed_ms']=(perf_counter()-start)*1000
            row['scores']=score_ranking(row['retrieved_ids'],case['relevant_ids'],k=k)
            if row['status']=='error' and not case['relevant_ids']:
                row['scores']['empty_gold_correct']=False
            rows.append(row)
        arms[mode]=_summary(rows,cases)
    identities={name:hashlib.sha256(Path(path).read_bytes()).hexdigest()
                for name,path in (('evaluator',__file__),('knowledge',knowledge.__file__))}
    return {'version':VERSION,'algorithm_sha256':hashlib.sha256(canonical_request(identities)).hexdigest(),
            'dataset_version':dataset['version'],'dataset_sha256':hashlib.sha256(canonical_request(dataset)).hexdigest(),
            'snapshot_sha256':snapshot['sha256'],'as_of':as_of.isoformat(),'k':k,
            'label_status':dataset['label_status'],'provider_calls':0,'arms':arms,
            'limitations':['Project-authored synthetic retrieval labels, not independently adjudicated gold data.',
                           'Exact-only versus lexical supplementation measures retrieval mechanics, not Analyst/model improvement.',
                           'Errors remain in scheduled metric denominators; no retries or significance claims.']}
