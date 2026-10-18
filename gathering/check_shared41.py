"""Exercise all portable shared suites and the new covered proof-search demo."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


def main():
    suites = []
    for folder in sorted(Path('shared').iterdir()):
        if not folder.is_dir() or not list(folder.glob('test_*.py')):
            continue
        cmd = [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', str(folder), '-p', 'test_*.py']
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        match = re.search(r'Ran (\d+) tests?', proc.stderr)
        row = {'tool':str(folder), 'command':cmd, 'exit':proc.returncode,
               'tests':int(match[1]) if match else 0, 'log':proc.stderr}
        suites.append(row)
        print(str(folder), row['tests'], proc.returncode, flush=True)
        assert proc.returncode == 0 and row['tests'] > 0, row
    demos = []
    for script in ('shared/proof-handoff/covered_search.py', 'shared/claim-bridge/bridge.py', 'shared/merge-dependencies/merge_equivalence.py', 'shared/merge-dependencies/merge_census.py', 'shared/merge-dependencies/merge_pins.py'):
        proc = subprocess.run([sys.executable, '-B', script, 'demo'], capture_output=True, text=True, timeout=90)
        assert proc.returncode == 0, proc.stderr
        demos.append({'command':'python3 -B '+script+' demo', 'exit':0, 'result':json.loads(proc.stdout)})
    root = Path('shared/proof-handoff')
    provenance = json.loads((root/'COVERAGE-PROVENANCE.json').read_text())
    for row in provenance:
        assert Path(row['source']).read_bytes() == (root/row['copy']).read_bytes()
        assert hashlib.sha256((root/row['copy']).read_bytes()).hexdigest() == row['sha256']
    for row in json.loads((root/'PROVENANCE.json').read_text()):
        assert hashlib.sha256((root/row['copy']).read_bytes()).hexdigest() == row['sha256']
    eq = json.loads(Path('shared/merge-dependencies/EQUIVALENCE-PROVENANCE.json').read_text())
    assert hashlib.sha256(Path(eq['source']).read_bytes()).hexdigest() == eq['source_sha256']
    assert hashlib.sha256(Path(eq['copy']).read_bytes()).hexdigest() == eq['copy_sha256']
    census = json.loads(Path('shared/merge-dependencies/CENSUS-PROVENANCE.json').read_text())
    assert hashlib.sha256(Path(census['source']).read_bytes()).hexdigest() == census['source_sha256']
    assert hashlib.sha256(Path(census['copy']).read_bytes()).hexdigest() == census['copy_sha256']
    pins = json.loads(Path('shared/merge-dependencies/PIN-CORE-PROVENANCE.json').read_text())
    assert hashlib.sha256(Path(pins['source']).read_bytes()).hexdigest() == pins['source_sha256']
    assert hashlib.sha256(Path(pins['copy']).read_bytes()).hexdigest() == pins['copy_sha256']
    result = {'suites':suites, 'total_tests':sum(x['tests'] for x in suites),
              'demos':demos, 'new_copied_sources_match':True,
              'inherited_proof_handoff_frozen_copies_match':True}
    Path('gathering/shared-checks-41.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__ == '__main__':
    main()
