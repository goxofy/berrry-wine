"""Immutable owner-policy supervisor. RAM admission revoked; process guards retained."""
import os,sys,pathlib,json,time,resource,subprocess,signal,hashlib,gzip
O=pathlib.Path(__file__).parent
R=pathlib.Path('/tmp/tuxracer-glcolor4dv-repair-oct30'); REPO=R/'repo'; M=1048576
ROOT=pathlib.Path('/home/user/wine-assembly')
OLD=pathlib.Path('/tmp/tuxracer-glcolor4dv-canonical-enter-runtime-oct30-report-corrected')
LAUNCH=ROOT/'scratch/usage-watch/tuxracer-vertex-color-gameplay-owner-policy-oct30'
ROOTS=[R,OLD,pathlib.Path('/tmp/tuxracer-glcolor4dv-canonical-enter-runtime-oct30'),O,LAUNCH]
SSH='ssh -i /home/user/.ssh/wine_github_ed25519 -o BatchMode=yes -o IdentitiesOnly=yes -o UserKnownHostsFile=/home/user/.ssh/wine_github_known_hosts -o StrictHostKeyChecking=yes'
ORIG={k:resource.getrlimit(k) for k in [resource.RLIMIT_DATA,resource.RLIMIT_AS,resource.RLIMIT_CPU,resource.RLIMIT_FSIZE]}
def cap(k,n):
 s,h=resource.getrlimit(k);resource.setrlimit(k,(min(n,s) if s!=-1 else min(n,h) if h!=-1 else n,h))
cap(resource.RLIMIT_DATA,128*M);cap(resource.RLIMIT_CPU,90);cap(resource.RLIMIT_FSIZE,12*M)
def save(n,v):
 p=O/n;p.parent.mkdir(exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
def allocated(p):return sum(x.lstat().st_blocks*512 for x in [p,*p.rglob('*')]) if p.exists() else 0
def admission(publication=False):
 sizes={str(p):allocated(p) for p in ROOTS};used=sum(sizes.values());s=os.statvfs(O);free=s.f_bavail*s.f_frsize
 mem=int(next(x.split()[1] for x in pathlib.Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))*1024
 # Retain conservative shared residual; never recharge the initial256MiB envelope.
 growth=max(0,200183808-max(0,used-27430912))
 v=dict(at=time.time(),sizes=sizes,used=used,budget=64*M,publicationReserve=8*M,free=free,remainingAggregate=growth,MemAvailable=mem,RAMPolicy='observation only; no admission hold',diskFloor=1610612736,checks=dict(allocation=used<=(64 if publication else 56)*M,disk=free-growth>=1610612736))
 save('admission.json',v)
 if not all(v['checks'].values()):save('first-denial.json',v);raise RuntimeError('allocation/disk denied')
 return v
def run(name,args,cwd=REPO,git=False,wall=120,publication=False,expect_capture=False):
 a=admission(publication);p=pathlib.Path(cwd).resolve();assert p==REPO or p.is_relative_to(O)
 env=dict(os.environ,GIT_SSH_COMMAND=SSH,GIT_NO_LAZY_FETCH='1',PYTHONDONTWRITEBYTECODE='1',BOAT_NO_UPDATE='1')
 def limits():
  if git:
   h=ORIG[resource.RLIMIT_DATA][1];assert h==-1 or h>=256*M;resource.setrlimit(resource.RLIMIT_DATA,(256*M,h))
  elif pathlib.Path(args[0]).name=='node':
   for k in [resource.RLIMIT_DATA,resource.RLIMIT_AS]:resource.setrlimit(k,ORIG[k])
  cap(resource.RLIMIT_CPU,90);cap(resource.RLIMIT_FSIZE,12*M)
 out=O/'live.stdout';err=O/'live.stderr';start=time.monotonic();peak=0;reason=None
 with out.open('wb') as x,err.open('wb') as y:
  q=subprocess.Popen(args,cwd=p,env=env,preexec_fn=limits,stdout=x,stderr=y,start_new_session=True)
  while True:
   rows={}
   for f in pathlib.Path('/proc').glob('[0-9]*/stat'):
    try:s=f.read_text().rsplit(')',1)[1].split();rows[int(f.parent.name)]=(int(s[1]),int(s[21])*4096)
    except (OSError,ValueError):pass
   ids={q.pid}
   while True:
    new=ids|{i for i,v in rows.items() if v[0] in ids}
    if new==ids:break
    ids=new
   rss=sum(rows.get(i,(0,0))[1] for i in ids);peak=max(peak,rss)
   reason='capture512KiB' if out.stat().st_size+err.stat().st_size>512*1024 else 'wall' if time.monotonic()-start>wall else 'groupRSS512MiB' if rss>512*M else 'supervisorRSS128MiB' if rows.get(os.getpid(),(0,0))[1]>128*M else None
   if reason:
    if q.poll() is None:os.killpg(q.pid,signal.SIGKILL)
    q.wait();break
   if q.poll() is not None:break
   time.sleep(.04)
 data=out.read_bytes();error=err.read_bytes()
 rec=dict(name=name,argv=[x if len(x)<1000 else {'bytes':len(x),'sha256':hashlib.sha256(x.encode()).hexdigest()} for x in args],exit=q.returncode,reason=reason,elapsed=time.monotonic()-start,peakRSS=peak,stdoutBytes=len(data),stderrBytes=len(error),inheritedLimits=ORIG,generatedFileLimit=12*M,captureLimit=512*1024)
 with gzip.open(O/'operations.jsonl.gz','ab') as f:f.write((json.dumps(dict(**rec,stdout=data.decode(errors='replace'),stderr=error.decode(errors='replace')))+'\n').encode())
 out.unlink();err.unlink()
 if reason:
  save('capture-control.json' if expect_capture else 'first-operation-denial.json',rec)
  if expect_capture and reason=='capture512KiB':return b''
  raise RuntimeError(str(rec))
 if q.returncode:raise RuntimeError(str(rec)+' '+error.decode(errors='replace')[-1500:])
 return data
def git(name,*args,**kw):return run(name,['git','-C',str(REPO),*args],git=True,**kw)
if __name__=='__main__':print(json.dumps(admission()))
