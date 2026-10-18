# Merge Dependencies

Review concurrent edits to a dependency catalog, then check whether the clean
merged result still has compatible versions. This joins line 1's Threeway and
Merge Review with line 4's Offline Resolver and Conflict Core. Python 3.9+,
standard library only. The folder is portable without the line folders.

From the repository root:

```sh
python3 -B shared/merge-dependencies/check_merge.py demo
```

The demo succeeds with exit 0 when it finds the deliberately incompatible merge.
The bundled **real Requests release metadata** resolves in base and in each
branch separately. One branch chooses Requests 2.25.1; the other chooses
`idna >=3.10`. Their text changes do not overlap, but Requests 2.25.1 requires
`idna >=2.5,<3`. The merged catalog has no solution. Its irreducible root core
contains those two requirements; removing either produces a checked assignment.
These are historical finite-catalog observations, not package recommendations.

For your own three workspace catalog files:

```sh
python3 -B shared/merge-dependencies/check_merge.py check shared/merge-dependencies/examples/base.json shared/merge-dependencies/examples/ours.json shared/merge-dependencies/examples/theirs.json
```

This exits **1**, as expected for the demonstrated incompatibility. Output is a
JSON report containing exact input hashes, diffs, conflict regions or merged
candidate text, dependency analysis, and a repeated core/assignment audit.
No input file is changed. Nothing is applied, installed, imported from the
catalog, fetched, signed or sent. It reads no environment or configuration.

Exit codes for `check`: 0 compatible; 1 text conflict or incompatible catalog;
2 invalid input or a clean text merge that is not a supported catalog;
3 search/audit/minimization incomplete. `--max-steps` bounds analysis to
1–1,000,000 solver states (default 10,000), and gives the audit a separate budget
of the same size. The report retains a known incompatible subset when reduction
is incomplete, but the overall status stays inconclusive. Text conflicts never
enter the solver. JSON duplicate keys and non-finite values are rejected.

Catalog format: exactly `packages` and nonempty `roots`. Each package maps
numeric release strings to dependency objects. Constraints support `*` or
comma-separated `==`, `!=`, `>=`, `<=`, `>`, `<`. This is not full PEP 440 or a
pip/npm installer. Files must resolve inside the current workspace. Each text
input is bounded to 1 MiB and 4,000 lines; the inherited catalog bounds are
1,000 packages, 10,000 releases and dependency depth 200. Stable inputs required;
no atomic filesystem snapshot or hard wall-clock bound is provided.

Ten integration tests passed, including the real semantic conflict, compatible
edits, preservation of files and conflict fragments, duplicate JSON, grammar,
UTF-8 and size errors, budget/minimization/audit incompleteness, determinism,
branch symmetry and CLI codes:

```sh
python3 -B shared/merge-dependencies/test_check_merge.py -v
```

## Provenance and limits

`merge.py` and `review.py` came from line 1's `threeway` and `merge-review`.
`resolve.py` and `core.py` came from line 4's `offline-resolver` and
`conflict-core`. Only the two sibling module lookup paths were adapted; the
engines are unchanged. `examples/sources.json` retains the upstream source URLs
and projection notes from line 4. The three example catalogs vary only roots
over that same release snapshot. `check_merge.py` is the new glue.

The audit uses the same solver to recheck impossibility. It is not independent
certification. Irreducible is not minimum cardinality, unique, or a suggested
repair. Catalog hashes do not authenticate publishers. Compatibility covers only
listed releases and constraints, not interpreter/platform markers, artifacts,
security or omitted releases. Text cleanliness alone never certifies semantics.
ZTO and IMD already suffice for any future coin-related evidence; this offline
workflow needs no token or payment.

## Second compatibility check (gathering 25)

```sh
python3 -B shared/merge-dependencies/second_check.py demo
```

This read-only, offline command merges the real Requests catalogs, runs the
existing resolver/core analysis, and separately enumerates all 24 candidate
assignments. Both searches find incompatibility. Demo exits 0 on this expected
result. The original checker remains available unchanged.

For supplied files, use `second_check.py check BASE OURS THEIRS`, all paths inside
the workspace. It emits one JSON report with the exact merge review, original
analysis, separate enumeration, and an independent edge check of a successful
solver assignment. Inputs stay unchanged. There are no installs or network calls.

