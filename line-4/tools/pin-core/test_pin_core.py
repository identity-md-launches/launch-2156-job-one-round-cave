import contextlib
import copy
import importlib.util
import io
import itertools
from pathlib import Path
import random
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('pin_core', Path(__file__).with_name('pin_core.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def catalog(packages, roots=None):
    return {'packages': packages, 'roots': roots or {'app': '*'}}


def raw_solutions(data):
    """Separate raw-edge oracle for *, ==1 and ==2 synthetic catalogs."""
    packages = data['packages']
    names = list(packages)
    result = []
    for values in itertools.product(*[[None] + list(packages[p]) for p in names]):
        selected = {p: v for p, v in zip(names, values) if v is not None}
        todo, reached, valid = list(data['roots'].items()), set(), True
        while todo:
            p, constraint = todo.pop()
            v = selected.get(p)
            if v is None or (constraint != '*' and v != constraint[2:]):
                valid = False
                break
            if p not in reached:
                reached.add(p)
                todo.extend(packages[p][v].items())
        if valid and reached == set(selected):
            result.append(selected)
    return result


class PinCoreTests(unittest.TestCase):
    def setUp(self):
        self.data = catalog({'app': {'1': {'dep': '==1'}, '2': {'dep': '==2'}},
                             'dep': {'1': {}, '2': {}}, 'extra': {'1': {}}})

    def verify_core(self, out, solutions):
        core = out['core']
        self.assertTrue(core)
        fits = lambda s, pins: all(s.get(p) == v for p, v in pins.items())
        self.assertFalse(any(fits(s, core) for s in solutions))
        self.assertEqual(set(core), {w['removed_pin'] for w in out['deletion_witnesses']})
        for w in out['deletion_witnesses']:
            self.assertIn(w['selected'], solutions)
            self.assertTrue(fits(w['selected'], {p: v for p, v in core.items()
                                               if p != w['removed_pin']}))
            self.assertNotEqual(w['selected'].get(w['removed_pin']), core[w['removed_pin']])

    def test_joint_core_with_redundant_pin(self):
        data = copy.deepcopy(self.data)
        data['roots']['extra'] = '*'
        out = m.pin_core(data, {'app': '1', 'dep': '2', 'extra': '1'})
        self.assertEqual(out['status'], 'incompatible')
        self.assertEqual(out['core'], {'app': '1', 'dep': '2'})
        self.assertEqual(out['discarded_pins'], {'extra': '1'})
        self.verify_core(out, raw_solutions(data))

    def test_unreachable_missing_and_absent_branch_pins(self):
        for pins in ({'extra': '1'}, {'missing': '1'}, {'dep': '9'}):
            out = m.pin_core(self.data, pins)
            self.assertEqual(out['core'], pins)
            self.verify_core(out, raw_solutions(self.data))
        data = catalog({'app': {'1': {}, '2': {'dep': '*'}}, 'dep': {'1': {}}})
        out = m.pin_core(data, {'app': '1', 'dep': '1'})
        self.assertEqual(len(out['core']), 2)
        self.verify_core(out, raw_solutions(data))

    def test_baseline_unsatisfiable_is_distinct(self):
        for data in (catalog({'app': {}}),
                     catalog({'app': {'1': {'missing': '*'}}}),
                     catalog({'app': {'1': {}}}, {'app': '==2'})):
            out = m.pin_core(data, {'app': '1'})
            self.assertEqual(out['status'], 'baseline-unsatisfiable')
            self.assertNotIn('core', out)

    def test_budget_boundaries_and_early_witness(self):
        data = catalog({'app': {'1': {}, '2': {}}})
        out = m.pin_core(data, {'app': '9'}, 1)
        self.assertEqual(out['status'], 'inconclusive')
        self.assertNotIn('core', out)
        self.assertNotIn('deletion_witnesses', out)
        out = m.pin_core(data, {'app': '9'}, 2)
        self.assertEqual(out['checked_assignments'], 2)
        self.assertEqual(out['status'], 'incompatible')
        self.verify_core(out, raw_solutions(data))
        self.assertEqual(m.pin_core(data, {'app': '1'}, 1)['status'], 'compatible')
        self.assertEqual(m.pin_core(data, {'app': '2'}, 1)['status'], 'inconclusive')

    def test_aliases_cycles_numeric_constraints_and_no_mutation(self):
        data = catalog({'My_App': {'1.0': {'dep': '>=2,!=3'}, '2': {'dep': '<2'}},
                        'dep': {'1': {}, '2': {'my.app': '==1'}}}, {'my-app': '*'})
        pins = {'MY.APP': '1', 'DEP': '1.0'}
        before = copy.deepcopy((data, pins))
        out = m.pin_core(data, pins)
        self.assertEqual(out['core'], {'dep': '1', 'my-app': '1.0'})
        self.assertEqual(len(out['deletion_witnesses']), 2)
        self.assertEqual((data, pins), before)
        self.assertEqual(m.pin_core(data, {'my-app': '1'})['witness'],
                         {'dep': '2', 'my-app': '1.0'})

    def test_invalid(self):
        for pins in ({}, [], {'app': 1}, {'app': 'v1'}, {'A_B': '1', 'a-b': '2'}):
            with self.assertRaises(m.fmt.Invalid):
                m.pin_core(self.data, pins)
        for budget in (True, 0, -1, 1.0, '1', 1000001):
            with self.assertRaises(m.fmt.Invalid):
                m.pin_core(self.data, {'app': '1'}, budget)

    def test_deterministic_but_not_cardinality_claim(self):
        # Two independent singleton conflicts: deterministic deletion picks
        # the last one. No promise to list all conflicts is made.
        out = m.pin_core(self.data, {'extra': '1', 'missing': '1'})
        self.assertEqual(out['core'], {'missing': '1'})
        self.assertIn('not necessarily minimum', out['minimality'])
        self.assertEqual(out, m.pin_core(self.data, {'missing': '1', 'extra': '1'}))

    def test_historical_requests(self):
        data = m.fmt.load(m.CHECKER.parent.parent / 'conflict-core/examples/requests-conflict.json')
        data['roots'] = {'requests': '*', 'urllib3': '<2'}
        out = m.pin_core(data, {'requests': '2.25.1', 'idna': '3.10', 'certifi': '2025.8.3'})
        self.assertEqual(out['core'], {'idna': '3.10', 'requests': '2.25.1'})
        self.assertEqual(out['checked_assignments'], 216)
        self.assertEqual(out['compatible_selections_seen'], 26)
        self.assertEqual(len(out['deletion_witnesses']), 2)

    def test_no_solver_calls_and_witness_recheck(self):
        with patch.object(m.fmt, 'solve', side_effect=AssertionError('solver')):
            with patch.object(m.fmt, 'accepts', side_effect=AssertionError('predicate')):
                self.assertEqual(m.pin_core(self.data, {'app': '1', 'dep': '2'})['status'], 'incompatible')
        real = m.checker.assignment
        calls = [0]
        def corrupt(packages, roots, selected):
            calls[0] += 1
            return None if calls[0] > 6 else real(packages, roots, selected)
        with patch.object(m.checker, 'assignment', side_effect=corrupt):
            with self.assertRaises(m.fmt.Invalid):
                m.pin_core(self.data, {'app': '1', 'dep': '2'})

    def test_loader_and_cli(self):
        for argv, expected in ((['demo'], 0), (['demo', '--require', 'idna=3.10'], 0),
                (['demo', '--require', 'idna=99'], 1),
                (['demo', '--max-assignments', '1'], 3),
                (['demo', '--require', 'app==1'], 2),
                (['demo', '--require', 'my_app=1', '--require', 'MY.APP=2'], 2),
                (['/tmp/outside-pin-core.json', '--require', 'app=1'], 2)):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(m.main(argv), expected)

    def test_seeded_independent_oracle(self):
        rng = random.Random(3804)
        for _ in range(400):
            names = ['app', 'b', 'c']
            packages = {p: {v: {q: rng.choice(('*', '==1', '==2'))
                                   for q in names if rng.random() < .25}
                            for v in ('1', '2') if rng.random() < .85}
                        for p in names}
            data = catalog(packages)
            solutions = raw_solutions(data)
            pins = {p: rng.choice(('1', '2', '3')) for p in names if rng.random() < .7}
            if not pins:
                pins = {'b': '2'}
            out = m.pin_core(data, pins)
            if not solutions:
                self.assertEqual(out['status'], 'baseline-unsatisfiable')
            elif any(all(s.get(p) == v for p, v in pins.items()) for s in solutions):
                self.assertEqual(out['status'], 'compatible')
                self.assertIn(out['witness'], solutions)
            else:
                self.assertEqual(out['status'], 'incompatible')
                self.verify_core(out, solutions)


if __name__ == '__main__':
    unittest.main()
