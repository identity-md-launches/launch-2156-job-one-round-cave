#!/usr/bin/env python3
"""Review a text merge and explain which exact release requests cannot coexist."""
import argparse
import json
import sys

import check_merge as merge
import pin_core

LABELS = ('base', 'ours', 'theirs', 'merged')


def assess(base, ours, theirs, pins, max_assignments=10000):
    if type(max_assignments) is not int or not 1 <= max_assignments <= 1000000:
        raise ValueError('assignment budget must be an integer from 1 to 1000000')
    packet = merge.review.packet(base, ours, theirs)
    report = {
        'format': 'merge-pin-review/v1', 'status': 'text_conflict',
        'review': packet, 'catalogs': None, 'lost_pin_compatibility_from': None,
        'limits': [
            'Review only: no merge, pin change or installation is applied.',
            'Pins require presence in the original roots dependency closure; they add no roots.',
            'A core is subset-minimal in its own catalog, not necessarily smallest.',
            'Deletion witnesses satisfy the remaining core, not necessarily discarded pins.',
            'Each catalog has its own assignment budget; incomplete search proves no conflict.',
            'Metadata compatibility does not establish artifact safety or installability.',
            'Hashes bind bytes or normalized catalogs, not authorship or trusted publishers.',
        ],
    }
    if not packet['clean']:
        return report
    catalogs = {}
    try:
        for label, text in zip(LABELS, (base, ours, theirs, packet['merged'])):
            catalogs[label] = merge.parse(text)
            pin_core.fmt.validate(catalogs[label])
    except (ValueError, TypeError, RecursionError):
        report['status'] = 'invalid_catalog'
        report['error'] = 'An input or the clean merge is not a supported catalog.'
        return report
    # Every result is recomputed from the exact candidate in the review packet;
    # there is no caller-supplied compatibility report to trust.
    reports = {label: pin_core.pin_core(catalogs[label], pins, max_assignments)
               for label in LABELS}
    report['catalogs'] = reports
    report['status'] = reports['merged']['status']
    if report['status'] in ('incompatible', 'baseline-unsatisfiable'):
        report['lost_pin_compatibility_from'] = [
            label for label in LABELS[:-1] if reports[label]['status'] == 'compatible']
    elif report['status'] == 'compatible':
        report['lost_pin_compatibility_from'] = []
    # For an inconclusive merge this remains null, even if earlier catalogs
    # yielded witnesses. No false negative conclusion from an exhausted budget.
    return report


def demo():
    folder = merge.HERE / 'examples'
    texts = [merge.review.engine.read_text(folder / ('plan-' + label + '.json'))
             for label in LABELS[:-1]]
    report = assess(*texts, {'idna': '2.10', 'certifi': '2025.8.3'})
    report['demo_note'] = (
        'Inherited historical Requests catalogs and illustrative exact pins: '
        'base and ours admit both pins; theirs and merged require idna >=3.10. '
        'The merged original roots remain compatible without the idna 2.10 pin.')
    return report


def exit_code(report):
    return {'compatible': 0, 'incompatible': 1, 'baseline-unsatisfiable': 1,
            'text_conflict': 1, 'invalid_catalog': 2, 'inconclusive': 3}[report['status']]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('demo')
    command = sub.add_parser('check')
    for label in LABELS[:-1]:
        command.add_argument(label)
    command.add_argument('--require', action='append', required=True,
                         metavar='PACKAGE=VERSION')
    command.add_argument('--max-assignments', type=int, default=10000)
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            report = demo()
            code = 0 if (report['status'] == 'incompatible' and
                         report['catalogs']['merged']['core'] == {'idna': '2.10'} and
                         report['lost_pin_compatibility_from'] == ['base', 'ours']) else 3
        else:
            pins = {}
            for item in args.require:
                if item.count('=') != 1:
                    raise ValueError('each --require must be PACKAGE=VERSION')
                raw, release = item.split('=')
                package = pin_core.fmt.name(raw)
                pin_core.fmt.version(release)
                if package in pins:
                    raise ValueError('duplicate canonical pin: ' + package)
                pins[package] = release
            texts = [merge.review.engine.read_text(path)
                     for path in (args.base, args.ours, args.theirs)]
            report = assess(*texts, pins, args.max_assignments)
            code = exit_code(report)
        print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
        return code
    except (ValueError, OSError, TypeError, RecursionError) as error:
        print(json.dumps({'status': 'invalid', 'error': str(error)}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
