#!/usr/bin/env python3
"""Compare labelled offline retrieval across two bounded document collections."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TOOLS = Path(__file__).absolute().parents[1]
spec = importlib.util.spec_from_file_location('search_evaluate', TOOLS / 'search-evaluate/evaluate.py')
evaluate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluate)
engine = evaluate.engine
FORMAT = 'evidence-search-comparison/v1'
METRICS = ('target_recall', 'labelled_hit_precision', 'reciprocal_rank')


def target_key(target):
    return (target['path'], target['line_start'], target['line_end'])


def run(baseline_root, candidate_root, plan):
    evaluate.validate(plan)
    # Isolate the shared labels from caller mutation; both sides get identical
    # settings. No externally supplied evaluation reports are trusted here.
    plan = copy.deepcopy(plan)
    encoded = json.dumps(plan, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    baseline = evaluate.run(baseline_root, plan)
    candidate = evaluate.run(candidate_root, plan)
    # Baseline may have changed while candidate was being evaluated. Recheck
    # both complete corpus identities before returning any comparison.
    for root, report in ((baseline_root, baseline), (candidate_root, candidate)):
        current = evaluate.batch.corpus_id(engine.build_index(root))
        if current != report['corpus_sha256']:
            raise engine.SearchError('corpus changed during comparison; retry with static files')
    rows = []
    for before, after in zip(baseline['queries'], candidate['queries']):
        delta = {metric: after[metric] - before[metric] for metric in METRICS}
        lost_metrics = [metric for metric in METRICS if delta[metric] < 0]
        gained_metrics = [metric for metric in METRICS if delta[metric] > 0]
        old_found = {target_key(t) for t in before['found']}
        new_found = {target_key(t) for t in after['found']}
        def targets(keys):
            return [dict(path=p, line_start=s, line_end=e) for p, s, e in sorted(keys)]
        rows.append({'id': before['id'], 'delta': delta,
                     'regressed_metrics': lost_metrics, 'improved_metrics': gained_metrics,
                     'lost_targets': targets(old_found - new_found),
                     'gained_targets': targets(new_found - old_found)})
    regressions = [row['id'] for row in rows if row['regressed_metrics']]
    return {'format': FORMAT, 'judgments_sha256': hashlib.sha256(encoded).hexdigest(),
            'judgments': plan, 'baseline': baseline, 'candidate': candidate,
            'queries': rows,
            'macro_delta': {metric: candidate['macro'][metric] - baseline['macro'][metric]
                            for metric in METRICS},
            'regressed_query_ids': regressions,
            'improved_query_ids': [row['id'] for row in rows if row['improved_metrics']],
            'no_regressions': not regressions}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('demo', help='compare the bundled historical ZTO/IMD corpus to itself')
    command = commands.add_parser('run')
    command.add_argument('baseline_root')
    command.add_argument('candidate_root')
    command.add_argument('judgments')
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            baseline = candidate = TOOLS / 'evidence-search/examples/docs'
            plan = evaluate.demo_plan()
        else:
            baseline, candidate = args.baseline_root, args.candidate_root
            plan = evaluate.load_plan(args.judgments)
        report = run(baseline, candidate, plan)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report['no_regressions'] else 1
    except (engine.SearchError, OSError, ValueError, RecursionError) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
