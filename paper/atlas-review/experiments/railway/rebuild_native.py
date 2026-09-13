"""Optional offline recompilation of the three project JARs using Java 8 javac.

Reads retained Java (including generated model/matcher sources); does not rerun
Xcore or VQL generators. Third-party JARs remain the frozen dependencies.
"""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,zipfile


def external_output(path):
    """Keep newly generated files outside the evidence release."""
    path = Path(path).resolve()
    release = next((p for p in Path(__file__).resolve().parents
                    if (p / "verify_release.py").is_file()
                    and (p / "RELEASE_MANIFEST.json").is_file()),
                   Path(__file__).resolve().parent)
    if path == release or path.is_relative_to(release):
        raise ValueError("Output must be outside the evidence release")
    return path


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--payload',required=True,type=Path,help='payload directory produced by review.py')
    p.add_argument('--out',required=True,type=Path,help='new build output directory')
    p.add_argument('--javac',default='javac',help='Java 8 javac executable')
    a=p.parse_args();javac=shutil.which(a.javac)
    if not javac:p.error('Java 8 JDK is required for optional recompilation')
    version=subprocess.run([javac,'-version'],capture_output=True,text=True,check=True)
    if '1.8.' not in version.stderr+version.stdout:p.error('Use Java 8 javac for this frozen stack')
    if a.out.exists():p.error('Refusing existing build output')
    out=external_output(a.out);out.mkdir(parents=True);classes=out/'classes';classes.mkdir()
    native=a.payload.resolve()/'native';sources=sorted((native/'source').rglob('*.java'))
    if not sources:raise ValueError('Retained Java sources missing')
    argfile=out/'javac.args'
    classpath=os.pathsep.join(str(p) for p in sorted((native/'lib').glob('*.jar')))
    args=['-g','-encoding','UTF-8','-source','1.8','-target','1.8','-cp',classpath,'-d',str(classes)]+[str(s) for s in sources]
    argfile.write_text('\n'.join('"'+s.replace('\\','/')+'"' for s in args),'utf-8')
    completed=subprocess.run([javac,'@'+str(argfile)],capture_output=True,text=True,timeout=120)
    (out/'javac.log').write_text(completed.stdout+'\n'+completed.stderr,'utf-8')
    if completed.returncode:raise RuntimeError('javac failed; see javac.log')
    records=[]
    for name in ['atlas-railway-native-verifier.jar','trainbenchmark-format-emf-model-1.0.0-atlas-native.jar','trainbenchmark-tool-viatra-patterns-1.0.0-atlas-native.jar']:
        matching=0;different=[];missing=[];total=0
        with zipfile.ZipFile(native/'lib'/name) as old,zipfile.ZipFile(out/name,'w',zipfile.ZIP_DEFLATED) as new:
            for entry in old.infolist():
                content=old.read(entry)
                if entry.filename.endswith('.class'):
                    total+=1;file=classes/entry.filename
                    if not file.exists():missing.append(entry.filename)
                    else:
                        rebuilt=file.read_bytes()
                        if rebuilt==content:matching+=1
                        else:different.append(entry.filename)
                        content=rebuilt
                new.writestr(entry,content)
        records.append({'jar':name,'class_count':total,'byte_identical_recompiled_classes':matching,'different_classes':different,'missing_classes':missing})
    result={'status':'PASS' if all(not r['missing_classes'] for r in records) else 'FAIL','source_files':len(sources),'jars':records,
            'scope':'Offline Java recompilation from retained generated model/matcher and runner source; original non-class resources retained. No Xcore/VQL generator rerun; third-party dependencies not rebuilt.'}
    (out/'REBUILD_RESULT.json').write_text(json.dumps(result,indent=2),'utf-8');print(json.dumps(result,indent=2))
    if result['status']!='PASS':raise AssertionError('Missing classes')

if __name__=='__main__':main()
