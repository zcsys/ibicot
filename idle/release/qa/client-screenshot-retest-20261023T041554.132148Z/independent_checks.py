#!/usr/bin/env python3
"""Independent bounded retest; generated controls are not native capture evidence."""
from pathlib import Path
import array, hashlib, importlib.util, json, struct, subprocess, sys, zlib
from PIL import Image

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
OLD=REPO/'release/qa/client-screenshot-export-20261023T040546.847914Z'
HIST=REPO/'release/native-proof/integration-ios-phone-20261021T112255.702927Z'
AUTHOR=REPO/'release/store/screenshot-export-repair-20261023T041208.557192Z'
TOOL=HERE/'export_screenshots.py'
CANDIDATE=json.loads((OLD/'author-export-manifest.json').read_text())['candidate_fingerprint']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def pins(folder):return {str(p.relative_to(folder)):sha(p) for p in sorted(folder.rglob('*')) if p.is_file()}
source_before=pins(HIST);old_before=pins(OLD)
spec=importlib.util.spec_from_file_location('reviewed_repair',TOOL);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
results=[]

def record(name,fn):
    try:
        details=fn();r={'case':name,'passed':True,'details':details}
    except Exception as exc:
        r={'case':name,'passed':False,'exception':type(exc).__name__,'message':str(exc)}
    results.append(r)
    (HERE/'checks-progress.json').write_text(json.dumps(results,indent=2)+'\n')
    print(name,r['passed'],r.get('message',''),flush=True)

def chunk(k,p):return struct.pack('>I',len(p))+k+p+struct.pack('>I',zlib.crc32(k+p))
def parse_png(path):
    data=path.read_bytes();assert data[:8]==b'\x89PNG\r\n\x1a\n'
    off=8;chunks=[]
    while off<len(data):
        n=int.from_bytes(data[off:off+4],'big');k=data[off+4:off+8];p=data[off+8:off+8+n]
        assert len(p)==n and zlib.crc32(k+p)==int.from_bytes(data[off+8+n:off+12+n],'big')
        chunks.append((k,p));off+=12+n
    assert off==len(data) and chunks[-1]==(b'IEND',b'')
    return chunks

def png(header,raster,colors=(),extra=(),compressed=None):
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',*header))+b''.join(chunk(k,p) for k,p in colors)+b''.join(chunk(k,p) for k,p in extra)+chunk(b'IDAT',zlib.compress(raster) if compressed is None else compressed)+chunk(b'IEND',b'')

def encode_filter(row,above,step,method):
    out=bytearray(len(row))
    for i,v in enumerate(row):
        a=row[i-step] if i>=step else 0;b=above[i];c=above[i-step] if i>=step else 0
        if method==0:pred=0
        elif method==1:pred=a
        elif method==2:pred=b
        elif method==3:pred=(a+b)//2
        else:
            target=a+b-c
            pred=min((a,b,c),key=lambda x:abs(target-x))
        out[i]=(v-pred)%256
    return bytes([method])+out

# The actual historical color definitions are copied byte-for-byte into controls.
source_color_chunks=[(k,p) for k,p in parse_png(HIST/'ios-phone-capture-main.png') if k in (b'iCCP',b'cICP',b'gAMA',b'cHRM',b'sRGB')]
CONTROLS=HERE/'native-controls';CONTROLS.mkdir()

