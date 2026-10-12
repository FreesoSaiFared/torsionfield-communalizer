#!/usr/bin/env python3
"""Integration test: local conversion, independent history, two opt-in contributors."""
import json, os, socket, subprocess, tempfile, time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
BASE=Path(__file__).resolve().parents[1]
def cmd(*args,cwd=None):
 return subprocess.run([str(a) for a in args],cwd=cwd,text=True,
                       capture_output=True,check=True).stdout.strip()
def count(a,b):
 return sum(n>1 and all(n%d for d in range(2,int(n**.5)+1)) for n in range(a,b))
def test():
 with tempfile.TemporaryDirectory(prefix='tf-verify-') as temp:
  t=Path(temp);src=t/'origin';src.mkdir()
  (src/'LICENSE').write_text('MIT License\n')
  (src/'README.md').write_text('Unmodified source\n')
  cmd('git','init','-b','main',src)
  cmd('git','-C',src,'config','user.name','Test')
  cmd('git','-C',src,'config','user.email','test@example.invalid')
  cmd('git','-C',src,'add','.')
  cmd('git','-C',src,'commit','-m','original')
  sha=cmd('git','-C',src,'rev-parse','HEAD')
  cmd('python3',BASE/'communalize.py',src,'--name','torsionfield-fixture',
      '--workspace',t/'output','--local')
  dst=t/'output'/'torsionfield-fixture'
  assert (dst/'README.md').read_text()=='Unmodified source\n'
  assert json.loads((dst/'.torsionfield'/'project.json').read_text())['project']['originCommit']==sha
  assert cmd('git','-C',dst,'rev-list','--count','HEAD')=='1'
  with socket.socket() as s:
   s.bind(('127.0.0.1',0));port=s.getsockname()[1]
  url='http://127.0.0.1:'+str(port)
  env={**os.environ,'TF_PORT':str(port)}
  hub=subprocess.Popen(['node',dst/'.torsionfield'/'hub.mjs'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
  def call(method,path,data=None):
   opts={'method':method}
   if data is not None:opts.update(data=json.dumps(data).encode(),headers={'Content-Type':'application/json'})
   with urlopen(Request(url+path,**opts),timeout=3) as resp:return json.load(resp)
  try:
   for i in range(50):
    try:call('GET','/api/health');break
    except Exception:time.sleep(.1)
   else:raise RuntimeError('Hub failed startup: '+hub.stderr.read().decode()[-1000:])
   job=call('POST','/api/tasks',{'kind':'prime-range','start':100000,'end':104000})
   a=call('POST','/api/lease',{'workerId':'contributor-A'})
   b=call('POST','/api/lease',{'workerId':'contributor-B'})
   assert a['unitId']!=b['unitId']
   try:
    call('POST','/api/result',{**{k:a[k] for k in ['taskId','unitId','leaseId','workerId']},'result':{'count':-1}})
    raise AssertionError('Bad proof accepted')
   except HTTPError as err:assert err.code==422
   a=call('POST','/api/lease',{'workerId':'contributor-A'})
   for unit in [a,b]:
    fields={k:unit[k] for k in ['taskId','unitId','leaseId','workerId']}
    result=call('POST','/api/result',{**fields,'result':{'count':count(unit['input']['start'],unit['input']['end'])}})
    assert result['verified'] and len(result['receiptSha256'])==64
   assert next(x for x in call('GET','/api/tasks') if x['id']==job['id'])['status']=='completed'
   proposal=call('POST','/api/tasks',{'kind':'agent-request','goal':'Inspect a public binary'})
   assert proposal['status']=='proposal' and not proposal['units']
   receipts=call('GET','/api/receipts')
   assert len(receipts)==2 and len(set(x['contributor'] for x in receipts))==2
   requests='\n'.join(json.dumps(x) for x in [
    {'jsonrpc':'2.0','id':1,'method':'tools/list'},
    {'jsonrpc':'2.0','id':2,'method':'resources/read',
     'params':{'uri':'ui://torsionfield/community'}}])+'\n'
   mcp=subprocess.run(['node',dst/'.torsionfield'/'mcp.mjs'],env={**env,'TF_HUB_URL':url},
                      input=requests,capture_output=True,text=True,timeout=5)
   responses=[json.loads(x) for x in mcp.stdout.splitlines()]
   assert 'ui' in responses[0]['result']['tools'][0]['_meta']
   assert 'ui/initialize' in responses[1]['result']['contents'][0]['text']
   print(json.dumps({'pass':True,'originalUnmodified':True,'independentHistory':True,
    'distinctWorkers':2,'badResultRejected':True,'verifiedReceipts':len(receipts),
    'agentProposalOnly':True,'mcpAppResource':True},indent=2))
  finally:
   hub.terminate()
   try:hub.wait(timeout=3)
   except subprocess.TimeoutExpired:hub.kill()
if __name__=='__main__':test()
