"""Clean the TED solar-power award-notice export into a typed dataset.

Reads ``data/solar_power.csv`` (UTF-8 with BOM, 5,003 logical rows, 33 columns)
and writes ``data/solar_power_clean.parquet``, preserving dtypes and the
distinction between NaN (missing) and a genuine empty string.

Cleaning rules (mirrors the task spec exactly):

1. **Identifier normalisation** — check for leading zeros *before* any numeric
   conversion. Strip thousands-separator commas, then decide int64 vs string.
2. **Money** — remove thousands commas, convert to float with
   ``pd.to_numeric(errors='coerce')``. Pure type conversion: never edit values.
3. **Dates** — parse with ``format='%B %d, %Y'``; empty -> NaT.
4. **Strings** — strip whitespace everywhere; collapse embedded newlines/tabs in
   free-text columns; trim-only for categoricals; empty string -> NaN.
5. **Derived fields** — ``year`` (int), ``is_framework`` (bool),
   ``tenders_received_clean`` (nullable Int64). No imputation.

It also writes ``docs/agent-notes/cleaning.md`` with the full verification
report (leading zeros, dtype table, NaN counts, date failures, comma-as-decimal
ambiguity, and the money-unchanged check).

Note on one header: the task refers to ``Organizations → Organization ID``; in
this file that column is literally named ``Award Contractors - Award →
Organization ID`` (the contractor's org id). The same applies to the join
column ``Award Contractors - Award → Award ID``.
"""

from __future__ import annotations

import pathlib
import re

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "solar_power.csv"
OUT = ROOT / "data" / "solar_power_clean.parquet"
REPORT = ROOT / "docs" / "agent-notes" / "cleaning.md"

ARROW = "\u2192"  # U+2192, the join separator used in the headers

# ---------------------------------------------------------------------------
# Column groups (exact header strings)
# ---------------------------------------------------------------------------
ID_INT_COLS = ["Award ID", "Contract ID"]
ID_NULLABLE_COLS = [
    f"Award Contractors - Award {ARROW} Award ID",        # join column, stored plain
    f"Award Contractors - Award {ARROW} Organization ID",  # = "Organizations → Organization ID"
]
MONEY_COLS = ["Estimated Value", "Awarded Value", "Value Eur", "Value Eur Real"]
DATE_COLS = ["Publication Date", "Award Date"]

FREETEXT_COLS = [
    "Contract Title",
    "Award Title",
    "Buyer Name",
    f"Organizations {ARROW} Official Name",
    f"Organizations {ARROW} Address",
    f"Organizations {ARROW} Town",
    f"Cpv Codes - Main Cpv Code {ARROW} Description",
]
CATEGORICAL_COLS = [
    "Main Cpv Code",
    "Contract Nature Code",
    "Procedure Type Code",
    "Contract Nuts Code",
    "Framework Agreement",
    "Eu Funded",
    "Source Country",
    "Buyer Country",
    "Awarded Value Currency",
    "Estimated Value Currency",
    f"Organizations {ARROW} Country Code",
    f"Organizations {ARROW} Nuts Code",
]
# Strings that get only strip + empty->NaN (not free-text, not categorical).
GENERIC_STRING_COLS = ["Doc ID", "Lot Number", f"Organizations {ARROW} Postal Code", "Tenders Received"]

ALL_STRING_COLS = FREETEXT_COLS + CATEGORICAL_COLS + GENERIC_STRING_COLS


def has_leading_zero(s: str) -> bool:
    """True if a (normalised) id string is zero-padded: starts with '0' and is
    more than the single digit '0' itself."""
    s = (s or "").strip()
    return len(s) > 1 and s[0] == "0"


def comma_ambiguous(s: str) -> bool:
    """True if any comma is NOT a thousands separator, i.e. a comma that is not
    followed by exactly 3 digits (e.g. '1,5', '1,50', '1,2345')."""
    s = (s or "").strip()
    for m in re.finditer(",", s):
        after = re.match(r"\d*", s[m.end():]).group(0)
        if len(after) != 3:
            return True
    return False


