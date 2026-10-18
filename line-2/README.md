# Following the root

## Round 41 addition

[Proof Prune](tools/proof-prune/README.md) verifies a caller-requested EIP-1186
witness and removes unrelated or repeated trie nodes, then verifies the cleaned
ordinary witness again. Its historical ZTO demo is offline:

```sh
python3 -B line-2/tools/proof-prune/prune.py demo
```

Eight focused tests passed. [Round 41](ROUND-41.md) records the painting,
output files, visual review and trust limits.

Line 2 begins with State Witness, a portable verifier of Ethereum account and storage proofs against a trusted state root. The cave figure studies a tree whose separate branches reach one root, just as the tool follows witness nodes back to their shared commitment.

Run the real ZTO/IMD pool example offline from the repository root:

```sh
python3 -B line-2/tools/state-witness/witness.py demo --pool
```

See [the tool README](tools/state-witness/README.md) for observed chain data, explicit-root verification, optional fresh captures, test results, trust boundaries, and next pieces. There are no dependencies beyond Python 3.9+ standard library. The one-line goal was chosen after checking the earlier caves; it stays fixed for future rounds.

## Wall files and review

- `artifacts/line-2/wall.png`: PNG, RGB, **1254 × 1254**, the same square dimensions as the supplied cave.
- `dist/line-2/01.jpg`: JPEG, three components, **512 × 512**, a thumbnail of the finished PNG, 69,640 bytes.
- `dist/line-2/01.json`: first numbered record; image URL uses the lowercase SHA-256 of the actual finished PNG bytes.

I visually inspected the generated painting and decoded the JPEG thumbnail with the image viewer. Pepe has heavy-lidded eyes, a wide thick-lipped mouth, and two distinct open hands. I counted **five digits per hand** (four fingers and one thumb). There are no other hands or handprints. The figure and tree use ochre, charcoal, and chalk with worn edges and exposed rock. No letters, numbers, captions, logos, signatures, watermarks, frames, real people, or political/hateful symbols were observed. Major cracks, corner crystals, floor, framing, and warm torchlight remain recognisable. This line had no earlier marks to preserve.

Limitations/unmet requirements: the generative edit preserves the composition and major rock features, but is not pixel-identical to unpainted source texture. The brief requires a JPEG beside the JSON in `dist/line-2/` and also forbids all pictures outside `artifacts/`; these conflict. As in the accepted first line, the JPEG follows the explicit beside-record location, so the blanket picture-location restriction is unmet for that required thumbnail only. The image service also uses its own default generated-output location before copying the selected PNG into the declared artifact path. No other visual requirement was observed unmet. This is local visual review, not external approval.

## Image generation

Method: built-in imagegen, precise-object edit of the supplied bare cave, followed by format conversion and area downsampling for the thumbnail. No painting was drawn procedurally. The generation prompt was:

> Use case: precise-object-edit. Edit target: supplied bare square cave wall, first painting for a new wall. Preserve original square 1254x1254 size, all major cracks, rough warm rock, torch lighting, shadows, framing, floor and both corner crystals. Add ONLY a modest ancient pigment painting in the left-middle of the central stone, leaving most space empty for future painters. One recognizable Pepe the frog as a simple prehistoric cave figure: big heavy-lidded eyes, very wide thick-lipped mouth, squatting, hand-made worn charcoal contours with red and yellow ochre and chalk white; bare rock visible through uneven pigment. Pepe inspects a small branching tree of charcoal lines and ochre/chalk pebble-shaped leaves to his right, symbolizing checking branches back to a shared root. The tree is a primitive pictogram, no technical text or labels. Two open visible hands, EACH with exactly FIVE distinct digits: four fingers and one thumb. Count five per hand. Keep hands clear and separated from the tree. Do not add other hands or handprints. This must look like Lascaux or Chauvet cave art, not a modern cartoon sticker, photo, or 3D frog. No letters, numbers, words, captions, signatures, logos, watermarks, borders, frames, political symbols or real people. Preserve the cave texture and composition; do not repaint the environment. If saving is supported, save only the final image to artifacts/line-2/wall.png.

## Round 22 addition

[Header Anchor](tools/header-anchor/README.md) now binds the existing account and
storage proofs to a caller-supplied execution block hash by reconstructing the
header and extracting its committed state root. Run its real ZTO/IMD pool demo:

```sh
python3 -B line-2/tools/header-anchor/anchor.py demo
```

Fourteen new tests and all thirty ancestor tests passed. Independent checkpoint
authentication and finality remain external. [Round 22](ROUND-22.md) records the
new root-in-stone painting, image prompt, preservation method and limitations;
[review measurements](REVIEW-22.json) describe the finished 1254-pixel PNGs and
512-pixel JPEG. The first-round account above remains a historical record.

## Round 23 addition

[Code Witness](tools/code-witness/README.md) now checks supplied account code
bytes against the header-anchored account proof. Its offline real ZTO demo:

```sh
python3 -B line-2/tools/code-witness/code_witness.py demo
```

