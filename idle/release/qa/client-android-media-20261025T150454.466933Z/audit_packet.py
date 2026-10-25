from pathlib import Path
import json,hashlib,struct
from PIL import Image,ImageChops,ImageStat
R=Path('/Users/csys/Desktop/ibicot/idle');O=Path(__file__).parent;M=R/'release/store/media-3b00-android-20261025T150512.754160Z';N=R/'release/native-proof/integration-android-20261023T085458.804768Z'
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();j=lambda p:json.loads(p.read_text())
assert h(M/'verification.json')=='b3f52be1e97cf140e62396f721120b3e5943216c3d20aa7053136df26d64b810'
assert h(M/'selection.json')=='2eb39ff0a0e58efa85819a8d2292900a2f00456d90c03e9a68b64a4e28cb8d3e'
assert h(M/'AUTHOR_REVIEW.md')=='ff81b3b56fb6c5fb776f4b313f84a8080926aac8dead04a6c02ccdae4ec4b0c3'
v=j(M/'verification.json');s=j(M/'selection.json');n=j(N/'verification.json');rec=j(N/'recording.json');res=j(N/'result.json');export=j(M/'preview-export.log');png=j(M/'screenshots/export-manifest.json');meta=j(O/'preview-decoded/metadata.json');raw=j(O/'prior-raw-review-bridge.json')['raw_metadata'];sample=j(O/'source-exact-sampled/metadata.json')
assert n['passed'] and not n['verification_errors'] and n['source_snapshot_unchanged'] and n['production_inputs_match_snapshot'] and not n['production_input_differences_after_run'] and not n['harness_source_differences_during_run']
assert n['candidate_fingerprint']==s['candidate_fingerprint']==v['candidate_fingerprint']==png['candidate_fingerprint']=='3b00cc8f71222f35b60f18ee83a8bb3ba71e39aa5364222dbeb7f6d2a5c45c59'
assert v['source_verification_sha256']==png['native_verification_sha256']==h(N/'verification.json')
for name,digest in n['evidence_sha256'].items():assert h(N/name)==digest,name
for name,digest in png['source_sha256'].items():assert h(N/name)==digest,name
for name,digest in v['outputs_sha256'].items():assert h(M/name)==digest,name
for name,digest in j(M/'input-pins.json').items():assert h(R/name)==digest,name
assert rec['passed'] and not rec['errors'] and rec['recorder_exit_code']==0
assert len(rec['android_screenshots'])==4 and rec['android_recording_stop']['recorder_stopped']
assert rec['android_recorder_start']['identity']==rec['android_recorder_stop']['identity']==rec['android_recording_stop']['recorder_identity']
assert rec['android_recorder_stop']['exit_code']==0 and res['actual_purchase_count_delta']==1 and res['automated_pointer_events_routed']==12
land=res['season_capture_landmark'];assert land['widget']=='SeasonScreen' and land['selected'] and land['route_is_current'] and land['primary_animation_status']=='completed' and land['secondary_animation_status']=='dismissed'
assert [x['path'] for x in s['listing_screenshots']]==['screenshots/android-capture-'+name+'.png' for name in ['main','chapter','challenge']]
assert [x['path'] for x in s['excluded_from_listing']]==['screenshots/android-capture-season.png']
assert not s['public_submission'] and not s['store_acceptance'] and not s['store_dimensions_qualified']
for x in s['listing_screenshots']:assert h(M/x['path'])==x['sha256'] and (x['width'],x['height'])==(1080,1920)
p=s['preview'];assert h(M/p['path'])==p['sha256'] and (M/p['path']).stat().st_size==p['bytes']
for field,key in [('duration_seconds','duration_seconds'),('width','display_width'),('height','display_height'),('frame_count','decoded_video_frames'),('audio_tracks','audio_track_count'),('measured_estimated_bits_per_second','estimated_bits_per_second')]:assert p[field]==meta[key]
assert meta['sample_read_complete'] and meta['decoded_video_frames']==570 and meta['duration_seconds']==19 and meta['audio_track_count']==0
assert abs(meta['nominal_frames_per_second']-30)<1e-4
assert abs(meta['last_frame_seconds']-569/30)<1e-9 and abs(meta['max_frame_gap_seconds']-1/30)<1e-9 and abs(meta['min_frame_gap_seconds']-1/30)<1e-9
assert (export['source_start_seconds'],export['requested_duration_seconds'],export['speed_multiplier'],export['padding_x'],export['padding_y'])==(.5,19,1,0,0)
assert export['target_video_bits_per_second']==11000000 and not export['generated_gameplay_added'] and export['full_frame_preserved']
assert (p['source_start_seconds'],p['source_end_seconds'],p['speed'],p['padding_pixels'])==(.5,19.5,1,0)
assert raw['decoded_video_frames']==p['source_decoded_frames']==44 and abs(raw['duration_seconds']-p['source_duration_seconds'])<1e-9 and raw['nominal_frames_per_second']==p['source_nominal_fps'] and raw['audio_track_count']==0
comparisons=[]
for x,y in zip(meta['frames'],sample['frames'],strict=True):
 assert abs(y['requested_source_seconds']-x['actual_seconds']-.5)<1e-9
 with Image.open(O/'preview-decoded'/x['file']) as z:im=z.convert('RGB')
 with Image.open(O/'source-exact-sampled'/y['file']) as z:src=z.convert('RGB')
 assert im.size==src.size==(1080,1920)
 mae=lambda a,b:sum(ImageStat.Stat(ImageChops.difference(a,b)).mean)/3
 c={'output_seconds':x['actual_seconds'],'source_requested_seconds':y['requested_source_seconds'],'actual_held_source_seconds':y['actual_source_seconds'],'mean_absolute_channel_error':mae(im,src),'horizontal_flip_control_error':mae(im,src.transpose(Image.Transpose.FLIP_LEFT_RIGHT)),'vertical_flip_control_error':mae(im,src.transpose(Image.Transpose.FLIP_TOP_BOTTOM))}
 assert c['mean_absolute_channel_error']<c['horizontal_flip_control_error'] and c['mean_absolute_channel_error']<c['vertical_flip_control_error'];comparisons.append(c)
