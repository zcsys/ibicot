#!/usr/bin/env python3
"""Read exact exported native artifacts; this is inventory, not traffic approval."""
import argparse
import hashlib
import json
import plistlib
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path, PurePosixPath


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def safe_relative(name):
    p = PurePosixPath(name)
    require(not p.is_absolute() and '..' not in p.parts and '\\' not in name,
            'unsafe artifact member/path')
    return p


def command(argv, output):
    result = subprocess.run(argv, capture_output=True, timeout=60)
    output.write_bytes(result.stdout)
    output.with_suffix(output.suffix + '.stderr').write_bytes(result.stderr)
    require(result.returncode == 0, f'inventory command failed: {argv[0]}')
    return {'argv': argv, 'exit_code': result.returncode,
            'stdout_sha256': sha(output),
            'stderr_sha256': sha(output.with_suffix(output.suffix + '.stderr'))}


def selected_members(archive):
    """Never extract arbitrary archive paths or executable payloads."""
    seen = set()
    result = []
    total = 0
    for info in archive.infolist():
        safe_relative(info.filename)
        require(info.filename not in seen, 'duplicate archive member')
        seen.add(info.filename)
        name = info.filename
        selected = (name.endswith('/PrivacyInfo.xcprivacy') or
                    name.endswith('/Info.plist') or name.endswith('.properties') or
                    ('META-INF/' in name and name.endswith('.version')))
        if not selected:
            continue
        require(info.file_size <= 1024 * 1024, 'oversized inventory member')
        total += info.file_size
        require(total <= 32 * 1024 * 1024, 'oversized inventory collection')
        data = archive.read(info)
        entry = {'member': name, 'bytes': len(data),
                 'sha256': hashlib.sha256(data).hexdigest()}
        if name.endswith(('.plist', '.xcprivacy')):
            value = plistlib.loads(data)
            require(type(value) is dict, 'plist root is not a dictionary')
            entry['plist'] = value
        else:
            entry['text'] = data.decode('utf-8')
        result.append((entry, data))
    return result


def android_summary(xml):
    document = ET.fromstring(xml)
    require(document.tag == 'manifest', 'not an Android manifest')
    ns = '{http://schemas.android.com/apk/res/android}'
    app = document.find('application')
    require(app is not None, 'missing Android application')
    return {
        'package': document.get('package'),
        'version_code': document.get(ns + 'versionCode'),
        'version_name': document.get(ns + 'versionName'),
        'sdk': [dict(x.attrib) for x in document.findall('uses-sdk')],
        'permissions': [dict(x.attrib) for x in document
                        if x.tag.startswith('uses-permission')],
        'application_attributes': dict(app.attrib),
        'components': [{'kind': x.tag, 'attributes': dict(x.attrib),
                        'metadata': [dict(y.attrib) for y in x.findall('meta-data')]}
                       for x in app if x.tag in
                       ['provider', 'service', 'receiver', 'activity', 'meta-data']],
    }


def inspect(root, candidate, reports, output, java, bundletool, aapt2):
    manifest = json.loads((candidate / 'manifest.json').read_text())
    fingerprint = manifest['source_fingerprint']
    pins = manifest['source_sha256']
    for rel, digest in pins.items():
        safe_relative(rel)
        require(sha(candidate / 'source' / rel) == digest, 'candidate source drift')
    require(hashlib.sha256(json.dumps(pins, sort_keys=True, separators=(',', ':'))
                           .encode()).hexdigest() == fingerprint,
            'candidate fingerprint mismatch')
    output.mkdir(parents=True, exist_ok=False)
    shutil.copy2(__file__, output / 'collector.py')
    results = []
    identities = set()
    for report_path in reports:
        report = json.loads(report_path.read_text())
        require(report['candidate_fingerprint'] == fingerprint,
                'different artifact candidate')
        require(Path(report['candidate_directory']).resolve() == candidate,
                'different candidate directory')
        require(report.get('source_snapshot_unchanged') is True and
                report.get('dependency_locks_unchanged') is True,
                'build source/locks not verified')
        mode = report['mode']
        for platform, build in report['results'].items():
            if platform not in ['ios', 'android', 'macos']:
                continue
            identity = (mode, platform)
            require(identity not in identities, 'duplicate platform/mode')
            identities.add(identity)
            require(build.get('build_succeeded') is True and
                    type(build.get('exit_code')) is int and build['exit_code'] == 0,
                    'unsuccessful native export')
            artifact = root / str(safe_relative(build['artifact']))
            require(sha(artifact) == build['artifact_sha256'] and
                    artifact.stat().st_size == build['artifact_bytes'],
                    'native artifact hash/size mismatch')
            dest = output / (platform + '-' + mode)
            dest.mkdir()
            with zipfile.ZipFile(artifact) as archive:
                members = selected_members(archive)
            inventory = []
            for i, (entry, data) in enumerate(members):
                file = dest / f'member-{i:03d}.bin'
                file.write_bytes(data)
                entry['raw_copy'] = str(file.relative_to(output))
                inventory.append(entry)
            record = {'platform': platform, 'mode': mode,
                      'artifact': str(artifact), 'artifact_sha256': sha(artifact),
                      'build_report': str(report_path),
                      'build_report_sha256': sha(report_path), 'members': inventory}
            if platform == 'android' and mode == 'release':
                xml = dest / 'packaged-manifest.xml'
                record['manifest_command'] = command(
                    [java, '-jar', str(bundletool), 'dump', 'manifest',
                     '--bundle=' + str(artifact), '--module=base'], xml)
                record['manifest_summary'] = android_summary(xml.read_bytes())
            elif platform == 'android':
                record['manifest_command'] = command(
                    [str(aapt2), 'dump', 'xmltree', str(artifact),
                     '--file', 'AndroidManifest.xml'], dest / 'packaged-manifest.txt')
                record['permissions_command'] = command(
                    [str(aapt2), 'dump', 'permissions', str(artifact)],
                    dest / 'permissions.txt')
            results.append(record)
    require(identities == {('debug', 'ios'), ('debug', 'android'),
                           ('debug', 'macos'), ('release', 'ios'),
                           ('release', 'android')}, 'incomplete five-export inventory')
    result = {'schema_version': 1, 'candidate_fingerprint': fingerprint,
              'candidate_manifest_sha256': sha(candidate / 'manifest.json'),
              'collector_sha256': sha(Path(__file__)),
              'tools': {'bundletool_sha256': sha(bundletool),
                        'aapt2_sha256': sha(aapt2), 'java': java},
              'artifacts': results, 'runtime_traffic_observed': False,
              'store_disclosure_approved': False, 'release_acceptance': False,
              'limitations': 'Packaged declarations and versions only. Apple plist '
              'inventory is not an Xcode-generated aggregate privacy report. '
              'Permissions/SDK presence does not establish actual data collection.'}
    (output / 'inventory.json').write_text(json.dumps(result, indent=2, default=str) + '\n')
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['root', 'candidate', 'output', 'bundletool', 'aapt2']:
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--report', type=Path, action='append', required=True)
    p.add_argument('--java', required=True)
    a = p.parse_args()
    value = inspect(a.root.resolve(), a.candidate.resolve(),
                    [v.resolve() for v in a.report], a.output.resolve(), a.java,
                    a.bundletool.resolve(), a.aapt2.resolve())
    print(json.dumps({'candidate': value['candidate_fingerprint'],
                      'artifacts': len(value['artifacts']),
                      'runtime_claim': False, 'release_acceptance': False}))
