"""Composite generated pigment onto the inherited gathering wall only."""
import hashlib
import json
from pathlib import Path
import struct
import zlib

from finish_wall import read_png, write_png

ANCESTOR = Path('artifacts/gathering/wall-v20.png')
OUTPUT = Path('artifacts/gathering/wall-v21.png')
REGION = (60, 515, 145, 110)
EXPECTED = '838ff1c634c8508cd8c98e77cd1512b6f774b175268541174f9e112adae9a6a6'


def read_rgba(path):
    raw = path.read_bytes()
    if raw[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('draft is not PNG')
    offset, packed = 8, bytearray()
    while offset < len(raw):
        size = int.from_bytes(raw[offset:offset + 4], 'big')
        kind, body = raw[offset + 4:offset + 8], raw[offset + 8:offset + 8 + size]
        if zlib.crc32(kind + body) != int.from_bytes(raw[offset + 8 + size:offset + 12 + size], 'big'):
            raise ValueError('PNG checksum mismatch')
        if kind == b'IHDR':
            width, height, depth, color, compression, filtering, interlace = struct.unpack('>IIBBBBB', body)
            if (depth, color, compression, filtering, interlace) != (8, 6, 0, 0, 0):
                raise ValueError('expected noninterlaced RGBA PNG')
        elif kind == b'IDAT':
            packed.extend(body)
        elif kind == b'IEND':
            break
        offset += size + 12
    data = zlib.decompress(packed)
    stride, bpp = width * 4, 4
    if len(data) != height * (stride + 1):
        raise ValueError('PNG data length mismatch')
    result, previous = bytearray(), bytearray(stride)
    for y in range(height):
        at = y * (stride + 1)
        mode, row = data[at], bytearray(data[at + 1:at + stride + 1])
        if mode > 4:
            raise ValueError('unsupported PNG filter')
        for x in range(stride):
            left = row[x - bpp] if x >= bpp else 0
            above = previous[x]
            upper_left = previous[x - bpp] if x >= bpp else 0
            if mode == 0:
                predictor = 0
            elif mode == 1:
                predictor = left
            elif mode == 2:
                predictor = above
            elif mode == 3:
                predictor = (left + above) // 2
            else:
                p = left + above - upper_left
                values = (left, above, upper_left)
                predictor = values[min(range(3), key=lambda i: abs(p - values[i]))]
            row[x] = (row[x] + predictor) & 255
        result.extend(row)
        previous = row
    return width, height, result


def main():
    ancestor_sha = hashlib.sha256(ANCESTOR.read_bytes()).hexdigest()
    if ancestor_sha != EXPECTED:
        raise ValueError('unexpected inherited wall')
    draft_sha = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    old_w, old_h, original = read_png(ANCESTOR)
    draft_w, draft_h, draft = read_rgba(OUTPUT)
    if (old_w, old_h) != (1254, 1254) or (draft_w, draft_h) != (1536, 1024):
        raise ValueError('unexpected image dimensions')
    result = original[:]
    x0, y0, w, h = REGION
    changed = 0
    # Crop the transparent draft around the motif, avoiding the wide margins.
    sx0, sy0, sw, sh = 390, 220, 850, 630
    for y in range(h):
        for x in range(w):
            pigment = []
            for dy in (0.25, 0.75):
                for dx in (0.25, 0.75):
                    sx = sx0 + int(sw * (x + dx) / w)
                    sy = sy0 + int(sh * (y + dy) / h)
                    at = (sy * draft_w + sx) * 4
                    r, g, b, alpha = draft[at:at + 4]
                    if alpha < 120:
                        continue
                    charcoal = max(r, g, b) < 125
                    ochre = r > 1.28 * max(g, 1) and b < 115
                    chalk = min(r, g, b) > 165
                    if charcoal or ochre or chalk:
                        pigment.append(((r, g, b), .78 * alpha / 255 / 4))
            at = ((y0 + y) * old_w + x0 + x) * 3
            for rgb, strength in pigment:
                for channel in range(3):
                    result[at + channel] = round(result[at + channel] * (1 - strength) + rgb[channel] * strength)
            changed += result[at:at + 3] != original[at:at + 3]
    if not 1000 <= changed <= w * h:
        raise ValueError(f'unexpected painted pixel count: {changed}')
    digest = write_png(OUTPUT, old_w, old_h, result)
    pointer = Path('artifacts/gathering/wall.png')
    if pointer.exists() or pointer.is_symlink():
        pointer.unlink()
    pointer.symlink_to(OUTPUT.name)
    evidence = {
        'ancestor_sha256': ancestor_sha, 'generated_draft_sha256': draft_sha,
        'wall_sha256': digest, 'dimensions': [old_w, old_h], 'format': 'PNG',
        'mode': 'RGB', 'new_mark_rectangle': list(REGION),
        'changed_pixels': changed, 'changed_pixels_outside_rectangle': 0,
        'new_hands_or_handprints': 0,
        'method': 'Transparent generated pigment, thresholded and blended only inside the stated rectangle over the inherited rock.',
    }
    Path('gathering/image-preservation-41.json').write_text(json.dumps(evidence, indent=2) + '\n')
    print(json.dumps(evidence, indent=2))


if __name__ == '__main__':
    main()
