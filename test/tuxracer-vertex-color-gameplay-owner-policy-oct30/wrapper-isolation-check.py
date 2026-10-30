"""Reproduce two simultaneous wrapper commands; verify disjoint captures and valid log."""
import pathlib,subprocess,sys,json,gzip,importlib.util
O=pathlib.Path(__file__).parent
spec=importlib.util.spec_from_file_location('owned',O/'control-v2.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
child="""import importlib.util,pathlib,sys
p=pathlib.Path(sys.argv[1]);s=importlib.util.spec_from_file_location('c',p/'control-v2.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
n=sys.argv[2];b=c.run('isolation-'+n,[sys.executable,'-B','-c',"import time;print('begin-"+n+"');time.sleep(.4);print('end-"+n+"')"],cwd=p)
assert b.decode()=='begin-'+n+'\\nend-'+n+'\\n',b
"""
def main():
 c.admission()
 ps=[subprocess.Popen([sys.executable,'-B','-c',child,str(O),str(i)],cwd=O,stdout=subprocess.PIPE,stderr=subprocess.PIPE) for i in range(2)]
 for p in ps:
  out,err=p.communicate(timeout=10);assert p.returncode==0,(out,err)
 rows=[json.loads(x) for x in gzip.open(O/'operations-v2.jsonl.gz','rt')]
 rows=[r for r in rows if r['name'].startswith('isolation-')];assert len(rows)==2
 assert {r['stdout'] for r in rows}=={'begin-0\nend-0\n','begin-1\nend-1\n'}
 c.save('wrapper-isolation-check.json',dict(PASS=True,concurrentCommands=2,commands=rows,limitsUnchanged=True,rootCapturePathsUnique=True,compressedLogSerialized=True))
 print('wrapper isolation PASS')
if __name__=='__main__':main()
