"""Check secret leakage, hash evidence and copy only deliverables into the Git repo."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT.parent/'mi-microservicio'/'actividad 3'
EXCLUDED={'tmp','.terraform','__pycache__','video-frames','video-frames-final','.env','.git'}


def publishable(path):
    rel=path.relative_to(ROOT)
    return path.is_file() and not any(p in EXCLUDED for p in rel.parts) and not (
        path.name.startswith('tmp-') or path.name=='experiment-run.log' or '.tfstate' in path.name or
        path.suffix=='.tfvars' or path.suffix=='.pyc')


paths=[p for p in ROOT.rglob('*') if publishable(p)]
secrets=[line.split('=',1)[1] for line in (ROOT/'.env').read_text().splitlines() if '=' in line]
leaks=[]
for p in paths:
    data=p.read_bytes()
    if any(secret.encode() in data for secret in secrets):
        leaks.append(p.relative_to(ROOT).as_posix())
if leaks:
    raise SystemExit('Secret found in publishable file(s): '+', '.join(leaks))
evidence=[p for p in paths if p.relative_to(ROOT).parts[0]=='evidencias' and p.name!='MANIFEST.sha256']
manifest=ROOT/'evidencias/MANIFEST.sha256'
manifest.write_text('\n'.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(ROOT).as_posix()
                              for p in sorted(evidence))+'\n',encoding='utf-8')
paths=[p for p in ROOT.rglob('*') if publishable(p)]
for p in paths:
    target=DEST/p.relative_to(ROOT)
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(p,target)
print(json.dumps({'published_files':len(paths),'evidence_files':len(evidence),
                  'secret_scan':'passed','destination':str(DEST)},indent=2))
