"""Run documented line tool tests and demos without editing any line folder."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

TOOLS = {
    1: ('threeway', 'merge-review', 'tree-review', 'review-recheck',
        'candidate-export', 'conflict-finish', 'stage-audit', 'resolution-review', 'merge-sanity', 'interface-review'),
    2: ('state-witness', 'header-anchor', 'code-witness', 'proof-set',
        'pool-state', 'header-chain', 'state-diff', 'ancestry-diff', 'proof-pack', 'state-gate', 'fresh-witness'),
    3: ('evidence-search', 'corpus-freshness', 'search-receipt',
        'evidence-bundle', 'corpus-change-receipt', 'query-impact',
        'collection-guide', 'reading-list', 'phrase-finder', 'citation-reanchor', 'citation-context'),
    4: ('offline-resolver', 'conflict-core', 'exhaustive-audit',
        'root-repair', 'lock-plan', 'plan-audit', 'release-map', 'selection-explain'),
}

DEMOS = [
    (1, 'conflict-finish/test_finish.py', []),
    (1, 'resolution-review/review.py', ['--demo']),
    (2, 'proof-pack/pack.py', ['demo']),
    (2, 'proof-pack/pack.py', ['demo', '--pool']),
    (3, 'phrase-finder/phrases.py', ['demo']),
    (4, 'release-map/release_map.py', ['demo']),
    (1, 'stage-audit/test_audit.py', []),
    (2, 'ancestry-diff/ancestry_diff.py', ['demo']),
    (3, 'reading-list/reading_list.py', ['demo']),
    (4, 'plan-audit/audit_plan.py', ['demo']),
    (1, 'threeway/merge.py', ['--demo', '--format', 'json']),
    (1, 'merge-review/review.py', ['--demo', 'clean', '--format', 'json']),
    (1, 'tree-review/tree_review.py', ['--demo', 'clean', '--format', 'json']),
    (1, 'review-recheck/recheck.py', ['--demo', 'clean']),
    (1, 'candidate-export/export.py', ['--demo']),
    (2, 'state-witness/witness.py', ['demo']),
    (2, 'header-anchor/anchor.py', ['demo']),
    (2, 'code-witness/code_witness.py', ['demo']),
    (2, 'proof-set/proof_set.py', ['demo']),
    (2, 'pool-state/pool_state.py', ['demo']),
    (2, 'header-chain/header_chain.py', ['demo']),
    (2, 'header-chain/header_chain.py', ['demo', '--pool']),
    (2, 'state-diff/state_diff.py', ['demo']),
    (2, 'state-diff/state_diff.py', ['demo', '--zto']),
    (3, 'evidence-search/search.py', ['demo']),
    (3, 'corpus-freshness/freshness.py', ['demo']),
    (3, 'search-receipt/receipt.py', ['demo']),
    (3, 'evidence-bundle/bundle.py', ['demo']),
    (3, 'corpus-change-receipt/receipt.py', ['demo']),
    (3, 'query-impact/impact.py', ['demo']),
    (3, 'collection-guide/guide.py', ['demo']),
    (4, 'offline-resolver/resolve.py', ['demo']),
    (4, 'conflict-core/core.py', ['demo']),
    (4, 'exhaustive-audit/audit.py', ['demo']),
    (4, 'root-repair/repair.py', ['demo']),
    (4, 'lock-plan/plan.py', ['demo']),
]


def fingerprints():
    return {p.as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for n in range(1, 5)
            for folder in (Path(f'line-{n}'), Path(f'dist/line-{n}'))
            for p in sorted(folder.rglob('*')) if p.is_file()}


def run(args, timeout=180, expected=0):
    proc = subprocess.run([sys.executable, '-B', *args], capture_output=True,
                          text=True, timeout=timeout)
    result = {'command': 'python3 -B ' + ' '.join(args), 'exit': proc.returncode, 'expected_exit': expected,
              'stdout_tail': proc.stdout[-600:], 'stderr_tail': proc.stderr[-600:]}
    if proc.returncode != expected:
        raise AssertionError(result)
    return result


def main():
    before = fingerprints()
    suites, demos = [], []
    scratch = Path('test/scratch')
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch, prefix='gathering41-') as temp:
        copy = Path(temp) / 'offline-resolver'
        shutil.copytree('line-4/tools/offline-resolver', copy)
        # Receipt Audit creates temporary inputs beside its test file. Run an
        # identical complete tool tree in scratch, never in the protected line.
        line1_tree = Path(temp) / 'line1-tools'
        shutil.copytree('line-1/tools', line1_tree)
        test_copy = line1_tree / 'candidate-order/test_candidate_order.py'
        test_copy.write_text(test_copy.read_text().replace("dir='/tmp'", "dir=str(Path('test/scratch').resolve())"))
        receipt_tree = Path(temp) / 'line2-tools'
        shutil.copytree('line-2/tools', receipt_tree)
        for n, names in {n: tuple(p.name for p in sorted(Path(f'line-{n}/tools').iterdir()) if p.is_dir() and list(p.glob('test_*.py'))) for n in range(1,5)}.items():
            for name in names:
                folder = f'line-{n}/tools/{name}'
                target = str(copy) if name == 'offline-resolver' else str(receipt_tree / name) if n == 2 and name == 'receipt-audit' else str(line1_tree / name) if n == 1 and name == 'candidate-order' else folder
                result = run(['-m', 'unittest', 'discover', '-s', target,
                              '-p', 'test_*.py'], 180)
                match = re.search(r'Ran (\d+) tests?', result['stderr_tail'])
                result.update(tool=folder, tests=int(match[1]) if match else 0)
                if not result['tests']:
                    raise AssertionError(result)
                suites.append(result)
                print(folder, result['tests'], flush=True)
    DEMOS.extend([(1, 'merge-sanity/sanity.py', ['--demo']), (1, 'merge-sanity/trial.py', []), (2, 'state-gate/gate.py', ['demo']), (2, 'state-gate/gate.py', ['demo', '--reject']), (3, 'citation-reanchor/reanchor.py', ['demo']), (4, 'selection-explain/explain.py', ['demo', '--why', 'idna']), (1, 'interface-review/interfaces.py', ['--demo']), (1, 'interface-review/trial.py', []), (2, 'fresh-witness/fresh_witness.py', ['demo']), (2, 'fresh-witness/fresh_witness.py', ['demo', '--reject']), (3, 'citation-context/context.py', ['demo'])])
    DEMOS.extend([(1, 'binding-review/bindings.py', ['--demo']), (1, 'binding-review/trial.py', []), (2, 'anchored-gate/anchored_gate.py', ['demo']), (2, 'anchored-gate/anchored_gate.py', ['demo', '--reject', 'both']), (3, 'citation-ledger/ledger.py', ['demo']), (4, 'core-audit/check_core.py', ['demo'])])
    DEMOS.extend([
        (1, 'addition-audit/addition_audit.py', ['--demo']),
        (2, 'balance-slot/balance_slot.py', ['demo']),
        (2, 'storage-fields/storage_fields.py', ['demo']),
        (3, 'query-diagnose/diagnose.py', ['demo']),
        (3, 'citation-report/report.py', ['demo']),
        (4, 'joint-check/joint.py', ['demo']),
        (4, 'catalog-delta/delta.py', ['demo']),
    ])
    DEMOS.extend([
        (1, 'deletion-audit/deletion_audit.py', ['--demo']),
        (2, 'proof-receipt/receipt.py', ['demo']),
        (3, 'citation-trail/demo.py', []),
        (4, 'catalog-health/health.py', ['demo']),
        (3, 'citation-report/report.py', ['demo']),
    ])
    DEMOS.extend([(1, 'candidate-additions/candidate_additions.py', ['--demo']),
                  (2, 'receipt-audit/audit.py', ['demo'])])
    DEMOS.extend([(1, 'candidate-order/candidate_order.py', ['--demo']), (2, 'receipt-capsule/capsule.py', ['demo']), (2, 'request-coverage/coverage.py', ['demo']), (3, 'search-replay/replay.py', ['demo']), (4, 'support-prune/prune.py', ['demo']), (4, 'solution-census/census.py', ['demo'])])
    DEMOS.extend([(1, 'json-change-audit/json_change_audit.py', ['--demo']), (1, 'merge-receipt/merge_receipt.py', ['shared/merge-dependencies/examples/base.json', 'shared/merge-dependencies/examples/ours.json', 'shared/merge-dependencies/examples/theirs.json']), (2, 'mapping-path/mapping_path.py', ['demo']), (3, 'search-batch/batch.py', ['demo']), (4, 'solution-equivalence/equivalence.py', ['demo'])])
    DEMOS.extend([(1, 'merge-receipt/merge_receipt.py', ['--demo']), (2, 'field-change/field_change.py', ['demo']), (3, 'evidence-bundle/bundle.py', ['demo']), (4, 'component-census/components.py', ['demo'])])
    DEMOS.extend([(2, 'proof-prune/prune.py', ['demo']), (3, 'search-evaluate/evaluate.py', ['demo']), (3, 'search-compare/compare.py', ['demo']), (4, 'pin-core/pin_core.py', ['demo'])])
    for n, script, args in DEMOS:
        expected = 1 if script in ('merge-sanity/sanity.py', 'interface-review/interfaces.py', 'binding-review/bindings.py') else 3 if '--reject' in args else 0
        result = run([f'line-{n}/tools/{script}', *args], 90, expected)
        result['line'] = n
        demos.append(result)
        print(result['command'], 'ok', flush=True)
    after = fingerprints()
    if before != after:
        raise AssertionError('line files or records changed')
    report = {'suites': suites, 'demos': demos,
              'total_tests': sum(item['tests'] for item in suites),
              'line_files_unchanged': True,
              'protected_files_count': len(before),
              'protected_files_sha256': hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest()}
    Path('gathering/checks-41.json').write_text(json.dumps(report, indent=2) + '\n')
    print('TOTAL', report['total_tests'], 'tests;', len(demos), 'demos')


if __name__ == '__main__':
    main()
