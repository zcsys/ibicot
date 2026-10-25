#!/usr/bin/env python3
"""Render original code-authored brand geometry for local store review."""
from pathlib import Path
import ast
import hashlib
import html
import json
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'release/store/creative'
OUT.mkdir(parents=True, exist_ok=True)
generator = ROOT / 'tool/generate_native_icons.py'
# Read the declared geometry without importing the native-catalog writer.
tree = ast.parse(generator.read_text())
shapes = next(ast.literal_eval(node.value) for node in tree.body
              if isinstance(node, ast.Assign)
              and any(isinstance(t, ast.Name) and t.id == 'SHAPES'
                      for t in node.targets))


def geometry(draw, scale, offset=(0, 0)):
    ox, oy = offset
    for kind, points, color in shapes:
        if kind == 'polygon':
            draw.polygon([(ox + x * scale, oy + y * scale)
                          for x, y in points], fill=color)
        else:
            coords = [ox + points[0] * scale, oy + points[1] * scale,
                      ox + points[2] * scale, oy + points[3] * scale]
            getattr(draw, 'rectangle' if kind == 'rect' else 'ellipse')(
                coords, fill=color)


icon = Image.new('RGB', (2048, 2048))
geometry(ImageDraw.Draw(icon), 2)
icon.resize((512, 512), Image.Resampling.LANCZOS).save(OUT / 'google-icon-512.png')

scale = 4
image = Image.new('RGB', (1024 * scale, 500 * scale), '#071923')
draw = ImageDraw.Draw(image)
geometry(draw, .4 * scale, (32 * scale, 42 * scale))
font_path = Path('/System/Library/Fonts/Supplemental/Georgia Bold.ttf')
caption_path = Path('/System/Library/Fonts/Supplemental/Arial.ttf')
if not font_path.is_file() or not caption_path.is_file():
    raise SystemExit('The recorded system fonts are unavailable; do not silently substitute.')
text = [('TIDEGLASS', 448, 159, 57, '#F5CC87', font_path, 'Georgia', 'bold'),
        ('A harbor of small lights', 451, 248, 27, '#DEE1C7', caption_path, 'Arial', 'normal'),
        ('Restore. Rechart. Discover.', 452, 300, 21, '#89ACAE', caption_path, 'Arial', 'normal')]
for value, x, y, size, color, font, family, weight in text:
    face = ImageFont.truetype(str(font), size * scale)
    bounds = draw.textbbox((x * scale, y * scale), value, font=face, anchor='lt')
    if bounds[2] > 984 * scale or bounds[3] > 450 * scale:
        raise SystemExit(f'Text exceeds creative safe area: {value}')
    draw.text((x * scale, y * scale), value, font=face, fill=color, anchor='lt')
draw.line([(452 * scale, 351 * scale), (858 * scale, 351 * scale)],
          fill='#244D59', width=2 * scale)
image.resize((1024, 500), Image.Resampling.LANCZOS).save(OUT / 'google-feature-1024x500.png')

icon_svg = (ROOT / 'game/client/art/app-icon.svg').read_text()
inner = icon_svg.split('>', 1)[1].rsplit('</svg>', 1)[0]
svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="500" viewBox="0 0 1024 500">',
       '<title>Tideglass — A harbor of small lights</title>',
       '<rect width="1024" height="500" fill="#071923"/>',
       '<g transform="translate(32 42) scale(.4)">' + inner + '</g>']
for value, x, y, size, color, font, family, weight in text:
    svg.append(f'<text x="{x}" y="{y}" dominant-baseline="text-before-edge" '
               f'font-family="{family}" font-size="{size}" font-weight="{weight}" '
               f'fill="{color}">{html.escape(value)}</text>')
svg.extend(['<path d="M452 351H858" stroke="#244D59" stroke-width="2"/>', '</svg>'])
(OUT / 'feature-graphic.svg').write_text('\n'.join(svg) + '\n')
inputs = [generator, Path(__file__), ROOT / 'game/client/art/app-icon.svg', font_path, caption_path]
outputs = {}
for file in sorted(OUT.glob('*.png')):
    with Image.open(file) as rendered:
        outputs[file.name] = {'sha256': hashlib.sha256(file.read_bytes()).hexdigest(),
                             'width': rendered.width, 'height': rendered.height,
                             'mode': rendered.mode, 'bytes': file.stat().st_size}
assert outputs['google-icon-512.png']['bytes'] < 1024 * 1024
assert all(item['mode'] == 'RGB' for item in outputs.values())
manifest = {'status': 'authored_pending_independent_visual_review',
            'purpose': 'Local brand/store preparation; not a gameplay screenshot or published listing',
            'geometry': 'Original Tideglass lighthouse, reused from native icon source; no third-party artwork',
            'fonts': 'System Georgia Bold and Arial rendered into pixels; font files are not distributed',
            'renderer': 'Pillow, RGB, four-times oversampled feature graphic',
            'source_sha256': {str(p.relative_to(ROOT) if p.is_relative_to(ROOT) else p):
                              hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
            'outputs': outputs}
(OUT / 'provenance.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps(outputs, indent=2))
