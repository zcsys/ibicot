import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import zlib

ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('exporter', ROOT/'release/store/tools/export_screenshots.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

def chunk(k,p):
    return struct.pack('>I',len(p))+k+p+struct.pack('>I',zlib.crc32(k+p)&0xffffffff)

def filtered(row,previous,step,method):
    output=[]
    for i,value in enumerate(row):
        a=row[i-step] if i>=step else 0;b=previous[i];c=previous[i-step] if i>=step else 0
        p=a+b-c
        predictions=[a,b,c]
        paeth=min(range(3),key=lambda index:abs(p-predictions[index]))
        predictor=[0,a,b,(a+b)//2,predictions[paeth]][method]
        output.append((value-predictor)%256)
    return bytes([method]+output)

def fixture(depth,channels,method,alpha=None,trns=False):
    values=[0,128,129,256,257,65535,2924,6324,8752,30000,50000,10000]
    if depth==8:values=[v//257 for v in values]
    maximum=255 if depth==8 else 65535
    full=[]
    for index in range(4):
        full.extend(values[index*3:index*3+3])
        if channels==4:full.append(maximum if alpha is None else alpha)
    data=bytes(full) if depth==8 else struct.pack('>'+str(len(full))+'H',*full)
    stride=2*channels*(depth//8);first=data[:stride];second=data[stride:]
    raster=filtered(first,bytes(stride),channels*(depth//8),method)+filtered(second,first,channels*(depth//8),method)
    header=struct.pack('>IIBBBBB',2,2,depth,2 if channels==3 else 6,0,0,0)
    extra=chunk(b'tRNS',struct.pack('>HHH',0,0,0)) if trns else b''
    png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',header)+chunk(b'cICP',bytes([12,13,0,1]))+extra+chunk(b'IDAT',zlib.compress(raster))+chunk(b'IEND',b'')
    expected=bytes(values if depth==8 else [(v+128)//257 for v in values])
    return png,expected

checks=[]
with tempfile.TemporaryDirectory() as directory:
    p=Path(directory)/'input.png'
    for depth in (8,16):
        for channels in (3,4):
            for method in range(5):
                png,expected=fixture(depth,channels,method);p.write_bytes(png)
                width,height,pixels,colors,details=mod.native_rgb8(p)
                assert (width,height,pixels)==(2,2,expected)
                assert colors==[(b'cICP',bytes([12,13,0,1]))]
                result=mod.encode_rgb8(width,height,pixels,colors)
                p.write_bytes(result);assert mod.native_rgb8(p)[2]==expected
                checks.append(f'RGB{depth}/{channels}channels/filter{method}: exact declared mapping and roundtrip')
    for name,png in [
        ('native alpha65534',fixture(16,4,0,alpha=65534)[0]),
        ('native alpha254',fixture(8,4,0,alpha=254)[0]),
        ('RGB+tRNS',fixture(8,3,0,trns=True)[0]),
        ('CRC',fixture(8,3,0)[0][:-1]+b'X'),
        ('truncated',fixture(8,3,0)[0][:-10]),
        ('trailing data',fixture(8,3,0)[0]+b'X'),
    ]:
        p.write_bytes(png)
        try:mod.native_rgb8(png and p)
        except ValueError:checks.append(name+': rejected')
        else:raise AssertionError(name)
print(json.dumps({'cases':checks,'count':len(checks),'native_execution':False},indent=2))
