#!/usr/bin/env python3
"""Export opaque RGB8 PNGs: same geometry, explicit native-depth quantization."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import zlib

from PIL import Image


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def png_chunk(kind, payload):
    return (struct.pack('>I', len(payload)) + kind + payload
            + struct.pack('>I', zlib.crc32(kind + payload) & 0xffffffff))


def native_rgb8(source):
    """Decode noninterlaced RGB(A) PNG at native depth; never infer alpha via Pillow.

    PNG Third Edition sections7/9: filters operate on bytes, including16-bit
    samples. Round each16-bit RGB sample to nearest8-bit: (v+128)//257.
    Preserve color-space chunks verbatim; no gamut conversion or retagging.
    """
    data = source.read_bytes()
    require(data[:8] == b'\x89PNG\r\n\x1a\n', 'Expected PNG signature')
    offset, chunks = 8, []
    while offset < len(data):
        require(offset + 12 <= len(data), 'Truncated PNG chunk')
        length = struct.unpack_from('>I', data, offset)[0]
        require(offset + 12 + length <= len(data), 'Truncated PNG payload')
        kind = data[offset+4:offset+8]
        payload = data[offset+8:offset+8+length]
        crc = struct.unpack_from('>I', data, offset+8+length)[0]
        require(zlib.crc32(kind + payload) & 0xffffffff == crc, 'PNG CRC mismatch')
        chunks.append((kind, payload))
        offset += length + 12
        if kind == b'IEND':
            require(length == 0 and offset == len(data), 'Unexpected data after IEND')
            break
    require(chunks and chunks[0][0] == b'IHDR' and len(chunks[0][1]) == 13
            and chunks[-1] == (b'IEND', b''), 'Invalid PNG structure')
    kinds = [kind for kind, _ in chunks]
    require(kinds.count(b'IHDR') == 1 and b'IDAT' in kinds, 'Invalid header/data count')
    require(not any(k in kinds for k in (b'tRNS', b'acTL', b'fcTL', b'fdAT')),
            'Transparency keys and animated PNGs are not supported')
    require(all(k in (b'IHDR', b'IDAT', b'IEND') or k[0] & 32 for k in kinds),
            'Unsupported critical PNG chunk')
    width, height, depth, color, compression, filtering, interlace = struct.unpack('>IIBBBBB', chunks[0][1])
    require(0 < width and 0 < height and width * height <= 16_000_000,
            'Native PNG dimensions exceed bound')
    require(depth in (8,16) and color in (2,6) and (compression, filtering, interlace) == (0,0,0),
            'Expected noninterlaced8/16-bit RGB/RGBA PNG')
    channels = 3 if color == 2 else 4
    step = channels * (depth // 8)
    stride = width * step
    expected = (stride + 1) * height
    decoder = zlib.decompressobj()
    raw = decoder.decompress(b''.join(p for k,p in chunks if k == b'IDAT'), expected + 1)
    require(len(raw) == expected and decoder.eof and not decoder.unused_data
            and not decoder.unconsumed_tail, 'PNG raster length/compression mismatch')
    rgb = bytearray(width * height * 3)
    previous = bytearray(stride)
    output_position = 0
    changed, maximum_error = 0, 0
    filters = set()
    for row in range(height):
        start = row * (stride + 1)
        method = raw[start]
        require(method <= 4, 'Invalid PNG filter')
        filters.add(method)
        scan = bytearray(raw[start+1:start+1+stride])
        if method:
            for index in range(stride):
                left = scan[index-step] if index >= step else 0
                above = previous[index]
                upper_left = previous[index-step] if index >= step else 0
                if method == 1:
                    predictor = left
                elif method == 2:
                    predictor = above
                elif method == 3:
                    predictor = (left + above) // 2
                else:
                    pa, pb, pc = abs(above-upper_left), abs(left-upper_left), abs(left+above-2*upper_left)
                    predictor = left if pa <= pb and pa <= pc else (above if pb <= pc else upper_left)
                scan[index] = (scan[index] + predictor) & 255
        for pixel in range(width):
            base = pixel * step
            if color == 6:
                alpha = scan[base+3] if depth == 8 else (scan[base+6] << 8) | scan[base+7]
                require(alpha == (255 if depth == 8 else 65535), 'Nonopaque native alpha sample')
            for channel in range(3):
                value = scan[base+channel] if depth == 8 else (scan[base+2*channel] << 8) | scan[base+2*channel+1]
                quantized = value if depth == 8 else (value + 128) // 257
                rgb[output_position] = quantized
                output_position += 1
                if depth == 16:
                    error = abs(value - quantized * 257)
                    changed += error != 0
                    maximum_error = max(maximum_error, error)
        previous = scan
    colors = [(k,p) for k,p in chunks if k in (b'iCCP', b'cICP', b'gAMA', b'cHRM', b'sRGB')]
    require(len({k for k,_ in colors}) == len(colors), 'Duplicate color-space chunk')
    details = {'source_bit_depth':depth, 'source_color_type':color,
               'native_alpha_all_opaque':True, 'source_filters':sorted(filters),
               'quantization':'identity' if depth == 8 else 'round16to8: (sample + 128) // 257',
               'rgb_samples_not_exactly_representable':changed, 'maximum_native_sample_error':maximum_error,
               'native_rgb_samples_unchanged':changed == 0,
               'color_chunks_sha256':{k.decode():hashlib.sha256(p).hexdigest() for k,p in colors},
               'non_color_ancillary_metadata':'omitted; no source data modified'}
    return width, height, bytes(rgb), colors, details


def encode_rgb8(width, height, pixels, colors):
    rows = b''.join(b'\x00' + pixels[y*width*3:(y+1)*width*3] for y in range(height))
    return (b'\x89PNG\r\n\x1a\n'
            + png_chunk(b'IHDR', struct.pack('>IIBBBBB', width,height,8,2,0,0,0))
            + b''.join(png_chunk(k,p) for k,p in colors)
            + png_chunk(b'IDAT', zlib.compress(rows, 6)) + png_chunk(b'IEND', b''))


def export(capture, output, candidate):
    require(bool(re.fullmatch(r'[a-f0-9]{64}', candidate)), 'Exact candidate fingerprint required')
    capture = capture.resolve()
    report_file, manifest_file = capture / 'verification.json', capture / 'capture-manifest.json'
    report = json.loads(report_file.read_text())
    manifest = json.loads(manifest_file.read_text())
    require(report.get('passed') is True and report.get('scenario') == 'capture-gallery', 'Successful native gallery required')
    require(manifest.get('native_verification_passed') is True, 'Capture is not native-qualified')
    require(report.get('candidate_fingerprint') == manifest.get('candidate_fingerprint') == candidate,
            'Capture belongs to a different candidate')
    require(report.get('evidence_sha256', {}).get('capture-manifest.json') == digest(manifest_file),
            'Manifest differs from native verification')
    for key, other in [('device', 'device'), ('device_label', 'label'), ('platform', 'platform'), ('run_id', 'run_id')]:
        require(manifest.get(key) == report.get(other), 'Capture identity mismatch: ' + key)
    require(manifest.get('harness_sha256') == report.get('harness_sha256', {}).get('harness.dart'),
            'Capture harness mismatch')
    rows = manifest.get('screenshots')
    require(isinstance(rows, list) and len(rows) == 4, 'Expected four declared native screens')
    before = {report_file: digest(report_file), manifest_file: digest(manifest_file)}
    decoded = []
    for row in rows:
        name = row['file']
        require(isinstance(name, str) and re.fullmatch(r'[A-Za-z0-9_-]+\.png', name), 'Unsafe screenshot filename')
        source = capture / name
        require(source.resolve().parent == capture and source.is_file(), 'Screenshot is outside capture directory')
        require(source.stat().st_size == row['bytes'] and source.stat().st_size <= 20 * 1024 * 1024,
                'Unexpected screenshot size')
        before[source] = digest(source)
        require(before[source] == row['sha256'] == report.get('evidence_sha256', {}).get(name),
                'Screenshot differs from native evidence')
        width, height, pixels, colors, precision = native_rgb8(source)
        require((width, height) == (row['width'], row['height']), 'Unexpected captured dimensions')
        decoded.append((name, width, height, pixels, colors, precision))
    require(len({row[0] for row in decoded}) == len(decoded), 'Duplicate screenshot filename')
    output.mkdir(parents=True, exist_ok=False)
    exports = []
    for name, width, height, pixels, colors, precision in decoded:
        path = output / name
        with path.open('xb') as handle:
            handle.write(encode_rgb8(width, height, pixels, colors))
        with Image.open(path) as actual:
            require(actual.mode == 'RGB' and actual.size == (width,height) and actual.tobytes() == pixels
                    and 'transparency' not in actual.info, 'Export differs from declared RGB8 mapping')
        exports.append({'file': name, 'sha256': digest(path), 'width': width, 'height': height,
                        'bytes': path.stat().st_size, 'mode': 'RGB', 'output_bit_depth':8,
                        'declared_rgb8_mapping_verified':True, **precision})
    require(all(digest(path) == value for path, value in before.items()), 'Native source changed during export')
    result = {'candidate_fingerprint': candidate, 'capture_directory': str(capture),
              'native_verification_sha256': before[report_file], 'capture_manifest_sha256': before[manifest_file],
              'tool_sha256': digest(Path(__file__)), 'source_sha256': {path.name: value for path, value in before.items()},
              'exports': exports, 'operation': 'Verify native opacity, remove alpha, round16-bit RGB to8-bit where needed; preserve dimensions and color-space definitions.',
              'crop_scale_composite_or_invented_ui': False, 'source_unchanged': True,
              'store_dimensions_qualified': False, 'visual_selection_qualified': False,
              'public_submission': False}
    (output / 'export-manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--candidate', required=True)
    args = parser.parse_args()
    print(json.dumps(export(args.capture, args.output, args.candidate), indent=2))
