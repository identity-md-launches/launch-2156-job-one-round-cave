#!/usr/bin/env python3
"""Verify and remove unused or repeated nodes from an EIP-1186 witness.

Offline, read-only, Python standard library only. Nothing is signed or sent.
"""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    'witness_for_proof_prune', HERE.parent / 'state-witness' / 'witness.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)

DEMO_ROOT = '0x70c13580735123b57c0a9a24692875f4ef366b04c69d92af9f539561e626d512'
DEMO_ADDRESS = w.ZTO
DEMO_SLOTS = ['0x0', '0x1']


def used_nodes(root, key, proof):
    """Return hashes of external proof nodes on the unique path for a key.

    This function runs only after the complete witness has passed w.verify.
    A second verification of the pruned witness checks this path selection.
    """
    w.require(isinstance(proof, list) and len(proof) <= 128, 'invalid proof node list')
    nodes = {}
    for item in proof:
        raw = w.hex_data(item, label='proof node')
        w.require(0 < len(raw) <= 32768, 'invalid proof node length')
        nodes[w.keccak256(raw)] = (w.rlp_decode(raw), len(raw))
    if root == w.EMPTY_TRIE:
        return set()

    remaining = w.nibbles(key)
    reference, is_root, used = root, True, set()
    for _ in range(130):
        if isinstance(reference, list):
            w.require(len(w.rlp_encode(reference)) < 32, 'oversized inline node')
            node = reference
        else:
            w.require(isinstance(reference, bytes) and len(reference) == 32,
                      'invalid trie child reference')
            w.require(reference in nodes, 'missing proof node')
            node, size = nodes[reference]
            w.require(is_root or size >= 32, 'short child must be inline')
            used.add(reference)
        is_root = False
        if len(node) == 17:
            w.require(isinstance(node[16], bytes), 'invalid branch value')
            if not remaining:
                return used
            reference, remaining = node[remaining[0]], remaining[1:]
            if reference == b'':
                return used
        elif len(node) == 2:
            leaf, path = w.compact_path(node[0])
            w.require(leaf or path, 'empty extension path')
            if remaining[:len(path)] != path:
                return used
            remaining = remaining[len(path):]
            if leaf:
                w.require(isinstance(node[1], bytes) and node[1], 'invalid leaf value')
                return used
            reference = node[1]
            w.require(reference != b'', 'empty extension child')
        else:
            raise w.Invalid('invalid trie node arity')
    raise w.Invalid('trie traversal exceeded bound')


def prune_list(proof, used):
    """Retain one original occurrence of each path node in encounter order."""
    kept, seen = [], set()
    for item in proof:
        digest = w.keccak256(w.hex_data(item, label='proof node'))
        if digest in used and digest not in seen:
            kept.append('0x' + item[2:].lower())
            seen.add(digest)
    w.require(seen == used, 'selected proof node was not present')
    return kept


def prune(bundle, root_hex, address_hex, slots):
    """Return an ordinary witness and a report, after verification twice."""
    w.require(isinstance(bundle, dict) and bundle.get('format') == 'state-witness/1',
              'unsupported witness format')
    original = w.verify(bundle.get('proof'), root_hex, address_hex, slots)
    proof = bundle['proof']
    account_root = w.hex_data(root_hex, 32, 'state root')
    address = w.hex_data(address_hex, 20, 'address')
    account_used = used_nodes(account_root, w.keccak256(address), proof['accountProof'])
    result = copy.deepcopy(bundle)
    result_proof = result['proof']
    before_account = len(proof['accountProof'])
    result_proof['accountProof'] = prune_list(proof['accountProof'], account_used)
    slot_reports = []
    storage_root = w.hex_data(original['storageRoot'], 32, 'storage root')
    for entry, output_entry in zip(proof['storageProof'], result_proof['storageProof']):
        slot = w.slot_number(entry['key'])
        selected = used_nodes(storage_root, w.keccak256(slot.to_bytes(32, 'big')),
                              entry['proof'])
        before = len(entry['proof'])
        output_entry['proof'] = prune_list(entry['proof'], selected)
        slot_reports.append({'slot': hex(slot), 'beforeNodes': before,
                             'afterNodes': len(output_entry['proof'])})

    after = w.verify(result_proof, root_hex, address_hex, slots)
    w.require(after == original, 'pruned proof changed the verified state')
    report = {
        'verified': True, 'format': 'proof-prune-report/1',
        'address': original['address'], 'stateRoot': original['stateRoot'],
        'account': {'beforeNodes': before_account,
                    'afterNodes': len(result_proof['accountProof'])},
        'storage': slot_reports,
        'removedOccurrences': (before_account - len(result_proof['accountProof'])
                               + sum(row['beforeNodes'] - row['afterNodes'] for row in slot_reports)),
        'state': after,
    }
    return result, report


def demo():
    source = HERE.parent / 'state-witness' / 'examples' / 'zto-mainnet.json'
    bundle = w.load_bundle(source)
    # A valid unrelated node from another real witness makes the surplus visible.
    unrelated = w.load_bundle(HERE.parent / 'state-witness' / 'examples' / 'zto-pool-mainnet.json')
    bundle['proof']['accountProof'].append(unrelated['proof']['accountProof'][0])
    bundle['proof']['accountProof'].append(bundle['proof']['accountProof'][0])
    _, report = prune(bundle, DEMO_ROOT, DEMO_ADDRESS, DEMO_SLOTS)
    report['demo'] = ('Real historical ZTO proof plus one unrelated real pool node and one duplicate; '
                      'the root is an RPC observation, not an independently trusted checkpoint.')
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('demo', help='prune surplus nodes from a real historical ZTO proof')
    for name in ('audit', 'prune'):
        command = sub.add_parser(name, help='verify then report or print a cleaned witness')
        command.add_argument('witness')
        command.add_argument('--state-root', required=True)
        command.add_argument('--address', required=True)
        command.add_argument('--slot', action='append', default=[])
    args = parser.parse_args(argv)
    try:
        if args.command == 'demo':
            output = demo()
        else:
            bundle = w.load_bundle(args.witness)
            cleaned, report = prune(bundle, args.state_root, args.address, args.slot)
            output = report if args.command == 'audit' else cleaned
        print(json.dumps(output, sort_keys=True, separators=(',', ':')))
        return 0
    except w.Invalid as error:
        print(json.dumps({'verified': False, 'error': str(error)}), file=sys.stderr)
        return 1
    except (OSError, ValueError, TypeError, KeyError, IndexError, RecursionError):
        print(json.dumps({'verified': False, 'error': 'Unreadable or malformed witness.'}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