`--max-steps` bounds each original solver pass and `--max-assignments` bounds the
separate enumeration, each from 1 to 1,000,000, default 10,000. The two searches
can select different valid versions. Their compatibility conclusions must agree;
budget exhaustion or unfinished core reduction keeps the combined result
inconclusive even if the other search finished. A text conflict or invalid catalog
skips enumeration. A malformed resolved assignment is reported as disagreement.

For `check`, exits are 0 compatible, 1 incompatible/text conflict, 2 invalid input,
3 inconclusive, 4 disagreement. A disagreement is a reason to investigate the
engines or input assumptions; it is never approval. The separate enumeration
checks the full merged catalog, not core irreducibility or explanatory fields.
It is exponential and shares the original parser and numeric grammar. It is a
second local implementation, not independent certification or formal proof.

Eleven additional integration tests passed (21 across this folder), including
false solver claims and assignments, both budget limits, conflict short-circuit,
strict JSON, unchanged inputs, deterministic output and standalone relocation:

```sh
python3 -B -m unittest discover -s shared/merge-dependencies -p 'test_*.py'
```

`exhaustive.py` is copied from line 4's `exhaustive-audit/audit.py`: only its
sibling resolver path was relocated and its original line-specific CLI removed.
The enumeration, assignment checker and audit functions are byte-for-byte as
written by that line. `SECOND-CHECK-PROVENANCE.json` records both hashes and the
exact adaptation. `second_check.py` supplies the merge integration and CLI.

## Minimum root repair after a checked merge (gathering 26)

```sh
python3 -B shared/merge-dependencies/repair_merge.py demo
```

This combines line 1's merge review with line 4's Root Repair. It first runs the
two compatibility searches above. Only when both finish and agree the merged
catalog is incompatible does it search for the fewest top-level requirements to
remove. On the bundled real Requests metadata, it proposes removing the new
`idna >=3.10` root, leaving Requests 2.25.1's transitive `idna 2.10` selection.
This is a review proposal, not an edit or package recommendation.

For your own three workspace catalog files:

```sh
python3 -B shared/merge-dependencies/repair_merge.py check BASE.json OURS.json THEIRS.json
```

The result includes the full merge and second-check report, plus the bounded
Root Repair report. `--max-steps`, `--max-assignments`, `--max-repair-steps` and
`--max-trials` bound the respective searches. Exit 0 means compatible, 1 means
a repair was proposed or text conflict remains, 2 means invalid input, 3 means
inconclusive, and 4 means the checks disagree. The demo exits 0 when it finds
the expected incompatibility and proposal. Search budgets do not bound wall
clock time. No input is written, applied, installed, executed, sent or paid.

`repair.py` is an ordinary copy of line 4's Root Repair, with its two sibling
module imports and demo fixture path adapted to this portable folder. Exact
source and copy hashes are in `REPAIR-PROVENANCE.json`; `repair_merge.py` is the
glue. Minimum is by root count, not user priority. The choice can remove a
requirement a user needs, so a worker must review the proposal and the selected
versions. Finite catalogs can omit releases and metadata. The search and audit
share the numeric constraint grammar and are local computational checks, not
publisher authentication or proof of installability.

All tests, including the new integration tests, run with:

```sh
python3 -B -m unittest discover -s shared/merge-dependencies -p 'test_*.py'
```

## Minimum-change plan after a compatible merge (gathering 27)

```sh
python3 -B shared/merge-dependencies/plan_merge.py demo
```

This connects line 1's reviewed text merge to line 4's Lock Plan. The demo uses
the existing historical Requests release catalog, two independent root edits,
and a saved compatible baseline. Both compatibility checks accept the clean
merged catalog. The planner then proves that changing only Requests from 2.31.0
to 2.32.5 is a minimum **one-package** change; the other four selected versions
stay put. It does not edit any input or install a package.

For your own workspace files, use:

```sh
python3 -B shared/merge-dependencies/plan_merge.py check BASE.json OURS.json THEIRS.json --baseline BASELINE.json
```

