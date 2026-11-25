"""Independent recomputation of the EU-funding & competition shares.

This module deliberately does **not** import ``scripts/eu_funding_competition.py``.
It re-implements the pipeline from scratch (its own EU-27 list, its own
procedure-code classification, its own de-duplication) so the fact-check can
compare an independent result against the committed ``data/eu_funding_competition.json``.
"""
from __future__ import annotations

import json
import pathlib

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
PARQUET = ROOT / "data" / "solar_power_clean.parquet"
JSON = ROOT / "data" / "eu_funding_competition.json"

EU27 = [
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "EL",
    "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK",
    "SI", "ES", "SE",
]
ALIAS = {"GR": "EL"}  # Greece is recorded as "GR" in the data; EU-27 uses "EL".

COMPETITIVE = {"open", "restricted", "neg-w-call", "comp-dial", "comp-tend", "oth-mult"}
NONCOMPETITIVE = {"neg-wo-call", "oth-single"}


def classify(code: object) -> str:
    """Map a procedure-type value to competitive / non-competitive / unknown."""
    if pd.isna(code) or str(code).strip() == "":
        return "unknown"
    c = str(code).strip()
    if c in COMPETITIVE:
        return "competitive"
    if c in NONCOMPETITIVE:
        return "non-competitive"
    return "unknown"


def canonical_country(code: str) -> str:
    return ALIAS.get(code, code)


def _shares(unit: pd.DataFrame, cc: str) -> dict:
    u = unit[unit["Buyer Country"].map(canonical_country) == cc]
    total = len(u)
    funded = int((u["Eu Funded"] == "true").sum())
    eu_pct = round(100.0 * funded / total, 1) if total else None
    b = u["Procedure Type Code"].map(classify)
    nc = int((b == "competitive").sum())
    nn = int((b == "non-competitive").sum())
    nk = int((b == "unknown").sum())
    known = nc + nn
    cpct = round(100.0 * nc / known, 1) if known else None
    return {
        "eu_n": funded,
        "non_eu_n": total - funded,
        "total_n": total,
        "eu_pct": eu_pct,
        "non_eu_pct": round(100.0 - eu_pct, 1) if eu_pct is not None else None,
        "competitive_n": nc,
        "noncompetitive_n": nn,
        "unknown_n": nk,
        "known_n": known,
        "competitive_pct": cpct,
        "noncompetitive_pct": round(100.0 - cpct, 1) if cpct is not None else None,
    }


def recompute(df: pd.DataFrame | None = None) -> dict:
    """Return ``{country: {'notice': {...}, 'award': {...}}}`` for the EU-27,
    with the same per-country fields as the committed JSON."""
    if df is None:
        df = pd.read_parquet(PARQUET)
    notices = df.drop_duplicates(subset="Contract ID")
    awards = df.drop_duplicates(subset="Award ID")
    return {cc: {"notice": _shares(notices, cc), "award": _shares(awards, cc)}
            for cc in EU27}


def sanity(df: pd.DataFrame) -> dict:
    """Flag- and country-uniqueness within each notice and award."""
    out: dict[str, int] = {}
    for key, label in [("Award ID", "award"), ("Contract ID", "notice")]:
        g = df.groupby(key)
        out[f"{label}_eu_mixed"] = int((g["Eu Funded"].nunique(dropna=False) > 1).sum())
        out[f"{label}_proc_mixed"] = int((g["Procedure Type Code"].nunique(dropna=False) > 1).sum())
        out[f"{label}_country_multi"] = int((g["Buyer Country"].nunique(dropna=False) > 1).sum())
    return out


def compare_to_json(df: pd.DataFrame | None = None) -> dict:
    """Compare the independent recomputation against the committed JSON,
    field-for-field, for every country / level / measure."""
    if df is None:
        df = pd.read_parquet(PARQUET)
    mine = recompute(df)
    j = json.loads(JSON.read_text(encoding="utf-8"))
    by_cc = {e["country"]: e for e in j["countries"]}

    mismatches: list[tuple] = []
    n_checked = 0
    max_eu = max_comp = 0.0
    for cc, levels in mine.items():
        entry = by_cc[cc]
        for level in ["notice", "award"]:
            m = levels[level]
            jf = entry["eu_funded"][level]
            jc = entry["competition"][level]
            for field, jv in jf.items():
                n_checked += 1
                if jv != m[field]:
                    mismatches.append((cc, level, "eu_funded", field, jv, m[field]))
            for field, jv in jc.items():
                n_checked += 1
                if jv != m[field]:
                    mismatches.append((cc, level, "competition", field, jv, m[field]))
            if m["eu_pct"] is not None and jf["eu_pct"] is not None:
                max_eu = max(max_eu, abs(m["eu_pct"] - jf["eu_pct"]))
            if m["competitive_pct"] is not None and jc["competitive_pct"] is not None:
                max_comp = max(max_comp, abs(m["competitive_pct"] - jc["competitive_pct"]))

    return {
        "n_checked": n_checked,
        "mismatches": mismatches,
        "max_eu_diff": max_eu,
        "max_comp_diff": max_comp,
        "primary_measure": j["meta"]["primary_measure"],
    }


if __name__ == "__main__":
    result = compare_to_json()
    print(f"fields checked: {result['n_checked']}")
    print(f"mismatches: {len(result['mismatches'])}")
    for m in result["mismatches"]:
        print("  MISMATCH", m)
    print(f"max eu_pct diff (pp): {result['max_eu_diff']}")
    print(f"max competitive_pct diff (pp): {result['max_comp_diff']}")
    print(f"primary_measure: {result['primary_measure']}")
