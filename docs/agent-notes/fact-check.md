# Fact-check report — solar TED dataset & EU-funding/competition analysis

Date: 2026-11-25. Author: fact-checking subagent.
Method: the 8-stage framework in `.opencode/skills/fact-check-data/SKILL.md`.
Statuses used: **PASS / FAIL / UNVERIFIED / NOT APPLICABLE**.

**Preservation:** no source data or analysis output was modified. Re-running
`scripts/eu_funding_competition.py` reproduced `data/eu_funding_competition.json`,
`docs/agent-notes/eu-funding-competition.md` and the `uncertainties.md` append
**byte-identically** (verified by `diff` against backups).

**Overall verdict: the dataset and analysis are internally consistent and
correct.** Every control total, dtype, sentinel, and the full per-country
analysis output were reproduced independently. Two things to note: (1)
**provenance is UNVERIFIED** — no record exists of how `solar_power.csv` was
originally downloaded; (2) the report's **overall "headline" share is computed
over ALL countries, not the EU-27**, a scope inconsistency worth fixing before
publication (details in Stage 8.2).

**Update (2026-11-28):** after this check, `oth-single` and `oth-mult` were
reclassified out of the competitive/non-competitive split and into **unknown**
(excluded from the denominator), because the `procurement-procedure-type`
codelist gives them no definition (see `ted-fields-reference.md` §4). This
changes the competitive/non-competitive figures in §8.2 below and the per-country
`competition` values in the JSON; the EU-funding figures are unaffected. The
pytest suite was updated in lockstep and still passes (37 tests).

---

## Stage 1 — Provenance (skill §1)

| Question | Finding | Status |
|---|---|---|
| Who collected the data | A tender-data / public-body-adoption research subagent produced `data/solar_power.csv` (a TED contract-award-notice export filtered to solar CPV codes `0933…`), per `csv-overview.md` | PASS (documented) |
| How | CSV export of TED (Tenders Electronic Daily) contract-award notices; documented in `csv-overview.md` §File structure and `ted-fields-reference.md` | PASS (documented) |
| When | Profiling/cleaning run 2026-11-25 | PASS (documented) |
| Why | To support a story on solar adoption by public bodies (EU-funded & competitive shares) | PASS (documented) |
| Stated row count | **5,003 logical rows / 4,668 awards / 3,123 notices** (also `Doc ID` = 3,123) | PASS (matches recomputation, Stage 2) |
| Data dictionary | `ted-fields-reference.md` maps the humanised column names to official TED CSV subset / eForms fields (with uncertainty flags) | PASS |
| Caveats documented | Header uses humanised names (`Eu Funded` vs official `B_EU_FUNDS`, `Value Eur` vs `VALUE_EURO_FIN_1`); the mapping is flagged as an *interpretation* in `ted-fields-reference.md` §5 | PASS (caveat recorded) |
| **Primary-source record of the raw download** | **`sources.md` (77 entries) contains NO record of how `solar_power.csv` was originally downloaded** — no URL, no export parameters, no access timestamp for the raw CSV itself. The file is a derivative whose exact provenance (which TED export endpoint/snapshot, what filter, what date) is undocumented. | **UNVERIFIED** |

**Provenance: UNVERIFIED** — the pipeline (CSV → parquet) is fully documented,
but the *primary acquisition* of `solar_power.csv` is not. This is the known gap
flagged in the task: `sources.md` has no entry for the raw download, and the
humanised headers (`Eu Funded`, `Doc ID`, `Value Eur Real`) are not the official
TED CSV subset names (`B_EU_FUNDS`, `ID_NOTICE_CAN`, `VALUE_EURO_FIN_1`), so the
export tool/filter cannot be independently traced.

---

## Stage 2 — Control totals (skill §2)

Recomputed from `data/solar_power_clean.parquet` (pandas 3.1.1, pyarrow 26.0.1).