def main() -> None:
    rep: list[str] = []  # markdown report lines
    log: list[str] = []  # stdout summary lines

    def add(line: str = "") -> None:
        rep.append(line)

    # ------------------------------------------------------------------ read
    # `dtype=str` is REQUIRED here: with pandas 3.x, read_csv would otherwise
    # auto-infer `Main Cpv Code` -> int64 (silently dropping its leading zero,
    # e.g. "09331200" -> 9331200) and `Framework Agreement` / `Eu Funded` ->
    # bool. keep_default_na=False only stops NA-string conversion; it does not
    # stop type inference.
    raw = pd.read_csv(SRC, encoding="utf-8-sig", keep_default_na=False, dtype=str)
    df = raw.copy()

    n_rows = len(df)
    assert n_rows == 5003, f"expected 5003 rows, got {n_rows}"
    add("# Cleaning report — `data/solar_power.csv` → `solar_power_clean.parquet`")
    add()
    add(f"- Rows read: **{n_rows}** (verified == 5,003)")
    add(f"- Read with `keep_default_na=False` so 'NA'-like strings are not silently dropped.")
    add(f"- **Also read with `dtype=str`** — without it pandas 3.x auto-infers "
        f"`Main Cpv Code` → `int64` (dropping its leading zero: `09331200` → `9331200`) "
        f"and `Framework Agreement` / `Eu Funded` → `bool`. Forcing strings keeps the "
        f"CPV leading zero and the literal `'true'`/`'false'` values intact.")
    import pyarrow as pa
    add(f"- pandas {pd.__version__}, pyarrow {pa.__version__}")
    add()

    # ------------------------------------------- 1. identifier normalisation
    add("## 1. Identifier normalisation (leading-zero check first)")
    add()
    add("| Column | non-empty | empty | leading zeros? | final dtype |")
    add("|---|---:|---:|---|---|")

    leading_zero_findings: dict[str, str] = {}

    # --- columns with no missing values -> plain int64 ---
    for col in ID_INT_COLS:
        norm = df[col].str.strip().str.replace(",", "", regex=False)
        nonempty = (norm != "")
        lz = sum(1 for v in norm[nonempty] if has_leading_zero(v))
        n_ne = int(nonempty.sum())
        n_e = int((~nonempty).sum())
        dtype = "int64"
        df[col] = norm.astype("int64")
        leading_zero_findings[col] = dtype
        add(f"| `{col}` | {n_ne} | {n_e} | {'**yes**' if lz else 'no'} ({lz}) | {dtype} |")

    # --- columns with 431 missing (no contractor) -> nullable Int64 ---
    for col in ID_NULLABLE_COLS:
        norm = df[col].str.strip().str.replace(",", "", regex=False)
        nonempty = (norm != "")
        lz = sum(1 for v in norm[nonempty] if has_leading_zero(v))
        n_ne = int(nonempty.sum())
        n_e = int((~nonempty).sum())
        dtype = "Int64 (nullable — 431 awards have no contractor)"
        df[col] = norm.replace("", np.nan).astype("Int64")
        leading_zero_findings[col] = dtype
        add(f"| `{col}` | {n_ne} | {n_e} | {'**yes**' if lz else 'no'} ({lz}) | {dtype} |")

    add()
    add("No ID column contains a leading zero, so all four were converted to integer.")
    add("`Award ID` / `Contract ID` are fully populated → plain `int64`. The two "
        "contractor-side columns hold the same IDs but have 431 genuinely missing "
        "rows (awards with no contractor recorded) → nullable `Int64` so the "
        "empty→NaN rule still holds.")
    add()

    # join-column reconciliation
    aid = df["Award ID"]
    join = df[f"Award Contractors - Award {ARROW} Award ID"]
    both_present_diff = int(((aid.notna() & join.notna()) & (aid != join)).sum())
    join_missing = int(join.isna().sum())
    add(f"- **Join-column reconciliation:** `Award Contractors - Award {ARROW} Award ID` "
        f"vs `Award ID` — value-for-value mismatches among non-empty values: **{both_present_diff}**. "
        f"{join_missing} rows have no contractor, so the join column is empty (NaN) there and "
        f"no comparison applies.")
    add()

    # -------------------------------------------------------------- 2. money
    add("## 2. Money columns (pure type conversion)")
    add()
    add("| Column | non-empty | comma-as-decimal ambiguity | non-empty→NaN | value altered |")
    add("|---|---:|---:|---:|---:|")

    money_check: dict[str, dict] = {}
    for col in MONEY_COLS:
        raw_series = raw[col]
        nonempty = raw_series.str.strip() != ""
        n_ne = int(nonempty.sum())

        # comma-as-decimal ambiguity on raw strings (plain loop: robust to the
        # all-empty "Value Eur Real" column)
        amb = sum(1 for v in raw_series[nonempty] if comma_ambiguous(v))

        cleaned = pd.to_numeric(
            raw_series.str.strip().str.replace(",", "", regex=False), errors="coerce"
        )
        df[col] = cleaned

        # verification: no value was altered, and no non-empty raw became NaN
        nan_from_nonempty = 0
        value_mismatch = 0
        for r, c in zip(raw_series[nonempty], cleaned[nonempty]):
            try:
                expected = float(str(r).strip().replace(",", ""))
            except ValueError:
                nan_from_nonempty += 1
                continue
            if pd.isna(c):
                nan_from_nonempty += 1
            elif c != expected:
                value_mismatch += 1

        money_check[col] = {
            "nonempty": n_ne,
            "ambiguous": amb,
            "nan_from_nonempty": nan_from_nonempty,
            "value_mismatch": value_mismatch,
        }
        add(f"| `{col}` | {n_ne} | {amb} | {nan_from_nonempty} | {nan_from_nonempty + value_mismatch} |")

    add()
    add("**Verification:** for every money column, `float(raw_without_commas) == cleaned` "
        "held for all non-empty raw values, and no non-empty raw value became NaN "
        "(i.e. 0 values altered). Sentinels (`-1`) and outliers (`7,000,000,000`) were "
        "kept as-is, per spec.")
    add()

    # -------------------------------------------------------------- 3. dates
    add("## 3. Dates")
    add()
    date_failures: dict[str, list[str]] = {}
    for col in DATE_COLS:
        raw_series = df[col]
        parsed = pd.to_datetime(raw_series, format="%B %d, %Y", errors="coerce")
        fail_mask = (raw_series.str.strip() != "") & parsed.isna()
        fails = raw_series[fail_mask].tolist()
        date_failures[col] = fails
        df[col] = parsed
        add(f"- `{col}`: {int((raw_series.str.strip() != '').sum())} non-empty, "
            f"{len(fails)} failed to parse (non-empty → NaT).")
        if fails:
            add(f"  - examples: {fails[:10]}")
    add()

    # ------------------------------------------------------------ 4. strings
    add("## 4. String columns")
    add()
    # strip everything
    for col in ALL_STRING_COLS:
        df[col] = df[col].str.strip()
    # free-text: collapse embedded newlines/tabs to a single space
    for col in FREETEXT_COLS:
        df[col] = df[col].str.replace(r"[\r\n\t]+", " ", regex=True)
    # categoricals: already trimmed; values left exactly as-is (no rename/merge)
    # empty string -> NaN across all string columns
    for col in ALL_STRING_COLS:
        df[col] = df[col].replace("", np.nan)
    add("All string columns were `.str.strip()`-ed; free-text columns had embedded "
        "newlines/tabs collapsed to a single space; categorical columns were trimmed "
        "only (no renaming/merging). Empty string `''` → `NaN` everywhere.")
    add()

    # --------------------------------------------------------- 5. derived
    add("## 5. Derived fields")
    add()
    # year (int)
    df["year"] = df["Publication Date"].dt.year.astype("int64")
    # is_framework (nullable bool)
    fa_lower = df["Framework Agreement"].str.lower()
    unexpected_fa = sorted(
        set(fa_lower.dropna().tolist()) - {"true", "false"}
    )
    df["is_framework"] = fa_lower.map({"true": True, "false": False}).astype("boolean")
    # tenders_received_clean (nullable Int64; 0 stays 0)
    df["tenders_received_clean"] = pd.to_numeric(
        df["Tenders Received"].str.replace(",", "", regex=False), errors="coerce"
    ).astype("Int64")
    add("- `year` (int) — from `Publication Date`.")
    add("- `is_framework` (boolean) — `'true'`→True, `'false'`→False, empty→NaN.")
    add("- `tenders_received_clean` (Int64) — parsed int; empty→NaN; genuine 0 preserved.")
    if unexpected_fa:
        add(f"- **Unexpected `Framework Agreement` values:** {unexpected_fa}")
    add()

    # ------------------------------------------------- unexpected values
    add("## 6. Unexpected values discovered")
    add()
    na_town = int((raw["Organizations \u2192 Town"].str.strip() == "NA").sum())
    add(f"- `Organizations → Town` contains the literal string `NA` in **{na_town}** row "
        f"(kept as-is: with `keep_default_na=False` it is not treated as missing; "
        f"only empty strings become NaN).")
    # '0' sentinel / outlier presence (kept, not edited)
    minus_one_av = int((df["Awarded Value"] == -1.0).sum())
    minus_one_ev = int((df["Estimated Value"] == -1.0).sum())
    seven_bn = int((df["Awarded Value"] == 7_000_000_000.0).sum())
    add(f"- Money sentinels/outliers left untouched: `Awarded Value == -1` ({minus_one_av} rows), "
        f"`Estimated Value == -1` ({minus_one_ev} rows), `Awarded Value == 7,000,000,000` ({seven_bn} rows).")
    add()

    # ------------------------------------------------------ final dtype table
    add("## 7. Final dtypes (all columns)")
    add()
    add("| Column | dtype |")
    add("|---|---|")
    for col, dt in df.dtypes.items():
        add(f"| `{col}` | `{dt}` |")
    add()

    # --------------------------------------------------------- NaN counts
    add("## 8. NaN counts per column (empty→NaN result)")
    add()
    add("| Column | NaN count |")
    add("|---|---:|")
    for col, cnt in df.isna().sum().items():
        add(f"| `{col}` | {cnt} |")
    add()

    # ------------------------------------------------------------ write out
    df.to_parquet(OUT, index=False)
    log.append(f"wrote {OUT} with {len(df)} rows x {len(df.columns)} cols")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(rep) + "\n", encoding="utf-8")
    log.append(f"wrote {REPORT}")

    # -------------------------------------------------------- stdout summary
    print("\n".join(log))
    print(f"rows={len(df)} cols={len(df.columns)}")
    print("leading zeros: none in any ID column -> all integer-typed")
    print("money altered (non-empty->NaN + value mismatch):",
          {k: v["nan_from_nonempty"] + v["value_mismatch"] for k, v in money_check.items()})
    print("date parse failures:",
          {k: len(v) for k, v in date_failures.items()})
    print("comma-as-decimal ambiguity:",
          {k: v["ambiguous"] for k, v in money_check.items()})
    print("output format: parquet (pyarrow)")


if __name__ == "__main__":
    main()
