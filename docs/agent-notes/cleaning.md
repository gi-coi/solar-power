# Cleaning report — `data/solar_power.csv` → `solar_power_clean.parquet`

- Rows read: **5003** (verified == 5,003)
- Read with `keep_default_na=False` so 'NA'-like strings are not silently dropped.
- **Also read with `dtype=str`** — without it pandas 3.x auto-infers `Main Cpv Code` → `int64` (dropping its leading zero: `09331200` → `9331200`) and `Framework Agreement` / `Eu Funded` → `bool`. Forcing strings keeps the CPV leading zero and the literal `'true'`/`'false'` values intact.
- pandas 3.1.1, pyarrow 26.0.1

## 1. Identifier normalisation (leading-zero check first)

| Column | non-empty | empty | leading zeros? | final dtype |
|---|---:|---:|---|---|
| `Award ID` | 5003 | 0 | no (0) | int64 |
| `Contract ID` | 5003 | 0 | no (0) | int64 |
| `Award Contractors - Award → Award ID` | 4572 | 431 | no (0) | Int64 (nullable — 431 awards have no contractor) |
| `Award Contractors - Award → Organization ID` | 4572 | 431 | no (0) | Int64 (nullable — 431 awards have no contractor) |

No ID column contains a leading zero, so all four were converted to integer.
`Award ID` / `Contract ID` are fully populated → plain `int64`. The two contractor-side columns hold the same IDs but have 431 genuinely missing rows (awards with no contractor recorded) → nullable `Int64` so the empty→NaN rule still holds.

- **Join-column reconciliation:** `Award Contractors - Award → Award ID` vs `Award ID` — value-for-value mismatches among non-empty values: **0**. 431 rows have no contractor, so the join column is empty (NaN) there and no comparison applies.

## 2. Money columns (pure type conversion)

| Column | non-empty | comma-as-decimal ambiguity | non-empty→NaN | value altered |
|---|---:|---:|---:|---:|
| `Estimated Value` | 847 | 0 | 0 | 0 |
| `Awarded Value` | 4011 | 0 | 0 | 0 |
| `Value Eur` | 1536 | 0 | 0 | 0 |
| `Value Eur Real` | 0 | 0 | 0 | 0 |

**Verification:** for every money column, `float(raw_without_commas) == cleaned` held for all non-empty raw values, and no non-empty raw value became NaN (i.e. 0 values altered). Sentinels (`-1`) and outliers (`7,000,000,000`) were kept as-is, per spec.

## 3. Dates

- `Publication Date`: 5003 non-empty, 0 failed to parse (non-empty → NaT).
- `Award Date`: 3233 non-empty, 0 failed to parse (non-empty → NaT).

## 4. String columns

All string columns were `.str.strip()`-ed; free-text columns had embedded newlines/tabs collapsed to a single space; categorical columns were trimmed only (no renaming/merging). Empty string `''` → `NaN` everywhere.

## 5. Derived fields

- `year` (int) — from `Publication Date`.
- `is_framework` (boolean) — `'true'`→True, `'false'`→False, empty→NaN.
- `tenders_received_clean` (Int64) — parsed int; empty→NaN; genuine 0 preserved.

## 6. Unexpected values discovered

- `Organizations → Town` contains the literal string `NA` in **1** row (kept as-is: with `keep_default_na=False` it is not treated as missing; only empty strings become NaN).
- Money sentinels/outliers left untouched: `Awarded Value == -1` (18 rows), `Estimated Value == -1` (0 rows), `Awarded Value == 7,000,000,000` (1 rows).

## 7. Final dtypes (all columns)

| Column | dtype |
|---|---|
| `Award ID` | `int64` |
| `Contract ID` | `int64` |
| `Doc ID` | `str` |
| `Publication Date` | `datetime64[us]` |
| `Source Country` | `str` |
| `Buyer Name` | `str` |
| `Buyer Country` | `str` |
| `Contract Title` | `str` |
| `Main Cpv Code` | `str` |
| `Contract Nature Code` | `str` |
| `Procedure Type Code` | `str` |
| `Contract Nuts Code` | `str` |
| `Framework Agreement` | `str` |
| `Eu Funded` | `str` |
| `Estimated Value` | `float64` |
| `Estimated Value Currency` | `str` |
| `Award Title` | `str` |
| `Awarded Value` | `float64` |
| `Awarded Value Currency` | `str` |
| `Tenders Received` | `str` |
| `Award Date` | `datetime64[us]` |
| `Lot Number` | `str` |
| `Value Eur` | `float64` |
| `Value Eur Real` | `float64` |
| `Award Contractors - Award → Award ID` | `Int64` |
| `Award Contractors - Award → Organization ID` | `Int64` |
| `Organizations → Official Name` | `str` |
| `Organizations → Address` | `str` |
| `Organizations → Town` | `str` |
| `Organizations → Postal Code` | `str` |
| `Organizations → Country Code` | `str` |
| `Organizations → Nuts Code` | `str` |
| `Cpv Codes - Main Cpv Code → Description` | `str` |
| `year` | `int64` |
| `is_framework` | `boolean` |
| `tenders_received_clean` | `Int64` |

## 8. NaN counts per column (empty→NaN result)

| Column | NaN count |
|---|---:|
| `Award ID` | 0 |
| `Contract ID` | 0 |
| `Doc ID` | 0 |
| `Publication Date` | 0 |
| `Source Country` | 0 |
| `Buyer Name` | 0 |
| `Buyer Country` | 0 |
| `Contract Title` | 1102 |
| `Main Cpv Code` | 0 |
| `Contract Nature Code` | 31 |
| `Procedure Type Code` | 324 |
| `Contract Nuts Code` | 382 |
| `Framework Agreement` | 0 |
| `Eu Funded` | 0 |
| `Estimated Value` | 4156 |
| `Estimated Value Currency` | 4156 |
| `Award Title` | 1543 |
| `Awarded Value` | 992 |
| `Awarded Value Currency` | 961 |
| `Tenders Received` | 989 |
| `Award Date` | 1770 |
| `Lot Number` | 549 |
| `Value Eur` | 3467 |
| `Value Eur Real` | 5003 |
| `Award Contractors - Award → Award ID` | 431 |
| `Award Contractors - Award → Organization ID` | 431 |
| `Organizations → Official Name` | 431 |
| `Organizations → Address` | 1248 |
| `Organizations → Town` | 473 |
| `Organizations → Postal Code` | 931 |
| `Organizations → Country Code` | 475 |
| `Organizations → Nuts Code` | 1103 |
| `Cpv Codes - Main Cpv Code → Description` | 0 |
| `year` | 0 |
| `is_framework` | 0 |
| `tenders_received_clean` | 989 |

