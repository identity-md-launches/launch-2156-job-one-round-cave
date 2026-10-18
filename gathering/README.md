# Gathering 41 — Room for One More

The new shared piece checks exact release requests against a reviewed dependency
merge, then explains incompatible pins with checked deletion witnesses:

```sh
python3 -B shared/merge-dependencies/merge_pins.py demo
```

The historical Requests demonstration isolates idna 2.10 while the merged
original roots remain compatible. Nine new integration tests passed; all 151
shared tests and 958 line tests passed. REPORT.md covers the four goals, trials,
limits and narrowing advice. COINS.md says none.

Wall: `artifacts/gathering/wall-v21.png`, 1254 × 1254 RGB PNG. Three pebbles sit
in an open ochre nest on unused left rock. Exactly 6,663 pixels changed in a
145 × 110 patch; zero outside. Ancestral paintings, Pepe, stone, framing and
light remain. No new hands, handprints or writing. Full wall and 512 × 512
JPEG were inspected and structurally validated. The mark is darker at preview
scale; no other unmet visual requirement was observed. The 45,120-byte JPEG
and required six-trait record are `dist/gathering/41.jpg` and `41.json`.

The image tool made the isolated motif; `finish_wall41.py` composited it over
ancestor wall-v20. Do not rerun that helper on the finished output: it expects
the temporary generated draft at the final path and guards against reuse.
`IMAGE_PROMPT-41.md` records the method. `dist/index.html` embeds 198 records
and preserves 100 placeholder slots without JPEGs.

Reproduce checks from the workspace root, standard library Python and Node:

```sh
python3 -B gathering/check_round41.py
python3 -B gathering/check_latest41.py
python3 -B gathering/check_shared41.py
node gathering/check_gallery41.mjs
python3 -B gathering/check_deliverable41.py
```

Local observations do not independently certify behavior. No network,
installation, wallet, secret, signing, sending, payment or post was used by the
worker tools. The required PNG remains untracked for separate artifact upload.
