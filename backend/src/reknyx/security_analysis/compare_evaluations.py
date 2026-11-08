"""Compare compatible frozen evaluation reports offline; never contact a provider."""
import argparse
import hashlib
import json
from pathlib import Path

from reknyx.contracts import canonical_request,parse_json

COMPATIBILITY=('dataset_version','dataset_sha256','algorithm_sha256','context_version','schema_version','schema_sha256','wire_schema_sha256','prompt_sha256','split')
STATUSES={'passed','failed','error','not_run'}


def checked_rows(report):
    rows=report.get('cases')
    if not isinstance(rows,list) or not rows:raise ValueError('Missing case results')
    indexed={}
    for row in rows:
        if not isinstance(row,dict) or not isinstance(row.get('id'),str) or row.get('status') not in STATUSES or row['id'] in indexed:
            raise ValueError('Invalid or duplicate case result')
        indexed[row['id']]=row
    attempted=sum(r['status']!='not_run' for r in rows)
    passed=sum(r['status']=='passed' for r in rows)
    if (report.get('selected')!=len(rows) or report.get('attempted')!=attempted
        or report.get('complete')!=(attempted==len(rows))
        or report.get('selection_passes')!={'numerator':passed,'denominator':attempted}
        or report.get('coverage')!={'numerator':attempted,'denominator':len(rows)}
        or report.get('errors')!=sum(r['status']=='error' for r in rows)
        or report.get('not_run')!=len(rows)-attempted):
        raise ValueError('Inconsistent evaluation counters')
    return indexed


def summary(report,rows):
    # Allowlist metadata rather than copying arbitrary report fields.
    options=report.get('model_options') or {}
    return {'provider':report.get('provider'),'model':options.get('model'),
      'temperature':options.get('temperature'),'reasoning_effort':options.get('reasoning_effort'),
      'selection_passes':report['selection_passes'],'attempted':report['attempted'],'selected':len(rows),
      'complete':report['complete'],'errors':report['errors'],'not_run':report['not_run']}


def compare(baseline,candidate):
    if not isinstance(baseline,dict) or not isinstance(candidate,dict):
        raise ValueError('Reports must be objects')
    if baseline.get('selection_policy_version') != candidate.get('selection_policy_version'):
        raise ValueError('Incompatible selection policy')
    for key in COMPATIBILITY:
        if not isinstance(baseline.get(key),str) or not baseline[key] or baseline[key]!=candidate.get(key):
            raise ValueError('Incompatible evaluation metadata: '+key)
    left,right=checked_rows(baseline),checked_rows(candidate)
    if left.keys()!=right.keys():raise ValueError('Case selections differ')
    paired=[]
    for identifier,a in left.items():
        b=right[identifier]
        if 'not_run' in (a['status'],b['status']):result='not_comparable'
        elif a['status']=='passed' and b['status']!='passed':result='candidate_regression'
        elif a['status']!='passed' and b['status']=='passed':result='candidate_improvement'
        elif a['status']=='passed':result='both_passed'
        else:result='neither_passed'
        paired.append({'id':identifier,'baseline_status':a['status'],'candidate_status':b['status'],'result':result})
    return {'comparison_version':'paired-review-comparison-v1',
      **{k:baseline[k] for k in COMPATIBILITY},
      'selection_policy_version':baseline.get('selection_policy_version'),
      'baseline_report_sha256':hashlib.sha256(canonical_request(baseline)).hexdigest(),
      'candidate_report_sha256':hashlib.sha256(canonical_request(candidate)).hexdigest(),
      'baseline':summary(baseline,left),'candidate':summary(candidate,right),
      'paired_counts':{kind:sum(r['result']==kind for r in paired) for kind in ('candidate_regression','candidate_improvement','both_passed','neither_passed','not_comparable')},
      'cases':paired,'provider_requests_sent':False,
      'limitations':['Synthetic selection labels are project-authored and not independently adjudicated.',
       'Matching this dataset does not establish vulnerability-detection accuracy, pentest success or real-world generalization.',
       'Development results may guide changes; do not tune on the reserved holdout cases or relabel failed cases to improve scores.',
       'No statistical significance or calibrated probability is inferred from this small sample.']}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline',type=Path,required=True)
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        result=compare(parse_json(args.baseline.read_bytes()),parse_json(args.candidate.read_bytes()))
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with args.output.open('x') as stream:json.dump(result,stream,indent=2)
    except (ValueError,KeyError,TypeError,OSError):
        parser.exit(2,'Reports are incompatible/invalid, or output already exists/is not writable. No provider request was sent.\n')
    print(json.dumps({k:result[k] for k in ('baseline','candidate','paired_counts','provider_requests_sent')}))
    return 0

if __name__=='__main__':raise SystemExit(main())
