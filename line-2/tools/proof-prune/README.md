# Proof Prune

Verify an Ethereum EIP-1186 account and storage witness against a caller
supplied state root, address and **complete** raw slot set, then remove trie
nodes that no requested path uses. Duplicate node occurrences are reduced to
one per proof. The output of `prune` is an ordinary `state-witness/1` JSON
witness that every earlier line 2 verifier can read. This is useful when an RPC
or handoff includes unrelated nodes: a smaller witness is easier to review and
carry, and it says exactly which nodes the requested claims needed.

From the repository root, Python 3.9+ standard library only:

```sh
python3 -B line-2/tools/proof-prune/prune.py demo
```

When tried, the offline demo verified the real historical ZTO proof for its
account and two absent raw storage slots against the saved mainnet root, then
added one **real but unrelated** node from the ZTO/IMD PoolManager proof and
one repeated ZTO node. Pruning removed both occurrences, reducing the account
proof from 12 to 10 nodes; the cleaned proof verified again and proved the same
state. The original two storage proofs remained at four and three nodes. The
saved root came from an RPC observation, not independent consensus
authentication. Historical public source: <https://ethereum-rpc.publicnode.com>.
No fresh network request was made.

## Use your own evidence

Supply an independently authenticated root and the exact requested address and
slots. Repeat `--slot` for each raw uint256 storage key; omit it for an
account-only witness. `audit` prints verified node counts and state; `prune`
prints only the cleaned witness, so it can be redirected to a **new** workspace
file. Never redirect onto the input file because a shell truncates it first.

```sh
python3 -B line-2/tools/proof-prune/prune.py audit \
  line-2/tools/state-witness/examples/zto-mainnet.json \
  --state-root 0x70c13580735123b57c0a9a24692875f4ef366b04c69d92af9f539561e626d512 \
  --address 0xd782bdea4ef02a0bd391eb9089470c8080f0a68e \
  --slot 0x0 --slot 0x1
```

Both commands verify the full original witness first. They trace each requested
account or storage key from its authenticated trie root, retain only the
external RLP nodes visited, and verify the cleaned witness again. Inline nodes
remain inside their parent RLP node. Nodes that happen to be useful for another
key still belong in that other key's proof; no cross-proof dictionary is made.
Node order is preserved and hex letters normalize to lowercase. The rest of
the witness, including untrusted labels, is unchanged. `audit` reports node
occurrences, not byte savings: JSON key order and whitespace may also change.

The sibling `state-witness/` folder must travel with this tool. Its 1 MB input,
64 slot, 128 node per proof, strict JSON and workspace-path limits apply. Input
files and symlink targets must stay inside the current working directory.
Exit 0 prints a complete report or witness; invalid evidence exits 1 with only
an error on stderr; argument errors exit 2. No partial success is printed.

The focused suite covers both real ZTO and pool proofs, duplicate and unrelated
nodes in account and storage tries, immutable inputs, wrong roots/requests,
missing path nodes, changed value claims and CLI failure behavior:

```sh
python3 -B -m unittest discover -s line-2/tools/proof-prune -v
```

The tool reads local evidence only. It does not capture network data, access
environment variables or secrets, handle keys or wallets, sign or send a
transaction, pay, post, or deploy. Removing unused nodes does not authenticate
the root, chain, canonicality, finality, freshness, contract layout or token
meaning. The user must supply the trusted root and reviewed request. The real
ZTO example uses the assignment coin directly; no new coin is needed.
