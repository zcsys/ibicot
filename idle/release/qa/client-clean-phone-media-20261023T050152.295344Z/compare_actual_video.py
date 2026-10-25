"""Analyze decoded source and output pixels in memory; do not write altered media."""
from pathlib import Path
from PIL import Image,ImageChops,ImageOps,ImageStat
import json,hashlib
ROOT=Path('/Users/csys/Desktop/ibicot/idle');OUT=Path(__file__).resolve().parent
MEDIA=ROOT/'release/store/media-3b00-phone-clean-20261023T045548.384747Z'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def js(p):return json.loads(p.read_text())
def mae(a,b):return sum(ImageStat.Stat(ImageChops.difference(a,b)).mean)/3
preview=js(OUT/'preview-decoded/metadata.json'); rootpreview=js(MEDIA/'preview-inspection/metadata.json')
assert preview==rootpreview
assert preview['decoded_video_frames']==570 and preview['duration_seconds']==19
assert [preview['display_width'],preview['display_height']]==[886,1920]
assert preview['audio_track_count']==0 and preview['codec_fourcc']==['avc1']
assert abs(preview['min_frame_gap_seconds']-1/30)<1e-10 and abs(preview['max_frame_gap_seconds']-1/30)<1e-10
assert preview['sample_read_complete'] and abs(preview['last_frame_seconds']-569/30)<1e-10
source=js(OUT/'source-mapped-frames/metadata.json'); rows=[]
for i in range(5):
 a=OUT/f'source-mapped-frames/source-frame-{i}.png';b=OUT/f'preview-decoded/frame-{i}.png'
 s=Image.open(a).convert('RGB');d=Image.open(b).convert('RGB')
 assert s.size==(1206,2622) and d.size==(886,1920)
 factor=min(d.width/s.width,d.height/s.height);px=(d.width-s.width*factor)/2;py=(d.height-s.height*factor)/2
 ref=s.transform(d.size,Image.Transform.AFFINE,(1/factor,0,-px/factor,0,1/factor,-py/factor),resample=Image.Resampling.BICUBIC,fillcolor=(5,15,26))
 assert abs(source['frames'][i]['requested_source_seconds']-(preview['frames'][i]['actual_seconds']+0.5))<1e-10
 rows.append({'frame':i,'source_request':source['frames'][i]['requested_source_seconds'],'actual_source_held_frame':source['frames'][i]['actual_source_seconds'],'actual_preview_time':preview['frames'][i]['actual_seconds'],'scale':factor,'padding':[px,py],'full_frame_aspect_fit_MAE':mae(ref,d),'horizontal_mirror_control_MAE':mae(ImageOps.mirror(ref),d),'vertical_flip_control_MAE':mae(ImageOps.flip(ref),d),'source_frame_sha256':sha(a),'output_frame_sha256':sha(b)})
baseline=js(ROOT/'release/store/capture-overlay-repair-20261023T044221.198274Z/baseline.json')
old=baseline['old_draft_and_raw_sha256']
for name,digest in old.items():assert sha(ROOT/name)==digest,name
# Reuse the independently compiled reviewed inspector, verifying its original sealed identity.
prior=ROOT/'release/qa/client-preview-tool-20261023T032106.818906Z'; pv=js(prior/'verification.json')
assert sha(prior/'inspect_preview')==pv['sha256']['inspect_preview']
assert sha(prior/'inspect_preview.swift')==sha(ROOT/'release/store/tools/inspect_preview.swift')
result={'actual_video_metadata':preview,'mapped_source_comparisons':rows,'comparison_scope':'Five actual output frames versus corresponding decoded source time at +0.5 seconds. In-memory aspect fit only; no source/output pixels rewritten. Compression and color/sampling differences expected; no pixel identity claim.','prior_failed_draft_and_raw_preserved':old,'reused_inspector_sha256':sha(prior/'inspect_preview'),'reused_inspector_source_sha256':sha(prior/'inspect_preview.swift'),'actual_source_probe_sha256':sha(OUT/'actual_source_probe.swift'),'source_probe_binary_sha256':sha(OUT/'actual_source_probe'),'store_submission_approved':False,'audio_conformance_approved':False,'bitrate_conformance_approved':False}
(OUT/'actual-video-analysis.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'compared_frames':len(rows),'old_evidence_files_unchanged':len(old),'rows':rows},indent=2))
