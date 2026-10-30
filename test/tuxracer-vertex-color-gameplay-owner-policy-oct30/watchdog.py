"""Task lifecycle only; no agent, no replacement assignment."""
import control as c,time,json,subprocess,pathlib,resource
schedule=json.loads((c.O/'schedule.json').read_text());box=json.loads((c.O/'boat-created.json').read_text())['id']
while time.time()<schedule['shutdownEpoch']:
 if (c.O/'snapshot-stop-proof.json').exists():raise SystemExit(0)
 time.sleep(min(30,max(0,schedule['shutdownEpoch']-time.time())))
for label,args in [('stop',['stop',box]),('info',['info',box])]:
 with (c.O/'raw'/('watchdog-'+label+'.stdout')).open('xb') as a,(c.O/'raw'/('watchdog-'+label+'.stderr')).open('xb') as b:
  q=subprocess.run(['/home/user/.ascii/boat','--no-update','--json',*args],stdout=a,stderr=b,timeout=90,cwd=c.O)
 c.save('watchdog-'+label+'.json',{'exit':q.returncode,'at':time.time(),'id':box})
