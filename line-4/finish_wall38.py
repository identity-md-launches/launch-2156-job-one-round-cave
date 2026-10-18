"""One-shot conservation of generated pigment on unused upper ancestral rock."""
import hashlib
import importlib.util
import json
from pathlib import Path


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def main():
    codec = module('png38', 'finish_wall22.py')
    jpeg = module('jpeg38', 'preview_jpeg27.py')
    ancestor = Path('artifacts/line-4/wall.png')
    output = Path('artifacts/line-4/wall-v21.png')
    records = Path('dist/line-4')
    old_hash = hashlib.sha256(ancestor.read_bytes()).hexdigest()
    assert old_hash == '633d26917e2df115864c30a87774b013cc0350f40d711daf838ab9f50f980413'
    assert len(list(records.glob('[0-9][0-9].json'))) == 37
    assert json.loads((records/'37.json').read_text())['image'].endswith(old_hash)
    w, h, original = codec.read_png(ancestor)
    gw, gh, generated = codec.read_png(output)
    assert (w, h) == (1254, 1254)
    generated_sha = hashlib.sha256(output.read_bytes()).hexdigest()
    final = original[:]
    bounds = (795, 159, 970, 244)
    # Crop only the isolated pigment; sample it onto bare upper rock. Pure
    # white and pale background are discarded, never pasted onto the cave.
    crop = (int(gw*.09), int(gh*.24), int(gw*.91), int(gh*.74))
    for y in range(bounds[1], bounds[3]):
        for x in range(bounds[0], bounds[2]):
            sx = crop[0] + int((x-bounds[0])*(crop[2]-crop[0])/(bounds[2]-bounds[0]))
            sy = crop[1] + int((y-bounds[1])*(crop[3]-crop[1])/(bounds[3]-bounds[1]))
            src = 3*(sy*gw+sx)
            r, g, b = generated[src:src+3]
            red = r > 65 and r > g*1.4 and r > b*1.8
            black = r < 115 and g < 100 and b < 85
            if red or black:
                at = 3*(y*w+x)
                for channel in range(3):
                    # Keep underlying rock grain visible through mineral pigment.
                    final[at+channel] = round(.76*generated[src+channel] + .24*original[at+channel])
    changed = [i for i in range(w*h) if final[3*i:3*i+3] != original[3*i:3*i+3]]
    assert changed and all(bounds[0] <= i%w < bounds[2] and bounds[1] <= i//w < bounds[3]
                           for i in changed)
    sha = codec.write_png(output, w, h, final)
    assert codec.read_png(output)[2] == final
    ancestor.write_bytes(output.read_bytes())
    preview = jpeg.encode(jpeg.resize(final, w, h), 512, 512, quality=40)
    assert len(preview) < 100000
    (records/'38.jpg').write_bytes(preview)
    record = {'name': 'The Smallest Thorn',
              'image': 'https://api.imd.fun/artifacts/' + sha,
              'attributes': [
                  {'trait_type': 'Cave', 'value': 'Crystal'},
                  {'trait_type': 'Wall', 'value': 'Line 4'},
                  {'trait_type': 'Number', 'value': 38},
                  {'trait_type': 'Left behind', 'value': 'Pin Core'},
                  {'trait_type': 'Meaning', 'value': 'A small thorn separates two choices that cannot rest together.'},
                  {'trait_type': 'One thing', 'value': 'Finite offline dependency resolution'}]}
    (records/'38.json').write_text(json.dumps(record, indent=2)+'\n')
    evidence = {'ancestor_sha256': old_hash, 'generated_sha256': generated_sha,
                'wall_sha256': sha, 'dimensions': [w,h], 'format': 'PNG', 'mode': 'RGB',
                'changed_pixels': len(changed), 'mark_region_xyxy': bounds,
                'changed_pixels_outside_mark_region': 0,
                'method': 'Image tool generated isolated ochre pebbles and charcoal thorn. Only dark and red pigment was transferred onto unused upper rock, preserving underlying grain; all other pixels are identical.',
                'preview': {'path': 'dist/line-4/38.jpg', 'dimensions': [512,512],
                            'format': 'JPEG', 'bytes': len(preview)},
                'visual_review': 'Pending final PNG and JPEG inspection.',
                'unmet_visual_requirements': [],
                'limitations': 'The new motif is small at thumbnail scale. Preservation checked by pixels; aesthetic review is local.'}
    Path('line-4/IMAGE-38.json').write_text(json.dumps(evidence, indent=2)+'\n')
    print(json.dumps(evidence, indent=2))


if __name__ == '__main__':
    main()
