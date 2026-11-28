"""Fact-check test suite for the solar TED dataset and the EU-funding/competition
analysis.

Covers:

1. Data-integrity tests (control totals, dtypes, sentinels, duplicates,
   flag/country uniqueness, missing-value counts).
2. Unit tests for the analysis script's procedure-type classification and
   country canonicalisation (``eu_funding_competition.py``).
3. Consistency tests on the committed ``eu_funding_competition.json``,
   including an independent recomputation (``independent_recompute.py``) that
   does not reuse the analysis script.
4. A mutation test that plants a known error in a temporary copy of the
   parquet and asserts it is detected.
"""
from __future__ import annotations

import math
import pathlib

import pandas as pd
import pytest

import eu_funding_competition as efc
import independent_recompute as ir
from conftest import DEFAULT_PARQUET, parquet_path

# ---------------------------------------------------------------------------
# Documented reference values (from docs/agent-notes/csv-overview.md,
# cleaning.md, and the committed run).
# ---------------------------------------------------------------------------
N_ROWS = 5003
N_AWARDS = 4668
N_NOTICES = 3123  # distinct Contract ID == distinct Doc ID
EU_FUNDED_TRUE = 3046
EU_FUNDED_FALSE = 1957
PROC_NAN = 324
SENTINEL_MINUS_ONE = 18          # Awarded Value == -1
SENTINEL_SEVEN_BN = 1            # Awarded Value == 7,000,000,000
TENDERS_RECEIVED_ZERO = 59       # Tenders Received == '0' (and *_clean == 0)


# ---------------------------------------------------------------------------
# 1. Data integrity
# ---------------------------------------------------------------------------
def test_row_count(df):
    assert len(df) == N_ROWS


def test_award_and_notice_counts(df):
    assert df["Award ID"].nunique() == N_AWARDS
    assert df["Contract ID"].nunique() == N_NOTICES
    assert df["Doc ID"].nunique() == N_NOTICES


def test_contract_id_doc_id_are_one_to_one(df):
    cid_to_doc = df.groupby("Contract ID")["Doc ID"].nunique()
    doc_to_cid = df.groupby("Doc ID")["Contract ID"].nunique()
    assert (cid_to_doc == 1).all()
    assert (doc_to_cid == 1).all()


def test_eu_funded_counts(df):
    vc = df["Eu Funded"].value_counts(dropna=False)
    assert vc.get("true", 0) == EU_FUNDED_TRUE
    assert vc.get("false", 0) == EU_FUNDED_FALSE
    assert df["Eu Funded"].isna().sum() == 0


def test_procedure_type_code_missing(df):
    assert int(df["Procedure Type Code"].isna().sum()) == PROC_NAN


def test_dtypes(df):
    str_cols = ["Doc ID", "Source Country", "Buyer Name", "Buyer Country",
                "Contract Title", "Main Cpv Code", "Contract Nature Code",
                "Procedure Type Code", "Contract Nuts Code", "Framework Agreement",
                "Eu Funded", "Estimated Value Currency", "Award Title",
                "Awarded Value Currency", "Tenders Received", "Lot Number",
                "Organizations → Official Name", "Organizations → Address",
                "Organizations → Town", "Organizations → Postal Code",
                "Organizations → Country Code", "Organizations → Nuts Code",
                "Cpv Codes - Main Cpv Code → Description"]
    for c in str_cols:
        assert str(df[c].dtype) == "str", f"{c} dtype {df[c].dtype}"
    for c in ["Award ID", "Contract ID", "year"]:
        assert str(df[c].dtype) == "int64", f"{c} dtype {df[c].dtype}"
    for c in ["Estimated Value", "Awarded Value", "Value Eur", "Value Eur Real"]:
        assert str(df[c].dtype) == "float64", f"{c} dtype {df[c].dtype}"
    for c in ["Publication Date", "Award Date"]:
        assert str(df[c].dtype) == "datetime64[us]", f"{c} dtype {df[c].dtype}"
    assert str(df["is_framework"].dtype) == "boolean"
    assert str(df["tenders_received_clean"].dtype) == "Int64"
    assert str(df["Award Contractors - Award → Award ID"].dtype) == "Int64"
    assert str(df["Award Contractors - Award → Organization ID"].dtype) == "Int64"


