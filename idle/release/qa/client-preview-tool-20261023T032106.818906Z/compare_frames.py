"""Pixel analysis only: compare decoded frames with full source-frame mappings.
No generated gameplay or replacement media files are written.
"""
from pathlib import Path
from PIL import Image, ImageChops, ImageOps, ImageStat
import json, hashlib

HERE = Path(__file__).resolve().parent
def mae(a,b): return sum(ImageStat.Stat(ImageChops.difference(a,b)).mean)/3
rows=[]
for mode, srcdir, dstdir, infofile in [
    ('portrait','source-frames','decoded','historical-export.stdout'),
    ('metadata-quarter-turn-control','rotated-source-frames','rotated-decoded','rotated-export.stdout')]:
    if not (HERE/srcdir/'metadata.json').is_file(): continue
    info=json.loads((HERE/infofile).read_text())
    sources=json.loads((HERE/srcdir/'metadata.json').read_text())
    outputs=json.loads((HERE/dstdir/'metadata.json').read_text())
    for i in range(5):
        srcpath=HERE/srcdir/f'source-{i}.png';dstpath=HERE/dstdir/f'frame-{i}.png'
        source=Image.open(srcpath).convert('RGB');output=Image.open(dstpath).convert('RGB')
        scale=min(output.width/source.width,output.height/source.height)
        px=(output.width-source.width*scale)/2;py=(output.height-source.height*scale)/2
        inverse=(1/scale,0,-px/scale,0,1/scale,-py/scale)
        reference=source.transform(output.size,Image.Transform.AFFINE,inverse,resample=Image.Resampling.BICUBIC,fillcolor=(5,15,26))
        rows.append({'mode':mode,'frame':i,'source_file':str(srcpath.relative_to(HERE)),
            'source_sha256':hashlib.sha256(srcpath.read_bytes()).hexdigest(),
            'output_file':str(dstpath.relative_to(HERE)),'output_sha256':hashlib.sha256(dstpath.read_bytes()).hexdigest(),
            'source_requested_seconds':sources['samples'][i]['requested'],
            'source_actual_held_frame_seconds':sources['samples'][i]['actual'],
            'output_requested_seconds':outputs['frames'][i]['requested_seconds'],
            'output_actual_sample_seconds':outputs['frames'][i]['actual_seconds'],
            'source_size':source.size,'output_size':output.size,'aspect_fit_scale':scale,
            'computed_padding':[px,py],'reported_padding':[info['padding_x'],info['padding_y']],
            'mean_absolute_channel_error_0_to_255':mae(reference,output),
            'horizontal_mirror_control_error':mae(ImageOps.mirror(reference),output),
            'vertical_flip_control_error':mae(ImageOps.flip(reference),output),
            'meaning':'Independent full-frame affine sampling versus compressed output. Small sampling/color/encoder differences expected; no pixel-identity or exhaustive visual approval claim.'})
(HERE/'frame-comparison.json').write_text(json.dumps(rows,indent=2)+'\n')
print(json.dumps([{'mode':r['mode'],'frame':r['frame'],'MAE':r['mean_absolute_channel_error_0_to_255'],
    'mirror_MAE':r['horizontal_mirror_control_error'],'flip_MAE':r['vertical_flip_control_error']} for r in rows],indent=2))
