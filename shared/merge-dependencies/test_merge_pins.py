"""Behavioral integration checks for merge review and exact-release conflicts."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import merge_pins as tool


def text(packages, roots):
    return json.dumps({'packages': packages, 'roots': roots}, sort_keys=True, indent=2) + '\n'


class MergePinsTests(unittest.TestCase):
    def test_historical_clean_merge_and_source_immutability(self):
        paths = [tool.merge.HERE / 'examples' / ('plan-' + p + '.json')
                 for p in tool.LABELS[:-1]]
        before = [p.read_bytes() for p in paths]
        r = tool.demo()
        self.assertTrue(r['review']['clean'])
        self.assertEqual(r['status'], 'incompatible')
        self.assertEqual(r['lost_pin_compatibility_from'], ['base', 'ours'])
        merged = r['catalogs']['merged']
        self.assertEqual(merged['core'], {'idna': '2.10'})
        self.assertEqual(merged['discarded_pins'], {'certifi': '2025.8.3'})
        self.assertGreater(merged['compatible_selections_seen'], 0)
        self.assertEqual(before, [p.read_bytes() for p in paths])

    def test_two_pin_core_and_each_deletion_witness(self):
        catalog = text({'app': {'1': {'dep': '==1'}, '2': {'dep': '==2'}},
                        'dep': {'1': {}, '2': {}}, 'extra': {'1': {}}},
                       {'app': '*', 'extra': '*'})
        pins = {'app': '1', 'dep': '2', 'extra': '1'}
        saved = copy.deepcopy(pins)
        r = tool.assess(catalog, catalog, catalog, pins)
        row = r['catalogs']['merged']
        self.assertEqual(row['core'], {'app': '1', 'dep': '2'})
        self.assertEqual(row['discarded_pins'], {'extra': '1'})
        data = json.loads(r['review']['merged'])
        packages, roots = tool.pin_core.fmt.validate(data)
        for witness in row['deletion_witnesses']:
            selected = witness['selected']
            self.assertEqual(tool.pin_core.checker.assignment(packages, roots, selected), selected)
            for p, v in row['core'].items():
                if p != witness['removed_pin']:
                    self.assertEqual(selected[p], v)
                else:
                    self.assertNotEqual(selected[p], v)
        self.assertEqual(pins, saved)

    def test_compatible_alias_and_unreachable_pin(self):
        raw = text({'app': {'1': {}}, 'unused': {'1': {}}}, {'app': '*'})
        r = tool.assess(raw, raw, raw, {'APP': '1.0'})
        self.assertEqual(r['status'], 'compatible')
        self.assertEqual(r['catalogs']['merged']['witness'], {'app': '1'})
        r = tool.assess(raw, raw, raw, {'unused': '1'})
        self.assertEqual(r['status'], 'incompatible')
        self.assertEqual(r['catalogs']['merged']['core'], {'unused': '1'})

    def test_baseline_unsatisfiable_does_not_blame_pins(self):
        raw = text({'app': {'1': {'missing': '*'}}}, {'app': '*'})
        r = tool.assess(raw, raw, raw, {'app': '1'})
        self.assertEqual(r['status'], 'baseline-unsatisfiable')
        self.assertNotIn('core', r['catalogs']['merged'])

    def test_partial_zero_stays_unknown_exact_budget_is_conclusive(self):
        raw = text({'app': {'1': {'dep': '==2'}}, 'dep': {'1': {}, '2': {}}},
                   {'app': '*'})
        r = tool.assess(raw, raw, raw, {'dep': '1'}, max_assignments=1)
        self.assertEqual(r['status'], 'inconclusive')
        self.assertIsNone(r['lost_pin_compatibility_from'])
        self.assertNotIn('core', r['catalogs']['merged'])
        r = tool.assess(raw, raw, raw, {'dep': '1'}, max_assignments=3)
        self.assertEqual(r['status'], 'incompatible')
        self.assertEqual(r['catalogs']['merged']['checked_assignments'], 3)

    def test_text_conflict_stops_before_dependency_claims(self):
        raw = text({'app': {'1': {}}}, {'app': '*'})
        r = tool.assess(raw, raw.replace('"*"', '">=1"'),
                        raw.replace('"*"', '"<2"'), {'app': '1'})
        self.assertEqual(r['status'], 'text_conflict')
        self.assertIsNone(r['catalogs'])

    def test_invalid_json_catalog_pins_and_budgets(self):
        self.assertEqual(tool.assess('{bad', '{bad', '{bad', {'app': '1'})['status'],
                         'invalid_catalog')
        dup = '{"packages":{},"roots":{"a":"*","a":"*"}}'
        self.assertEqual(tool.assess(dup, dup, dup, {'a': '1'})['status'], 'invalid_catalog')
        raw = text({'app': {'1': {}}}, {'app': '*'})
        for pins in ({}, {'APP': '1', 'app': '1'}, {'app': 'latest'}):
            with self.assertRaises(ValueError):
                tool.assess(raw, raw, raw, pins)
        for budget in (0, True, 1000001):
            with self.assertRaises(ValueError):
                tool.assess(raw, raw, raw, {'app': '1'}, budget)

    def test_cli_statuses_and_external_path_refusal(self):
        script = str(Path(tool.__file__).resolve())
        paths = [str(tool.merge.HERE / 'examples' / ('plan-' + s + '.json'))
                 for s in tool.LABELS[:-1]]
        cases = [(['demo'], 0), (['check', *paths, '--require', 'idna=2.10'], 1),
                 (['check', *paths, '--require', 'idna=3.10'], 0),
                 (['check', *paths, '--require', 'idna=2.10', '--max-assignments', '1'], 3),
                 (['check', *paths, '--require', 'IDNA=3.10', '--require', 'idna=2.10'], 2),
                 (['check', '/outside-merge-pins', *paths[1:], '--require', 'idna=2.10'], 2)]
        for args, expected in cases:
            p = subprocess.run([sys.executable, '-B', script, *args],
                               capture_output=True, text=True, check=False)
            self.assertEqual(p.returncode, expected, (args, p.stderr, p.stdout))
            if expected == 2:
                self.assertEqual(p.stdout, '')

    def test_portable_without_line_folders(self):
        scratch = Path('test/scratch')
        scratch.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as temp:
            target = Path(temp) / 'portable'
            shutil.copytree(tool.merge.HERE, target)
            p = subprocess.run([sys.executable, '-B', str(target / 'merge_pins.py'), 'demo'],
                               capture_output=True, text=True, check=False)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(json.loads(p.stdout)['status'], 'incompatible')


if __name__ == '__main__':
    unittest.main()
