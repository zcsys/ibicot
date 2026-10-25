from pathlib import Path
import hashlib,json,struct,sys
from PIL import Image,ImageChops,ImageStat
ROOT=Path('/Users/csys/Desktop/ibicot/idle');OUT=Path(__file__).resolve().parent/'tablet';RAW=ROOT/'release/native-proof/integration-ios-tablet-20261023T080707.958916Z';MEDIA=ROOT/'release/store/media-3b00-tablet-corrected-20261023T0811Z';CAND=ROOT/'.tooling/build-candidates/20261023T040445.261666Z-3b00cc8f7122'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def js(p):return json.loads(p.read_text())
v=js(RAW/'verification.json');m=js(CAND/'manifest.json');e=js(MEDIA/'screenshots/export-manifest.json');result=js(RAW/'result.json');r=js(RAW/'recording.json')
assert v['passed'] and not v['verification_errors'] and v['source_snapshot_unchanged'] and v['production_inputs_match_snapshot'] and not v['production_input_differences_after_run'] and not v['harness_source_differences_during_run']
assert v['candidate_fingerprint']==e['candidate_fingerprint']==m['source_fingerprint']=='3b00cc8f71222f35b60f18ee83a8bb3ba71e39aa5364222dbeb7f6d2a5c45c59'
for name,digest in v['evidence_sha256'].items():assert sha(RAW/name)==digest,name
for name,digest in e['source_sha256'].items():assert sha(RAW/name)==digest,name
assert sha(RAW/'verification.json')==e['native_verification_sha256']
assert v['native_process_stop']['exit_code']==0
assert result['actual_purchase_count_delta']==1 and result['automated_pointer_events_routed']>0
landmark=result['season_capture_landmark'];assert landmark['widget']=='SeasonScreen' and landmark['key']=='season-tab-0' and landmark['selected'] and landmark['route_is_current'] and landmark['primary_animation_status']=='completed' and landmark['secondary_animation_status']=='dismissed'
for n,digest in m['source_sha256'].items():assert sha(CAND/'source'/n)==digest,n
sys.path.insert(0,str(ROOT/'tool'));import verify_native
prod=verify_native.production_inputs(m['source_sha256'])
for n,digest in prod.items():assert sha(ROOT/n)==sha(CAND/'workspace'/n)==digest,n
preview=js(OUT/'preview-decoded/metadata.json');export=js(MEDIA/'preview-export.log');sample=js(OUT/'source-sampled/metadata.json')
assert preview['sample_read_complete'] and preview['decoded_video_frames']==570 and preview['duration_seconds']==19 and preview['display_width']==1200 and preview['display_height']==1600 and preview['audio_track_count']==0
assert abs(preview['last_frame_seconds']-569/30)<1e-9 and abs(preview['max_frame_gap_seconds']-1/30)<1e-9 and abs(preview['min_frame_gap_seconds']-1/30)<1e-9
assert export['source_start_seconds']==.5 and export['requested_duration_seconds']==19 and export['speed_multiplier']==1 and export['target_video_bits_per_second']==11000000 and export['padding_x']==export['padding_y']==0
comparisons=[]
for i,(o,s) in enumerate(zip(preview['frames'],sample['frames'],strict=True)):
 assert abs(s['requested_source_seconds']-o['actual_seconds']-.5)<1e-9
 with Image.open(OUT/'preview-decoded'/o['file']) as im:a=im.convert('RGB')
 with Image.open(OUT/'source-sampled'/s['file']) as im:b=im.convert('RGB').resize(a.size,Image.Resampling.LANCZOS)
 def mae(x,y):return sum(ImageStat.Stat(ImageChops.difference(x,y)).mean)/3
 observed=mae(a,b);horizontal=mae(a,b.transpose(Image.Transpose.FLIP_LEFT_RIGHT));vertical=mae(a,b.transpose(Image.Transpose.FLIP_TOP_BOTTOM));assert observed<horizontal and observed<vertical
 comparisons.append({'index':i,'output_actual_seconds':o['actual_seconds'],'requested_raw_seconds':s['requested_source_seconds'],'actual_raw_seconds':s['actual_source_seconds'],'full_frame_scale':1200/2064,'padding':[0,0],'mean_absolute_channel_error':observed,'horizontal_flip_control_error':horizontal,'vertical_flip_control_error':vertical,'comparison_in_memory_only':True})
blob=(MEDIA/'tideglass-ipad-preview.mp4').read_bytes();configs=[]
def walk(start,end,ancestry):
 pos=start
 while pos<end:
  assert end-pos>=8;length,kind=struct.unpack('>I4s',blob[pos:pos+8]);head=8
  if length==1:length=struct.unpack('>Q',blob[pos+8:pos+16])[0];head=16
  elif length==0:length=end-pos
  assert length>=head and pos+length<=end;body=pos+head;stop=pos+length;kind=kind.decode('ascii');path=ancestry+[kind]
  if kind in ['moov','trak','mdia','minf','stbl']:walk(body,stop,path)
  elif kind=='stsd':assert struct.unpack('>I',blob[body+4:body+8])[0]==1;walk(body+8,stop,path)
  elif kind=='avc1':walk(body+78,stop,path)
  elif kind=='avcC':
   b=blob[body:stop];configs.append({'ancestry':path,'box_offset':pos,'box_bytes':length,'configuration_version':b[0],'profile_idc':b[1],'compatibility':b[2],'level_idc':b[3],'configuration_sha256':hashlib.sha256(b).hexdigest()})
  pos=stop
 assert pos==end
walk(0,len(blob),[]);assert len(configs)==1 and configs[0]['profile_idc']==100 and configs[0]['level_idc']==40
inputs={str(p.relative_to(ROOT)):sha(p) for folder in [RAW,MEDIA] for p in folder.rglob('*') if p.is_file()}
for p in ['release/store/tools/export_screenshots.py','release/store/tools/export_preview.swift','release/store/tools/inspect_preview.swift','release/qa/client-preview-tool-20261023T032106.818906Z/inspect_preview','release/qa/client-clean-phone-media-20261023T050152.295344Z/actual_source_probe','release/qa/lead-capture-driver-braces-20261023T080433.341792Z/review.json']:
 inputs[p]=sha(ROOT/p)
(OUT/'inspected-input-pins.json').write_text(json.dumps(inputs,indent=2)+'\n')
(OUT/'native-and-video-analysis.json').write_text(json.dumps({'native_verification_sha256':sha(RAW/'verification.json'),'native_evidence_files_rehashed':len(v['evidence_sha256']),'frozen_source_files_rehashed':len(m['source_sha256']),'live_and_workspace_production_inputs_checked':len(prod),'capture_harnesses':v['harness_sha256'],'season_capture_landmark':landmark,'real_gameplay_elapsed_ms':result['real_gameplay_elapsed_ms'],'actual_purchase_count_delta':1,'automated_pointer_events_routed':result['automated_pointer_events_routed'],'preview_decoded':preview,'source_comparisons':comparisons,'h264_configuration_records':configs,'passed':True},indent=2)+'\n')
print(json.dumps({'passed':True,'frame_errors':[x['mean_absolute_channel_error'] for x in comparisons],'avcC':configs,'native_verification':sha(RAW/'verification.json')},indent=2))
