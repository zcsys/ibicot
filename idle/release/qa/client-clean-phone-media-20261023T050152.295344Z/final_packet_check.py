from pathlib import Path
import hashlib,json,struct
ROOT=Path('/Users/csys/Desktop/ibicot/idle');OUT=Path(__file__).resolve().parent
MEDIA=ROOT/'release/store/media-3b00-phone-clean-20261023T045548.384747Z'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def js(p):return json.loads(p.read_text())
assert sha(MEDIA/'verification.json')=='f7f82cd8d4517a615669e4c8f17bec398143f39b5686c0f89dc26b4b4d930c15'
assert sha(MEDIA/'selection.json')=='a10fbaad069c510a08fdb52477de572b46f36106b189947fd71c0a35d629488b'
v=js(MEDIA/'verification.json');s=js(MEDIA/'selection.json')
for n,d in v['pins'].items():assert sha(ROOT/n)==d,n
assert v['selection_sha256']==sha(MEDIA/'selection.json') and v['review_sha256']==sha(MEDIA/'AUTHOR_REVIEW.md')
assert not s['public_submission'] and not s['store_acceptance'] and not v['scope_or_package_acceptance']
expected=['screenshots/ios-phone-capture-main.png','screenshots/ios-phone-capture-chapter.png','screenshots/ios-phone-capture-challenge.png']
assert [r['path'] for r in s['listing_screenshots']]==expected
assert [r['path'] for r in s['excluded_from_listing']]==['screenshots/ios-phone-capture-season.png']
for r in s['listing_screenshots']:assert sha(MEDIA/r['path'])==r['sha256'] and (r['width'],r['height'])==(1206,2622)
p=s['preview'];assert sha(MEDIA/p['path'])==p['sha256'] and (MEDIA/p['path']).stat().st_size==p['bytes']
m=js(OUT/'preview-decoded/metadata.json');export=js(MEDIA/'preview-export.log')
for pk,mk in [('duration_seconds','duration_seconds'),('width','display_width'),('height','display_height'),('frame_count','decoded_video_frames'),('nominal_fps','nominal_frames_per_second'),('audio_tracks','audio_track_count'),('measured_estimated_bits_per_second','estimated_bits_per_second')]:assert p[pk]==m[mk]
assert p['source_start_seconds']==export['source_start_seconds']==.5 and p['source_end_seconds']==19.5
assert p['speed']==export['speed_multiplier']==1 and p['requested_bits_per_second']==export['target_video_bits_per_second']==11000000
blob=(MEDIA/p['path']).read_bytes();configs=[]
def walk(start,end,ancestry):
 pos=start
 while pos<end:
  assert end-pos>=8
  length,kind=struct.unpack('>I4s',blob[pos:pos+8]);head=8
  if length==1:length=struct.unpack('>Q',blob[pos+8:pos+16])[0];head=16
  elif length==0:length=end-pos
  assert length>=head and pos+length<=end
  body=pos+head; stop=pos+length; kind=kind.decode('ascii');path=ancestry+[kind]
  if kind in ['moov','trak','mdia','minf','stbl']:walk(body,stop,path)
  elif kind=='stsd':
   assert struct.unpack('>I',blob[body+4:body+8])[0]==1
   walk(body+8,stop,path)
  elif kind=='avc1':walk(body+78,stop,path)
  elif kind=='avcC':
   b=blob[body:stop];configs.append({'ancestry':path,'box_offset':pos,'box_bytes':length,'configuration_version':b[0],'profile_idc':b[1],'compatibility':b[2],'level_idc':b[3],'configuration_sha256':hashlib.sha256(b).hexdigest()})
  pos=stop
 assert pos==end
walk(0,len(blob),[]); assert len(configs)==1
actual=configs[0];assert all(actual[k]==value for k,value in p['h264_configuration_record'].items())
for n,d in js(OUT/'input-pins-before.json').items():assert sha(ROOT/n)==d,n
old=js(OUT/'actual-video-analysis.json')['prior_failed_draft_and_raw_preserved']
for n,d in old.items():assert sha(ROOT/n)==d,n
summary={'author_verification_sha256':sha(MEDIA/'verification.json'),'author_review_sha256':sha(MEDIA/'AUTHOR_REVIEW.md'),'selection_sha256':sha(MEDIA/'selection.json'),'author_packet_files_rehashed':len(v['pins']),'selection_exact':True,'actual_structural_avcC':actual,'unchanged_original_review_inputs':True,'previous_failed_draft_raw_files_unchanged':len(old),'passed':True}
(OUT/'final-packet-check.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