blob=(M/p['path']).read_bytes();configs=[]
def boxes(start,end,path):
 pos=start
 while pos<end:
  assert end-pos>=8;length,kind=struct.unpack('>I4s',blob[pos:pos+8]);head=8
  if length==1:length=struct.unpack('>Q',blob[pos+8:pos+16])[0];head=16
  elif length==0:length=end-pos
  assert length>=head and pos+length<=end;body=pos+head;stop=pos+length;kind=kind.decode('ascii');ancestry=path+[kind]
  if kind in ['moov','trak','mdia','minf','stbl']:boxes(body,stop,ancestry)
  elif kind=='stsd':assert struct.unpack('>I',blob[body+4:body+8])[0]==1;boxes(body+8,stop,ancestry)
  elif kind=='avc1':boxes(body+78,stop,ancestry)
  elif kind=='avcC':configs.append({'ancestry':ancestry,'offset':pos,'profile':blob[body+1],'level':blob[body+3],'sha256':hashlib.sha256(blob[body:stop]).hexdigest()})
  pos=stop
 assert pos==end
boxes(0,len(blob),[]);assert len(configs)==1 and configs[0]['profile']==p['h264_profile_idc']==100 and configs[0]['level']==p['h264_level_idc']==40
refs=['release/qa/lead-capture-repair-20261023T053647.917618Z/REVIEW.md','release/qa/lead-capture-driver-braces-20261023T080433.341792Z/review.json','release/qa/lead-android-ack-20261023T081709.354596Z/REVIEW.md','release/qa/lead-android-cadence-20261023T083724.231954Z/REVIEW.md','release/qa/lead-recorder-headroom-20261023T085031.238934Z/REVIEW.md','release/qa/client-current-media-20261023T080835.670842Z/audit_pngs.py','release/store/tools/export_screenshots.py','release/store/tools/export_preview.swift','release/store/tools/inspect_preview.swift']
pins={str(f.relative_to(R)):h(f) for d in [M,N] for f in d.rglob('*') if f.is_file()};pins.update({x:h(R/x) for x in refs})
(O/'inspected-input-pins.json').write_text(json.dumps(pins,indent=2)+'\n')
(O/'packet-analysis.json').write_text(json.dumps({'passed':True,'author_packet_files_rehashed':len(v['outputs_sha256']),'author_inputs_rehashed':len(j(M/'input-pins.json')),'native_evidence_files_rehashed':len(n['evidence_sha256']),'source_comparisons':comparisons,'h264_configs':configs,'different_author_capture_reviews':{x:pins[x] for x in refs[:5]},'source_frames':44,'output_frames':570,'actual_bitrate_bps':meta['estimated_bits_per_second'],'audio_tracks':0,'no_native_or_flutter_commands':True},indent=2)+'\n');print(json.dumps({'passed':True,'mae':[x['mean_absolute_channel_error'] for x in comparisons],'pins':len(pins)},indent=2))