`BASELINE.json` is a plain package-to-version object, not a solver report. The
tool validates it before checking the merge. It plans only if the text merge is
clean and both bounded compatibility searches complete and agree it is
compatible. Text conflict, incompatibility, search disagreement or budget
exhaustion never yields a completed plan. `--max-steps`, `--max-assignments` and
`--max-plan-steps` bound the three searches separately. Exit codes are 0 for an
optimal plan, 1 for text conflict or incompatibility, 2 for invalid input, 3
for inconclusive work and 4 for disagreement.

The portable `lock_plan.py` is an ordinary adapted copy of line 4's planner;
`LOCK-PLAN-PROVENANCE.json` records both hashes and the import/CLI adaptations.
The new glue and five integration tests live beside the older integrations.
All 31 shared merge-dependencies tests passed locally. This is a finite numeric
catalog proposal: package edits have equal cost, and metadata provenance,
platform rules, artifacts, security and installability are not checked.
# Audited minimum-change proposals (gathering 28)

Connect line 1's reviewed text merge to line 4's Lock Plan and separate Plan
Audit. Run from the workspace root, using Python 3.10+ standard library only:

```sh
python3 -B shared/merge-dependencies/audited_plan.py demo
```

Tried here: the historical Requests catalog edits merge cleanly, both
compatibility searches agree, and the planner proposes one package change.
The separate audit exhausts **24 Cartesian assignments** of the actual merged
catalog and confirms minimum cost **1**, changing Requests 2.31.0 to 2.32.5.
This is a finite historical example, not a version recommendation or install.

For your own inputs:

```sh
python3 -B shared/merge-dependencies/audited_plan.py check BASE.json OURS.json THEIRS.json --baseline BASELINE.json
```

Use actual workspace files in the existing catalog and baseline formats below.
The command writes JSON to stdout and never changes inputs. Keep this entire
folder together; it works without the original line folders or network access.
`plan_audit.py` is an ordinary adapted copy of line 4's Plan Audit, recorded
with both source and copy hashes in `PLAN-AUDIT-PROVENANCE.json`.

Exit 0 (`audited`) requires both compatibility checks, a completed plan and a
completed minimum audit. Exit 1 means text conflict or incompatible catalog;
2 invalid input; 3 inconclusive budget; 4 disagreement. An audit budget can be
set with `--max-audit-assignments` (1–1,000,000). Earlier stages retain separate
`--max-steps`, `--max-assignments` and `--max-plan-steps` budgets. An unfinished
audit retains the proposal for inspection but never labels it audited.

The audit checks the selected witness and minimum edit count. It does not
authenticate metadata, origin, authors or the planner's diagnostic fields.
The two algorithms share numeric parsing and edge checking, so shared defects
remain possible. Enumeration is exponential; limits do not bound elapsed time
or memory. No artifact, security, platform or installability claim is made.

Six integration tests passed, including false optima, bad witnesses, exact
budget boundaries, skipped audits, immutable inputs and a portable folder copy:

```sh
python3 -B -m unittest discover -s shared/merge-dependencies -p 'test_audited_plan.py' -v
```

## Release choices after a merge (gathering 29)

See every release that can participate in a compatible selection of the actual
merged catalog, with full assignment witnesses. This combines line 1's review
packet with line 4's Release Map. Run offline from the workspace root:

```sh
python3 -B shared/merge-dependencies/merge_choices.py demo
```

Tried here: all **24 candidates** exhausted, **eight compatible selections**,
**eight viable releases**, and four stored witnesses covering those releases.
Five other releases are excluded under this merged catalog's constraints.
The bundled historical Requests metadata is a compatibility example, not a
current package recommendation. No files, roots or pins are changed.

For your own workspace-local inputs:

```sh
python3 -B shared/merge-dependencies/merge_choices.py check BASE.json OURS.json THEIRS.json --max-assignments 10000
```

Use the same finite numeric catalog schema as the original merger. JSON output
includes the exact merge packet and a `choices` map. Every `viable` release
references a full compatible selection by zero-based witness index. A completed
map with no selections is incompatible. A partial map preserves positive
witnesses but labels every unproved release `unknown`, never `excluded`.
Text conflicts skip mapping; malformed or duplicate-key JSON is rejected.

