"""Content-addressed provenance for research runs (including untracked research)."""
from __future__ import annotations

import datetime
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def command(*args):
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def provenance(directory, specification):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    paths = sorted(set(ROOT.glob('economy/**/*.py')) | set(ROOT.glob('tools/buying_research/*.py'))
                   | set(ROOT.glob('tests/py/test_buying*.py')) | set(ROOT.glob('catalogs/midbridge-4259-recursive/*.json'))
                   | {ROOT/'economy/core/catalog.json'})
    hashes = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    identity = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
    patch = subprocess.check_output(['git', 'diff', '--binary', 'HEAD'], cwd=ROOT)
    (directory/'starting.patch').write_bytes(patch)
    # A self-contained source snapshot also preserves untracked experimental code.
    import tarfile
    with tarfile.open(directory/'source.tar.gz', 'w:gz') as archive:
        for p in paths:
            archive.add(p, arcname=str(p.relative_to(ROOT)))
    import numpy, numba
    manifest = dict(schema=1, createdUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    commit=command('git','rev-parse','HEAD'), branch=command('git','branch','--show-current'),
                    startingStatus=command('git','status','--short'), sourceIdentity=identity,
                    sourceHashes=hashes, patchSHA256=hashlib.sha256(patch).hexdigest(),
                    python=sys.version, executable=sys.executable, numpy=numpy.__version__, numba=numba.__version__,
                    platform=platform.platform(), machine=platform.machine(),
                    processor=command('sysctl','-n','machdep.cpu.brand_string'),
                    memoryBytes=int(command('sysctl','-n','hw.memsize')),
                    command=sys.argv, specification=specification, status='running')
    (directory/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return manifest
