#!/usr/bin/env python3
"""Independent bounded exporter review. Synthetic controls are never native evidence."""
import array
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import zlib
from PIL import Image

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
TOOL = ROOT / 'export_screenshots.py'
HIST = REPO / 'release/native-proof/integration-ios-phone-20261021T112255.702927Z'
CANDIDATE = json.loads((ROOT / 'author-export-manifest.json').read_text())['candidate_fingerprint']
CASES = ROOT / 'controls'
CASES.mkdir(exist_ok=False)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def pins(folder):
    return {str(p.relative_to(folder)): sha(p) for p in sorted(folder.rglob('*')) if p.is_file()}

def chunk(kind, payload):
    return struct.pack('>I', len(payload)) + kind + payload + struct.pack('>I', zlib.crc32(kind + payload))

def png16(alpha=65535, width=8, height=7):
    row = struct.pack('>HHHH', 2924, 6324, 8752, alpha) * width
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB',width,height,16,6,0,0,0)) + chunk(b'IDAT',zlib.compress((b'\0'+row)*height)) + chunk(b'IEND',b'')

def png_chunks(path):
    b = path.read_bytes()
    assert b[:8] == b'\x89PNG\r\n\x1a\n'
    pos=8; out=[]
    while pos<len(b):
        n=struct.unpack('>I',b[pos:pos+4])[0]; kind=b[pos+4:pos+8]; payload=b[pos+8:pos+8+n]
        assert struct.unpack('>I',b[pos+8+n:pos+12+n])[0] == zlib.crc32(kind+payload)
        out.append((kind,payload)); pos+=12+n
    assert pos==len(b) and out[-1][0]==b'IEND'
    return out

def describe(path):
    chunks=png_chunks(path)
    ihdr=struct.unpack('>IIBBBBB',chunks[0][1])
    with Image.open(path) as im:
        return {'sha256':sha(path),'ihdr':list(ihdr),'mode':im.mode,'chunk_types':[k.decode() for k,_ in chunks], 'effective_alpha_extrema':list(im.convert('RGBA').getchannel('A').getextrema())}

def fixture(folder, kind='opaque8'):
    folder.mkdir(parents=True)
    rows=[]
    for screen in ('main','chapter','challenge','season'):
        p=folder/(screen+'.png')
        if kind in ('rgba16','translucent16'):
            p.write_bytes(png16(65535 if kind=='rgba16' else 65534))
        elif kind=='trns':
            Image.new('RGB',(8,7),(23,42,91)).save(p,transparency=(23,42,91))
        else:
            Image.new('RGBA',(8,7),(23,42,91,254 if kind=='translucent8' else 255)).save(p)
        rows.append({'file':p.name,'sha256':sha(p),'bytes':p.stat().st_size,'width':8,'height':7})
    m={'candidate_fingerprint':CANDIDATE,'native_verification_passed':True,'device':'SYNTHETIC_CONTROL_NOT_NATIVE','device_label':'SYNTHETIC_CONTROL_NOT_NATIVE','platform':'synthetic','run_id':'synthetic-only','harness_sha256':'a'*64,'screenshots':rows}
    r={'candidate_fingerprint':CANDIDATE,'passed':True,'scenario':'capture-gallery','device':m['device'],'label':m['device_label'],'platform':'synthetic','run_id':'synthetic-only','harness_sha256':{'harness.dart':'a'*64},'evidence_sha256':{}}
    commit(folder,m,r)
    return m,r

def commit(folder,m,r):
    mf=folder/'capture-manifest.json'; mf.write_text(json.dumps(m,indent=2)+'\n')
    r['evidence_sha256']={row['file']:row['sha256'] for row in m['screenshots']}
    r['evidence_sha256']['capture-manifest.json']=sha(mf)
    (folder/'verification.json').write_text(json.dumps(r,indent=2)+'\n')

