"""Try the latest line pieces against inherited historical evidence, offline."""
import json
from pathlib import Path
import subprocess
import sys


def run(args):
    proc = subprocess.run([sys.executable, '-B', *args], capture_output=True,
                          text=True, timeout=90, check=False)
    if proc.returncode:
        raise AssertionError((args, proc.returncode, proc.stderr[-1000:]))
    return json.loads(proc.stdout)


def main():
    receipt = run(['line-1/tools/merge-receipt/merge_receipt.py', *(
        'shared/merge-dependencies/examples/' + label + '.json'
        for label in ('base', 'ours', 'theirs'))])
    prune = run(['line-2/tools/proof-prune/prune.py', 'demo'])
    evaluate = run(['line-3/tools/search-evaluate/evaluate.py', 'demo'])
    compare = run(['line-3/tools/search-compare/compare.py', 'demo'])
    core = run(['line-4/tools/pin-core/pin_core.py', 'demo'])
    assert all(row['total_changes'] == 1 and not row['truncated']
               for row in receipt['branches'])
    assert prune['verified'] and prune['removedOccurrences'] == 2
    assert core['core'] == {'idna': '3.10', 'requests': '2.25.1'}
    assert core['checked_assignments'] == 216
    assert compare['no_regressions'] and all(x == 0 for x in compare['macro_delta'].values())
    report = {
        'line_1': {'tool': 'Bounded Merge Receipt', 'branch_hunks': [
            row['total_changes'] for row in receipt['branches']], 'exit': 0},
        'line_2': {'tool': 'Proof Prune', 'report': prune, 'exit': 0},
        'line_3': {'tool': 'Search Evaluate and Search Compare',
                   'evaluation_macro': evaluate['macro'],
                   'comparison_macro_delta': compare['macro_delta'],
                   'no_regressions': compare['no_regressions'], 'exit': 0},
        'line_4': {'tool': 'Pin Core', 'report': core, 'exit': 0},
        'qualification': 'Historical offline evidence; no fresh RPC, live price, installation or consensus claim.',
    }
    Path('gathering/latest-checks-41.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