Exit codes: **0** mapped, **1** text conflict or incompatible, **2** invalid,
**3** inconclusive. `--max-assignments` accepts 1–1,000,000 complete tuples;
completion exactly at the limit succeeds. No solver search or root reduction
is called by this workflow. It shares the inherited numeric parser and edge
checker, so their defects remain possible. Enumeration is exponential and the
budget does not cap wall time, parsing, memory or output size. Witnesses do not
establish platform compatibility, artifact authenticity, security or installability.

`release_map.py` is an ordinary copy of line 4's algorithm, with its checker
lookup relocated and line-specific CLI removed. Source and copy hashes are in
`RELEASE-MAP-PROVENANCE.json`. Keep this entire shared folder together; Python
3.10+ standard library suffices without line folders, installation or network.
Seven new tests passed, including real merged-catalog witnesses, exact budgets,
partial-map semantics, incompatible merges of separately compatible branches,
conflict short-circuiting, malformed inputs and portable read-only execution:

```sh
python3 -B -m unittest discover -s shared/merge-dependencies -p 'test_merge_choices.py' -v
```

## Selection changes after a merge (gathering 39)

A clean, compatible merge can still remove or add valid dependency selections.
Compare the actual merged catalog with base and both branches:

```sh
python3 -B shared/merge-dependencies/merge_equivalence.py demo
```

Tried here: the historical Requests example merges cleanly and remains
compatible, but all three input selection sets differ from the merged set.
The tool supplies a full selection accepted before and rejected after each
comparison (found after 21, 23 and 27 candidate checks). This helps a reviewer
see the effect of combined root edits; differences may be intentional.

For workspace-local files:

```sh
python3 -B shared/merge-dependencies/merge_equivalence.py check BASE.json OURS.json THEIRS.json --max-assignments 10000
```

Exit 0 `preserved` requires all three finite selection sets to match the merged
set after exhaustive enumeration. Two empty sets match; preserved does **not**
mean compatible. Exit 1 is `changed` with counterexamples, or `text_conflict`
with no enumeration. Exit 2 means invalid inputs; exit 3 `inconclusive` means
at least one comparison exhausted its budget. Known differences are retained
in an incomplete report. The demo exits 0 when it finds its expected changes.

Each comparison receives its own 1–1,000,000 assignment budget (default 10,000).
A difference requires only one counterexample, while equality requires complete
enumeration. Catalog identities coalesce numeric release labels; the merge
packet separately retains hashes of exact input bytes and candidate text.
No inputs change, and no package is installed, executed, fetched, signed or sent.

`equivalence.py` copies line 4's Solution Equivalence algorithm unchanged;
only its checker and demo paths are adapted. `EQUIVALENCE-PROVENANCE.json`
records exact hashes. It uses the existing portable line 1 merger and line 4
parser/edge checker in this folder; no line folders or dependencies are needed.
Eight integration tests cover real counterexamples, added/removed selections,
branch symmetry, empty sets, exact budget boundaries, partial reports,
conflict short-circuiting, invalid JSON, CLI codes, immutable inputs and
standalone relocation:

```sh
python3 -B -m unittest discover -s shared/merge-dependencies -p 'test_merge_equivalence.py' -v
```

Keep inputs static. This is finite numeric metadata equivalence, not a full
package manager or semantic equivalence of installed programs. Shared parser
and edge-checker defects remain possible. Enumeration is exponential and the
assignment budget is not a time/memory bound. Hashes identify bytes, not trust.

## Compatible selection counts after a merge (gathering 40)

`merge_census.py` joins line 1's reviewable three-way merge with line 4's
Component Census. It counts the complete reachable selections in the base,
both branches and clean merged catalog. Independent dependency groups are
counted separately, so their candidate cross-product need not be enumerated.
It reports exact count changes only when all four counts finish. A partial
zero remains unknown; an exhausted empty component proves incompatibility.

```sh
python3 -B shared/merge-dependencies/merge_census.py demo
python3 -B -m unittest discover -s shared/merge-dependencies -p 'test_*.py'
```

The historical Requests demo returned exact counts **12, 12, 8, 8** for base,
ours, theirs and merged, so the merged count is four below base and ours and
equal to theirs. These numbers concern the inherited finite metadata snapshot,
not a current package recommendation. The six new integration tests cover this
case, independent groups, partial and exact zero, text conflict, invalid input,
budget rejection, CLI output and source immutability. The full shared folder
passed 58 tests locally.

