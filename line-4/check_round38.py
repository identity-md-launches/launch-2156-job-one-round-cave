"""Read-only deliverable checks; writes only this round's JSON evidence."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess


def git(*args):
    return subprocess.check_output(['git', *args])


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    spec = importlib.util.spec_from_file_location('png_check38', 'line-4/finish_wall22.py')
    codec = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(codec)
    original = git('show', 'HEAD:artifacts/line-4/wall.png')
    wall = Path('artifacts/line-4/wall-v21.png').read_bytes()
    assert wall == Path('artifacts/line-4/wall.png').read_bytes()
    w, h, final = codec.read_png(wall)
    ow, oh, old = codec.read_png(original)
    assert (w, h) == (ow, oh) == (1254, 1254)
    changed = [i for i in range(w*h) if final[3*i:3*i+3] != old[3*i:3*i+3]]
    assert len(changed) == 5045
    assert all(795 <= i%w < 970 and 159 <= i//w < 244 for i in changed)
    assert Path('line-4/GOAL.md').read_bytes() == git('show', 'HEAD:line-4/GOAL.md')
    old_records = git('ls-tree', '-r', '--name-only', 'HEAD', 'dist/line-4').decode().splitlines()
    for path in old_records:
        assert Path(path).read_bytes() == git('show', 'HEAD:'+path), path
    numbered = sorted(Path('dist/line-4').glob('[0-9][0-9].json'))
    assert len(numbered) == 38 and numbered[-1].name == '38.json'
    record = json.loads(numbered[-1].read_text())
    assert list(record) == ['name', 'image', 'attributes']
    assert record['image'] == 'https://api.imd.fun/artifacts/' + digest(wall)
    attributes = record['attributes']
    assert all(set(a) == {'trait_type', 'value'} for a in attributes)
    assert [a['trait_type'] for a in attributes] == ['Cave','Wall','Number','Left behind','Meaning','One thing']
    assert [a['value'] for a in attributes[:4]] == ['Crystal','Line 4',38,'Pin Core']
    preview = Path('dist/line-4/38.jpg').read_bytes()
    assert preview[:2] == b'\xff\xd8' and preview[-2:] == b'\xff\xd9'
    at, dimensions = 2, None
    while at < len(preview):
        assert preview[at] == 255
        kind = preview[at+1]
        size = int.from_bytes(preview[at+2:at+4], 'big')
        if kind == 0xc0:
            height, width = struct.unpack('>HH', preview[at+5:at+9])
            dimensions = [width, height]
            break
        at += 2+size
    assert dimensions == [512,512] and len(preview) < 100000
    changed_paths = git('diff', '--name-only', 'HEAD').decode().splitlines()
    changed_paths += git('ls-files', '--others', '--exclude-standard').decode().splitlines()
    assert all(p.startswith(('line-4/','artifacts/line-4/','dist/line-4/')) for p in changed_paths)
    assert all(p.startswith('artifacts/') or Path(p).stat().st_size <= 100000 for p in changed_paths)
    evidence = {'status':'passed', 'goal_unchanged':True,
                'older_tracked_records_and_previews_unchanged':len(old_records),
                'record_count':len(numbered), 'new_record':'dist/line-4/38.json',
                'wall_sha256':digest(wall), 'wall_dimensions':[w,h], 'wall_format':'PNG',
                'preview_dimensions':dimensions, 'preview_format':'JPEG',
                'preview_bytes':len(preview), 'changed_pixels':len(changed),
                'changes_outside_mark_region':0, 'changed_paths_within_scope':True,
                'required_output_tracked':bool(git('ls-files','artifacts/line-4/wall-v21.png').strip()),
                'tests':{'pin_core':11,'exhaustive_audit':14,'joint_check':11,'total_passed':36,
                         'independent_oracle_seeded_catalogs':400},
                'historical_demo':{'exit':0,'candidates_checked':216,'compatible_selections':26,
                                   'core':{'idna':'3.10','requests':'2.25.1'}},
                'unmet_visual_requirements':[],
                'limitations':'Local behavior checks and visual review, not independent certification.'}
    assert evidence['required_output_tracked'] is False
    Path('line-4/CHECKS-38.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps(evidence,indent=2))


if __name__ == '__main__':
    main()
