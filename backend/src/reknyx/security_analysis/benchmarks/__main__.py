"""Create an offline coverage report; never calls providers or scanners."""
import argparse
import json
from pathlib import Path
from reknyx.contracts import parse_json
from .runner import run_replay
from .reporting import summarize


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases',type=Path,required=True)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        result=run_replay(parse_json(args.cases.read_bytes()),parse_json(args.manifest.read_bytes()))
        result['reporting']=summarize(result)
        with args.output.open('x') as stream:
            json.dump(result,stream,indent=2,allow_nan=False)
    except (ValueError,KeyError,TypeError,OSError):
        parser.exit(2,'Invalid inputs or output unavailable. No provider request was sent.\n')
    print(json.dumps({'evidence_level':result['evidence_level'],'transport_calls':0,'summary':result['summary']}))
    return 0

if __name__=='__main__':raise SystemExit(main())