| Metric | Documented | Recomputed | Status |
|---|---:|---:|---|
| Rows | 5,003 | **5,003** | PASS |
| Distinct `Award ID` | 4,668 | **4,668** | PASS |
| Distinct `Contract ID` | 3,123 | **3,123** | PASS |
| Distinct `Doc ID` | 3,123 | **3,123** | PASS |
| `Contract ID` ↔ `Doc ID` 1:1 | yes | **yes** (each maps to exactly one of the other) | PASS |
| `Eu Funded` = true (row level) | 3,046 | **3,046** | PASS |
| `Eu Funded` = false (row level) | 1,957 | **1,957** | PASS |
| `Eu Funded` true % | 60.9% | **60.9%** (3,046/5,003 = 60.884%) | PASS |
| `Procedure Type Code` missing | 324 | **324** | PASS |
| Country: PL | 1,985 | **1,985** | PASS |
| Country: CZ | 769 | **769** | PASS |
| Country: ES | 450 | **450** | PASS |
| Country: NL / DE / SI | 283 / 242 / 146 | **283 / 242 / 146** | PASS |
| Country: GB / FR / PT / LV | 137 / 111 / 98 / 91 | **137 / 111 / 98 / 91** | PASS |
| Country: CH | 42 | **42** | PASS |
| Distinct `Buyer Country` | 38 | **38** | PASS |

**Control totals: PASS** (all 18 figures match exactly).

---

## Stage 3 — Column types (skill §3)

All 36 columns in the parquet match the dtype table in `cleaning.md` §7 exactly:

- `Award ID`, `Contract ID`, `year` → `int64` ✓
- `Estimated Value`, `Awarded Value`, `Value Eur`, `Value Eur Real` → `float64` ✓
- `Publication Date`, `Award Date` → `datetime64[us]` ✓
- `is_framework` → `boolean` ✓
- `tenders_received_clean`, `Award Contractors - Award → Award ID`, `Award Contractors - Award → Organization ID` → `Int64` (nullable) ✓
- all 23 string/categorical columns → `str` (`StringDtype`) ✓

No mixed types in any column. **Column types: PASS.**

---

## Stage 4 — Numeric columns (skill §4)

- Money columns were confirmed **not altered** by cleaning: for every non-empty
  raw CSV value, `float(raw_without_commas) == parquet_value` (0 values altered
  across all four money columns, incl. the all-empty `Value Eur Real`).
  **PASS.**
- Sentinels/outliers present and **preserved as-is** (not dropped/edited):

| Sentinel / outlier | Documented | Recomputed | Status |
|---|---:|---:|---|
| `Awarded Value == -1` | 18 | **18** | PASS |
| `Awarded Value == 7,000,000,000` | 1 | **1** | PASS |
| `Estimated Value == -1` | 0 | **0** | PASS |
| `Tenders Received == 0` (and `tenders_received_clean == 0`) | 59 | **59** | PASS |
| `Awarded Value == 0` | 20 | **20** | PASS |
| `Value Eur == -1` | 18 | **18** | PASS |

- Distributions (min/max) match `csv-overview.md` §6: `Estimated Value` 0 …
  7,000,000,000 (n=847); `Awarded Value` −1 … 7,000,000,000 (n=4,011);
  `Value Eur` −1 … 125,000,000 (n=1,536); `Value Eur Real` 100% empty.
- `tenders_received_clean`: min 0, max 98, 59 zeros, n=4,014. ✓

**Numeric columns: PASS.**

---

## Stage 5 — String columns (skill §5)

- Categorical values clean and fully covered:
  `Procedure Type Code` = {`open` (4,134), `restricted` (268), `neg-wo-call`
  (118), `neg-w-call` (112), `oth-single` (33), `oth-mult` (6), `comp-dial`
  (6), `comp-tend` (2)} + 324 NaN. All 8 codes fall into the
  competitive/non-competitive mapping (no unhandled codes).
- `Eu Funded` = only `'true'`/`'false'` (no NaN, no case variants).
- `Framework Agreement` = only `'true'`/`'false'`.
- `Buyer Country` / `Source Country` = 38 two-letter codes each, identical
  distributions (no trailing whitespace, no case variants).