def test_sentinel_and_outlier_values(df):
    assert int((df["Awarded Value"] == -1.0).sum()) == SENTINEL_MINUS_ONE
    assert int((df["Awarded Value"] == 7_000_000_000.0).sum()) == SENTINEL_SEVEN_BN
    assert int((df["Estimated Value"] == -1.0).sum()) == 0
    assert int((df["Tenders Received"] == "0").sum()) == TENDERS_RECEIVED_ZERO
    assert int((df["tenders_received_clean"] == 0).sum()) == TENDERS_RECEIVED_ZERO


def test_no_duplicate_rows(df):
    assert int(df.duplicated().sum()) == 0


def test_flags_constant_within_unit(df):
    s = ir.sanity(df)
    assert s["notice_eu_mixed"] == 0
    assert s["notice_proc_mixed"] == 0
    assert s["award_eu_mixed"] == 0
    assert s["award_proc_mixed"] == 0


def test_no_unit_spans_multiple_countries(df):
    s = ir.sanity(df)
    assert s["notice_country_multi"] == 0
    assert s["award_country_multi"] == 0


def test_value_eur_real_fully_empty(df):
    # 'Value Eur Real' is the one known 100%-empty column.
    assert int(df["Value Eur Real"].isna().sum()) == N_ROWS


def test_no_unexpected_mostly_empty_columns(df):
    # Only these columns are documented as >50% empty (from csv-overview.md §5).
    known_heavy = {"Value Eur Real", "Estimated Value", "Estimated Value Currency",
                   "Value Eur", "Award Date", "Award Title",
                   "Organizations → Address", "Organizations → Nuts Code",
                   "Contract Title"}
    for c in df.columns:
        frac = df[c].isna().mean()
        if frac > 0.5:
            assert c in known_heavy, f"unexpected mostly-empty column: {c} ({frac:.1%})"


def test_buyer_country_distinct_and_non_eu(df):
    vc = df["Buyer Country"].value_counts(dropna=False)
    assert df["Buyer Country"].nunique(dropna=False) == 38
    # Non-EU countries flagged in the analysis (GR is EU, mapped to EL).
    non_eu = {"BO", "CA", "CD", "CH", "GB", "KE", "MK", "MX", "NO", "RS", "TR"}
    assert non_eu <= set(vc.index)
    # Documented row-level country counts (spot checks).
    assert vc["PL"] == 1985
    assert vc["CZ"] == 769
    assert vc["ES"] == 450
    assert vc["GB"] == 137
    assert vc["CH"] == 42


def test_money_values_unchanged_by_cleaning():
    """Re-derive each money column from the raw CSV and confirm the parquet
    value matches float(raw minus thousands-commas) for every non-empty raw."""
    raw = pd.read_csv(DEFAULT_PARQUET.parent / "solar_power.csv",
                      encoding="utf-8-sig", keep_default_na=False, dtype=str)
    clean = pd.read_parquet(DEFAULT_PARQUET)
    for col in ["Estimated Value", "Awarded Value", "Value Eur", "Value Eur Real"]:
        nonempty = raw[col].str.strip() != ""
        for r, c in zip(raw[col][nonempty], clean[col][nonempty]):
            expected = float(str(r).strip().replace(",", ""))
            assert pd.notna(c) and c == expected, f"{col}: {r!r} -> {c}"


# ---------------------------------------------------------------------------
# 2. Unit tests — procedure classification & country canonicalisation
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("code", ["open", "restricted", "neg-w-call",
                                  "comp-dial", "comp-tend"])
def test_bucket_of_competitive(code):
    assert efc.bucket_of(code) == "competitive"


