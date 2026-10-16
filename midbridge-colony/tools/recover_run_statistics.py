"""Replay a saved run, verifying every old statistic before accepting new data.

Usage: PYTHONPATH=.pydeps:. python tools/recover_run_statistics.py RUN_DIRECTORY
Never alters the original log. A mismatch stops recovery rather than presenting
different simulation results as reconstructed historical results.
"""
import argparse
import json
import math
import time
from pathlib import Path

from economy.core.state import reset_world
from economy.kernel.tick import tick
from economy.server.runtime import stats_row
from economy.server.recording import CompanyHistory
from economy.server.persistence import save_checkpoint


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('run',type=Path)
    ap.add_argument('--limit',type=int)
    args=ap.parse_args()
    old=[json.loads(x) for x in (args.run/'generation_run.jsonl').read_text().splitlines()]
    if args.limit:old=old[:args.limit]
    cfg,w=reset_world(json.loads((args.run/'initial-snapshot.json').read_text())['cfg'])
    dest=args.run/('recovered-'+str(time.time_ns()));dest.mkdir()
    recorder=CompanyHistory(dest,cfg);state={};start=time.monotonic()
    print(str(dest),flush=True)
    with (dest/'generation_run.jsonl').open('w') as output:
        for index,expected in enumerate(old,1):
            if expected['tick']!=index:raise ValueError('Original ticks are not contiguous')
            tick(w,cfg,index,state=state)
            actual=stats_row(w,cfg,index,index//30)
            for key,value in expected.items():
                found=actual[key]
                matches=(math.isclose(found,value,rel_tol=1e-10,abs_tol=1e-5)
                         if isinstance(value,(int,float)) and not isinstance(value,bool)
                         else found==value)
                if not matches:raise ValueError(f'Tick {index}: {key}: original={value}, replay={found}')
            recorder.record(w,cfg,index)
            output.write(json.dumps(actual)+'\n')
            if index%30==0:output.flush()
            if index%360==0:print(f'Verified tick {index}/{len(old)}; {time.monotonic()-start:.1f}s',flush=True)
    recorder.flush(w,cfg)
    save_checkpoint(str(dest/'final-checkpoint'),cfg,len(old),w,state)
    (dest/'verified.json').write_text(json.dumps({'verifiedTicks':len(old),'original':str(args.run),
        'elapsedSeconds':time.monotonic()-start,'comparison':'every original field; rtol=1e-10, atol=1e-5'},indent=2)+'\n')
    print('Verified recovery complete',flush=True)


if __name__=='__main__':main()
