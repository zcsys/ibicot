"""Serve a verified historical replay with full statistics and generation pause.

Usage: PYTHONPATH=.pydeps:. python tools/serve_recovery.py ORIGINAL_RUN
The UI attaches to this replay; the original run is never overwritten.
"""
import argparse
import asyncio
import json
import math
import os
import time
from pathlib import Path

import uvicorn
import economy.server.runtime as runtime_module
import economy.server.service as service


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('run',type=Path)
    parser.add_argument('--resume',type=str,help='Checkpoint stem; preserve the current tick and world')
    args=parser.parse_args()
    expected=[json.loads(x) for x in (args.run/'generation_run.jsonl').read_text().splitlines()]
    cfg=json.loads((args.run/'initial-snapshot.json').read_text())['cfg']
    destination=args.run/('served-recovery-'+str(time.time_ns()))
    destination.mkdir()
    runtime_module._STATS_DIR=service._STATS_DIR=destination
    os.environ['ECONOMY_MAX_TICK']=str(len(expected))

    class VerifiedRuntime(runtime_module.KernelRuntime):
        def _record_stats(self):
            actual=runtime_module.stats_row(self.world,self.cfg,self.tick,self.month)
            original=expected[self.tick-1]
            for key,value in original.items():
                found=actual[key]
                matches=(math.isclose(found,value,rel_tol=1e-10,abs_tol=1e-5)
                         if isinstance(value,(int,float)) and not isinstance(value,bool)
                         else found==value)
                if not matches:
                    self.running=False
                    message=f'Tick {self.tick}: {key}: original={value}, replay={found}'
                    (destination/'verification-error.txt').write_text(message+'\n')
                    raise ValueError(message)
            super()._record_stats()
            if self.tick%30==0:
                (destination/'verification.json').write_text(json.dumps({
                    'verifiedTicks':self.tick,'targetTicks':len(expected),
                    'original':str(args.run),'complete':self.tick==len(expected)},indent=2)+'\n')
            if self.tick%360==0:print(f'Verified tick {self.tick}/{len(expected)}',flush=True)

    service._runtime=VerifiedRuntime(cfg)
    if args.resume:
        asyncio.run(service.checkpoint_load(service.CheckpointRequest(path=args.resume)))
        service._runtime.__class__=VerifiedRuntime
        (destination/'resume-source.json').write_text(json.dumps({
            'checkpoint':args.resume,'resumedAtTick':service._runtime.tick},indent=2)+'\n')
    (destination/'initial-snapshot.json').write_text(json.dumps(service._runtime.publish())+'\n')
    (args.run/'served-recovery-path.txt').write_text(str(destination)+'\n')
    print(f'Serving verified recovery: {destination}',flush=True)
    uvicorn.run(service.app,host='127.0.0.1',port=8000)


if __name__=='__main__':main()
