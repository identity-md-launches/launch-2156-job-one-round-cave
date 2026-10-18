#!/usr/bin/env python3
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('compare', Path(__file__).with_name('compare.py'))
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        scratch = Path('test/scratch')
        scratch.mkdir(parents=True, exist_ok=True)
        self.root = Path(tempfile.mkdtemp(prefix='compare-', dir=scratch))
        self.addCleanup(shutil.rmtree, self.root)
        self.before, self.after = self.root / 'before', self.root / 'after'
        for root in (self.before, self.after):
            root.mkdir()
            (root / 'b.md').write_text('alpha\n', encoding='utf-8')
        self.plan = {'format': c.evaluate.PLAN_FORMAT, 'queries': [
            {'id': 'q', 'query': 'alpha', 'limit': 1, 'require_all': True,
             'targets': [{'path': 'b.md', 'line_start': 1, 'line_end': 1}]}]}

    def test_stable_deterministic_and_immutable(self):
        original = copy.deepcopy(self.plan)
        first = c.run(self.before, self.after, self.plan)
        self.assertEqual(first, c.run(self.before, self.after, self.plan))
        self.assertTrue(first['no_regressions'])
        self.assertEqual(first['regressed_query_ids'], [])
        self.assertEqual(first['macro_delta'], dict.fromkeys(c.METRICS, 0))
        self.assertEqual(self.plan, original)
        self.assertEqual((self.before / 'b.md').read_text(), 'alpha\n')
        self.assertTrue(first['candidate']['queries'][0]['hits'][0]['source_verified'])

    def test_loss_and_gain(self):
        (self.after / 'b.md').write_text('omega\n')
        lost = c.run(self.before, self.after, self.plan)
        self.assertEqual(lost['regressed_query_ids'], ['q'])
        self.assertEqual(lost['queries'][0]['lost_targets'], self.plan['queries'][0]['targets'])
        self.assertEqual(lost['macro_delta']['target_recall'], -1)
        gained = c.run(self.after, self.before, self.plan)
        self.assertEqual(gained['improved_query_ids'], ['q'])
        self.assertTrue(gained['no_regressions'])
        self.assertEqual(gained['queries'][0]['gained_targets'], self.plan['queries'][0]['targets'])

    def test_aggregate_cannot_hide_regression(self):
        (self.after / 'b.md').write_text('omega\n')
        other = copy.deepcopy(self.plan['queries'][0])
        other.update(id='other', query='omega')
        self.plan['queries'].append(other)
        report = c.run(self.before, self.after, self.plan)
        self.assertEqual(report['macro_delta'], dict.fromkeys(c.METRICS, 0))
        self.assertFalse(report['no_regressions'])
        self.assertEqual(report['regressed_query_ids'], ['q'])
        self.assertEqual(report['improved_query_ids'], ['other'])

    def test_rank_loss_without_target_loss(self):
        (self.before / 'a.md').write_text('omega\n')
        (self.after / 'a.md').write_text('alpha alpha alpha\n')
        self.plan['queries'][0]['limit'] = 2
        report = c.run(self.before, self.after, self.plan)
        self.assertEqual(report['queries'][0]['lost_targets'], [])
        self.assertEqual(report['queries'][0]['delta']['reciprocal_rank'], -.5)
        self.assertFalse(report['no_regressions'])

    def test_missing_labels_fail_instead_of_claiming_miss(self):
        (self.after / 'b.md').unlink()
        with self.assertRaisesRegex(c.engine.SearchError, 'does not exist'):
            c.run(self.before, self.after, self.plan)

    def test_baseline_changes_during_candidate_evaluation(self):
        original_run = c.evaluate.run
        def changing(root, plan):
            report = original_run(root, plan)
            if root == self.after:
                (self.before / 'b.md').write_text('changed\n')
            return report
        with patch.object(c.evaluate, 'run', side_effect=changing):
            with self.assertRaisesRegex(c.engine.SearchError, 'during comparison'):
                c.run(self.before, self.after, self.plan)

    def test_invalid_plan_and_symlink(self):
        self.plan['queries'][0]['limit'] = True
        with self.assertRaises(c.engine.SearchError):
            c.run(self.before, self.after, self.plan)
        self.plan['queries'][0]['limit'] = 1
        (self.after / 'b.md').unlink()
        (self.after / 'b.md').symlink_to('../before/b.md')
        with self.assertRaises(c.engine.SearchError):
            c.run(self.before, self.after, self.plan)

    def test_cli_status_and_no_partial_output(self):
        plan = self.root / 'judgments.json'
        plan.write_text(json.dumps(self.plan))
        def call():
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = c.main(['run', str(self.before), str(self.after), str(plan)])
            return code, out.getvalue(), err.getvalue()
        self.assertEqual(call()[0], 0)
        (self.after / 'b.md').write_text('omega\n')
        code, out, err = call()
        self.assertEqual(code, 1)
        self.assertFalse(json.loads(out)['no_regressions'])
        self.assertEqual(err, '')
        plan.write_text('{"format":1,"format":2}')
        code, out, err = call()
        self.assertEqual(code, 2)
        self.assertEqual(out, '')
        self.assertIn('error', json.loads(err))

    def test_real_historical_demo(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(c.main(['demo']), 0)
        report = json.loads(out.getvalue())
        self.assertTrue(report['no_regressions'])
        self.assertEqual(report['baseline']['corpus_sha256'], report['candidate']['corpus_sha256'])
        self.assertEqual(report['baseline']['queries'][0]['hits'][0]['citation'], 'zto.md:1-9')
        self.assertEqual(report['baseline']['macro']['target_recall'], 2/3)


if __name__ == '__main__':
    unittest.main()
