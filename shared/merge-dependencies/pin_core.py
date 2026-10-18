#!/usr/bin/env python3
"""Explain incompatible exact release requests with a subset-minimal pin core."""
import argparse
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys

CHECKER = Path(__file__).resolve().parent / 'exhaustive.py'
if not CHECKER.is_relative_to(Path.cwd().resolve()):
    raise RuntimeError('run from the workspace containing the tools')
spec = importlib.util.spec_from_file_location('pin_core_checker', CHECKER)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)
fmt = checker.fmt


def pin_core(data, pins, max_assignments=10000):
    if type(max_assignments) is not int or not 1 <= max_assignments <= 1000000:
        raise fmt.Invalid('max_assignments must be an integer from 1 to 1000000')
    packages, roots = fmt.validate(data)
    if not isinstance(pins, dict) or not pins or len(pins) > 1000:
        raise fmt.Invalid('pins must be a nonempty object of at most 1000 releases')
    normalized = {}
    for raw, release in pins.items():
        p = fmt.name(raw)
        if p in normalized:
            raise fmt.Invalid('duplicate canonical pin: ' + p)
        numeric = fmt.version(release)
        normalized[p] = next((v for v in packages.get(p, {})
                              if fmt.version(v) == numeric), release)
    pins = dict(sorted(normalized.items()))
    pin_items = list(pins.items())
    full = (1 << len(pins)) - 1
    possible, todo = set(), list(roots)
    while todo:
        p = todo.pop()
        if p in possible:
            continue
        possible.add(p)
        for deps in packages.get(p, {}).values():
            todo.extend(deps)
    names, domains, total = sorted(possible), [], 1
    for p in names:
        releases = sorted(packages.get(p, {}), key=fmt.version)
        domain = ([v for v in releases if checker.matches(v, roots[p])]
                  if p in roots else [None] + releases)
        domains.append(domain)
        total *= len(domain)

    def selection_at(index):
        # Recover a witness from its mixed-radix Cartesian index. Only integer
        # indices are retained during search, rather than full assignment maps.
        selected = {}
        for p, domain in reversed(list(zip(names, domains))):
            index, digit = divmod(index, len(domain))
            if domain[digit] is not None:
                selected[p] = domain[digit]
        selected = dict(sorted(selected.items()))
        if checker.assignment(packages, roots, selected) != selected:
            raise fmt.Invalid('reconstructed witness failed validation')
        return selected

    payload = {'packages': packages, 'roots': roots}
    base = {'method': 'finite-pin-core-v1', 'pins': pins,
            'catalog_sha256': hashlib.sha256(json.dumps(payload, sort_keys=True,
                separators=(',', ':')).encode()).hexdigest(),
            'candidate_assignments': total, 'max_assignments': max_assignments}
    masks, checked, compatible = {}, 0, 0
    for values in itertools.product(*domains):
        if checked == max_assignments:
            break
        index = checked
        checked += 1
        selected = {p: v for p, v in zip(names, values) if v is not None}
        if checker.assignment(packages, roots, selected) != selected:
            continue
        compatible += 1
        mask = sum(1 << i for i, (p, v) in enumerate(pin_items)
                   if selected.get(p) == v)
        masks.setdefault(mask, index)
        if mask == full:
            return dict(base, status='compatible', checked_assignments=checked,
                        compatible_selections_seen=compatible, witness=selected)
    base.update(checked_assignments=checked, compatible_selections_seen=compatible,
                observed_pin_patterns=len(masks))
    if checked < total:
        return dict(base, status='inconclusive',
                    reason='budget exhausted; no conflict or minimality claim')
    if not masks:
        return dict(base, status='baseline-unsatisfiable',
                    reason='original roots have no solution even without pins')

    # Complete enumeration gives a finite truth table for every pin subset.
    # Deletion is monotone: a removed pin can never become necessary later.
    core = full
    for i in range(len(pin_items)):
        trial = core & ~(1 << i)
        if not any(mask & trial == trial for mask in masks):
            core = trial
    core_pins = {p: v for i, (p, v) in enumerate(pin_items) if core & (1 << i)}
    witnesses = []
    for i, (p, v) in enumerate(pin_items):
        if not core & (1 << i):
            continue
        trial = core & ~(1 << i)
        index = next(index for mask, index in masks.items() if mask & trial == trial)
        selected = selection_at(index)
        if selected.get(p) == v or not all(selected.get(q) == w
                for q, w in core_pins.items() if q != p):
            raise fmt.Invalid('core deletion witness failed validation')
        witnesses.append({'removed_pin': p, 'selected': selected})
    return dict(base, status='incompatible', core=core_pins,
                minimality='subset-minimal, not necessarily minimum cardinality',
                deletion_witnesses=witnesses,
                discarded_pins={p: v for p, v in pins.items() if p not in core_pins})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('catalog', help='workspace-local catalog JSON or demo')
    parser.add_argument('--require', action='append', default=[], metavar='PACKAGE=VERSION')
    parser.add_argument('--max-assignments', type=int, default=10000)
    args = parser.parse_args(argv)
    try:
        pins = {}
        for text in args.require:
            if text.count('=') != 1:
                raise fmt.Invalid('each --require must be PACKAGE=VERSION')
            raw, release = text.split('=')
            p = fmt.name(raw)
            if p in pins:
                raise fmt.Invalid('duplicate canonical pin: ' + p)
            pins[p] = release
        path = (CHECKER.parent / 'examples/base.json'
                if args.catalog == 'demo' else args.catalog)
        data = fmt.load(path)
        demonstration = args.catalog == 'demo' and not pins
        if args.catalog == 'demo':
            data = dict(data, roots={'requests': '*', 'urllib3': '<2'})
            if demonstration:
                pins = {'requests': '2.25.1', 'idna': '3.10', 'certifi': '2025.8.3'}
        result = pin_core(data, pins, args.max_assignments)
        code = {'compatible': 0, 'incompatible': 1, 'baseline-unsatisfiable': 1,
                'inconclusive': 3}[result['status']]
        if args.catalog == 'demo':
            result['demonstration_roots'] = data['roots']
        if demonstration and result.get('core') == {'idna': '3.10', 'requests': '2.25.1'}:
            code = 0
    except (fmt.Invalid, OSError, UnicodeError, ValueError, TypeError, RecursionError) as exc:
        result, code = {'status': 'invalid', 'error': str(exc)}, 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return code


if __name__ == '__main__':
    sys.exit(main())