- The literal `"NA"` in `Organizations → Town` (1 row) is preserved as data
  (not treated as missing) — matches `cleaning.md` §6. ✓

**String columns: PASS.**

---

## Stage 6 — Rows (skill §6)

- Full-row duplicates: **0** ✓
- Mostly-empty rows: none (every row carries `Award ID`/`Contract ID`/`Doc ID`
  and `Buyer Country`). ✓
- Row count 5,003 == stated count. ✓
- The raw `data/solar_power.csv` reads to **5,003 logical rows** via the `csv`
  module (5,052 physical lines = 1 header + 5,003 rows + **48 embedded
  newlines** inside quoted fields). ✓ — the 48-newline note applies only to the
  raw CSV, not the parquet.

**Rows: PASS.**

---

## Stage 7 — Columns (skill §7)

- `Value Eur Real` is 100% empty (5,003/5,003) — the one known fully-empty
  column. ✓
- No *unexpected* mostly-empty columns: the only columns >50% empty are the
  documented set {`Value Eur Real`, `Estimated Value`, `Estimated Value
  Currency`, `Value Eur`, `Award Date`, `Award Title`, `Organizations →
  Address`, `Organizations → Nuts Code`, `Contract Title`}. ✓
- 38 distinct `Buyer Country`, including non-EU codes present in the data:
  **`GB` (137), `CH` (42), `NO` (6), `MK` (3), `BO`/`RS`/`CD` (2 each),
  `CA`/`KE`/`MX`/`TR` (1 each)** — 11 non-EU codes total, plus `GR` (Greece,
  an EU member recorded under its pre-EU27 code, mapped to `EL`). ✓

**Columns: PASS.**

---

## Stage 8 — Fact-check the analysis output (skill §8)

### 8.1 Independent recomputation (the important part)

A separate, minimal script (`scripts/tests/independent_recompute.py`) was
written that **does not import or reuse any function from
`eu_funding_competition.py`**. It independently re-declares the EU-27 list, the
`GR→EL` alias, the competitive/non-competitive code sets, and its own
deduplication (on `Contract ID` for notice, `Award ID` for award).

**Result: EXACT MATCH.** Every per-country value in
`data/eu_funding_competition.json` was compared field-for-field:

- **594 fields checked** (27 countries × 2 levels × (5 eu-funding fields + 6
  competition fields)).
- **0 mismatches.**
- Max `eu_pct` difference = **0.0 pp**; max `competitive_pct` difference =
  **0.0 pp** (tolerance target was 0.01 pp).

The independent recomputation therefore confirms the committed JSON is correct
for every country, both levels, both measures.

### 8.2 Cross-check of headline figures & transcription drift

Re-ran `uv run python scripts/eu_funding_competition.py` and diffed the outputs
against pre-run backups: `eu_funding_competition.json`,
`eu-funding-competition.md`, and the `uncertainties.md` append are all
**byte-identical** — no transcription drift.

Headline figures (from the committed run) match the script's own output:

| Figure | Committed / script | Verified |
|---|---|---|
| Overall EU-funded, notice | 58.9% | 58.9% ✓ (58.918%) |
| Overall EU-funded, award | 59.8% | 59.8% ✓ (59.790%) |
| Overall competitive, notice | 96.5% | 96.5% ✓ |
| Overall competitive, award | 96.6% | 96.6% ✓ |
| Portugal EU-funded, notice | 58.6% | 58.6% ✓ |
| Portugal EU-funded, award | 87.4% | 87.4% ✓ |
| Portugal competitive (both) | 100.0% | 100.0% ✓ |

**⚠ Scope caveat (not a computation error, but a reporting inconsistency).**
The script's `overall_pct()` computes the "overall" headline over **ALL
countries** (including the 108 non-EU notices / 188 non-EU awards), whereas the
per-country tables are **EU-27 only**. Concretely:

- ALL-country EU-funded share: **58.92%** (notice, 1,840/3,123) / **59.79%**
  (award, 2,791/4,668) → these are the published headline numbers.
- EU-27-only EU-funded share: **60.70%** (notice, 1,830/3,015) / **61.90%**
  (award, 2,773/4,480).

