import copy
import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('proof_prune_under_test', HERE / 'prune.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
w = p.w
ZTO_FILE = HERE.parent / 'state-witness' / 'examples' / 'zto-mainnet.json'
POOL_FILE = HERE.parent / 'state-witness' / 'examples' / 'zto-pool-mainnet.json'
POOL_ADDRESS = w.POOL_MANAGER
POOL_SLOT = '0x85763e16f60121d4266264cb693cca4d6bdb9e98ff9cc3d698d892d90342971b'


class ProofPruneTests(unittest.TestCase):
    def setUp(self):
        self.zto = w.load_bundle(ZTO_FILE)
        self.pool = w.load_bundle(POOL_FILE)

    def test_real_zto_absence_and_original_immutable(self):
        before = copy.deepcopy(self.zto)
        cleaned, report = p.prune(self.zto, p.DEMO_ROOT, w.ZTO, ['0x0', '0x1'])
        self.assertEqual(self.zto, before)
        self.assertEqual(report['removedOccurrences'], 0)
        self.assertFalse(report['state']['storage'][0]['exists'])
        self.assertEqual(cleaned['format'], 'state-witness/1')
        self.assertEqual(w.verify(cleaned['proof'], p.DEMO_ROOT, w.ZTO, ['0x0', '0x1']),
                         report['state'])

    def test_real_pool_present_slot(self):
        cleaned, report = p.prune(self.pool, p.DEMO_ROOT, POOL_ADDRESS, [POOL_SLOT])
        self.assertTrue(report['state']['storage'][0]['exists'])
        self.assertNotEqual(report['state']['storage'][0]['value'], '0x0')
        self.assertEqual(report['removedOccurrences'], 0)
        self.assertEqual(cleaned['proof'], self.pool['proof'])

    def test_unrelated_and_duplicate_nodes_removed_across_tries(self):
        original = copy.deepcopy(self.zto)
        self.zto['proof']['accountProof'].insert(0, self.pool['proof']['accountProof'][0])
        self.zto['proof']['accountProof'].append(self.zto['proof']['accountProof'][1])
        self.zto['proof']['storageProof'][0]['proof'].append(self.pool['proof']['storageProof'][0]['proof'][0])
        self.zto['proof']['storageProof'][1]['proof'].append(self.zto['proof']['storageProof'][1]['proof'][0])
        cleaned, report = p.prune(self.zto, p.DEMO_ROOT, w.ZTO, ['0x0', '0x1'])
        self.assertEqual(report['removedOccurrences'], 4)
        self.assertEqual(cleaned['proof'], original['proof'])
        self.assertEqual(len(self.zto['proof']['accountProof']), len(original['proof']['accountProof']) + 2)

    def test_wrong_root_rejected(self):
        with self.assertRaises(w.Invalid):
            p.prune(self.zto, '0x' + '00' * 32, w.ZTO, ['0x0', '0x1'])

    def test_missing_path_node_rejected(self):
        self.zto['proof']['accountProof'].pop(0)
        with self.assertRaises(w.Invalid):
            p.prune(self.zto, p.DEMO_ROOT, w.ZTO, ['0x0', '0x1'])

    def test_changed_value_rejected(self):
        self.pool['proof']['storageProof'][0]['value'] = '0x0'
        with self.assertRaises(w.Invalid):
            p.prune(self.pool, p.DEMO_ROOT, POOL_ADDRESS, [POOL_SLOT])

    def test_wrong_slot_or_address_rejected(self):
        for address, slots in [(w.ZTO, ['0x2']), (POOL_ADDRESS, ['0x0', '0x1'])]:
            with self.assertRaises(w.Invalid):
                p.prune(self.zto, p.DEMO_ROOT, address, slots)

    def test_cli_demo_and_error_status(self):
        command = [sys.executable, '-B', str(HERE / 'prune.py')]
        demo = subprocess.run(command + ['demo'], capture_output=True, text=True)
        self.assertEqual(demo.returncode, 0, demo.stderr)
        self.assertIn('"removedOccurrences":2', demo.stdout)
        bad = subprocess.run(command + ['audit', str(ZTO_FILE),
                                      '--state-root', '0x' + '00' * 32,
                                      '--address', w.ZTO, '--slot', '0x0', '--slot', '0x1'],
                             capture_output=True, text=True)
        self.assertEqual(bad.returncode, 1)
        self.assertEqual(bad.stdout, '')
        self.assertIn('"verified": false', bad.stderr)


if __name__ == '__main__':
    unittest.main()