spec=importlib.util.spec_from_file_location('reviewed_exporter',TOOL)
exporter=importlib.util.module_from_spec(spec);spec.loader.exec_module(exporter)
results=[]
def run_case(name,kind='opaque8',change=None,expected_reject=True,candidate=CANDIDATE):
    base=CASES/name; capture=base/'capture'; output=base/'output'
    m,r=fixture(capture,kind)
    if change: change(capture,output,m,r)
    before=pins(capture); outbefore=pins(output) if output.exists() else None
    try:
        data=exporter.export(capture,output,candidate)
        exception=None; accepted=True
    except Exception as exc:
        exception={'type':type(exc).__name__,'message':str(exc)};accepted=False
    row={'case':name,'synthetic_control_only':True,'expected_reject':expected_reject,'accepted':accepted,'expectation_satisfied':accepted != expected_reject,'exception':exception,'source_unchanged':before==pins(capture),'source_sha256':before,'output_existed_before':outbefore is not None,'output_unchanged':outbefore==pins(output) if outbefore is not None else None,'output_exists_after':output.exists()}
    if accepted: row['pngs']={p.name:describe(p) for p in output.glob('*.png')}
    (base/'result.json').write_text(json.dumps(row,indent=2)+'\n');results.append(row)

def edit(change):
    def mutate(c,o,m,r):
        change(c,o,m,r); commit(c,m,r)
    return mutate

def mutate_raw(c,o,m,r):
    p=c/'main.png';p.write_bytes(p.read_bytes()+b'x')
    m['screenshots'][0]['bytes']=p.stat().st_size
    commit(c,m,r)

def over_bytes(c,o,m,r):
    p=c/'main.png';p.write_bytes(p.read_bytes()+bytes(20*1024*1024))
    m['screenshots'][0].update(sha256=sha(p),bytes=p.stat().st_size)
    commit(c,m,r)

def over_pixels(c,o,m,r):
    p=c/'main.png';p.write_bytes(png16(width=4001,height=4000))
    m['screenshots'][0].update(sha256=sha(p),bytes=p.stat().st_size,width=4001,height=4000)
    commit(c,m,r)

def existing(c,o,m,r):
    o.mkdir();(o/'sentinel.txt').write_text('PRESERVE_EXISTING_BYTES\n')

run_case('opaque8_positive',expected_reject=False)
run_case('opaque16_precision_positive',kind='rgba16',expected_reject=False)
run_case('translucent8_rejected',kind='translucent8')
run_case('trns_must_reject',kind='trns')
run_case('translucent16_must_reject',kind='translucent16')
run_case('invalid_candidate',candidate='not-an-exact-candidate')
run_case('mismatched_candidate_argument',candidate='b'*64)
run_case('mismatched_candidate_manifest',change=edit(lambda c,o,m,r:m.update(candidate_fingerprint='b'*64)))
run_case('mismatched_candidate_verification',change=edit(lambda c,o,m,r:r.update(candidate_fingerprint='b'*64)))
run_case('missing_manifest',change=lambda c,o,m,r:(c/'capture-manifest.json').unlink())
run_case('missing_verification',change=lambda c,o,m,r:(c/'verification.json').unlink())
run_case('manifest_hash_mismatch',change=lambda c,o,m,r:(c/'capture-manifest.json').write_text(json.dumps(m)+' '))
run_case('raw_hash_mismatch',change=mutate_raw)
run_case('missing_raw',change=lambda c,o,m,r:(c/'main.png').unlink())
run_case('raw_byte_count_mismatch',change=edit(lambda c,o,m,r:m['screenshots'][0].update(bytes=1)))
run_case('raw_dimension_mismatch',change=edit(lambda c,o,m,r:m['screenshots'][0].update(width=9)))
run_case('failed_native_verification',change=edit(lambda c,o,m,r:r.update(passed=False)))
run_case('failed_manifest_verification',change=edit(lambda c,o,m,r:m.update(native_verification_passed=False)))
run_case('mismatched_device',change=edit(lambda c,o,m,r:m.update(device='other-synthetic')))
run_case('mismatched_harness',change=edit(lambda c,o,m,r:m.update(harness_sha256='b'*64)))
run_case('unsafe_filename',change=edit(lambda c,o,m,r:m['screenshots'][0].update(file='../main.png')))
run_case('duplicate_filename',change=edit(lambda c,o,m,r:m['screenshots'].__setitem__(1,dict(m['screenshots'][0]))))
run_case('existing_output_nonoverwrite',change=existing)
run_case('over_20MiB',change=over_bytes)
run_case('over_16M_pixels',change=over_pixels)
cli=subprocess.run([sys.executable,str(TOOL),str(CASES/'opaque8_positive/capture'),str(ROOT/'missing-cli-candidate-output')],capture_output=True,text=True)
(ROOT/'missing-candidate-cli.log').write_text(cli.stdout+cli.stderr)
results.append({'case':'missing_candidate_cli','synthetic_control_only':True,'expected_reject':True,'accepted':cli.returncode==0,'returncode':cli.returncode,'expectation_satisfied':cli.returncode!=0,'output_exists_after':(ROOT/'missing-cli-candidate-output').exists()})
(ROOT/'controls.json').write_text(json.dumps(results,indent=2)+'\n')
print('Controls:',len(results),'unexpected accepted:',[r['case'] for r in results if not r['expectation_satisfied']],flush=True)

