"""Independent actual-pixel audit, not a new converter or creative output."""
from pathlib import Path
from array import array
from collections import Counter
import hashlib,json,struct,sys,zlib
from PIL import Image
ROOT=Path('/Users/csys/Desktop/ibicot/idle')
RAW=ROOT/sys.argv[1];MEDIA=ROOT/sys.argv[2];OUT=ROOT/sys.argv[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def parse(p):
 data=p.read_bytes();assert data[:8]==b'\x89PNG\r\n\x1a\n';at=8;chunks=[]
 while at<len(data):
  n=struct.unpack('>I',data[at:at+4])[0];tag=data[at+4:at+8];body=data[at+8:at+8+n]
  assert len(body)==n and zlib.crc32(tag+body)&0xffffffff==struct.unpack('>I',data[at+8+n:at+12+n])[0]
  chunks.append((tag,body));at+=n+12
 assert at==len(data) and chunks[0][0]==b'IHDR' and chunks[-1]==(b'IEND',b'')
 w,h,depth,ct,comp,filt,inter=struct.unpack('>IIBBBBB',chunks[0][1]);assert comp==filt==inter==0
 assert (depth,ct) in [(16,6),(8,6),(8,2)]
 return {'size':(w,h),'depth':depth,'type':ct,'chunks':chunks}
manifest=json.loads((MEDIA/'screenshots/export-manifest.json').read_text());rows=[]
for rec in manifest['exports']:
 name=rec['file'];source=RAW/name;output=MEDIA/'screenshots'/name;s=parse(source);o=parse(output)
 assert sha(source)==manifest['source_sha256'][name] and sha(output)==rec['sha256']
 assert s['size']==o['size']==(rec['width'],rec['height'])
 assert o['depth']==8 and o['type']==2 and not any(t in [b'tRNS',b'acTL',b'fcTL',b'fdAT'] for t,b in o['chunks'])
 if s['depth']==16:
  assert s['type']==6
  w,h=s['size'];stride=w*8;stream=zlib.decompress(b''.join(b for t,b in s['chunks'] if t==b'IDAT'));assert len(stream)==h*(stride+1)
  filters=sorted(set(stream[y*(stride+1)] for y in range(h)));assert filters==[0],'Actual native 16-bit capture uses unexpected filtering; stop for explicit decoder extension'
  pixels=b''.join(stream[y*(stride+1)+1:(y+1)*(stride+1)] for y in range(h))
  vals=array('H');vals.frombytes(pixels)
  if sys.byteorder=='little':vals.byteswap()
  assert min(vals[3::4])==max(vals[3::4])==65535
  lut=bytes(round(n/257) for n in range(65536));rgba=bytes(lut[v] for v in vals)
  expected=Image.frombytes('RGBA',s['size'],rgba).convert('RGB').tobytes()
  counts=Counter(vals);changed=sum(count for n,count in counts.items() if n%257);maxerror=max(min(n%257,257-n%257) for n in counts)
  alpha=[65535,65535];mapping='Every sample equals independent round(native/257)'
 else:
  with Image.open(source) as im:
   assert im.size==s['size']
   if s['type']==6:assert im.mode=='RGBA' and im.getchannel('A').getextrema()==(255,255)
   else:assert im.mode=='RGB'
   expected=im.convert('RGB').tobytes()
  alpha=[255,255] if s['type']==6 else None;changed=0;maxerror=0;mapping='Every RGB8 source sample preserved exactly'
 with Image.open(output) as im:assert im.mode=='RGB' and im.tobytes()==expected
 assert changed==rec['rgb_samples_not_exactly_representable'] and maxerror==rec['maximum_native_sample_error']
 color={b'iCCP',b'cICP',b'sRGB',b'gAMA',b'cHRM',b'mDCv',b'cLLi'}
 sc=[(t,b) for t,b in s['chunks'] if t in color];oc=[(t,b) for t,b in o['chunks'] if t in color];assert sc==oc
 row={'file':name,'source_sha256':sha(source),'output_sha256':sha(output),'size':s['size'],'source_depth':s['depth'],'source_color_type':s['type'],'source_alpha_range':alpha,'output_depth':8,'output_color_type':2,'mapping':mapping,'nonrepresentable_samples':changed,'maximum_native_sample_error':maxerror,'color_chunks_unchanged':{t.decode():hashlib.sha256(b).hexdigest() for t,b in sc},'all_pixels_checked':True,'crop_resize_composite':False}
 rows.append(row);print(name,'passed',flush=True)
(OUT/'actual-png-analysis.json').write_text(json.dumps(rows,indent=2)+'\n')
