#!/usr/bin/env python3
"""Read-only exact-export font and notice inventory; no full-font claim for subsets."""
import gzip
import hashlib
import json
import pathlib
import sys
import zipfile

ROOT = pathlib.Path('/Users/csys/Desktop/ibicot/idle')
CANDIDATE = ROOT / '.tooling/build-candidates/20261023T040445.261666Z-3b00cc8f7122'
OUTPUT = pathlib.Path(__file__).resolve().parent / 'packaged-font-evidence'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    OUTPUT.mkdir(exist_ok=False)
    manifest_bytes = (CANDIDATE / 'manifest.json').read_bytes()
    manifest = json.loads(manifest_bytes)
    relative = 'game/mobile/assets/licenses/MaterialIcons_LICENSE.txt'
    source = (CANDIDATE / 'source' / relative).read_bytes()
    assert sha(source) == manifest['source_sha256'][relative]
    sdk_font_path = ROOT / '.tooling/flutter/bin/cache/artifacts/material_fonts/MaterialIcons-Regular.otf'
    sdk_font = sdk_font_path.read_bytes()
    (OUTPUT / 'source-MaterialIcons_LICENSE.txt').write_bytes(source)
    records = []
    reports = {}
    for arg in sys.argv[1:]:
        path = pathlib.Path(arg)
        raw = path.read_bytes()
        report = json.loads(raw)
        reports[str(path)] = sha(raw)
        assert report['candidate_fingerprint'] == manifest['source_fingerprint']
        for platform, result in report['results'].items():
            assert result['build_succeeded'] and result['exit_code'] == 0
            artifact = ROOT / result['artifact']
            artifact_bytes = artifact.read_bytes()
            assert sha(artifact_bytes) == result['artifact_sha256']
            row = {'platform': platform, 'mode': report['mode'], 'artifact': str(artifact),
                   'artifact_sha256': sha(artifact_bytes), 'members': []}
            prefix = platform + '-' + report['mode']
            with zipfile.ZipFile(artifact) as archive:
                names = [n for n in archive.namelist() if '__MACOSX/' not in n]
                license_names = [n for n in names if n.endswith('/assets/licenses/MaterialIcons_LICENSE.txt')]
                font_names = [n for n in names if n.endswith('/fonts/MaterialIcons-Regular.otf')]
                notice_names = [n for n in names if n.endswith(('/NOTICES', '/NOTICES.Z'))]
                assert len(license_names) == 1 and len(font_names) == 1 and len(notice_names) == 1
                for name in license_names + font_names + notice_names:
                    data = archive.read(name)
                    kind = 'license' if name in license_names else 'font' if name in font_names else 'notices'
                    dest = prefix + '-' + pathlib.PurePosixPath(name).name
                    (OUTPUT / dest).write_bytes(data)
                    entry = {'member': name, 'kind': kind, 'bytes': len(data), 'sha256': sha(data), 'raw_copy': dest}
                    if kind == 'license':
                        assert data == source
                        entry['equals_frozen_explicit_license'] = True
                    elif kind == 'font':
                        entry['equals_full_pinned_sdk_font'] = data == sdk_font
                        entry['scope'] = 'Exact packaged bytes; release tree-shaken subset may differ from full SDK font'
                        assert len(data) > 0
                    else:
                        decoded = gzip.decompress(data) if name.endswith('.Z') else data
                        (OUTPUT / (prefix + '-NOTICES.txt')).write_bytes(decoded)
                        text = decoded.decode('utf-8')
                        entry.update(decoded_sha256=sha(decoded), decoded_bytes=len(decoded),
                                     mentions_material_icons='Material Icons' in text,
                                     mentions_apache='Apache License' in text)
                    row['members'].append(entry)
            records.append(row)
    assert len(records) == 5
    assert sha((CANDIDATE / 'manifest.json').read_bytes()) == sha(manifest_bytes)
    assert sdk_font_path.read_bytes() == sdk_font
    for arg, pin in reports.items():
        assert sha(pathlib.Path(arg).read_bytes()) == pin
    for row in records:
        assert sha(pathlib.Path(row['artifact']).read_bytes()) == row['artifact_sha256']
    out = {'candidate_fingerprint': manifest['source_fingerprint'], 'manifest_sha256': sha(manifest_bytes),
           'source_license_sha256': sha(source), 'full_sdk_font_sha256': sha(sdk_font),
           'reports': reports, 'artifacts': records, 'release_acceptance': False,
           'scope': 'Exact export asset inclusion, license bytes and font bytes; not store approval or legal certification'}
    (OUTPUT / 'verification.json').write_text(json.dumps(out, indent=2) + '\n')
    print(json.dumps({'exports': len(records), 'source_license_sha256': sha(source)}))


if __name__ == '__main__':
    main()