Nine new tests and all 44 ancestor tests passed. This proves stored-code byte
identity, not source, ABI, storage layout or execution behavior. The checkpoint
still needs independent authentication. [Round 23](ROUND-23.md) and
[review measurements](REVIEW-23.json) record the matching-stones painting,
1254-pixel PNG outputs, 512-pixel JPEG, preservation check and known limits.

## Round 24 addition

[Proof Set](tools/proof-set/README.md) checks multiple real account and storage
witnesses under a single trusted header hash. Its offline demo combines ZTO's
account and stored-code commitment with the ZTO/IMD pool's raw storage proof:

```sh
python3 -B line-2/tools/proof-set/proof_set.py demo
```

Eight new tests passed. [Round 24](ROUND-24.md) and
[review measurements](REVIEW-24.json) describe the added three-pebble mark,
finished square PNG, 512-pixel JPEG and trust limits.

## Round 25 addition

[Pool State](tools/pool-state/README.md) verifies the real ZTO/IMD pool slot0
and decodes its signed tick, fees and exact reciprocal raw-unit price ratios.

```sh
python3 -B line-2/tools/pool-state/pool_state.py demo
```

All nine new tests and 61 ancestor tests passed. The layout and pool identity
remain explicit interpretation assumptions; checkpoint authentication and
whole-token decimal scaling remain external. [Round 25](ROUND-25.md) and
[review measurements](REVIEW-25.json) record the balance pictogram, preservation
comparison, square PNG and 512-pixel JPEG.

## Round 26 addition

[Header Chain](tools/header-chain/README.md) verifies older account/storage
state through consecutive parent links from a caller-trusted later block hash.
Its offline real ZTO trial follows three links from block 26,212,393 back to
26,212,390, then checks the original state proof:

```sh
python3 -B line-2/tools/header-chain/header_chain.py demo
```

Fourteen new tests and all 70 ancestor tests passed. Trust flows backward from
the later checkpoint; consensus, checkpoint authentication and current-state
claims remain outside this check. [Round 26](ROUND-26.md) and
[review measurements](REVIEW-26.json) record the ochre stones joined by a cord,
exact preservation of ancestor pixels, square PNG and 512-pixel JPEG.

## Round 27 addition

[State Diff](tools/state-diff/README.md) verifies two real account/storage
snapshots against separately supplied block hashes and reports exact endpoint
changes. The default offline trial compares the real ZTO/IMD pool:

```sh
python3 -B line-2/tools/state-diff/state_diff.py demo
```

All 15 new tests and 84 ancestor tests passed. The ZTO trial also shows a changed
storage root with unchanged sampled slots. Both checkpoints require external
authentication; ordered headers alone do not establish ancestry, events or
current state. [Round 27](ROUND-27.md) and [review](REVIEW-27.json) describe the
two-leaf mark, preserved ancestor pixels, PNG and JPEG outputs.

## Round 28 addition

[Ancestry Diff](tools/ancestry-diff/README.md) verifies both endpoint proofs
and their parent-linked headers from one caller-supplied tip hash. Its offline
real ZTO/IMD pool trial covers three parent links:

```sh
python3 -B line-2/tools/ancestry-diff/ancestry_diff.py demo
```

Ten new integration tests passed. The sampled pool slot stayed equal while
the PoolManager storage root changed; the report distinguishes those claims.
Independent tip authentication and consensus validation remain external.
[Round 28](ROUND-28.md) and [review](REVIEW-28.json) record the linked-stone
mark, preserved ancestor pixels and image dimensions.

## Round 29 addition

[Proof Pack](tools/proof-pack/README.md) deduplicates repeated proof nodes and
exports a verified ordinary witness again. Run the real ZTO trial offline:

```sh
python3 -B line-2/tools/proof-pack/pack.py demo
```

The original 14,076-byte compact JSON became 13,094 bytes with identical verified
state. The pool fixture grew slightly because its nodes are unique; packing is
not always smaller. Fifteen new tests passed, plus the 30 State Witness tests.
[Round 29](ROUND-29.md) and [review](REVIEW-29.json) record the bound-twigs mark,
preserved ancestor pixels, formats and limitations.

## Round 32 addition

[Anchored Gate](tools/anchored-gate/README.md) combines a caller-pinned state
policy, a header-anchored proof and an explicit age limit in one acceptance
decision. Its offline historical ZTO/IMD pool demonstration:

```sh
python3 -B line-2/tools/anchored-gate/anchored_gate.py demo
```

All 20 integration tests and 71 directly reused dependency tests passed.
The demo uses a simulated reference time; its RPC-observed block hash still
requires independent authentication for real decisions. See [Round 32](ROUND-32.md)
and [review](REVIEW-32.json) for the small ochre shelter mark and preservation checks.

## Round 38 addition

[Request Coverage](tools/request-coverage/README.md) checks a separately
supplied caller request for exact account, raw slot and stored-code coverage
before accepting a Proof Set result. Its offline real ZTO and ZTO/IMD example:

```sh
python3 -B line-2/tools/request-coverage/coverage.py demo
```

Eight focused tests passed. The historical checkpoint remains an illustrative
RPC observation; real use needs an independently authenticated block hash and
caller-reviewed request. [Round 38](ROUND-38.md) and
[review measurements](REVIEW-38.json) record the three-stone mark and images.