For your own files, run `python3 -B shared/merge-dependencies/merge_census.py
check BASE.json OURS.json THEIRS.json --max-assignments 10000` from the workspace
root. Exit 0 means all counts are exact, 1 means a text conflict, 2 means an
invalid catalog or input, and 3 means at least one count remains inconclusive.
Each catalog receives its own finite budget. Equal counts do not imply equal
selection sets; use `merge_equivalence.py` for that question. This workflow
reads only supplied workspace files, writes JSON to stdout, and never installs
or changes a package. Search remains exponential within a connected group.

`components.py` is an ordinary copy of line 4's algorithm with only its
checker and demo paths adapted to this portable folder. Exact source and copy
hashes are in `CENSUS-PROVENANCE.json`. This folder needs no line folders,
network, wallet or new coin at runtime.
## Gathering 41: exact pins after a merge

`merge_pins.py` joins line 1's reviewed three-way text merge with line 4's
Pin Core. It checks the same caller-supplied exact release requests against
base, ours, theirs and the actual merged catalog. A clean text merge can leave
the catalog compatible but make a particular requested release impossible.
This report keeps those two situations separate.

From the workspace root, Python 3.10+ and the standard library only:

```sh
python3 -B shared/merge-dependencies/merge_pins.py demo
```

When tried over the inherited historical Requests catalogs, base and ours
admitted the illustrative pins `idna=2.10` and `certifi=2025.8.3`. Theirs and
merged required idna >=3.10, so the merged report returned the singleton core
`idna=2.10` and discarded certifi from the explanation. A full compatible
selection after dropping the idna pin shows that the original merged roots
remain satisfiable. The demo exits 0 when this expected conflict is found.
It makes no current package recommendation or network request.

For your own three workspace-local catalogs:

```sh
python3 -B shared/merge-dependencies/merge_pins.py check BASE.json OURS.json THEIRS.json --require idna=2.10 --require certifi=2025.8.3 --max-assignments 10000
```

Use the existing finite numeric catalog grammar. Repeat `--require` for each
exact package release; canonical duplicate pins are refused. Pins require the
package to be selected in the original roots' reachable closure; they do not
add roots. Each of four catalogs gets its own assignment budget, 1–1,000,000.
`status` describes the merged catalog; inspect all four `catalogs` rows for
their individual statuses. `lost_pin_compatibility_from` lists earlier catalogs
with positive pin witnesses when the merge is conclusively incompatible;
it is null for an inconclusive merge. It does not assign blame to a branch.

Exit 0 means compatible; 1 means incompatible pins, baseline-unsatisfiable
roots, or a text conflict; 2 means invalid input; 3 means the merged pin search
is inconclusive. A text conflict stops dependency work. An invalid catalog is
reported before enumeration. JSON goes to stdout for complete review reports;
CLI input errors go to stderr with empty stdout. The CLI demo's expected
conflict exception is limited to the built-in demonstration.

An incompatible report contains a subset-minimal core and one checked full
selection for deleting each core pin. These witnesses need not satisfy pins
discarded from the explanation. A core is not necessarily smallest, and no
core is claimed for an unsatisfiable original baseline or incomplete search.
An early positive witness is conclusive without a complete count. Finite
metadata says nothing about platforms, artifacts, security or installation.
Enumeration and core reduction can grow exponentially; the assignment budget
is not a bound on parsing, memory, output or elapsed time.

This entire folder is portable without line folders or installation. The new
`pin_core.py` copy has only two path adaptations recorded with exact hashes in
`PIN-CORE-PROVENANCE.json`. It uses the existing portable `exhaustive.py` and
`resolve.py`. The merger bounds each input to 1 MiB / 4,000 lines and requires
paths inside the current workspace. It rejects external symlink targets;
stable trusted path ancestors are required. Runtime prints a proposed candidate
and reports but applies no edit, installs no package, and accesses no network,
environment, wallet, secret, signing, transaction, payment or post.

Nine new integration tests passed, including historical immutability, a
two-pin conflict with checked deletion witnesses, aliases and unreachable pins,
baseline failure, exact/partial budgets, invalid inputs, text conflicts, all
CLI statuses and a standalone copied folder:

```sh
python3 -B -m unittest discover -s shared/merge-dependencies -p test_merge_pins.py -v
```

