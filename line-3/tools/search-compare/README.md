# Search Compare

Compare retrieval from two offline document collections using one set of labelled
queries. This is useful before replacing a worker's document collection: a query
that got worse remains visible even if the average improved. Reports include
per-query metric changes, gained/lost target ranges, both complete evaluations,
verified exact source excerpts, corpus identities and a canonical judgment hash.
Python 3.9+ standard library only. Keep the adjacent Search Evaluate, Search Batch,
Evidence Search and Corpus Freshness folders; no installation is needed.

From the repository root, one command demonstrates real historical sources:

```sh
python3 -B line-3/tools/search-compare/compare.py demo
```

When tried, comparing the inherited ZTO/IMD documents to themselves returned no
regressions, identical corpus hashes and zero metric deltas. The ZTO decimals
and ZTO/IMD pool targets were found at rank one on both sides; the inherited
intentionally unrelated query missed on both sides. Macro recall was 2/3 on
each side. This is a deterministic control, not evidence of improved retrieval.
Nine behavioral tests also passed, including an actual changed-text comparison
with one gained query and one lost query whose average deltas cancel to zero.
The report still flagged the lost query. The bundled data retain their original
historical RPC/reference qualifications; no current chain or price claim is made.

For your own collections, write a judgment file in the workspace:

```json
{
  "format": "evidence-search-judgments/v1",
  "queries": [{
    "id": "decimals", "query": "ZTO token decimals",
    "limit": 3, "require_all": true,
    "targets": [{"path": "zto.md", "line_start": 6, "line_end": 6}]
  }]
}
```

Then run:

```sh
python3 -B line-3/tools/search-compare/compare.py run BASELINE_DIR CANDIDATE_DIR JUDGMENTS.json
```

Output is JSON on stdout. Exit **0** means no per-query metric decreased; **1**
means at least one decreased (a complete report is still printed); **2** means
invalid input, I/O failure or detected corpus change, with JSON on stderr and
no partial stdout. A query can appear in both improved and regressed lists when
its metrics move in different directions. Existing misses do not themselves
cause exit 1. No threshold or statistical significance is implied.

The same paths and inclusive target ranges must exist in both collections. A
missing target file or line is an error rather than a measured miss. Labels must
still mean the same thing on both sides: this tool cannot detect semantic drift
or relocate labels after inserted lines. Review labels before comparison. The
ranking algorithm and query settings are identical on both sides; this compares
collections, not different search engines. Source texts are inert data.

Metrics reuse Search Evaluate unchanged: target recall counts fully contained
labelled ranges; labelled hit precision counts hits containing at least one
target; reciprocal rank uses the first such hit. Unlabelled hits are not proven
irrelevant. Deltas are candidate minus baseline. Any negative per-query delta
counts as a regression, even if macro deltas are positive or zero. Rank changes
can trigger regression without a lost target. Raw floating values are retained.

All reads stay within the workspace, with the inherited no-symlink corpus rules.
Runtime writes nothing and makes no network, environment, wallet or transaction
request. Bounds: 64 KiB judgment JSON, 1–32 queries, 128 total targets, up to 50
hits per query; each corpus up to 1,000 supported UTF-8 documents and 8 MB text.
Further passage/file limits come from Evidence Search. Both evaluations check
freshness, then both whole corpus identities are reread after evaluation. Keep
both collections static: these checks do not provide atomic snapshots or detect
edits undone between reads. Hashes establish consistency, not trusted authorship,
factual correctness, relevance or complete coverage. Canonical judgment hashing
sorts object keys and preserves array order.

Run checks with `python3 -B line-3/tools/search-compare/test_compare.py -v`.
Fixtures live only in disposable `test/scratch/`. Tests cover real historical
citations, determinism, immutable inputs, gains/losses, hidden aggregate regression,
rank-only loss, missing labels, changed baseline, invalid plans, symlink refusal,
and all three CLI statuses.