The non-EU records are predominantly non-EU-funded (98 of 108 notices, 170 of
188 awards are `false`), which drags the all-country headline ~1.8–2.1 pp below
the EU-27 figure. The report is titled "per EU country (EU-27)" but its headline
is not EU-27-scoped. **Recommendation:** either label the headline as
"all countries in the dataset" or compute it over the EU-27 to match the
tables. This is recorded here as a caveat, not a failed check (the numbers are
each internally correct for their stated population).

**Resolution (same day):** the headline is now computed over the EU-27 to match
the tables — `overall_pct()` in `scripts/eu_funding_competition.py` filters to
EU-27 before computing the headline. Corrected EU-27 headline: EU-funded
**60.7%** notice / **61.9%** award; competitive **96.5%** notice / **96.5%**
award. The per-country JSON values were already EU-27-scoped and are unchanged
(byte-identical).

### 8.3 Sanity of the "notice-level primary" decision

The decision rests on two premises, both verified:

- **Flags constant within each unit:** 0 notices and 0 awards have mixed
  `Eu Funded`; 0 have mixed `Procedure Type Code`. ✓
- **No unit spans multiple buyer countries:** 0 notices and 0 awards map to
  more than one `Buyer Country`, so the de-duplication is unambiguous. ✓

(The report's line "296 awards (192 notices) across the EU-27 … 302 distinct
awards and 194 distinct notices" is internally consistent: the global NaN
procedure-type rows — 324 rows → 302 awards → 194 notices — minus the 6
awards / 2 notices in non-EU countries give the EU-27 296 / 192. No error; the
sentence just mixes EU-27 and global counts and could be worded more clearly.)

### 8.4 Automated tests (skill §8.2)

Added a pytest suite under `scripts/tests/`:

- `scripts/tests/test_fact_check.py` — 37 tests
- `scripts/tests/independent_recompute.py` — standalone recomputation (helper)
- `scripts/tests/conftest.py` — shared fixtures (dataset path overridable via
  `SOLAR_PARQUET` for the mutation run)

Coverage: data-integrity (row/award/notice counts, 1:1 `Contract ID`↔`Doc ID`,
flag/country uniqueness, dtypes, sentinels, `Eu Funded`/`Procedure Type Code`
missing counts, no duplicates, no unexpected mostly-empty columns, money-not-
altered), unit tests for `bucket_of`/`canonical_country` (`GR→EL`), JSON
consistency (`eu_pct+non_eu_pct == 100`, `competitive+noncompetitive == 100`,
`primary_measure == "notice"`), and the independent recomputation vs JSON.

```
$ uv run pytest scripts/tests/ -q
.....................................                                    [100%]
37 passed in 0.28s
```

**Mutation test (skill §8.2).** A temporary copy of the parquet was created
(never the real file), one `Eu Funded` value was flipped (`true`→`false` on
Award ID `8363261`, Contract ID `2592193` — a multi-award notice in Slovenia),
and the suite was re-run against it via `SOLAR_PARQUET=…/mutated.parquet`:

```
FAILED scripts/tests/test_fact_check.py::test_eu_funded_counts
FAILED scripts/tests/test_fact_check.py::test_flags_constant_within_unit
FAILED scripts/tests/test_fact_check.py::test_json_matches_independent_recomputation
3 failed, 34 passed
```

The planted error is caught by **three** independent tests (the `Eu Funded`
control total, the within-notice flag-uniqueness check, and the independent
recomputation vs JSON). The temporary copy was then discarded. The
detection logic is also encoded as `test_mutation_flip_eu_funded_is_detected`
(a self-checking regression test in the suite). **Mutation test: PASS** —
the suite fails loudly on tampered data.

### 8.5 Manual verification procedure — **PENDING human verification**

The agent's own checks do **not** constitute independent human verification.
Please perform the following by hand and report discrepancies. Mark this
**pending** until done.

