"""Run one full declared condition only after the lead grants the Flutter lane.
Does not install/promote staged sources or change production/status files.
"""
import argparse,datetime,hashlib,json,subprocess,sys
from pathlib import Path
from content_contract import load,write,sha
from check_content_report import validate_run

p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--viewport',choices=['phone','tablet'],required=True);p.add_argument('--text-percent',choices=[100,150,200],type=int,required=True);p.add_argument('--pseudo',choices=['true','false'],required=True);a=p.parse_args();root=a.root.resolve();stage=Path(__file__).resolve().parents[1]
require=lambda condition,message:None if condition else (_ for _ in ()).throw(ValueError(message))
for f in ['content_presentation_test.dart','content_presentation_probe.dart']:
    require((root/'game/mobile/test'/f).read_bytes()==(stage/'game/mobile/test'/f).read_bytes(),'installed test differs from reviewed stage: '+f)
output=a.output.resolve();output.mkdir(parents=True,exist_ok=False)
def inventory():
    paths=set()
    for package in ['mobile','core','progression','events','persistence','platform']:
        base=root/'game'/package
        for folder in ['lib','assets','content']:
            if (base/folder).exists():paths.update(p for p in (base/folder).rglob('*')if p.is_file())
        for file in ['pubspec.yaml','pubspec.lock']:
            if (base/file).is_file():paths.add(base/file)
    paths.update(root/'game/mobile/test'/f for f in ['content_presentation_test.dart','content_presentation_probe.dart'])
    paths.update(root/f for f in ['implementation/art/production_contract.json','implementation/content/launch_manifest.json','economy.json','tool/flutter','tool/dart'])
    paths.update(p for p in stage.rglob('*')if p.is_file()and '__pycache__'not in p.parts)
    return {str(p.relative_to(root)):sha(p)for p in sorted(paths)}
before=inventory()
for rel in before:
    dst=output/'source'/rel;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes((root/rel).read_bytes())
condition={'viewport':a.viewport,'text_percent':a.text_percent,'pseudo':a.pseudo=='true'}
command=[str(root/'tool/flutter'),'test','--reporter=json','test/content_presentation_test.dart',f'--dart-define=TIDEGLASS_TEST_VIEWPORT={a.viewport}',f'--dart-define=TIDEGLASS_TEST_TEXT_PERCENT={a.text_percent}',f'--dart-define=TIDEGLASS_PSEUDO={a.pseudo}',f'--dart-define=TIDEGLASS_CONTENT_REPORT={output/"observations.json"}']
with (output/'test.jsonl').open('w')as log:completed=subprocess.run(command,cwd=root/'game/mobile',stdout=log,stderr=subprocess.STDOUT)
after=inventory();write(output/'run.json',{'schema_version':1,'command':command,'condition':condition,'exit_code':completed.returncode,'source_before':before,'source_after':after,'output_hashes':{f:sha(output/f)for f in ['test.jsonl','observations.json']if(output/f).exists()}})
if completed.returncode:sys.exit(completed.returncode)
result=validate_run(output,load(stage/'expected-rows.json'));write(output/'verification.json',result);print(json.dumps(result))