before=pins(HIST)
histout=ROOT/'historical-reproduction'
sub=subprocess.run([sys.executable,str(TOOL),str(HIST),str(histout),'--candidate',CANDIDATE],capture_output=True,text=True)
(ROOT/'historical-reproduction.log').write_text(sub.stdout+sub.stderr)
assert sub.returncode==0
historical=[]
for source in sorted(HIST.glob('*.png')):
    output=histout/source.name
    if not output.exists():continue
    source_chunks=png_chunks(source);ihdr=struct.unpack('>IIBBBBB',source_chunks[0][1])
    w,h,depth,ctype,_,_,interlace=ihdr
    assert (depth,ctype,interlace)==(16,6,0)
    raw=zlib.decompress(b''.join(data for kind,data in source_chunks if kind==b'IDAT'))
    stride=1+w*8;assert len(raw)==stride*h and set(raw[::stride])=={0}
    pixels=b''.join(raw[y*stride+1:(y+1)*stride] for y in range(h))
    native=array.array('H');native.frombytes(pixels)
    if sys.byteorder=='little':native.byteswap()
    r,g,b,a=native[0::4],native[1::4],native[2::4],native[3::4]
    nonrepresentable=sum(v%257!=0 for channel in (r,g,b) for v in channel)
    rgb_high=bytearray(w*h*3)
    for channel_index,channel in enumerate((r,g,b)):
        rgb_high[channel_index::3]=bytes(v>>8 for v in channel)
    with Image.open(output) as exported:
        output_pixels=exported.tobytes()
    output_description=describe(output)
    author=json.loads((ROOT/'author-export-manifest.json').read_text())
    expected=next(row['sha256'] for row in author['exports'] if row['file']==source.name)
    row={'source':source.name,'source_sha256':sha(source),'source_ihdr':list(ihdr),'source_scanline_filters':[0],'source_alpha16_min':min(a),'source_alpha16_max':max(a),'source_rgb_sample_count':w*h*3,'native_rgb_samples_not_exactly_8bit_representable':nonrepresentable,'all_source_pixels_alpha65535':min(a)==max(a)==65535,'output_equals_each_source_RGB16_high_byte':output_pixels==bytes(rgb_high),'dimensions_preserved':output_description['ihdr'][:2]==[w,h],'output_has_no_alpha_channel_or_trns':output_description['ihdr'][3]==2 and 'tRNS' not in output_description['chunk_types'],'output':output_description,'matches_author_output_bytes':sha(output)==expected,'source_first_pixel_rgb16':list(native[:3]),'output_first_pixel_rgb8':list(output_pixels[:3])}
    historical.append(row)
    print(source.name,nonrepresentable,'nonrepresentable RGB16 samples; dimensions',row['dimensions_preserved'],'native alpha',min(a),max(a),'exact high bytes',row['output_equals_each_source_RGB16_high_byte'],flush=True)
summary={'candidate_fingerprint':CANDIDATE,'historical_tool_control_only':True,'reviewed_script_sha256':sha(TOOL),'live_script_sha256_at_completion':sha(REPO/'release/store/tools/export_screenshots.py'),'source_sha256_before':before,'source_sha256_after':pins(HIST),'source_unchanged':before==pins(HIST),'rows':historical}
(ROOT/'historical-independent-checks.json').write_text(json.dumps(summary,indent=2)+'\n')
print('Historical source unchanged:',summary['source_unchanged'],flush=True)
