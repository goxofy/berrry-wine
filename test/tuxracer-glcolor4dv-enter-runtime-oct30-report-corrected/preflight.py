import control as c,pathlib,json,hashlib,re,tarfile,os
O=c.O;ROOT=pathlib.Path('/home/user/wine-assembly');SRC=pathlib.Path('/tmp/coordinator-tuxracer-render-inputs-oct30');DONOR=pathlib.Path('/tmp/tuxracer-software-render-msvcrt-retest-oct30');CAND='4068d12a28b5a96260dfbdd8fb26a8954f35d923'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 c.admission()
 node='/usr/local/bin/node'; flags=['--max-old-space-size=128']
 assert json.loads((O/'e/node-startup.json').read_text())['exit']==0
 receipt=json.loads((O/'reused-mount-receipt.json').read_text());assert sha(pathlib.Path(receipt['path']).read_bytes())==receipt['sha256']
 assert (O/'raw/head.stdout').read_text().strip()==CAND
 assert json.loads((O/'e/born-branch.json').read_text())['exit']==0
 closure=json.loads((ROOT/'scratch/usage-watch/tuxracer-glcolor4dv-canonical-closure-oct30.json').read_text()); rows=closure['inputs'].copy()
 extras=['tools/region-layout.js','tools/watx-closure.js','tools/watx.js','tools/region-layout-hash.js','lib/dispatch-trampoline.js','tools/watx-src/compiler-parser.js','tools/watx-src/compiler-stages.js','tools/watx-src/compiler-codegen.js']
 # Only exact required paths; root and donor objects are read-only, no fetch or ancestry scan.
 for name in extras:
  oid=(O/('raw/oid-'+name.replace('/','_')+'.stdout')).read_text().strip()
  rows[name]=dict(oid=oid)
 for i,(name,row) in enumerate(rows.items()):
  p=c.REPO/name
  if p.is_file() and ('sha256' not in row or sha(p.read_bytes())==row['sha256']):
   b=p.read_bytes()
   assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==row['oid']
  else:
   # Exact candidate object store is available; root is not a complete donor.
   # The failed root read remains preserved and is never replayed.
   b=c.git('candidate-blob-'+str(i),'cat-file','blob',row['oid'])
   assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==row['oid']
   p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
   (O/('raw/candidate-blob-'+str(i)+'.stdout')).unlink()
  if 'sha256' in row:assert sha(b)==row['sha256']
  row.update(bytes=len(b),sha256=sha(b))
 c.save('source-manifest.json',dict(candidate=CAND,inputs=rows,canonicalIncludeCount=128))
 # Resolve all includes recursively from exact canonical main; no synthetic module.
 seen=set()
 def walk(n):
  if n in seen:return
  seen.add(n)
  for child in re.findall(r'\(include\s+"([^"]+)"\)',(c.REPO/n).read_text()):walk(str(pathlib.PurePosixPath(n).parent/child))
 walk('src/main.watx');assert len(seen)==128 and seen=={n for n in rows if n.startswith('src/')}
 compilerNames=set(extras)|{'tools/build-compile-wat.js','lib/compile-wat.js','lib/wat-manifest.js','tools/watx-src/compiler.js'}
 # Loading entries verifies V8/parser imports cheaply without compiling the module.
 code="require('./lib/compile-wat.js');require('./tools/watx-closure.js');require('./tools/watx.js');require('./tools/region-layout-hash.js');require('./lib/dispatch-trampoline.js');console.log('compiler entries loaded; no compilation')"
 c.run('compiler-entry-smoke',[node,*flags,'-e',code])
 a=json.loads((DONOR/'archive.json').read_text());p=DONOR/'packet.tar.gz';assert p.stat().st_size==a['bytes'] and sha(p.read_bytes())==a['sha256']
 packet=[]
 with tarfile.open(p) as t:
  for m in t:
   assert m.isfile() and '..' not in pathlib.PurePosixPath(m.name).parts and not m.name.startswith('/')
   b=t.extractfile(m).read();packet.append(dict(path=m.name,bytes=len(b),sha256=sha(b)))
 assert len(packet)==318
 c.save('standing-packet-manifest.json',dict(archive=a,files=packet,hostRevision='898d2ec8d9db7d4f9236d9eb705adfd431ea19c9',historicalModuleExcluded=True))
 sourceFiles=sorted(rows)
 # Remote replacement packet contains ONLY exact source/compiler inputs, no media duplication.
 with tarfile.open(O/'candidate.tar.gz','w:gz') as t:
  for n in sourceFiles:t.add(c.REPO/n,arcname=n,recursive=False)
 c.save('preflight.json',dict(PASS=True,sourceCount=len(rows),includeCount=len(seen),archive=a,candidateArchiveSHA=sha((O/'candidate.tar.gz').read_bytes()),candidateArchiveBytes=(O/'candidate.tar.gz').stat().st_size,compilerNames=sorted(compilerNames),admission=c.admission(),SSH=c.SSH))
 print('PREFLIGHT PASS')
if __name__=='__main__':main()
