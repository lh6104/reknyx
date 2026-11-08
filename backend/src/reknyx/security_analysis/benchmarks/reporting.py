"""Summaries retain failed groups and unknown cost/timing."""
import math
from .scoring import aggregate_trials


def summarize(report: dict) -> dict:
    repetitions=report['manifest']['repetitions']
    total=aggregate_trials(report['cases'],report['trials'],repetitions)
    if total != report['summary']:raise ValueError('inconsistent_counters')
    groups={}
    for group in sorted({c['group'] for c in report['cases']}):
        cases=[c for c in report['cases'] if c['group']==group]
        rows=[r for r in report['trials'] if r['group']==group]
        groups[group]=aggregate_trials(cases,rows,repetitions)
    times=sorted(r['latency_ms'] for r in report['trials'] if type(r.get('latency_ms')) in (int,float) and math.isfinite(r['latency_ms']) and r['latency_ms']>=0)
    return {'total':total,'groups':groups,'cost':None,'evidence_level':'synthetic_offline',
        'latency_ms':{'measured':len(times),'p50':times[math.ceil(len(times)*.5)-1] if times else None,
          'p95':times[math.ceil(len(times)*.95)-1] if times else None},
        'limitations':['Human gold review, open-claim scoring and live acceptance are not established.']}
