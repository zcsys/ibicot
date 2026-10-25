"""Independent PNG inspection and isolated deterministic renderer replay."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
AUTHOR = ROOT / 'release/store/google-icon-format-20261023T034820.052804Z'
CREATIVE = ROOT / 'release/store/creative'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def png(path):
    raw = path.read_bytes()
    assert raw[:8] == b'\x89PNG\r\n\x1a\n'
    assert raw[12:16] == b'IHDR' and struct.unpack('>I', raw[8:12])[0] == 13
    width, height, depth, color, compression, filtering, interlace = struct.unpack('>IIBBBBB', raw[16:29])
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        alpha = image.getchannel('A').getextrema() if image.mode == 'RGBA' else None
        result = dict(width=width, height=height, bit_depth=depth, color_type=color,
                      mode=image.mode, bytes=len(raw), alpha_range=alpha, sha256=sha(path))
    return result


before = AUTHOR / 'before/release/store/creative'
icon = png(CREATIVE / 'google-icon-512.png')
old_icon = png(before / 'google-icon-512.png')
feature = png(CREATIVE / 'google-feature-1024x500.png')
assert (icon['width'], icon['height'], icon['bit_depth'], icon['color_type'], icon['mode']) == (512, 512, 8, 6, 'RGBA')
assert icon['bytes'] < 1024 * 1024 and icon['alpha_range'] == (255, 255)
assert (old_icon['bit_depth'], old_icon['color_type'], old_icon['mode']) == (8, 2, 'RGB')
assert (feature['width'], feature['height'], feature['bit_depth'], feature['color_type'], feature['mode']) == (1024, 500, 8, 2, 'RGB')
with Image.open(before / 'google-icon-512.png') as old, Image.open(CREATIVE / 'google-icon-512.png') as new:
    assert old.convert('RGB').tobytes() == new.convert('RGB').tobytes()
for name in ['google-feature-1024x500.png', 'feature-graphic.svg']:
    assert (before / name).read_bytes() == (CREATIVE / name).read_bytes()
old_manifest = json.loads((before / 'provenance.json').read_text())
manifest = json.loads((CREATIVE / 'provenance.json').read_text())
for name, digest in manifest['source_sha256'].items():
    path = Path(name) if Path(name).is_absolute() else ROOT / name
    assert sha(path) == digest, name
    if name != 'tool/render_store_creative.py':
        assert old_manifest['source_sha256'][name] == digest, name
for name, row in manifest['outputs'].items():
    actual = png(CREATIVE / name)
    for key in ['width', 'height', 'mode', 'bytes', 'sha256']:
        assert row[key] == actual[key], (name, key)

with tempfile.TemporaryDirectory(prefix='tideglass-icon-review-') as directory:
    workspace = Path(directory)
    for name in ['tool/render_store_creative.py', 'tool/generate_native_icons.py', 'game/client/art/app-icon.svg']:
        target = workspace / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
    command = [sys.executable, str(workspace / 'tool/render_store_creative.py')]
    run = subprocess.run(command, cwd=workspace, capture_output=True, text=True)
    (HERE / 'renderer.log').write_text(run.stdout + run.stderr)
    assert run.returncode == 0
    reproduced = {}
    for name in ['google-icon-512.png', 'google-feature-1024x500.png', 'feature-graphic.svg', 'provenance.json']:
        result = workspace / 'release/store/creative' / name
        assert result.read_bytes() == (CREATIVE / name).read_bytes(), name
        reproduced[name] = sha(result)
        (HERE / 'reproduced').mkdir(exist_ok=True)
        shutil.copy2(result, HERE / 'reproduced' / name)
    (HERE / 'renderer-command.json').write_text(json.dumps({'command': command, 'exit_code': run.returncode, 'workspace_disposable': True}, indent=2) + '\n')

pins = json.loads((HERE / 'inputs-before.json').read_text())
assert all(sha(ROOT / name) == digest for name, digest in pins.items())
report = dict(reviewer='/root/native_verifier', inspected_utc=datetime.now(timezone.utc).isoformat(),
              status='encoding-correction-independently-verified', icon=icon, prior_icon=old_icon,
              feature=feature, all_262144_rgb_pixels_identical=True,
              alpha_all_opaque=True, feature_png_and_svg_byte_identical=True,
              geometry_and_fonts_pins_unchanged=True, live_inputs_unchanged=True,
              isolated_reproduction_sha256=reproduced,
              official_reference='https://support.google.com/googleplay/android-developer/answer/9866151?hl=en',
              official_reference_inspected_utc_date='2026-10-23',
              flutter_run=False, native_device_touched=False,
              original_work_item_accepted=False, platform_ingestion_verified=False)
(HERE / 'inspection.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
