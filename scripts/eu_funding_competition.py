"""Compute per-country EU-funding and competition shares for the solar award dataset.

Reads ``data/solar_power_clean.parquet`` and computes, for the **EU-27** only,
two measures at **two levels of analysis** each:

1. the share of **EU-funded vs non-EU-funded** tenders (from ``Eu Funded``), and
2. the share of **competitive vs non-competitive** tenders (from
   ``Procedure Type Code``).

Each measure is computed at:

- **notice level** — one row per distinct ``Contract ID`` (= ``Doc ID``, the TED
  notice); **this is the primary measure**.
- **award level** — one row per distinct ``Award ID`` (each lot/award within a
  notice); kept as a secondary, sensitivity measure.

Method:

- **Primary unit = the notice** (``Contract ID``). Both flags are notice-level
  fields (constant across all awards in a notice), and — critically — we cannot
  prove that an individual award is *genuinely* EU-funded as opposed to merely
  *inheriting* the flag from its parent notice. Counting awards would therefore
  weight every lot of a multi-lot EU-funded framework as if it were a separate,
  independently EU-funded tender. To avoid that risk we report the notice level
  as the headline and the award level as secondary.
- **EU-funded share** = (``Eu Funded == 'true'``) / (non-missing ``Eu Funded``).
  ``Eu Funded`` is fully populated (no NaN).
- **Competitive vs non-competitive** (see ``COMPETITIVE`` / ``NONCOMPETITIVE``).
  ``NaN``/unknown procedure types are **excluded from the denominator** but
  reported per country as an unknown count.
- **Country scope = EU-27** only. Greece is recorded as ``GR`` in the data and
  mapped to the EU-27 code ``EL``. Non-EU countries are listed separately.

Writes ``data/eu_funding_competition.json`` (chart-ready, notice + award level),
``docs/agent-notes/eu-funding-competition.md`` (report), and appends a dated
section to ``docs/agent-notes/uncertainties.md``.
"""

from __future__ import annotations

import json
import pathlib

import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "solar_power_clean.parquet"
REPORT = ROOT / "docs" / "agent-notes" / "eu-funding-competition.md"
JSON_OUT = ROOT / "data" / "eu_funding_competition.json"
UNCERTAINTIES = ROOT / "docs" / "agent-notes" / "uncertainties.md"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
# EU-27 (post-Brexit) ISO alpha-2 codes, in sort order.
EU27 = [
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE",
    "EL", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT",
    "RO", "SK", "SI", "ES", "SE",
]
# Greece appears as "GR" in the data (never "EL"); map it to the EU-27 code.
COUNTRY_ALIAS = {"GR": "EL"}

COMPETITIVE = {"open", "restricted", "neg-w-call", "comp-dial", "comp-tend", "oth-mult"}
NONCOMPETITIVE = {"neg-wo-call", "oth-single"}

COUNTRY_NAMES = {
    "AT": "Austria", "BE": "Belgium", "BG": "Bulgaria", "HR": "Croatia",
    "CY": "Cyprus", "CZ": "Czechia", "DK": "Denmark", "EE": "Estonia",
    "FI": "Finland", "FR": "France", "DE": "Germany", "EL": "Greece",
    "HU": "Hungary", "IE": "Ireland", "IT": "Italy", "LV": "Latvia",
    "LT": "Lithuania", "LU": "Luxembourg", "MT": "Malta", "NL": "Netherlands",
    "PL": "Poland", "PT": "Portugal", "RO": "Romania", "SK": "Slovakia",
    "SI": "Slovenia", "ES": "Spain", "SE": "Sweden",
}


def bucket_of(code: object) -> str:
    """Map a ``Procedure Type Code`` value to competitive/non-competitive/unknown."""
    if pd.isna(code) or str(code).strip() == "":
        return "unknown"
    c = str(code).strip()
    if c in COMPETITIVE:
        return "competitive"
    if c in NONCOMPETITIVE:
        return "non-competitive"
    return "unknown"  # anything not in the two lists


