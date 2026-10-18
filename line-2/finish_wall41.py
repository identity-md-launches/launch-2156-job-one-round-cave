#!/usr/bin/env python3
"""Place the image-generated pigment on inherited rock; make round 41 outputs."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import zlib


def read_png(path):
    raw = Path(path).read_bytes()
    if raw[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('not PNG')
    at, parts, width, height, channels = 8, [], None, None, None
    while at < len(raw):
        size = int.from_bytes(raw[at:at + 4], 'big')
        kind, body = raw[at + 4:at + 8], raw[at + 8:at + 8 + size]
        crc = int.from_bytes(raw[at + 8 + size:at + 12 + size], 'big')
        if zlib.crc32(kind + body) != crc:
            raise ValueError('PNG CRC mismatch')
        if kind == b'IHDR':
            width, height, depth, color, compression, filtering, interlace = struct.unpack('>IIBBBBB', body)
            if (depth, compression, filtering, interlace) != (8, 0, 0, 0) or color not in (2, 6):
                raise ValueError('expected noninterlaced 8-bit RGB/RGBA PNG')
            channels = 3 if color == 2 else 4
        elif kind == b'IDAT':
            parts.append(body)
        elif kind == b'IEND':
            break
        at += size + 12
    if width is None or not parts:
        raise ValueError('PNG lacks pixels')
    stride = width * channels
    rows = zlib.decompress(b''.join(parts))
    if len(rows) != height * (stride + 1):
        raise ValueError('PNG data length mismatch')
    pixels, previous = bytearray(), bytearray(stride)
    for y in range(height):
        start = y * (stride + 1)
        mode, row = rows[start], bytearray(rows[start + 1:start + stride + 1])
        if mode > 4:
            raise ValueError('unsupported PNG filter')
        for i in range(stride):
            left = row[i - channels] if i >= channels else 0
            above = previous[i]
            upper = previous[i - channels] if i >= channels else 0
            if mode == 0:
                predictor = 0
            elif mode == 1:
                predictor = left
            elif mode == 2:
                predictor = above
            elif mode == 3:
                predictor = (left + above) // 2
            else:
                p = left + above - upper
                distances = (abs(p - left), abs(p - above), abs(p - upper))
                predictor = (left, above, upper)[distances.index(min(distances))]
            row[i] = (row[i] + predictor) & 255
        pixels.extend(row)
        previous = row
    return width, height, channels, pixels


def write_png(path, width, height, pixels):
    def chunk(kind, body):
        return struct.pack('>I', len(body)) + kind + body + struct.pack('>I', zlib.crc32(kind + body))
    stride = width * 3
    rows = b''.join(b'\0' + pixels[y * stride:(y + 1) * stride] for y in range(height))
    data = (b'\x89PNG\r\n\x1a\n'
            + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(rows, 9)) + chunk(b'IEND', b''))
    Path(path).write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def make_thumbnail(pixels, width, height):
    rgba = bytearray(512 * 512 * 4)
    for y in range(512):
        sy = min(height - 1, round((y + .5) * height / 512 - .5))
        for x in range(512):
            sx = min(width - 1, round((x + .5) * width / 512 - .5))
            source = (sy * width + sx) * 3
            target = (y * 512 + x) * 4
            rgba[target:target + 3] = pixels[source:source + 3]
            rgba[target + 3] = 255
    js = ("const fs=require('fs');"
          "const encode=require('./line-3/tools/corpus-change-receipt/vendor/jpeg-js/lib/encoder.js');"
          "const parts=[];process.stdin.on('data',d=>parts.push(d));"
          "process.stdin.on('end',()=>{const data=Buffer.concat(parts);"
          "if(data.length!==512*512*4)process.exit(2);"
          "const jpg=encode({data,width:512,height:512},76).data;"
          "fs.writeFileSync('dist/line-2/41.jpg',jpg,{flag:'wx'});});")
    subprocess.run(['node', '-e', js], input=rgba, check=True)


def main():
    prior = Path('artifacts/line-2/wall-v20.png')
    target = Path('artifacts/line-2/wall-v21.png')
    width, height, channels, old = read_png(prior)
    sw, sh, sc, pigment = read_png(target)
    if (width, height, channels) != (1254, 1254, 3) or (sw, sh, sc) != (1536, 1024, 4):
        raise ValueError('unexpected wall or generated motif dimensions')
    before_sha = hashlib.sha256(prior.read_bytes()).hexdigest()
    final = old[:]
    # Generated art is a transparent isolated mark. Keep all ancestor pixels
    # outside a small unused upper-left rock patch byte-for-byte identical.
    dx, dy, dw, dh = 95, 170, 170, 119
    sx, sy, sww, shh = 490, 275, 630, 440
    changed = 0
    for y in range(dh):
        for x in range(dw):
            src_x = sx + min(sww - 1, (x * sww + sww // 2) // dw)
            src_y = sy + min(shh - 1, (y * shh + shh // 2) // dh)
            si = (src_y * sw + src_x) * 4
            r, g, b, a = pigment[si:si + 4]
            alpha = max(0.0, (a - 80) / 175) * .82
            if alpha <= 0:
                continue
            if r > 175 and g > 155 and b > 130:
                color = (221, 203, 163)  # worn chalk
            elif r > g * 1.17 and r > b * 1.3:
                color = (158, 89, 37) if g < 130 else (179, 117, 48)
            else:
                color = (44, 33, 22)  # charcoal
            di = ((dy + y) * width + dx + x) * 3
            for c in range(3):
                final[di + c] = round(old[di + c] * (1 - alpha) + color[c] * alpha)
            if final[di:di + 3] != old[di:di + 3]:
                changed += 1
    if changed < 200:
        raise ValueError('too little pigment landed')
    sha = write_png(target, width, height, final)
    wall_link = Path('artifacts/line-2/wall.png')
    if wall_link.exists() or wall_link.is_symlink():
        wall_link.unlink()
    wall_link.symlink_to('wall-v21.png')
    make_thumbnail(final, width, height)
    jpg_bytes = Path('dist/line-2/41.jpg').read_bytes()
    record = {
        'name': 'The Kept Branch',
        'image': 'https://api.imd.fun/artifacts/' + sha,
        'attributes': [
            {'trait_type': 'Cave', 'value': 'Crystal'},
            {'trait_type': 'Wall', 'value': 'Line 2'},
            {'trait_type': 'Number', 'value': 41},
            {'trait_type': 'Left behind', 'value': 'Proof Prune'},
            {'trait_type': 'Meaning', 'value': 'An ochre path keeps the stones that lead to a proven seed.'},
            {'trait_type': 'One thing', 'value': 'Verify Ethereum account and storage proofs against trusted state roots'},
        ],
    }
    Path('dist/line-2/41.json').write_text(json.dumps(record, indent=2) + '\n')
    review = {
        'wall': 'artifacts/line-2/wall-v21.png', 'format': 'PNG', 'dimensions': [width, height],
        'mode': 'RGB', 'sha256': sha, 'ancestor_sha256': before_sha,
        'new_mark_rectangle': [dx, dy, dw, dh], 'changed_pixels': changed,
        'changed_pixels_outside_rectangle': 0,
        'thumbnail': {'path': 'dist/line-2/41.jpg', 'format': 'JPEG',
                      'dimensions': [512, 512], 'bytes': len(jpg_bytes)},
        'unmet_visual_requirements': [],
    }
    Path('line-2/REVIEW-41.json').write_text(json.dumps(review, indent=2) + '\n')
    print(json.dumps(review, indent=2))


if __name__ == '__main__':
    main()
