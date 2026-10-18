# Pin Core

Explain why a set of exact release requests cannot coexist. This tool returns
a **subset-minimal conflicting set of pins** and a complete compatible selection
for dropping each pin in that set. It helps a worker decide which requested
release to reconsider without blaming unrelated pins. Pins require presence in
the original roots' dependency closure; they never introduce new roots.

From the repository root, run with Python 3.9+ and only its standard library:

```sh
python3 -B line-4/tools/pin-core/pin_core.py demo
```

I ran this command over the inherited historical Requests metadata projection,
using explicit illustrative roots `requests: *` and `urllib3: <2`. It checked all
216 candidates and found 26 compatible original-root selections. The requested
pins were Requests 2.25.1, idna 3.10 and certifi 2025.8.3. It discarded certifi
and returned the other two pins as the conflict. Dropping idna admits idna 2.10;
dropping Requests admits Requests 2.31.0. Each witness contains a full reachable
selection checked against the unchanged catalog. No live metadata was fetched;
these are finite historical metadata results, not installation recommendations.

For an explicit workspace-local catalog:

```sh
python3 -B line-4/tools/pin-core/pin_core.py path/to/catalog.json --require app=1 --require dep=2
```

Use Offline Resolver's `packages` and `roots` format, numeric versions and
conjunctive comparisons. Keep the adjacent `exhaustive-audit/` and
`offline-resolver/` folders; the demo also needs the stored
`conflict-core/examples/requests-conflict.json`. Canonical package names and
numeric version aliases normalize to the catalog's labels. Duplicate canonical
pins, duplicate JSON keys, unsupported syntax, catalogs above 1 MB and paths
resolving outside the current workspace are rejected by the inherited loader.
The input and pins are never modified.

The algorithm enumerates the original roots' possible reachable assignments,
rejects invalid edges and extraneous unreachable selections, and records which
pins each compatible selection satisfies. It retains one integer assignment
index per distinct pin pattern, rather than every full witness. A full-pin
witness establishes `compatible` immediately. Otherwise **only complete search**
allows a negative conclusion. If no compatible selection exists without pins,
the status is `baseline-unsatisfiable` and no pin core is claimed. For a
compatible baseline with conflicting pins, deterministic deletion in sorted
package order removes each pin whose absence still leaves a conflict.

Every pin left in `core` has a `deletion_witnesses` entry: its selection satisfies
all the other core pins and violates the removed pin. Witnesses are reconstructed
from mixed-radix assignment indices and checked again against the original
catalog and the final core. These witnesses establish subset minimality.
The witnesses need not satisfy discarded pins. This is **not** a minimum-size
core, an enumeration of all cores, or a suggested package upgrade. Deletion order
can select one of several different valid cores. Complete enumeration proves
the core itself has no witness in this finite catalog.

`--max-assignments N` accepts 1–1,000,000 (default 10,000), shared across the
single enumeration. Exact completion at the budget is conclusive. Empty root
domains prove baseline incompatibility without checking a candidate. A partial
search without a full-pin witness says `inconclusive`, omitting the core and
minimality witnesses even if an incompatible pattern seems likely. Counts of
compatible selections are observations before any early return, not necessarily
complete counts. The catalog SHA-256 binds normalized input, not metadata truth
or artifact integrity.

Exit 0 means compatible, or the expected built-in conflict demo; exit 1 means
incompatible pins or an unsatisfiable baseline; exit 2 means invalid input;
exit 3 means inconclusive. Explicit `--require` arguments with `demo` use the
ordinary status exits and the same illustrative roots.

Checks run successfully:

```sh
python3 -B -m unittest discover -s line-4/tools/pin-core -p 'test_*.py' -v
```

All 11 tests passed, including a separate raw-edge oracle over 400 seeded
catalogs, redundant pins, missing/unreachable pins, branch-dependent presence,
cycles, numeric aliases, unchanged inputs, corrupt reconstructed witnesses,
baseline conflicts, exact/partial budgets, CLI exits and the historical demo.
The inherited Exhaustive Audit and Joint Check suites also passed. These are
local checks, not independent certification.

Limits: enumeration and pin patterns can grow exponentially. The assignment
budget does not bound parsing, memory, core reduction, output or wall-clock time;
core reduction scans observed patterns for each pin. This shares grammar and
edge checking with inherited tools, but never calls the resolver search or its
comparison predicate. Platform markers, extras, full PEP 440, package artifacts,
security and actual installation behavior are outside this finite model.
The tool only reads explicit inputs and sibling modules and prints JSON. It
uses no network, environment variables, configuration discovery, installation,
package execution, wallet, key, signing, payment, transaction or post.
