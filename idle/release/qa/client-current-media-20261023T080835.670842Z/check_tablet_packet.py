from pathlib import Path
import json,hashlib
ROOT=Path('/Users/csys/Desktop/ibicot/idle');OUT=Path(__file__).resolve().parent/'tablet';MEDIA=ROOT/'release/store/media-3b00-tablet-corrected-20261023T0811Z'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def js(p):return json.loads(p.read_text())
assert h(MEDIA/'verification.json')=='d7cce21cd56dede6f6443fcb19f0bee304f8470cc019a6e31de641dcb32cb387'
assert h(MEDIA/'selection.json')=='685757f65f52dc55103a549c11d4b00da1c9c7ab456fca4d15be8d87758d4d9f'
assert h(MEDIA/'input-pins.json')=='a48edd8acc64372f93e5afa54de08fb293a35cdf99a635f0063d158d84bdc1fb'
v=js(MEDIA/'verification.json');s=js(MEDIA/'selection.json');native=js(MEDIA/'input-pins.json');actual=js(OUT/'native-and-video-analysis.json')
for mapping in [v['pins'],native['pins'],js(OUT/'inspected-input-pins.json')]:
 for p,digest in mapping.items():assert h(ROOT/p)==digest,p
assert h(MEDIA/'AUTHOR_REVIEW.md')==v['review_sha256'] and h(MEDIA/'selection.json')==v['selection_sha256']
assert not s['public_submission'] and not s['store_acceptance'] and not v['scope_or_package_acceptance']
assert [x['path'] for x in s['listing_screenshots']]==['screenshots/ios-tablet-capture-'+n+'.png' for n in ['main','chapter','challenge']]
assert [x['path'] for x in s['excluded_from_listing']]==['screenshots/ios-tablet-capture-season.png']
for x in s['listing_screenshots']:assert h(MEDIA/x['path'])==x['sha256'] and (x['width'],x['height'])==(2064,2752)
p=s['preview'];a=actual['preview_decoded'];assert h(MEDIA/p['path'])==p['sha256'] and (MEDIA/p['path']).stat().st_size==p['bytes']
for x,y in [('duration_seconds','duration_seconds'),('width','display_width'),('height','display_height'),('frame_count','decoded_video_frames'),('nominal_fps','nominal_frames_per_second'),('audio_tracks','audio_track_count'),('measured_estimated_bits_per_second','estimated_bits_per_second')]:assert p[x]==a[y]
for k,val in p['h264_configuration_record'].items():assert actual['h264_configuration_records'][0][k]==val
assert (p['source_start_seconds'],p['source_end_seconds'],p['speed'],p['requested_bits_per_second'],p['padding_pixels'])==(.5,19.5,1,11000000,0)
prior={}
for f in ['release/store/android-capture-repair-season-20261023T054210.236050Z/baseline.json','release/store/android-ack-repair-20261023T081049.643189Z/baseline.json']:
 prior.update({p:digest for p,digest in js(ROOT/f).items() if p.startswith('release/native-proof/')})
prior.update(js(ROOT/'release/store/android-capture-repair-20261023T052223.188133Z/baseline.json')['failed_gallery'])
for p,digest in prior.items():assert h(ROOT/p)==digest,p
reviews=['release/qa/lead-capture-repair-20261023T053647.917618Z/REVIEW.md','release/qa/lead-capture-repair-20261023T053647.917618Z/verification.json','release/qa/lead-capture-driver-braces-20261023T080433.341792Z/review.json']
summary={'passed':True,'author_verification_sha256':h(MEDIA/'verification.json'),'author_selection_sha256':h(MEDIA/'selection.json'),'author_review_sha256':h(MEDIA/'AUTHOR_REVIEW.md'),'author_packet_files_rehashed':len(v['pins']),'author_input_pins_rehashed':len(native['pins']),'all_previously_inspected_inputs_unchanged':True,'selected_outputs_match_actual_samples_and_metadata':True,'earlier_native_failure_records_preserved':prior,'different_author_capture_reviews':{p:h(ROOT/p) for p in reviews}}
(OUT/'final-packet-check.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k!='earlier_native_failure_records_preserved'},indent=2))
