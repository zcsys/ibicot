"""Validate and hash the completed research delivery without changing evidence."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlsplit


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def audit(repo, root, output):
    def read(name):
        return json.loads((root / name).read_text())

    proof = read('baseline-measurement-replay-verification.json')
    evidence = read('final-evidence-audit.json')
    study = read('final-study/study.json')
    comparison = read('final-comparisons.json')
    stress = read('final-stress-phases.json')
    plan = read('all-delivery-evidence-plan.json')
    assert proof['status'] == 'pass' and not proof['differences']
    assert evidence['status'] == 'pass' and not evidence['errors']
    assert evidence['runs'] == len(plan) == len({x['id'] for x in plan}) == 93
    assert study['status'] == 'complete' and not study['pending']
    assert len(study['runs']) == 82
    assert comparison['diagnosticCoverage'] == {'runs': 82, 'exactStudyMatch': True}
    assert stress['status'] == 'complete' and len(stress['runs']) == 25 and not stress['pending']
    assert len(comparison['performance']) == 10 and len(comparison['performanceGates']) == 5
    assert not comparison['invariants']['gateFailures']
    assert comparison['invariants']['baselineSupplement']['gate']
    assert read('final-proof-queue-results.json')['status'] == 'complete'
    assert read('final-preference-event-audit.json')['status'] == 'pass'
    for job in study['runs']:
        inv = job['invariants']
        assert inv['minCash'] >= 0 and inv['minStock'] >= 0, job['id']
    runtime_catalog = [f'catalogs/midbridge-4259-recursive/{x}.json'
                       for x in ('catalog', 'naming', 'starting-selection', 'consumption-calibration')]
    protected = ['economy', 'web'] + runtime_catalog
    diff = subprocess.check_output(['git', 'diff', '--name-only', 'HEAD', '--', *protected],
                                   cwd=repo, text=True)
    assert not diff.strip(), 'Production/runtime-catalog changes: ' + diff

    docs = sorted((repo / 'docs').glob('buying-behavior-*.md'))
    assert len(docs) == 8
    report = (repo / 'docs/buying-behavior-research-report.md').read_text()
    closing = report.split('## Final decision table\n')
    assert len(closing) == 2 and '\n## ' not in closing[1]
    assert len([x for x in closing[1].splitlines() if x.startswith('| ')]) == 22
    assert 'Working report' not in report and 'research task remains unfinished' not in report
    assert 'reject historical R1' in report
    audit_text = (repo / 'docs/buying-behavior-requirements-audit.md').read_text()
    assert 'Status: **complete' in audit_text
    assert '| In progress |' not in audit_text and '| Incomplete' not in audit_text
    files = set(docs + [repo / 'README.md'])
    code = sorted((repo / 'tools/buying_research').glob('*.py'))
    code += sorted((repo / 'tests/py').glob('test_buying*.py'))
    for file in code:
        compile(file.read_text(), str(file), 'exec')
    files.update(code)
    local_links = 0
    for document in docs:
        for target in re.findall(r'\]\(([^\s)]+)\)', document.read_text()):
            target = target.strip('<>')
            parsed = urlsplit(target)
            if parsed.scheme or not parsed.path:
                continue
            path = (document.parent / unquote(parsed.path)).resolve()
            local_links += 1
            assert path == output or path.exists(), (document, target)
            if path == output:
                continue
            if path.is_dir():
                files.update(x for x in path.rglob('*') if x.is_file())
            else:
                files.add(path)
            if parsed.fragment and path.suffix == '.md':
                headings = re.findall(r'^#+\s+(.+)$', path.read_text(), re.M)
                slugs = {re.sub(r'[^\w\- ]', '', x.lower()).replace(' ', '-') for x in headings}
                assert unquote(parsed.fragment) in slugs, (document, target, 'missing anchor')
    # Hash every file in all 93 completed run directories, including raw product,
    # company, request and tick records, archives, patches and checkpoints.
    run_identities = []
    for job in plan:
        directory = root / job['id']
        manifest = json.loads((directory / 'manifest.json').read_text())
        assert manifest['status'] == 'complete', job['id']
        files.update(x for x in directory.rglob('*') if x.is_file())
        run_identities.append(dict(id=job['id'], sourceIdentity=manifest['sourceIdentity'],
                                   window=manifest['specification']['window']))
    # Preserve root-level plans, proofs, interim results and logs, plus final
    # aggregate evidence and figures. Dependency installations are not artifacts.
    files.update(x for x in root.iterdir() if x.is_file())
    for directory in [root/'final-study', root/'final-diagnostics', *root.glob('figures-*')]:
        files.update(x for x in directory.rglob('*') if x.is_file())
    files = sorted({x.resolve() for x in files if x.resolve() != output})
    # The auditor's own stdout log is still open; hash logs of completed work only.
    files = [x for x in files if x != output.with_suffix('.log')]
    print(json.dumps(dict(stage='checks_passed', localLinks=local_links,
                          pythonSources=len(code), filesToHash=len(files))), flush=True)
    hashes = {}
    total = 0
    for i, file in enumerate(files):
        before = file.stat()
        digest = sha(file)
        after = file.stat()
        assert (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns), file
        hashes[str(file.relative_to(repo))] = dict(bytes=after.st_size, sha256=digest)
        total += after.st_size
        if (i + 1) % 2000 == 0:
            print(json.dumps(dict(stage='hashing', files=i+1, bytes=total)), flush=True)
    return dict(status='pass', completedUTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        decision='Reject historical R1; retain production baseline with documented defects.',
        repository=str(repo), gitHead=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),
        productionAndRuntimeCatalogDiff=[], economicRuns=82, measurementReplays=1, timingProfiles=10,
        archiveAudit=evidence['status'], exactBaselineReplay=proof['status'],
        localLinksChecked=local_links, pythonSourcesSyntaxChecked=len(code),
        researchTests='20 passed; final-research-regression-tests.log',
        baselineTests='93 passed in baseline full discovery; curated launcher/JS results separately retained',
        runIdentities=run_identities, hashedFiles=len(hashes), hashedBytes=total, files=hashes,
        scope='Hashes cover all files in the 93 delivery-plan runs, delivered documents/code/tests, '
              'root-level evidence/plans/logs and linked/final aggregate/figure artifacts. '
              'The manifest itself, its still-open stdout log, dependency installations and unrelated '
              'workspace files are excluded. Research completion does not turn failed or unmeasured '
              'adoption requirements into passes.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists(), 'Preserve existing delivery manifests; select a new path.'
    result = audit(Path(__file__).resolve().parents[2], a.root.resolve(), a.output.resolve())
    with a.output.open('x') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print(json.dumps({k: result[k] for k in ('status','hashedFiles','hashedBytes','localLinksChecked')}))


if __name__ == '__main__':
    main()