**(a) Raw-row spot check — 12 award IDs.** Open `data/solar_power.csv` (the raw
CSV; award/contract IDs appear as text *with* thousands separators, e.g.
`9,350,663`). For each award below, find its row(s) and confirm the
`Eu Funded`, `Procedure Type Code` and `Buyer Country` columns match exactly:

| Award ID (CSV text) | Contract ID (CSV text) | Doc ID        | Buyer Country | Eu Funded | Procedure Type Code |
| ------------------- | ---------------------- | ------------- | ------------- | --------- | ------------------- |
| 9,350,663           | 2,863,028              | 00602221-2025 | CZ            | true      | open                |
| 1,562,383           | 709,618                | 076019-2016   | NL            | false     | restricted          |
| 9,529,199           | 2,914,843              | 00713486-2025 | DE            | false     | neg-wo-call         |
| 2,338,286           | 1,063,994              | 351336-2018   | SE            | false     | neg-w-call          |
| 8,241,442           | 2,553,531              | 00729722-2024 | CZ            | false     | oth-single          |
| 8,391,819           | 2,601,963              | 00024003-2025 | CZ            | false     | comp-dial           |
| 7,233,794           | 2,265,658              | 00056636-2024 | RO            | false     | comp-tend           |
| 9,825,640           | 3,008,054              | 00027139-2026 | PL            | false     | oth-mult            |
| 8,363,261           | 2,592,193              | 00006377-2025 | SI            | true      | *(empty)*           |
| 8,314,313           | 2,576,606              | 00775573-2024 | PT            | true      | open                |
| 1,113,832           | 509,323                | 356984-2014   | GB            | false     | restricted          |
| 7,415,639           | 2,312,005              | 00172009-2024 | GR            | true      | open                |

Note award `8,363,261` should have an **empty** `Procedure Type Code`, and
`7,415,639` shows Greece recorded as **GR** (mapped to `EL` in the output).

**(b) Country×level share re-calculation.** Filter the raw CSV to a single
`Buyer Country`, de-duplicate on `Contract ID` (notice) and `Award ID` (award),
then count `Eu Funded == true` / total, and confirm against the JSON:

1. **Portugal, EU-funded, notice** — expect **17 / 29 = 58.6%**; **award** —
   expect **83 / 95 = 87.4%**.
2. **Czechia, EU-funded, notice** — expect **444 / 562 = 79.0%**.
3. **Germany, competitive, award** — expect competitive **205 / 240 known =
   85.4%** (2 unknown).
4. **Slovenia, competitive, award** — expect competitive **64 / 89 known =
   71.9%** (54 unknown).

**How to record discrepancies:** list the award ID or country×level value, the
expected value (from this report / the JSON), the value you read from the raw
CSV, and the row number in the CSV. Report back; until then this check is
**pending**.

---

## Summary verdict

| Stage | Result |
|---|---|
| 1. Provenance | **UNVERIFIED** (no primary record of the raw CSV download) |
| 2. Control totals | **PASS** (all 18 figures exact) |
| 3. Column types | **PASS** |
| 4. Numeric columns | **PASS** (money unaltered; sentinels preserved) |
| 5. String columns | **PASS** |
| 6. Rows | **PASS** (0 duplicates; 5,003 rows; 48 embedded newlines = CSV-only) |
| 7. Columns | **PASS** (38 countries; 11 non-EU flagged) |
| 8.1 Independent recompute | **PASS** (594 fields, 0 mismatches, 0.0 pp) |
| 8.2 Headline cross-check | **PASS** with one **scope caveat** (overall headline is all-country, not EU-27) |
| 8.3 Decision sanity | **PASS** (0 mixed flags; 0 multi-country units) |
| 8.4 Automated tests | **PASS** (37 passed; mutation detected by 3 tests) |
| 8.5 Manual verification | **PENDING human verification** |

**Files created by this fact-check:**
- `docs/agent-notes/fact-check.md` (this report)
- `scripts/tests/test_fact_check.py`
- `scripts/tests/independent_recompute.py`
- `scripts/tests/conftest.py`

(`pytest` was added as a dev dependency via `uv add --dev pytest`; the
`pyproject.toml`/`uv.lock` change has been committed.)
