# CSV overview — `data/solar_power.csv`

Analysis run 2026-11-25 with Python's standard `csv` module (pandas not installed). Source: EU TED (Tenders Electronic Daily) contract-award notices filtered to solar CPV codes.

> **Row-count note:** the file has 5,052 physical lines (1 header + 5,051 data *lines*), but only **5,003 logical data rows**. The difference is **48 embedded newlines inside quoted fields** (see Data issues #2). All numbers below refer to the 5,003 logical rows.

---

## File structure

- **Encoding:** UTF-8 with a byte-order mark (`EF BB BF`). Read with `utf-8-sig` to strip it.
- **Columns:** 33.
- **Delimiter:** comma, RFC-4180 quoting (`"…"`), embedded newlines and quotes inside quoted fields.
- **Layout:** the file is a **denormalised join** — one row per *award × contractor* pair, not one row per award. An award with *N* contractors appears on *N* rows. This is why unique-Award-ID < row count.
- **Header uses `→` (U+2192)** as the join separator, e.g. `Organizations → Official Name`.

### Columns (inferred meaning)

| # | Column | Meaning (inferred) |
|---|--------|--------------------|
| 0 | Award ID | Unique award identifier (text with thousands separators) |
| 1 | Contract ID | Parent contract identifier (text with thousands separators) |
| 2 | Doc ID | TED notice number, `NNNNNNNN-YYYY` |
| 3 | Publication Date | Notice publication date (text, `Month D, YYYY`) |
| 4 | Source Country | Country of the notice source (2-letter code) |
| 5 | Buyer Name | Contracting authority / buyer name |
| 6 | Buyer Country | Buyer's country (2-letter code) |
| 7 | Contract Title | Contract description |
| 8 | Main Cpv Code | Primary CPV code (5 distinct values) |
| 9 | Contract Nature Code | supplies / works / services |
| 10 | Procedure Type Code | open / restricted / neg-… |
| 11 | Contract Nuts Code | NUTS region |
| 12 | Framework Agreement | true / false |
| 13 | Eu Funded | true / false |
| 14 | Estimated Value | Estimated contract value (text, thousands separators) |
| 15 | Estimated Value Currency | Currency of estimated value |
| 16 | Award Title | Award description |
| 17 | Awarded Value | Awarded value (text, thousands separators) |
| 18 | Awarded Value Currency | Currency of awarded value |
| 19 | Tenders Received | Number of bids received |
| 20 | Award Date | Award date (text, `Month D, YYYY`) |
| 21 | Lot Number | Lot identifier (`LOT-0001`, `1`, …) |
| 22 | Value Eur | Awarded value converted to EUR |
| 23 | Value Eur Real | Second EUR field — **empty for all rows** |
| 24 | Award Contractors - Award → Award ID | Award ID again, **plain numeric** (no separators) |
| 25 | Award Contractors - Award → Organization ID | Contractor organisation ID |
| 26 | Organizations → Official Name | Contractor name |
| 27–31 | Organizations → Address/Town/Postal/Country/Nuts | Contractor address fields |
| 32 | Cpv Codes - Main Cpv Code → Description | CPV description text |

### Cardinality / key counts

| Field | Rows | Unique |
|-------|-----:|-------:|
| Award ID | 5,003 | **4,668** |
| Contract ID | 5,003 | **3,123** |
| Doc ID | 5,003 | **3,123** |
| Buyer Name | 5,003 | 1,962 |
| Organizations → Official Name | 4,572 | **2,223** |
| Organizations → Organization ID | 4,572 | 2,828 |

- **Contract ID ↔ Doc ID is a perfect 1:1 mapping** (3,123 distinct each; no contract maps to two docs and vice-versa). They are two keys for the same underlying contract.
- 4,668 distinct awards from 3,123 contracts ⇒ ~1.5 awards (lots) per contract on average.
- The 5,003 rows = 4,668 awards exploded into award×contractor pairs (431 rows have no contractor recorded).

### Methodological note — summing values in an exploded dataset

This file is intentionally kept **exploded** (denormalised): one row per *award × contractor*, and one row per *award × lot*. We do **not** de-duplicate it. The consequence for any aggregation:

- **Award values are stored once per award but repeated on every contractor row.** Example: the Spanish award `436940-2023` has 6 contractor rows, each carrying the same `3,623,518.24` EUR. Summing `Awarded Value` / `Value Eur` directly over rows therefore **over-counts by the number of contractors** on that award.
- **To total correctly**, aggregate at the *award* level first (group by `Award ID` and take the value once per award), then sum those unique award values. If a row-level sum is unavoidable, weight each row's value by `1 / (number of rows for that Award ID)`.
- **Lots**: a notice can contain several lots, and the value may be stated per lot or once at notice (total) level. Sum lot-level values once per award; do not add a notice-level total on top of its lots.
- **No currency conversion is applied** in this project: values keep their original `Awarded Value Currency` and must **not** be summed across different currencies.

---

## Data issues

### 1. UTF-8 BOM
A BOM precedes the first header cell `Award ID`. Harmless if read with `utf-8-sig`, but it will corrupt the first column name if read as plain `utf-8`.

### 2. Embedded newlines inside quoted fields → row-count mismatch
48 embedded `\n` characters occur inside quoted fields (44 fields across 5 columns):

| Column | Fields with newline |
|--------|----:|
| Contract Title | 20 |
| Award Title | 19 |
| Buyer Name | 2 |
| Organizations → Official Name | 2 |
| Organizations → Address | 1 |

Because of these, a naive `wc -l` / `splitlines()` reports 5,051 data lines, while `csv.reader` correctly yields **5,003** rows. Use the `csv` module, not line counting.

### 3. Numeric fields stored as text with thousands separators (and inconsistent formatting)
`Award ID`, `Contract ID`, and the value columns are quoted strings with comma thousands separators and `.` decimals:

- `"Award ID": "8,363,261"`, `"Contract ID": "2,592,193"`
- `"Awarded Value": "142,478.56"`, `"Estimated Value": "165,000,000"`

The join column `Award Contractors - Award → Award ID` stores the **same ID as plain digits** (`8363261`), so the two representations must be reconciled. `Doc ID` (`00006377-2025`) and `Lot Number` are genuinely text.

### 4. Duplicate / denormalised Award IDs
- **Full-row duplicates: 0.**
- **201 Award IDs appear on more than one row** (335 excess rows); 200 of them correspond to multiple distinct contractor names (i.e. legitimate multi-contractor awards). Example: Award ID `6651561` has 6 rows (6 contractors). See the methodological note under *File structure* for the summing implication.

### 5. Missing values (per column)

| Column | Empty | % |
|--------|------:|--:|
| Value Eur Real | 5,003 | **100.00%** |
| Estimated Value | 4,156 | 83.07% |
| Estimated Value Currency | 4,156 | 83.07% |
| Value Eur | 3,467 | 69.30% |
| Award Date | 1,770 | 35.38% |
| Award Title | 1,543 | 30.84% |
| Organizations → Address | 1,248 | 24.95% |
| Contract Title | 1,102 | 22.03% |
| Organizations → Nuts Code | 1,103 | 22.05% |
| Awarded Value | 992 | 19.83% |
| Tenders Received | 989 | 19.77% |
| Awarded Value Currency | 961 | 19.21% |
| Organizations → Postal Code | 931 | 18.61% |
| Lot Number | 549 | 10.97% |
| Organizations → Town | 473 | 9.45% |
| Organizations → Country Code | 475 | 9.49% |
| Contractor (award/organization/name) | 431 | 8.61% |
| Contract Nuts Code | 382 | 7.64% |
| Procedure Type Code | 324 | 6.48% |
| Contract Nature Code | 31 | 0.62% |

Key gaps: **`Value Eur` (EUR-converted value) is empty for 69% of rows**, and **`Value Eur Real` is empty for every row**, so EUR-normalised figures are only available for a minority of records.

### 6. Currency mix and anomalies
`Awarded Value Currency` spans **17 distinct currencies** (top): PLN 1,643 (32.8%), EUR 1,549 (31.0%), *(empty)* 961, CZK 605 (12.1%), RON 57, CHF 42, GBP 37, BGN 36, DKK 26, HUF 13, HRK 12, SEK 9, LVL 5, USD 3, BOB 2, NOK 1, CYP 1, MKD 1.

- Cross-country comparison requires currency conversion; `Value Eur` would do this but is 69% empty.
- Several currencies are **obsolete or non-EU**: LVL (Latvian lats, ended 2014), CYP (Cypriot pound, ended 2008), HRK (kuna, ended 2023), CHF, GBP, USD, BOB (Bolivia).

**Outlier / sentinel values:**

| Field | min | max | zeros | negatives |
|-------|----:|----:|------:|----------:|
| Estimated Value | 0 | **7,000,000,000** | 8 | 0 |
| Awarded Value | −1 | **7,000,000,000** | 20 | 18 |
| Value Eur | −1 | 125,000,000 | 12 | 18 |
| Tenders Received | 0 | 98 | 59 | 0 |

- Max awarded value = **7,000,000,000 CZK** (buyer "ČEZ PV & Wind a.s.", 4 awards) — an extreme outlier, almost certainly a framework ceiling, not an actual contract sum. Max estimated value is also 7bn CZK.
- **−1 is used as a sentinel** for "not disclosed / unknown" (18 rows, e.g. buyer "Deutsche Gesellschaft für Internationale Zusammenarbeit (GIZ)"). Treat negative values as missing before aggregating.
- 59 awards report **0 tenders received**; 20 report 0 awarded value.

### 7. Date format and range
- All dates use `Month D, YYYY` text (e.g. `January 7, 2025`) — **not ISO-8601**; parse before sorting/filtering.
- **Publication Date:** full coverage, range **2011–2026**. Distribution skews recent: 2023 (678), 2024 (756), 2025 (808), 2026 (366).
- **Award Date:** 35.4% empty; present range **2010–2026**.
- The year suffix of `Doc ID` matches the publication year exactly (same distribution).

### 8. Country scope (includes non-EU)
38 distinct `Buyer Country` / `Source Country` values; the two columns have identical distributions.

| Country | Rows | % |
|---------|-----:|--:|
| PL | 1,985 | 39.7% |
| CZ | 769 | 15.4% |
| ES | 450 | 9.0% |
| NL | 283 | 5.7% |
| DE | 242 | 4.8% |
| SI | 146 | 2.9% |
| GB | 137 | 2.7% |
| FR | 111 | 2.2% |
| PT | 98 | 2.0% |
| LV | 91 | 1.8% |
| … (28 more) | … | … |

Note **GB (137) and CH (42)** are non-EU; Poland alone is ~40% of the dataset.

### 9. Categorical distributions

**Main CPV code** (5 values): 09331200 *Solar photovoltaic modules* 47.6%, 09332000 *Solar installation* 16.3%, 09331000 *Solar panels* 14.9%, 09330000 *Solar energy* 11.8%, 09331100 *Solar collectors for heat production* 9.4%.

**Contract Nature Code:** supplies 94.2%, works 3.7%, services 1.5%, *(empty)* 0.6%.

**Procedure Type Code:** open 82.6%, *(empty)* 6.5%, restricted 5.4%, neg-wo-call 2.4%, neg-w-call 2.2%, oth-single 0.7%, oth-mult/comp-dial/comp-tend <0.2%.

**Framework Agreement:** false 98.2%, true 1.8%. **Eu Funded:** true 60.9%, false 39.1%.

### 10. Top buyers

By award count (top 10):

| Buyer | Awards | Total value |
|-------|-------:|------------:|
| Consorci Català pel Desenvolupament Local (CCDL) | 92 | €216m |
| Ukmergės rajono savivaldybės administracija | 70 | €11.6m |
| Deutsche Gesellschaft für Internationale Zusammenarbeit (GIZ) | 65 | €10.3m |
| OBČINA RAVNE NA KOROŠKEM | 61 | €8.5m |
| Administração Regional de Saúde do Norte, I.P. | 61 | *(0 — value missing)* |
| Àrea Metropolitana de Barcelona | 57 | €18.2m |
| Technologie hlavního města Prahy, a.s. | 43 | €78.4m |
| AS "Sadales tīkls" | 41 | €1.9m |
| CHEMINVEST s.r.o. | 40 | €97.5m |
| Statutární město Děčín | 35 | €20.6m |

By total awarded value (top 8):

| Buyer | Awards | Total value |
|-------|-------:|------------:|
| ČEZ PV & Wind a.s. | 4 | **7.49bn CZK** (~€300m) |
| YPO | 5 | €750m |
| BKM Budapesti Közművek | 4 | €491m |
| North Somerset Housing Limited | 1 | €450m |
| Fenster Technik Seifert | 1 | €436m |
| Jablonecká energetická a.s. | 3 | €330m |
| Gmina Sosnowiec | 5 | €317m |
| Berliner Wasserbetriebe | 16 | €246m |

(Note: values above are summed in their native currency and labelled with the buyer's dominant currency — treat cross-currency totals as indicative only given the currency mix in issue #6.)

### 11. Encoding / character health
No replacement characters (`\ufffd`) or non-UTF8 byte sequences. The only control characters are the 48 embedded newlines (#2). Text is otherwise clean UTF-8 (many diacritics in Polish/Czech/Slovenian titles render correctly once the BOM is stripped).