@pytest.mark.parametrize("code", ["neg-wo-call"])
def test_bucket_of_noncompetitive(code):
    assert efc.bucket_of(code) == "non-competitive"


@pytest.mark.parametrize("code", [None, float("nan"), "", "  ", "innovation",
                                  "exp-int-rail", "oth-single", "oth-mult",
                                  "garbage"])
def test_bucket_of_unknown(code):
    assert efc.bucket_of(code) == "unknown"


def test_canonical_country_gr_to_el():
    assert efc.canonical_country("GR") == "EL"


def test_canonical_country_identity_for_others():
    for c in ["PL", "CZ", "DE", "GB", "EL", "AT"]:
        assert efc.canonical_country(c) == c


def test_classification_matches_independent_impl():
    # The standalone classifier must agree with the script's on the data's codes.
    df = pd.read_parquet(parquet_path())
    for v in df["Procedure Type Code"].dropna().unique():
        assert ir.classify(v) == efc.bucket_of(v)


# ---------------------------------------------------------------------------
# 3. Committed JSON consistency
# ---------------------------------------------------------------------------
def _close_to_100(x, y, tol=1e-6):
    return (x is not None) and (y is not None) and abs((x + y) - 100.0) < tol


def test_json_primary_measure_is_notice(json_data):
    assert json_data["meta"]["primary_measure"] == "notice"


def test_json_shares_sum_to_100(json_data):
    for entry in json_data["countries"]:
        cc = entry["country"]
        for level in ["notice", "award"]:
            f = entry["eu_funded"][level]
            assert _close_to_100(f["eu_pct"], f["non_eu_pct"]), \
                f"{cc}/{level} eu_pct+non_eu_pct != 100: {f}"
            c = entry["competition"][level]
            assert _close_to_100(c["competitive_pct"], c["noncompetitive_pct"]), \
                f"{cc}/{level} competitive+noncompetitive != 100: {c}"


def test_json_matches_independent_recomputation(df):
    result = ir.compare_to_json(df)
    assert result["mismatches"] == [], f"discrepancies: {result['mismatches']}"
    assert result["max_eu_diff"] <= 0.01, result["max_eu_diff"]
    assert result["max_comp_diff"] <= 0.01, result["max_comp_diff"]


def test_json_headline_spot_checks(json_data):
    by_cc = {e["country"]: e for e in json_data["countries"]}
    pt = by_cc["PT"]
    assert pt["eu_funded"]["notice"]["eu_pct"] == 58.6
    assert pt["eu_funded"]["award"]["eu_pct"] == 87.4
    assert pt["competition"]["notice"]["competitive_pct"] == 100.0
    assert pt["competition"]["award"]["competitive_pct"] == 100.0


# ---------------------------------------------------------------------------
# 4. Mutation test — plant a known error in a TEMPORARY copy, confirm detection
# ---------------------------------------------------------------------------
def test_mutation_flip_eu_funded_is_detected(tmp_path):
    """Flip one ``Eu Funded`` value in a temp copy of the parquet and confirm
    the suite's control-total invariant would catch it (true count moves off
    the documented 3046). Reads the REAL parquet directly and never touches it
    in place; writes only to a temporary copy."""
    mutated = pd.read_parquet(DEFAULT_PARQUET)
    # Flip the first row's flag to its opposite.
    mutated.loc[mutated.index[0], "Eu Funded"] = \
        "false" if mutated.loc[mutated.index[0], "Eu Funded"] == "true" else "true"
    out = tmp_path / "mutated.parquet"
    mutated.to_parquet(out, index=False)

    reloaded = pd.read_parquet(out)
    true_n = int((reloaded["Eu Funded"] == "true").sum())
    assert true_n != EU_FUNDED_TRUE, "mutation was not actually applied"
    # The documented control total is violated, so test_eu_funded_counts fails.
    assert true_n in (EU_FUNDED_TRUE - 1, EU_FUNDED_TRUE + 1)
