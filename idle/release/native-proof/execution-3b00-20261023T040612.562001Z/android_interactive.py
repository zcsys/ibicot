#!/usr/bin/env python3
"""Evidence-only bounded native operator, reacting to this invocation's exact output path."""
import argparse,pathlib,subprocess,sys,threading,time
from execute_cells import ROOT,EVIDENCE
p=argparse.ArgumentParser();p.add_argument('action',choices=['clock','share']);p.add_argument('run_id');a=p.parse_args()
scenario='clock-start' if a.action=='clock' else 'share-cancel'
command=[sys.executable,str(EVIDENCE/'execute_cells.py'),'android','single','--scenario',scenario,'--run-id',a.run_id]
operator=[];threads=[]
def operate(folder):
    marker=b'TIDEGLASS_NATIVE_CLOCK_BACKGROUND_READY' if a.action=='clock' else b'TIDEGLASS_NATIVE_SHARE_READY'
    deadline=time.monotonic()+180
    while time.monotonic()<deadline:
        log=folder/'run.log'
        if log.exists() and marker in log.read_bytes():
            result=subprocess.run([sys.executable,str(EVIDENCE/'android_operator.py'),a.action,str(folder)],cwd=ROOT)
            operator.append(result.returncode);return
        if native.poll() is not None: operator.append(125);return
        time.sleep(.2)
    operator.append(124)
native=subprocess.Popen(command,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
for line in native.stdout:
    print(line,end='',flush=True)
    if line.startswith('Native checks for '):
        folder=pathlib.Path(line.split('evidence: ',1)[1].strip());assert folder.parent==ROOT/'release/native-proof'
        t=threading.Thread(target=operate,args=(folder,));t.start();threads.append(t)
result=native.wait()
for t in threads:t.join()
assert operator==[0],operator
raise SystemExit(result)
