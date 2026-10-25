#!/usr/bin/env python3
"""Bounded disposable HTTP/TLS load rehearsal. Never accepts a remote target."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import http.client
import json
import math
import os
from pathlib import Path
import signal
import socket
import ssl
import statistics
import subprocess
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def request(port, method='GET', path='/health', body=None, headers=None, context=None):
    client = (http.client.HTTPSConnection('127.0.0.1', port, timeout=8, context=context)
              if context else http.client.HTTPConnection('127.0.0.1', port, timeout=8))
    start = time.monotonic()
    try:
        client.request(method, path, body, headers or {})
        response = client.getresponse(); data = response.read(65537)
        if len(data) > 65536: raise AssertionError('Unbounded response.')
        return response.status, data, (time.monotonic()-start)*1000
    finally: client.close()


def children(pid):
    result = subprocess.run(['ps', '-axo', 'pid=,ppid=,rss='], capture_output=True, text=True, timeout=2, check=True)
    rows = [line.split() for line in result.stdout.splitlines()]
    return {int(p): int(rss) for p, parent, rss in rows if int(parent) == pid}


def ready(port, process, timeout=10, context=None):
    until = time.monotonic()+timeout
    while time.monotonic() < until:
        if process.poll() is not None: raise AssertionError('Server exited before readiness.')
        try:
            if request(port, context=context)[0] == 200:return
        except (OSError, http.client.HTTPException): pass
        time.sleep(.05)
    raise AssertionError('Server readiness deadline exceeded.')


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0)); return sock.getsockname()[1]


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    output=Path(args.output).resolve();output.mkdir(parents=True,exist_ok=False)
    report={'format':'tideglass-local-serving-rehearsal-v1','synthetic_only':True,
            'release_gate_verified':False,'python':sys.version,'host':sys.platform,'scenarios':[]}
    start=time.monotonic()
    try:
        with tempfile.TemporaryDirectory(prefix='tideglass-serving-synthetic-') as directory:
            folder=Path(directory);folder.chmod(0o700)
            for mode in ('loopback_http','tls'):
                port=free_port()
                value={'version':1,'mode':mode,'host':'127.0.0.1','port':port,
                       'database':str(folder/(mode+'.sqlite3')),'workers':2,'timeout_seconds':2,
                       'backlog':16,'max_requests':1000}
                context=None
                if mode=='tls':
                    key=folder/'local.key';cert=folder/'local.crt'
                    # Self-signed fixture trusted ONLY by this local client, never disable verification.
                    subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(key),
                        '-out',str(cert),'-days','1','-subj','/CN=127.0.0.1',
                        '-addext','subjectAltName=IP:127.0.0.1'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=10,check=True)
                    key.chmod(0o600);cert.chmod(0o600)
                    value.update(certificate_file=str(cert),private_key_file=str(key))
                    context=ssl.create_default_context(cafile=str(cert))
                    report['synthetic_tls_certificate_sha256']=hashlib.sha256(cert.read_bytes()).hexdigest()
                config=folder/(mode+'.json');config.write_text(json.dumps(value));config.chmod(0o600)
                check=subprocess.run([sys.executable,'-m','services.tideglass_service.deployment','--config',str(config),'--check'],cwd=ROOT,capture_output=True,timeout=10)
                assert check.returncode==0,check.stderr.decode()
                assert not Path(value['database']).exists(),'Check mode initialized DB.'
                raw_log=output/(mode+'-server.log')
                with raw_log.open('wb') as log:
                    process=subprocess.Popen([sys.executable,'-m','services.tideglass_service.deployment','--config',str(config)],cwd=ROOT,stdout=log,stderr=log,env={**os.environ,'GUNICORN_CMD_ARGS':'--workers 40 --timeout 0 --access-logfile -'})
                    try:
                        ready(port,process,context=context)
                        until=time.monotonic()+5
                        while time.monotonic()<until:
                            initial=children(process.pid)
                            if len(initial)==2:break
                            time.sleep(.05)
                        assert len(initial)==2,initial
                        seen=[];stop=threading.Event()
                        def sample():
                            while not stop.wait(.05):seen.append(children(process.pid))
                        thread=threading.Thread(target=sample);thread.start()
                        try:
                            with ThreadPoolExecutor(max_workers=8) as pool:
                                results=list(pool.map(lambda _:request(port,context=context),range(64)))
                        finally:stop.set();thread.join(3)
                        assert all(status==200 for status,_,_ in results)
                        assert all(len(row)<=2 for row in seen),'Worker ceiling exceeded.'
                        times=sorted(result[2] for result in results)
                        report['scenarios'].append({'name':mode+'_concurrent_health','requests':64,'client_concurrency':8,
                            'status_counts':{'200':64},'p50_ms':statistics.median(times),'p95_ms':times[math.ceil(.95*len(times))-1],
                            'maximum_ms':max(times),'maximum_observed_worker_count':max([2]+[len(row) for row in seen]),
                            'maximum_sampled_workers_rss_kib':max([sum(initial.values())]+[sum(row.values()) for row in seen]),
                            'status':'passed'})
                        status,body,_=request(port,'POST','/v1/accounts',json.dumps({'consent_cloud':True}),{'Content-Type':'application/json'},context)
                        assert status==201,status
                        account=json.loads(body)
                        authorization={'Authorization':'Bearer '+account['session_token']}
                        with ThreadPoolExecutor(max_workers=8) as pool:
                            authenticated=list(pool.map(lambda _:request(port,path='/v1/entitlements',headers=authorization,context=context),range(64)))
                        assert all(status==200 for status,_,_ in authenticated)
                        auth_times=sorted(result[2] for result in authenticated)
                        report['scenarios'].append({'name':mode+'_concurrent_authenticated_entitlements','requests':64,'client_concurrency':8,
                            'status_counts':{'200':64},'p50_ms':statistics.median(auth_times),'p95_ms':auth_times[math.ceil(.95*len(auth_times))-1],
                            'maximum_ms':max(auth_times),'status':'passed','synthetic_account_only':True})
                        # Existing API body limit exercised through real server without sending huge bytes.
                        status,_,_=request(port,'POST','/v1/accounts',b'',{'Content-Type':'application/json','Content-Length':str(2*1024*1024+65537)},context)
                        assert status==413,status
                        status,_,_=request(port,'GET','/health',headers={'X-Synthetic-Probe':'SensitiveSentinel'*400},context=context)
                        assert status in (400,431),status
                        status,_,_=request(port,'GET','/health?SensitiveSentinel',context=context)
                        assert status==400,status
                        report['scenarios'].append({'name':mode+'_request_bounds_and_redacted_logs','status':'passed'})
                        # Forwarded scheme cannot impersonate TLS. Plain mode app's WSGI identity
                        # is fixed by connection, not this spoofed client header.
                        assert request(port,headers={'X-Forwarded-Proto':'https'},context=context)[0]==200
                        original=children(process.pid)
                        os.kill(next(iter(original)),signal.SIGKILL)
                        until=time.monotonic()+8
                        while time.monotonic()<until:
                            after=children(process.pid)
                            if len(after)==2 and set(after)!=set(original):break
                            time.sleep(.05)
                        assert len(after)==2 and set(after)!=set(original),'Worker not replaced.'
                        ready(port,process,context=context)
                        report['scenarios'].append({'name':mode+'_host_killed_worker_replacement','status':'passed',
                            'parent_pid':process.pid,'before_worker_pids':sorted(original),'after_worker_pids':sorted(after),
                            'classification':'controlled_process_stop_not_crash_or_observed_session'})
                        if mode=='loopback_http':
                            stalled=[]
                            try:
                                before=children(process.pid)
                                for _ in range(2):
                                    sock=socket.create_connection(('127.0.0.1',port),timeout=8)
                                    sock.sendall(b'POST /v1/accounts HTTP/1.1\r\nHost: 127.0.0.1\r\nContent-Type: application/json\r\nContent-Length: 100\r\n\r\n{')
                                    stalled.append(sock)
                                # Both request-reading sync workers become silent; Gunicorn replaces them.
                                until=time.monotonic()+8
                                while time.monotonic()<until:
                                    after=children(process.pid)
                                    if len(after)==2 and set(before).isdisjoint(after):break
                                    time.sleep(.05)
                                assert len(after)==2 and set(before).isdisjoint(after),'Slow body workers not replaced.'
                                ready(port,process)
                                report['scenarios'].append({'name':'incomplete_body_worker_timeout_and_recovery','status':'passed',
                                    'before_worker_pids':sorted(before),'after_worker_pids':sorted(after),
                                    'request_outcome':'not_committed_fixture_invalid_body; general mutation response loss remains unknown'})
                            finally:
                                for sock in stalled:sock.close()
                    finally:
                        if process.poll() is None:process.terminate()
                        try:process.wait(timeout=12)
                        except subprocess.TimeoutExpired:
                            # Children inherit the rehearsal group, so its outer deadline
                            # can stop the entire tree even if this cleanup is interrupted.
                            for worker in children(process.pid):
                                try:os.kill(worker,signal.SIGKILL)
                                except ProcessLookupError:pass
                            process.kill();process.wait(timeout=3)
                text=raw_log.read_text()
                assert 'SensitiveSentinel' not in text,'Unredacted request content in logs.'
                assert account['session_token'] not in text and account['recovery_code'] not in text,'Credentials in server log.'
                if mode=='loopback_http':assert 'worker_timeout' in text,'Timeout diagnostic absent.'
                report.setdefault('logs',{})[raw_log.name]=hashlib.sha256(raw_log.read_bytes()).hexdigest()
            report['status']='passed'
    except Exception as error:
        report['status']='failed';report['failure_type']=type(error).__name__;report['failure']=str(error)
        raise
    finally:
        report['elapsed_seconds']=time.monotonic()-start
        (output/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')


if __name__=='__main__':main()
