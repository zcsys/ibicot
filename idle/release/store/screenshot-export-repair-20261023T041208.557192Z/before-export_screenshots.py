#!/usr/bin/env python3
"""Export opaque RGB PNGs without changing any captured UI pixel or dimension."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from PIL import Image


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def export(capture, output, candidate):
    require(bool(re.fullmatch(r'[a-f0-9]{64}', candidate)), 'Exact candidate fingerprint required')
    capture = capture.resolve()
    report_file, manifest_file = capture / 'verification.json', capture / 'capture-manifest.json'
    report = json.loads(report_file.read_text())
    manifest = json.loads(manifest_file.read_text())
    require(report.get('passed') is True and report.get('scenario') == 'capture-gallery', 'Successful native gallery required')
    require(manifest.get('native_verification_passed') is True, 'Capture is not native-qualified')
    require(report.get('candidate_fingerprint') == manifest.get('candidate_fingerprint') == candidate,
            'Capture belongs to a different candidate')
    require(report.get('evidence_sha256', {}).get('capture-manifest.json') == digest(manifest_file),
            'Manifest differs from native verification')
    for key, other in [('device', 'device'), ('device_label', 'label'), ('platform', 'platform'), ('run_id', 'run_id')]:
        require(manifest.get(key) == report.get(other), 'Capture identity mismatch: ' + key)
    require(manifest.get('harness_sha256') == report.get('harness_sha256', {}).get('harness.dart'),
            'Capture harness mismatch')
    rows = manifest.get('screenshots')
    require(isinstance(rows, list) and len(rows) == 4, 'Expected four declared native screens')
    before = {report_file: digest(report_file), manifest_file: digest(manifest_file)}
    decoded = []
    for row in rows:
        name = row['file']
        require(isinstance(name, str) and re.fullmatch(r'[A-Za-z0-9_-]+\.png', name), 'Unsafe screenshot filename')
        source = capture / name
        require(source.resolve().parent == capture and source.is_file(), 'Screenshot is outside capture directory')
        require(source.stat().st_size == row['bytes'] and source.stat().st_size <= 20 * 1024 * 1024,
                'Unexpected screenshot size')
        before[source] = digest(source)
        require(before[source] == row['sha256'] == report.get('evidence_sha256', {}).get(name),
                'Screenshot differs from native evidence')
        with Image.open(source) as image:
            require(image.format == 'PNG' and image.mode in {'RGB', 'RGBA'}, 'Expected actual RGB/RGBA PNG')
            require(image.size == (row['width'], row['height']) and image.width * image.height <= 16_000_000,
                    'Unexpected captured dimensions')
            if image.mode == 'RGBA':
                require(image.getchannel('A').getextrema() == (255, 255),
                        'Refusing to composite a transparent pixel')
            decoded.append((name, image.convert('RGB')))
    require(len({name for name, _ in decoded}) == len(decoded), 'Duplicate screenshot filename')
    output.mkdir(parents=True, exist_ok=False)
    exports = []
    for name, image in decoded:
        path = output / name
        with path.open('xb') as handle:
            image.save(handle, format='PNG')
        with Image.open(path) as actual:
            require(actual.mode == 'RGB' and actual.size == image.size and actual.tobytes() == image.tobytes(),
                    'Export changed captured RGB pixels')
        exports.append({'file': name, 'sha256': digest(path), 'width': image.width, 'height': image.height,
                        'bytes': path.stat().st_size, 'mode': 'RGB', 'rgb_pixels_unchanged': True})
    require(all(digest(path) == value for path, value in before.items()), 'Native source changed during export')
    result = {'candidate_fingerprint': candidate, 'capture_directory': str(capture),
              'native_verification_sha256': before[report_file], 'capture_manifest_sha256': before[manifest_file],
              'tool_sha256': digest(Path(__file__)), 'source_sha256': {path.name: value for path, value in before.items()},
              'exports': exports, 'operation': 'Remove an entirely opaque alpha channel; preserve every RGB pixel and dimension.',
              'crop_scale_composite_or_invented_ui': False, 'source_unchanged': True,
              'store_dimensions_qualified': False, 'visual_selection_qualified': False,
              'public_submission': False}
    (output / 'export-manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--candidate', required=True)
    args = parser.parse_args()
    print(json.dumps(export(args.capture, args.output, args.candidate), indent=2))
