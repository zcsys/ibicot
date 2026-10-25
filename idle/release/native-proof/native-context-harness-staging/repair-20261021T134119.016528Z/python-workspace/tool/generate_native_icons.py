#!/usr/bin/env python3
"""Render original Tideglass vector geometry into the native icon catalogs."""
from pathlib import Path
import json
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
ART = ROOT / 'game/client/art'
ART.mkdir(parents=True, exist_ok=True)
# Original authored geometry, adapted from the project's lighthouse silhouette.
SHAPES = [
 ('rect', [0, 0, 1024, 1024], '#071923'),
 ('ellipse', [146, 144, 878, 876], '#0D273A'),
 ('polygon', [(460, 351), (834, 174), (834, 548), (460, 402)], '#173B4A'),
 ('polygon', [(194, 813), (326, 705), (496, 697), (668, 817)], '#23434A'),
 ('polygon', [(368, 430), (482, 430), (522, 748), (426, 808), (326, 748)], '#DEE1C7'),
 ('polygon', [(438, 430), (482, 430), (522, 748), (426, 808), (426, 470)], '#709C9C'),
 ('rect', [349, 342, 501, 437], '#244D59'),
 ('rect', [370, 352, 422, 414], '#F5CC87'),
 ('rect', [438, 352, 480, 414], '#F5CC87'),
 ('polygon', [(330, 341), (426, 268), (520, 341)], '#557F85'),
 ('ellipse', [416, 258, 436, 278], '#F5CC87'),
 ('rect', [329, 425, 520, 451], '#244D59'),
 ('rect', [388, 511, 412, 550], '#244D59'),
 ('rect', [379, 604, 407, 643], '#244D59'),
 ('ellipse', [384, 690, 432, 738], '#244D59'),
 ('rect', [384, 716, 432, 771], '#244D59'),
 ('polygon', [(734, 206), (752, 249), (795, 267), (752, 285), (734, 328), (716, 285), (673, 267), (716, 249)], '#F5CC87'),
 ('polygon', [(231, 858), (366, 846), (501, 858), (635, 846), (792, 858), (792, 869), (635, 858), (501, 870), (366, 858), (231, 870)], '#709C9C'),
]
svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">']
image = Image.new('RGB', (4096, 4096))
draw = ImageDraw.Draw(image)
for kind, points, color in SHAPES:
    if kind == 'polygon':
        svg.append('<polygon points="' + ' '.join(f'{x},{y}' for x,y in points) + f'" fill="{color}"/>')
        draw.polygon([(x*4,y*4) for x,y in points], fill=color)
    elif kind == 'rect':
        x,y,r,b = points
        svg.append(f'<rect x="{x}" y="{y}" width="{r-x}" height="{b-y}" fill="{color}"/>')
        draw.rectangle([p*4 for p in points], fill=color)
    else:
        x,y,r,b = points
        svg.append(f'<ellipse cx="{(x+r)/2}" cy="{(y+b)/2}" rx="{(r-x)/2}" ry="{(b-y)/2}" fill="{color}"/>')
        draw.ellipse([p*4 for p in points], fill=color)
svg.append('</svg>')
(ART / 'app-icon.svg').write_text('\n'.join(svg) + '\n')
image.resize((1024,1024), Image.Resampling.LANCZOS).save(ART / 'app-icon-1024.png')
for platform in ['ios', 'macos']:
    catalog = ROOT / f'game/mobile/{platform}/Runner/Assets.xcassets/AppIcon.appiconset'
    for entry in json.loads((catalog / 'Contents.json').read_text())['images']:
        size = round(float(entry['size'].split('x')[0]) * float(entry['scale'].removesuffix('x')))
        image.resize((size,size), Image.Resampling.LANCZOS).save(catalog / entry['filename'])
for density,size in [('mdpi',48),('hdpi',72),('xhdpi',96),('xxhdpi',144),('xxxhdpi',192)]:
    target = ROOT / f'game/mobile/android/app/src/main/res/mipmap-{density}/ic_launcher.png'
    image.resize((size,size), Image.Resampling.LANCZOS).save(target)
for scale in (1, 2, 3):
    suffix = '' if scale == 1 else f'@{scale}x'
    image.resize((160*scale,160*scale), Image.Resampling.LANCZOS).save(ROOT / f'game/mobile/ios/Runner/Assets.xcassets/LaunchImage.imageset/LaunchImage{suffix}.png')
(ART / 'app-icon-provenance.json').write_text(json.dumps({
    'asset': 'app-icon.svg', 'type': 'original authored vector',
    'source': 'tool/generate_native_icons.py; lighthouse silhouette and palette adapted from game/mobile/lib/harbor_art.dart',
    'third_party_art': False, 'render_library': 'Pillow', 'opaque_background': True,
    'note': 'No text; native icon masks are applied by each operating system. Requires owner visual approval before public distribution.'
}, indent=2)+'\n')
print('Rendered original vector and all iOS, Android and macOS icon sizes.')
