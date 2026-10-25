#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Start disposable normal/test binders, validate, and stop both processes."""
import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--workspace',type=Path,default=Path(__file__).resolve().parents[1])
p.add_argument('--binder',default='afb-binder')
a=p.parse_args()
root=a.workspace.resolve()
launcher=Path(__file__).resolve().parents[1]/'scripts/run-demo.py'

def request(base,verb,arg=None):
    data=None if arg is None else json.dumps(arg).encode()
    req=urllib.request.Request(base+'/sameloop-api/'+verb,data=data,
                              headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=3) as response:
        return json.load(response)

for test_controls in (False,True,False):
    with socket.socket() as s:
        s.bind(('127.0.0.1',0)); port=s.getsockname()[1]
    base=f'http://127.0.0.1:{port}/api'
    with tempfile.TemporaryFile(mode='w+') as log:
        cmd=[sys.executable,str(launcher),'--workspace',str(root),
             '--binder',a.binder,'--port',str(port)]
        if test_controls: cmd.append('--test-controls')
        child=subprocess.Popen(cmd,stdout=log,stderr=log)
        try:
            for _ in range(100):
                if child.poll() is not None: raise RuntimeError('binder exited at startup')
                try:
                    state=request(base,'get')['response']; break
                except OSError: time.sleep(.05)
            else: raise RuntimeError('binder did not become ready')
            assert state['controller']=={'mode':'OFF','setpoint':25}
            if test_controls:
                subprocess.run([sys.executable,str(Path(__file__).with_name('integration.py')),
                                '--url',f'ws://127.0.0.1:{port}/api'],check=True)
            else:
                # Use the WS failure code rather than relying on HTTP error mapping.
                code='''import asyncio,sys
sys.path.insert(0,sys.argv[1])
from afb_ws import Client,AfbError
async def test():
 async with Client(sys.argv[2]) as c:
  try: await c.call('sameloop-api','fault',{'valid':False})
  except AfbError: return
  raise AssertionError('test fault controls enabled by default')
asyncio.run(test())
'''
                subprocess.run([sys.executable,'-c',code,str(Path(__file__).resolve().parents[1]/'tools'),
                                f'ws://127.0.0.1:{port}/api'],check=True)
                result=request(base,'settings',{'mode':'AUTO','setpoint':26})
                assert result['response']['controller']=={'mode':'AUTO','setpoint':26}
                print('PASS: fresh startup OFF/25, fault disabled, HTTP settings accepted',flush=True)
        except BaseException:
            log.seek(0); print(log.read(),file=sys.stderr); raise
        finally:
            child.terminate()
            try: child.wait(timeout=5)
            except subprocess.TimeoutExpired: child.kill();child.wait()
print('PASS: full suite, including restart reset')
