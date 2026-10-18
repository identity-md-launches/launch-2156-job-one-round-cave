"""Check gathering 41 output bytes, records, ancestry and permitted paths."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

from check_deliverable import jpeg_size
from check_round41 import fingerprints
from finish_wall import read_png


def load(name):
    return json.loads(Path(name).read_text())


def main():
    checks = load('gathering/checks-41.json')
    protected = fingerprints()
    assert checks['line_files_unchanged']
    assert len(protected) == checks['protected_files_count']
    assert hashlib.sha256(json.dumps(protected, sort_keys=True).encode()).hexdigest() == checks['protected_files_sha256']
    assert len(checks['suites']) == 74 and checks['total_tests'] == 958
    assert len(checks['demos']) == 86
    assert all(row['exit'] == row['expected_exit'] for row in checks['suites'] + checks['demos'])
    latest = load('gathering/latest-checks-41.json')
    assert all(latest[f'line_{n}']['exit'] == 0 for n in range(1, 5))
    assert latest['line_3']['no_regressions']
    shared = load('gathering/shared-checks-41.json')
    assert len(shared['suites']) == 5 and shared['total_tests'] == 151
    assert all(row['exit'] == 0 for row in shared['suites'])
    assert all(row['exit'] == 0 for row in shared['demos'])

    wall = Path('artifacts/gathering/wall-v21.png')
    ancestor = Path('artifacts/gathering/wall-v20.png')
    width, height, painted = read_png(wall)
    aw, ah, old = read_png(ancestor)
    evidence = load('gathering/image-preservation-41.json')
    assert (width, height) == (aw, ah) == (1254, 1254)
    digest = hashlib.sha256(wall.read_bytes()).hexdigest()
    assert digest == evidence['wall_sha256']
    assert hashlib.sha256(ancestor.read_bytes()).hexdigest() == evidence['ancestor_sha256']
    x0, y0, w, h = evidence['new_mark_rectangle']
    changed = outside = 0
    for i in range(width * height):
        if painted[3*i:3*i+3] != old[3*i:3*i+3]:
            changed += 1
            x, y = i % width, i // width
            outside += not (x0 <= x < x0+w and y0 <= y < y0+h)
    assert changed == evidence['changed_pixels'] == 6663 and outside == 0
    assert Path('artifacts/gathering/wall.png').resolve() == wall.resolve()
    assert wall.as_posix() not in subprocess.check_output(['git', 'ls-files', '--', str(wall)]).decode().splitlines()

    record = load('dist/gathering/41.json')
    assert set(record) == {'name', 'image', 'attributes'}
    assert record['image'] == 'https://api.imd.fun/artifacts/' + digest
    assert len(record['attributes']) == 6
    assert all(set(row) == {'trait_type', 'value'} for row in record['attributes'])
    traits = {row['trait_type']: row['value'] for row in record['attributes']}
    assert set(traits) == {'Cave', 'Wall', 'Number', 'Left behind', 'Meaning', 'One thing'}
    assert traits['Cave'] == 'Crystal' and traits['Wall'] == 'Gathering'
    assert type(traits['Number']) is int and traits['Number'] == 41
    assert traits['One thing'] == 'Gathering' and traits['Left behind'] == 'Merged Pin Review'
    preview = Path('dist/gathering/41.jpg')
    assert jpeg_size(preview.read_bytes()) == (512, 512)
    assert preview.stat().st_size <= 100000

    goals = [{'line': n, 'goal': Path(f'line-{n}/GOAL.md').read_text().strip()} for n in range(1, 5)]
    assert load('dist/goals.json') == goals
    page = Path('dist/index.html').read_text()
    groups = json.loads(re.search(r'<script id="records" type="application/json">(.*?)</script>', page, re.S)[1])
    assert len(groups) == 5
    total = pending = 0
    for group, folder in zip(groups, ('line-1', 'line-2', 'line-3', 'line-4', 'gathering')):
        paths = sorted(Path('dist', folder).glob('[0-9][0-9].json'), reverse=True)
        expected = [{'number': int(p.stem), 'path': p.relative_to('dist').as_posix(), **load(p)}
                    for p in paths]
        assert group['records'] == expected
        total += len(paths)
        for row in expected:
            if row['name'] == 'Not painted yet':
                pending += 1
                assert not Path('dist', row['path']).with_suffix('.jpg').exists()
    assert total == 198 and pending == 100
    assert Path('gathering/COINS.md').read_text().startswith('none\n')
    assert not Path('gathering/coin-order.json').exists()
    assert not Path('gathering/deploy-order.json').exists()
    for folder in ('gathering', 'shared', 'dist'):
        assert all(p.stat().st_size <= 100000 for p in Path(folder).rglob('*') if p.is_file())
    changed_names = subprocess.check_output(['git', 'diff', '--name-only', '-z']).decode().split('\0')
    new_names = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard', '-z']).decode().split('\0')
    for name in changed_names + new_names:
        if name:
            assert name.startswith(('gathering/', 'shared/', 'dist/', 'artifacts/gathering/', 'test/scratch/')), name

    review = {
        'number': 41, 'line_files_and_records_unchanged': True,
        'line_suites_passed': 74, 'line_tests_passed': 958, 'expected_demo_statuses': 86,
        'direct_current_trials_passed': 4, 'shared_tests_passed': 151,
        'gallery_records': total, 'preserved_placeholders': pending,
        'wall': {'path': str(wall), 'dimensions': [width, height], 'format': 'PNG',
                 'mode': 'RGB', 'sha256': digest},
        'preview': {'path': str(preview), 'dimensions': [512, 512], 'format': 'JPEG',
                    'bytes': preview.stat().st_size},
        'changed_pixels': changed, 'changed_pixels_outside_rectangle': outside,
        'visual_review': {
            'method': 'Full PNG and 512-pixel JPEG explicitly inspected with view_image.',
            'pepe': 'Inherited heavy-lidded eyes and wide mouth remain visible.',
            'hands': 'No hands or handprints added; inherited folded limbs expose no fingers to count.',
            'text_or_prohibited_symbols_observed': False,
            'limitation': 'The small new motif is darker at thumbnail scale.'},
        'unmet_visual_requirements': [], 'coins': 'none',
    }
    Path('gathering/REVIEW-41.json').write_text(json.dumps(review, indent=2) + '\n')
    print(json.dumps(review, indent=2))


if __name__ == '__main__':
    main()