def canonical_country(code: str) -> str:
    return COUNTRY_ALIAS.get(code, code)


def make_share_tables(unit: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (funding, competition) DataFrames for one deduplicated unit.

    ``unit`` has one row per unit, with columns ``Buyer Country``, ``Eu Funded``
    and ``Procedure Type Code``.
    """
    unit = unit.copy()
    unit["country"] = unit["Buyer Country"].map(canonical_country)

    funding_rows: list[dict] = []
    comp_rows: list[dict] = []
    for cc in EU27:
        sub = unit[unit["country"] == cc]

        # EU funding (Eu Funded fully populated; only 'true' counts as EU-funded)
        total = int(len(sub))
        funded = int((sub["Eu Funded"] == "true").sum())
        non_funded = total - funded
        eu_pct = round(100.0 * funded / total, 1) if total else float("nan")
        funding_rows.append({
            "country": cc,
            "eu_n": funded,
            "non_eu_n": non_funded,
            "total_n": total,
            "eu_pct": eu_pct,
            # complement of eu_pct so the two sum to exactly 100.0
            "non_eu_pct": round(100.0 - eu_pct, 1) if total else float("nan"),
        })

        # competition
        buckets = sub["Procedure Type Code"].map(bucket_of)
        n_comp = int((buckets == "competitive").sum())
        n_noncomp = int((buckets == "non-competitive").sum())
        n_unknown = int((buckets == "unknown").sum())
        known = n_comp + n_noncomp
        competitive_pct = round(100.0 * n_comp / known, 1) if known else float("nan")
        comp_rows.append({
            "country": cc,
            "competitive_n": n_comp,
            "noncompetitive_n": n_noncomp,
            "unknown_n": n_unknown,
            "known_n": known,
            "competitive_pct": competitive_pct,
            "noncompetitive_pct": round(100.0 - competitive_pct, 1) if known else float("nan"),
        })

    return pd.DataFrame(funding_rows), pd.DataFrame(comp_rows)


def fmt_pct(x: object) -> str:
    return "—" if pd.isna(x) else f"{x:.1f}%"


def md_table(df: pd.DataFrame, columns: list[str], headers: list[str]) -> str:
    """Render a DataFrame subset as a GitHub-flavoured markdown table."""
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(row[c]) for c in columns) + " |")
    return "\n".join(lines)


def pct_col(df: pd.DataFrame, col: str) -> pd.Series:
    """Formatted percentage column ('12.3%' / '—')."""
    return df[col].map(fmt_pct)


def main() -> None:
    df = pd.read_parquet(SRC)

    # ---------------------------------------------------------------- sanity 1
    # Flag uniqueness within Award ID (and within Contract ID): each unit must
    # have exactly one distinct value per flag (NaN treated as a value).
    for key, label in [("Award ID", "award"), ("Contract ID", "notice")]:
        g = df.groupby(key).agg(
            eu_unique=("Eu Funded", lambda s: s.nunique(dropna=False)),
            proc_unique=("Procedure Type Code", lambda s: s.nunique(dropna=False)),
        )
        assert (g["eu_unique"] <= 1).all(), f"Eu Funded not unique within {label}!"
        assert (g["proc_unique"] <= 1).all(), f"Procedure Type Code not unique within {label}!"

    # ---------------------------------------------------------------- sanity 2
    # Country uniqueness: no notice/award may span multiple buyer countries,
    # otherwise a dedup on the unit id would silently drop a country.
    for key, label in [("Award ID", "award"), ("Contract ID", "notice")]:
        n_multi = int((df.groupby(key)["Buyer Country"].nunique() > 1).sum())
        assert n_multi == 0, f"{n_multi} {label}s span multiple buyer countries!"

    # ------------------------------------------------------ distinct procedure codes
    proc_values = sorted(df["Procedure Type Code"].dropna().unique().tolist())
    proc_mapping = {v: bucket_of(v) for v in proc_values}
    uncovered = [v for v in proc_values if bucket_of(v) == "unknown"]
    assert not uncovered, f"unexpected procedure codes not bucketed: {uncovered}"

    # ------------------------------------------------------ dedup at both levels
    awards = df.drop_duplicates(subset="Award ID").reset_index(drop=True)
    notices = df.drop_duplicates(subset="Contract ID").reset_index(drop=True)

    fund_award, comp_award = make_share_tables(awards)
    fund_notice, comp_notice = make_share_tables(notices)

    # ---------------------------------------------------------------- comparison
    def max_abs_diff(a: pd.DataFrame, b: pd.DataFrame, col: str) -> float:
        d = (a[col] - b[col]).abs()
        return float(d.max()) if d.notna().any() else 0.0

    def overall_pct(unit: pd.DataFrame, flag: str) -> float:
        if flag == "eu":
            total = int(len(unit))
            return 100.0 * (unit["Eu Funded"] == "true").sum() / total if total else float("nan")
        b = unit["Procedure Type Code"].map(bucket_of)
        n_c = int((b == "competitive").sum())
        n_n = int((b == "non-competitive").sum())
        return 100.0 * n_c / (n_c + n_n) if (n_c + n_n) else float("nan")

    eu_max_diff = max_abs_diff(fund_award, fund_notice, "eu_pct")
    comp_max_diff = max_abs_diff(comp_award, comp_notice, "competitive_pct")

    # awards-per-notice by flag, to explain the EU-funding gap between levels
    apc = awards.groupby(["Contract ID", "Eu Funded"]).size().groupby("Eu Funded").mean()
    apc_true = float(apc.get("true", float("nan")))
    apc_false = float(apc.get("false", float("nan")))

    # ------------------------------------------------------ non-EU country list
    non_eu_notice = (
        notices[~notices["Buyer Country"].map(canonical_country).isin(EU27)]
        ["Buyer Country"].value_counts().sort_index()
    )
    non_eu_award = (
        awards[~awards["Buyer Country"].map(canonical_country).isin(EU27)]
        ["Buyer Country"].value_counts().sort_index()
    )

    # ------------------------------------------------------------------ report
    lines: list[str] = []

    def add(line: str = "") -> None:
        lines.append(line)

    add("# EU funding & competition shares — per EU country (EU-27)")
    add()
    add("Computed from `data/solar_power_clean.parquet` by "
        "`scripts/eu_funding_competition.py` (2026-11-25).")
    add()
    add("## Decision: notice-level is primary, award-level is secondary")
    add()
    add("Both flags (`Eu Funded`, `Procedure Type Code`) are **notice-level** fields: "
        "they are declared once per notice and are constant across every award/lot "
        "in that notice (0 conflicting notices, 0 conflicting awards — verified).")
    add()
    add("- **Notice level is the headline measure.** We cannot prove that an "
        "individual award is *genuinely* EU-funded as opposed to merely "
        "*inheriting* the flag from its parent notice — the data gives us one "
        "value per notice, not per lot. Counting awards would weight every lot of "
        "a multi-lot EU-funded framework as if it were a separate, independently "
        "EU-funded tender. To avoid introducing that error we report the share "
        "over distinct notices.")
    add("- **Award level is kept as a secondary/sensitivity measure.** It reads "
        "slightly higher for EU funding because EU-funded notices average more "
        "awards per notice than non-EU-funded ones — a real feature of how "
        "EU-funded solar procurement is channelled through aggregated, multi-lot "
        "frameworks — but it is not the headline number.")
    add()
    add("## Method decisions")
    add()
    add("- **Unit of analysis:** notice (primary, de-duplicated on `Contract ID` "
        f"= `Doc ID`, {int(notices['Contract ID'].nunique()):,} notices) and award "
        f"(secondary, de-duplicated on `Award ID`, {int(awards['Award ID'].nunique()):,} awards) — "
        f"both from {len(df):,} exploded award×contractor rows.")
    add("- **EU-funded** = `Eu Funded == 'true'`; denominator = non-missing "
        "`Eu Funded` (none missing). Non-EU-funded = `Eu Funded == 'false'`.")
    add("- **Competitive / non-competitive** mapping (see table below); "
        "**unknown** (`NaN`/empty or any other code) is excluded from the "
        "denominator but reported per country as an unknown count.")
    add("- **Country scope = EU-27 only.** Greece is recorded as `GR` in the data "
        "and mapped to the EU-27 code `EL`. Non-EU countries are listed "
        "separately at the end, not silently dropped.")
    add()
    add("## Sanity checks")
    add()
    add("- **Flag uniqueness:** every `Contract ID` and every `Award ID` has "
        "exactly one `Eu Funded` value and exactly one `Procedure Type Code` "
        "value — **confirmed** (0 conflicts).")
    add("- **Country uniqueness:** no notice and no award spans more than one "
        "buyer country — **confirmed**, so the level de-duplications are "
        "unambiguous.")
    add(f"- **Notice vs award level are NOT identical.** EU-funding share: "
        f"**{overall_pct(notices, 'eu'):.1f}%** (notice) vs "
        f"**{overall_pct(awards, 'eu'):.1f}%** (award); competitive share: "
        f"**{overall_pct(notices, 'comp'):.1f}%** (notice) vs "
        f"**{overall_pct(awards, 'comp'):.1f}%** (award). Max per-country gap: "
        f"{eu_max_diff:.1f} pp (EU funding), {comp_max_diff:.1f} pp (competition).")
    add(f"  - **Why:** EU-funded notices average {apc_true:.2f} awards per notice "
        f"vs {apc_false:.2f} for non-EU-funded ones, so the award-level EU share "
        "runs slightly higher. This is the reason award level is secondary.")
    add()
    add("## Distinct `Procedure Type Code` values → bucket")
    add()
    add("| Code | Bucket |")
    add("|---|---|")
    for v in proc_values:
        add(f"| `{v}` | {proc_mapping[v]} |")
    add()
    add("No procedure code in the data falls outside the competitive/"
        "non-competitive lists, so nothing is silently mis-bucketed.")
    add()

    # -------- primary (notice) tables
    add("## EU-funding share — **notice level (primary)**")
    add()
    add(md_table(
        fund_notice.assign(eu_pct=pct_col(fund_notice, "eu_pct"),
                           non_eu_pct=pct_col(fund_notice, "non_eu_pct")),
        ["country", "eu_n", "non_eu_n", "eu_pct", "non_eu_pct"],
        ["Country", "EU-funded n", "Non-EU-funded n", "EU-funded %", "Non-EU-funded %"],
    ))
    add()
    add("## Competitive vs non-competitive — **notice level (primary)**")
    add()
    add(md_table(
        comp_notice.assign(
            competitive_pct=pct_col(comp_notice, "competitive_pct"),
            noncompetitive_pct=pct_col(comp_notice, "noncompetitive_pct"),
        ),
        ["country", "competitive_n", "noncompetitive_n", "unknown_n",
         "competitive_pct", "noncompetitive_pct"],
        ["Country", "Competitive n", "Non-competitive n", "Unknown n",
         "Competitive %", "Non-competitive %"],
    ))
    add()

    # -------- secondary (award) tables
    add("## EU-funding share — **award level (secondary)**")
    add()
    add(md_table(
        fund_award.assign(eu_pct=pct_col(fund_award, "eu_pct"),
                          non_eu_pct=pct_col(fund_award, "non_eu_pct")),
        ["country", "eu_n", "non_eu_n", "eu_pct", "non_eu_pct"],
        ["Country", "EU-funded n", "Non-EU-funded n", "EU-funded %", "Non-EU-funded %"],
    ))
    add()
    add("## Competitive vs non-competitive — **award level (secondary)**")
    add()
    add(md_table(
        comp_award.assign(
            competitive_pct=pct_col(comp_award, "competitive_pct"),
            noncompetitive_pct=pct_col(comp_award, "noncompetitive_pct"),
        ),
        ["country", "competitive_n", "noncompetitive_n", "unknown_n",
         "competitive_pct", "noncompetitive_pct"],
        ["Country", "Competitive n", "Non-competitive n", "Unknown n",
         "Competitive %", "Non-competitive %"],
    ))
    add()
    add(f"**Unknown procedure type:** {int(comp_award['unknown_n'].sum())} awards "
        f"({int(comp_notice['unknown_n'].sum())} notices) across the EU-27 — the "
        f"{int(df['Procedure Type Code'].isna().sum())} NaN rows correspond to "
        f"{int(df.loc[df['Procedure Type Code'].isna(), 'Award ID'].nunique())} distinct "
        "awards and "
        f"{int(df.loc[df['Procedure Type Code'].isna(), 'Contract ID'].nunique())} distinct notices.")
    add()
    add("## Non-EU countries present in the data (excluded from EU-27 shares)")
    add()
    add("| Country | Notice count | Award count |")
    add("|---|---:|---:|")
    all_non_eu = sorted(set(non_eu_notice.index) | set(non_eu_award.index))
    for cc in all_non_eu:
        add(f"| `{cc}` | {int(non_eu_notice.get(cc, 0))} | {int(non_eu_award.get(cc, 0))} |")
    add()

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # ------------------------------------------------------------------- JSON
    def funding_record(row: pd.Series) -> dict:
        return {
            "eu_n": int(row["eu_n"]),
            "non_eu_n": int(row["non_eu_n"]),
            "total_n": int(row["total_n"]),
            "eu_pct": None if pd.isna(row["eu_pct"]) else float(row["eu_pct"]),
            "non_eu_pct": None if pd.isna(row["non_eu_pct"]) else float(row["non_eu_pct"]),
        }

    def comp_record(row: pd.Series) -> dict:
        return {
            "competitive_n": int(row["competitive_n"]),
            "noncompetitive_n": int(row["noncompetitive_n"]),
            "unknown_n": int(row["unknown_n"]),
            "known_n": int(row["known_n"]),
            "competitive_pct": None if pd.isna(row["competitive_pct"]) else float(row["competitive_pct"]),
            "noncompetitive_pct": None if pd.isna(row["noncompetitive_pct"]) else float(row["noncompetitive_pct"]),
        }

    fund_notice_idx = fund_notice.set_index("country")
    comp_notice_idx = comp_notice.set_index("country")
    fund_award_idx = fund_award.set_index("country")
    comp_award_idx = comp_award.set_index("country")

    countries = []
    for cc in EU27:
        countries.append({
            "country": cc,
            "name": COUNTRY_NAMES.get(cc, cc),
            "eu_funded": {
                "notice": funding_record(fund_notice_idx.loc[cc]),
                "award": funding_record(fund_award_idx.loc[cc]),
            },
            "competition": {
                "notice": comp_record(comp_notice_idx.loc[cc]),
                "award": comp_record(comp_award_idx.loc[cc]),
            },
        })

    json_out = {
        "meta": {
            "title": "EU-funded and competitive tenders by EU country (EU-27)",
            "generated": "2026-11-25",
            "source": "data/solar_power_clean.parquet",
            "scope": "EU-27",
            "primary_measure": "notice",
            "secondary_measure": "award",
            "levels": {
                "notice": "one row per Contract ID (= Doc ID, the TED notice)",
                "award": "one row per Award ID (each lot/award within a notice)",
            },
            "eu_funded_definition": "Eu Funded == 'true' (buyer self-declaration, TED BT-60 / B_EU_FUNDS)",
            "competitive_codes": sorted(COMPETITIVE),
            "noncompetitive_codes": sorted(NONCOMPETITIVE),
            "competitive_denominator": "competitive + noncompetitive; unknown excluded",
            "greece_code_note": "Greece appears as 'GR' in the data; mapped to 'EL'.",
            "non_eu_countries_excluded": all_non_eu,
        },
        "countries": countries,
        "non_eu": [
            {
                "country": cc,
                "notice_n": int(non_eu_notice.get(cc, 0)),
                "award_n": int(non_eu_award.get(cc, 0)),
            }
            for cc in all_non_eu
        ],
    }
    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(json_out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # ------------------------------------------------------ uncertainties append
    section = (
        "\n\n## EU funding & competition shares (2026-11-25)\n\n"
        "Computed by `scripts/eu_funding_competition.py`.\n\n"
        "- **(a) Unknown procedure type:** `Procedure Type Code` is missing on "
        f"{int(df['Procedure Type Code'].isna().sum())} rows, corresponding to "
        f"{int(df.loc[df['Procedure Type Code'].isna(), 'Award ID'].nunique())} distinct awards "
        f"({int(df.loc[df['Procedure Type Code'].isna(), 'Contract ID'].nunique())} notices). "
        "These are excluded from the competitive/non-competitive denominator but "
        "reported per country.\n"
        "- **(b) Non-EU countries excluded from the EU-27 scope:** "
        f"{', '.join(all_non_eu)} are present in the data and excluded from the "
        "EU-27 share tables (counts reported separately).\n"
        "- **(c) \"EU funded\" is a buyer self-declaration** (TED field `BT-60`), "
        "not a verified funding record.\n"
        "- **(d) Primary unit = the notice** (de-duplicated on `Contract ID`), "
        "with the award level kept as secondary. **Reason:** both flags are "
        "notice-level, so we cannot prove an individual award is genuinely "
        "EU-funded rather than merely inheriting the flag from its parent "
        "notice — counting awards would risk overstating EU funding for "
        "multi-lot frameworks. Award-level figures are reported alongside for "
        "transparency but are not the headline.\n"
    )
    existing = UNCERTAINTIES.read_text(encoding="utf-8") if UNCERTAINTIES.exists() else ""
    if "## EU funding & competition shares (2026-11-25)" not in existing:
        with open(UNCERTAINTIES, "a", encoding="utf-8") as f:
            f.write(section)

    # ------------------------------------------------------------------ print
    print("distinct Procedure Type Code -> bucket:")
    for v in proc_values:
        print(f"  {v:<12} -> {proc_mapping[v]}")
    print()
    print(f"overall EU-funded share: notice {overall_pct(notices, 'eu'):.1f}% | "
          f"award {overall_pct(awards, 'eu'):.1f}%")
    print(f"overall competitive share: notice {overall_pct(notices, 'comp'):.1f}% | "
          f"award {overall_pct(awards, 'comp'):.1f}%")
    print()
    print("EU-funding share by country (EU-27) — notice level (primary):")
    print(fund_notice.assign(eu_pct=pct_col(fund_notice, "eu_pct")).to_string(index=False))
    print()
    print("Competitive vs non-competitive by country (EU-27) — notice level (primary):")
    print(comp_notice.assign(
        competitive_pct=pct_col(comp_notice, "competitive_pct"),
        noncompetitive_pct=pct_col(comp_notice, "noncompetitive_pct"),
    ).to_string(index=False))
    print()
    print("Non-EU countries (notice/award counts):")
    print(pd.DataFrame({"notice": non_eu_notice, "award": non_eu_award}).fillna(0).astype(int).to_string())
    print()
    print(f"wrote {REPORT}")
    print(f"wrote {JSON_OUT}")
    print(f"appended to {UNCERTAINTIES}")


if __name__ == "__main__":
    main()
