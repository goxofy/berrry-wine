"""Fresh task-owned supervisor; prior controls and receipts are immutable."""
import os,sys,pathlib,json,time,resource,subprocess,signal
O=pathlib.Path(__file__).parent
R=pathlib.Path('/tmp/tuxracer-glcolor4dv-repair-oct30');REPO=R/'repo';M=1048576
ROOT=pathlib.Path('/home/user/wine-assembly')
OLD=pathlib.Path('/tmp/tuxracer-glcolor4dv-canonical-enter-runtime-oct30')
LAUNCH=ROOT/'scratch/usage-watch/tuxracer-glcolor4dv-canonical-enter-runtime-oct30-report-corrected'
SSH='ssh -i /home/user/.ssh/wine_github_ed25519 -o BatchMode=yes -o IdentitiesOnly=yes -o UserKnownHostsFile=/home/user/.ssh/wine_github_known_hosts -o StrictHostKeyChecking=yes'
ORIG={k:resource.getrlimit(k) for k in [resource.RLIMIT_DATA,resource.RLIMIT_AS,resource.RLIMIT_CPU,resource.RLIMIT_FSIZE]}
def cap(k,n):
 s,h=resource.getrlimit(k);v=min(n,h) if h!=-1 else n
 resource.setrlimit(k,(min(v,s) if s!=-1 else v,h))
cap(resource.RLIMIT_DATA,128*M);cap(resource.RLIMIT_CPU,90);cap(resource.RLIMIT_FSIZE,4*M)
def save(n,v): (O/n).write_text(json.dumps(v,indent=2)+'\n')
def allocated(p):return sum(x.lstat().st_blocks*512 for x in [p,*p.rglob('*')]) if p.exists() else 0
def admission():
 sizes={str(p):allocated(p) for p in [R,OLD,O,LAUNCH]};used=sum(sizes.values())
 free=os.statvfs(O).f_bavail*os.statvfs(O).f_frsize
 mem=int(next(x.split()[1] for x in pathlib.Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))*1024
 init=json.loads((ROOT/'scratch/usage-watch/owner133-runtime-next-dispatch-admission-oct30.json').read_text())
 growth=max(0,init['remainingAggregateGrowth']-max(0,used-init['existingMaterializedRoots'][str(R)]))
 v=dict(at=time.time(),sizes=sizes,used=used,budget=64*M,publicationReserve=8*M,remainingTask=max(0,64*M-used),free=free,remainingAggregate=growth,MemAvailable=mem,checks=dict(allocation=used<=56*M,disk=free-growth>=3*1024**3,memory=mem>=2*1024**3))
 save('admission.json',v)
 if not all(v['checks'].values()):save('first-denial.json',v);raise RuntimeError('resource admission denied')
 return v
def run(name,args,cwd=REPO,git=False,wall=120):
 admission();env=dict(os.environ,GIT_SSH_COMMAND=SSH,GIT_NO_LAZY_FETCH='1',PYTHONDONTWRITEBYTECODE='1',BOAT_NO_UPDATE='1')
 def limits():
  if git:
   h=resource.getrlimit(resource.RLIMIT_DATA)[1]
   if h!=-1 and h<256*M:raise RuntimeError('inherited Git DATA hard limit incompatible')
   resource.setrlimit(resource.RLIMIT_DATA,(256*M,h))
  elif pathlib.Path(args[0]).name=='node':
   resource.setrlimit(resource.RLIMIT_DATA,ORIG[resource.RLIMIT_DATA]);resource.setrlimit(resource.RLIMIT_AS,ORIG[resource.RLIMIT_AS])
  cap(resource.RLIMIT_CPU,90);cap(resource.RLIMIT_FSIZE,4*M)
 a=O/'raw'/f'{name}.stdout';b=O/'raw'/f'{name}.stderr'
 if a.exists() or b.exists():raise RuntimeError('immutable operation name already used: '+name)
 start=time.monotonic();peak=0
 with a.open('wb') as x,b.open('wb') as y:
  q=subprocess.Popen(args,cwd=cwd,env=env,preexec_fn=limits,stdout=x,stderr=y,start_new_session=True)
  while q.poll() is None:
   rows={}
   for f in pathlib.Path('/proc').glob('[0-9]*/stat'):
    try:
     s=f.read_text().rsplit(')',1)[1].split();rows[int(f.parent.name)]=(int(s[1]),int(s[21])*4096)
    except (OSError,ValueError):pass
   ids={q.pid}
   while True:
    new=ids|{p for p,v in rows.items() if v[0] in ids}
    if new==ids:break
    ids=new
   rss=sum(rows.get(p,(0,0))[1] for p in ids);peak=max(peak,rss)
   reason='wall' if time.monotonic()-start>wall else 'groupRSS' if rss>512*M else 'supervisorRSS' if rows.get(os.getpid(),(0,0))[1]>128*M else 'output' if a.stat().st_size+b.stat().st_size>2*M else None
   if reason:os.killpg(q.pid,signal.SIGKILL);q.wait();save('first-operation-denial.json',dict(name=name,reason=reason));raise RuntimeError(reason)
   time.sleep(.04)
 argv=[x if len(x)<1000 else {'bytes':len(x),'sha256':__import__('hashlib').sha256(x.encode()).hexdigest()} for x in args]
 v=dict(exit=q.returncode,args=argv,elapsed=time.monotonic()-start,peakRSS=peak,stdoutBytes=a.stat().st_size,stderrBytes=b.stat().st_size);save('e/'+name+'.json',v)
 if q.returncode:raise RuntimeError(str(v)+' '+b.read_text()[-1200:])
 return a.read_bytes()
def git(name,*args):return run(name,['git','-C',str(REPO),*args],git=True)
if __name__=='__main__':print(json.dumps(admission()))