def fixture(depth,channels,filters,width=9,height=7,alpha=None):
    maximum=2**depth-1;rgb=[];rows=[]
    # Boundary values, varying preceding rows, and all channel positions exercise byte predictors.
    boundaries=[0,1,127,128,129,255,256,257,258,65534,65535,2924,6324,8752,32767,32768]
    for y in range(height):
        full=[]
        for x in range(width):
            vals=[boundaries[(y*width*3+x*3+c)%len(boundaries)]% (maximum+1) for c in range(3)]
            rgb.extend(vals);full.extend(vals)
            if channels==4:full.append(maximum if alpha is None or (x,y)!=(width-1,height-1) else alpha)
        rows.append(bytes(full) if depth==8 else struct.pack('>'+'H'*len(full),*full))
    stride=len(rows[0]);raster=b'';prior=bytes(stride)
    for y,row in enumerate(rows):
        raster+=encode_filter(row,prior,channels*(depth//8),filters[y%len(filters)]);prior=row
    return png((width,height,depth,2 if channels==3 else 6,0,0,0),raster,source_color_chunks),rgb

def verify_output(path,w,h,expected,colors):
    chunks=parse_png(path);header=struct.unpack('>IIBBBBB',chunks[0][1]);assert header==(w,h,8,2,0,0,0)
    assert not any(k in (b'tRNS',b'acTL',b'fcTL',b'fdAT') for k,p in chunks)
    actualcolors=[(k,p) for k,p in chunks if k in (b'iCCP',b'cICP',b'gAMA',b'cHRM',b'sRGB')];assert actualcolors==colors
    raw=zlib.decompress(b''.join(p for k,p in chunks if k==b'IDAT'));stride=w*3+1
    assert len(raw)==stride*h and set(raw[::stride])=={0}
    pixels=b''.join(raw[y*stride+1:(y+1)*stride] for y in range(h));assert pixels==expected
    with Image.open(path) as im:
        assert im.mode=='RGB' and im.size==(w,h) and im.tobytes()==expected and 'transparency' not in im.info
    return {'sha256':sha(path),'ihdr':list(header),'native_decoded_rgb_sha256':hashlib.sha256(pixels).hexdigest(),'color_chunk_payload_sha256':{k.decode():hashlib.sha256(p).hexdigest() for k,p in actualcolors}}

def positive(name,depth,channels,filters):
    src=CONTROLS/(name+'.png');data,values=fixture(depth,channels,filters);src.write_bytes(data)
    w,h,actual,colors,details=mod.native_rgb8(src)
    expected=bytes(values if depth==8 else (round(v/257) for v in values))
    assert (w,h)==(9,7) and actual==expected and colors==source_color_chunks
    errors=[abs(v-out*257) for v,out in zip(values,expected)] if depth==16 else [0]*len(values)
    assert details['rgb_samples_not_exactly_representable']==sum(e!=0 for e in errors)
    assert details['maximum_native_sample_error']==max(errors)
    assert details['native_rgb_samples_unchanged']==(max(errors)==0)
    assert details['source_filters']==sorted(set(filters))
    out=CONTROLS/(name+'-output.png');out.write_bytes(mod.encode_rgb8(w,h,actual,colors))
    return {'synthetic_control_only':True,'source_sha256':sha(src),'precision':details,'output':verify_output(out,w,h,expected,source_color_chunks)}

for depth in (8,16):
    for channels in (3,4):
        for filter_method in range(5):
            name=f'depth{depth}-channels{channels}-filter{filter_method}'
            record(name,lambda n=name,d=depth,c=channels,f=filter_method:positive(n,d,c,[f]))
        name=f'depth{depth}-channels{channels}-mixed-filters'
        record(name,lambda n=name,d=depth,c=channels:positive(n,d,c,[0,1,2,3,4]))

def exhaustive16():
    values=list(range(65536));rgb=[x for v in values for x in (v,v,v)]
    rows=[b'\0'+b''.join(struct.pack('>HHH',v,v,v) for v in range(y*256,(y+1)*256)) for y in range(256)]
    source=CONTROLS/'exhaustive16.png';source.write_bytes(png((256,256,16,2,0,0,0),b''.join(rows)))
    w,h,actual,colors,details=mod.native_rgb8(source);expected=bytes(round(v/257) for v in rgb)
    assert actual==expected
    errors=[abs(v-round(v/257)*257) for v in rgb]
    assert details['maximum_native_sample_error']==max(errors)==128
    assert details['rgb_samples_not_exactly_representable']==sum(v!=0 for v in errors)==195840
    out=CONTROLS/'exhaustive16-output.png';out.write_bytes(mod.encode_rgb8(w,h,actual,colors))
    return {'all_65536_native_values_checked_per_RGB_channel':True,'precision':details,'output':verify_output(out,w,h,expected,[])}
record('exhaustive16-nearest8-and-error-count',exhaustive16)

def exhaustive8():
    values=bytes(x for v in range(256) for x in (v,v,255-v));source=CONTROLS/'exhaustive8.png';source.write_bytes(png((256,1,8,2,0,0,0),b'\0'+values))
    w,h,actual,colors,details=mod.native_rgb8(source);assert actual==values and details['native_rgb_samples_unchanged'] and details['maximum_native_sample_error']==0
    out=CONTROLS/'exhaustive8-output.png';out.write_bytes(mod.encode_rgb8(w,h,actual,colors))
    return {'all_256_native_values_checked':True,'output':verify_output(out,w,h,values,[])}
record('exhaustive8-exact-samples',exhaustive8)

base_raster=b'\0'+bytes([1,2,3,255]);header=(1,1,8,6,0,0,0)
base=png(header,base_raster)
negatives={
 'signature':b'X'+base[1:], 'crc':base[:-1]+bytes([base[-1]^1]),'truncated_chunk':base[:-3], 'trailing_after_iend':base+b'X',
 'short_raster':png(header,base_raster[:-1]), 'long_raster':png(header,base_raster+b'X'),
 'zlib_second_stream':png(header,base_raster,compressed=zlib.compress(base_raster)+zlib.compress(b'X')),
 'zlib_trailing_bytes':png(header,base_raster,compressed=zlib.compress(base_raster)+b'X'),
 'zlib_truncated':png(header,base_raster,compressed=zlib.compress(base_raster)[:-1]),
 'bad_filter':png(header,b'\x05'+base_raster[1:]),
 'native_alpha8_254':png(header,b'\0'+bytes([1,2,3,254])),
 'native_alpha16_65534_filter4':fixture(16,4,[4],alpha=65534)[0],
 'native_alpha16_65280_filter3':fixture(16,4,[3],alpha=65280)[0],
 'native_alpha16_0_filter1':fixture(16,4,[1],alpha=0)[0],
 'trns_rgb_key':png((1,1,8,2,0,0,0),b'\0\1\2\3',extra=[(b'tRNS',struct.pack('>HHH',1,2,3))]),
 'animation':png(header,base_raster,extra=[(b'acTL',struct.pack('>II',1,0))]),
 'unsupported_critical':png(header,base_raster,extra=[(b'ABCD',b'')]),
 'interlaced':png((1,1,8,6,0,0,1),base_raster),
 'palette':png((1,1,8,3,0,0,0),base_raster),
 'depth4':png((1,1,4,6,0,0,0),base_raster),
 'zero_width':png((0,1,8,6,0,0,0),base_raster),
 'native_over_16M_pixels':png((4001,4000,8,6,0,0,0),b''),
 'duplicate_ihdr':png(header,base_raster,extra=[(b'IHDR',struct.pack('>IIBBBBB',*header))]),
 'duplicate_color':png(header,base_raster,colors=[(b'cICP',bytes([12,13,0,1]))]*2),
}
for name,data in negatives.items():
    def reject(n=name,b=data):
        source=CONTROLS/('reject-'+n+'.png');source.write_bytes(b)
        try:mod.native_rgb8(source)
        except ValueError as exc:return {'synthetic_control_only':True,'rejected':True,'source_sha256':sha(source),'reason':str(exc)}
        raise AssertionError('Malformed/nonopaque source accepted')
    record('reject-'+name,reject)

# Reuse every original immutable input, including both actual old failure fixtures.
REPLAY=HERE/'original-controls-replayed';REPLAY.mkdir()
old_results=json.loads((OLD/'controls.json').read_text())
for previous in old_results:
    name=previous['case']
    def replay(n=name,pr=previous):
        source=OLD/'controls'/n/'capture';output=REPLAY/n
        candidate='not-an-exact-candidate' if n=='invalid_candidate' else ('b'*64 if n=='mismatched_candidate_argument' else CANDIDATE)
        if n=='missing_candidate_cli':
            run=subprocess.run([sys.executable,str(TOOL),str(OLD/'controls/opaque8_positive/capture'),str(output)],capture_output=True,text=True)
            (REPLAY/(n+'.log')).write_text(run.stdout+run.stderr);assert run.returncode!=0 and not output.exists();return {'returncode':run.returncode,'rejected':True}
        before=pins(source)
        if n=='existing_output_nonoverwrite':output.mkdir();(output/'sentinel').write_bytes(b'EXISTING_OUTPUT_MUST_SURVIVE')
        preout=pins(output) if output.exists() else None
        try:manifest=mod.export(source,output,candidate);accepted=True;error=None
        except Exception as exc:accepted=False;error={'type':type(exc).__name__,'message':str(exc)}
        assert accepted != pr['expected_reject'], f'Acceptance {accepted}: {error}'
        assert before==pins(source)
        if preout is not None:assert pins(output)==preout
        elif not accepted:assert not output.exists()
        return {'synthetic_control_only':True,'accepted':accepted,'error':error,'source_unchanged':True,'source_sha256':before,'output_sha256':pins(output) if output.exists() else None}
    record('original-'+name,replay)

HISTOUT=HERE/'historical-reproduction'
run=subprocess.run([sys.executable,str(TOOL),str(HIST),str(HISTOUT),'--candidate',CANDIDATE],capture_output=True,text=True)
(HERE/'historical-reproduction.log').write_text(run.stdout+run.stderr)
assert run.returncode==0,run.stderr
manifest=json.loads((HISTOUT/'export-manifest.json').read_text())
authormanifest=json.loads((AUTHOR/'historical-phone/export-manifest.json').read_text())
for row in manifest['exports']:
    def historical(r=row):
        source=HIST/r['file'];output=HISTOUT/r['file'];chunks=parse_png(source)
        width,height,depth,color,compression,filtering,interlace=struct.unpack('>IIBBBBB',chunks[0][1]);assert (depth,color,compression,filtering,interlace)==(16,6,0,0,0)
        raw=zlib.decompress(b''.join(p for k,p in chunks if k==b'IDAT'));stride=width*8+1;assert len(raw)==stride*height and set(raw[::stride])=={0}
        pixels=b''.join(raw[y*stride+1:(y+1)*stride] for y in range(height));samples=array.array('H');samples.frombytes(pixels)
        if sys.byteorder=='little':samples.byteswap()
        alpha=samples[3::4];assert min(alpha)==max(alpha)==65535
        rgb=bytearray(width*height*3);changed=0;maximum_error=0
        for c in range(3):
            values=samples[c::4];mapped=bytes(round(v/257) for v in values);rgb[c::3]=mapped
            errors=[abs(v-out*257) for v,out in zip(values,mapped)];changed+=sum(e!=0 for e in errors);maximum_error=max(maximum_error,max(errors))
        colors=[(k,p) for k,p in chunks if k in (b'iCCP',b'cICP',b'gAMA',b'cHRM',b'sRGB')]
        observation=verify_output(output,width,height,bytes(rgb),colors)
        assert r['rgb_samples_not_exactly_representable']==changed and r['maximum_native_sample_error']==maximum_error==128
        assert r['source_bit_depth']==16 and r['source_color_type']==6 and r['native_alpha_all_opaque'] is True and r['native_rgb_samples_unchanged'] is False
        assert r['color_chunks_sha256']==observation['color_chunk_payload_sha256']
        assert r['quantization']=='round16to8: (sample + 128) // 257'
        author=next(x for x in authormanifest['exports'] if x['file']==r['file']);assert sha(output)==r['sha256']==author['sha256']
        return {'historical_tool_control_only':True,'source_sha256':sha(source),'native_source_alpha_all65535':True,'native_rgb_sample_count':width*height*3,'not_exactly_8bit_representable':changed,'maximum_native_error':maximum_error,'independent_mapping':'Python round(native_sample / 257); no ties for integer16-bit samples','source_first_pixel_rgb16':list(samples[:3]),'output_first_pixel_rgb8':list(rgb[:3]),'matches_author_output':True,'output':observation}
    record('historical-'+row['file'],historical)

summary={'reviewed_tool_sha256':sha(TOOL),'live_tool_sha256_after':sha(REPO/'release/store/tools/export_screenshots.py'),'candidate_fingerprint':CANDIDATE,'historical_control_only':True,'source_sha256_before':source_before,'source_sha256_after':pins(HIST),'native_sources_unchanged':source_before==pins(HIST),'old_failure_evidence_unchanged':old_before==pins(OLD),'old_evidence_sha256_before':old_before,'case_count':len(results),'all_passed':all(r['passed'] for r in results),'failed_cases':[r['case'] for r in results if not r['passed']],'results':results}
(HERE/'checks.json').write_text(json.dumps(summary,indent=2)+'\n')
print('COMPLETE',summary['case_count'],'all_passed',summary['all_passed'],'native_sources_unchanged',summary['native_sources_unchanged'],'old_failure_evidence_unchanged',summary['old_failure_evidence_unchanged'],flush=True)
