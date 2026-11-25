# EU funding & competition shares — per EU country (EU-27)

Computed from `data/solar_power_clean.parquet` by `scripts/eu_funding_competition.py` (2026-11-25).

## Decision: notice-level is primary, award-level is secondary

Both flags (`Eu Funded`, `Procedure Type Code`) are **notice-level** fields: they are declared once per notice and are constant across every award/lot in that notice (0 conflicting notices, 0 conflicting awards — verified).

- **Notice level is the headline measure.** We cannot prove that an individual award is *genuinely* EU-funded as opposed to merely *inheriting* the flag from its parent notice — the data gives us one value per notice, not per lot. Counting awards would weight every lot of a multi-lot EU-funded framework as if it were a separate, independently EU-funded tender. To avoid introducing that error we report the share over distinct notices.
- **Award level is kept as a secondary/sensitivity measure.** It reads slightly higher for EU funding because EU-funded notices average more awards per notice than non-EU-funded ones — a real feature of how EU-funded solar procurement is channelled through aggregated, multi-lot frameworks — but it is not the headline number.

## Method decisions

- **Unit of analysis:** notice (primary, de-duplicated on `Contract ID` = `Doc ID`, 3,123 notices) and award (secondary, de-duplicated on `Award ID`, 4,668 awards) — both from 5,003 exploded award×contractor rows.
- **EU-funded** = `Eu Funded == 'true'`; denominator = non-missing `Eu Funded` (none missing). Non-EU-funded = `Eu Funded == 'false'`.
- **Competitive / non-competitive** mapping (see table below); **unknown** (`NaN`/empty or any other code) is excluded from the denominator but reported per country as an unknown count.
- **Country scope = EU-27 only.** Greece is recorded as `GR` in the data and mapped to the EU-27 code `EL`. Non-EU countries are listed separately at the end, not silently dropped.

## Sanity checks

- **Flag uniqueness:** every `Contract ID` and every `Award ID` has exactly one `Eu Funded` value and exactly one `Procedure Type Code` value — **confirmed** (0 conflicts).
- **Country uniqueness:** no notice and no award spans more than one buyer country — **confirmed**, so the level de-duplications are unambiguous.
- **Notice vs award level are NOT identical (EU-27).** EU-funding share: **60.7%** (notice) vs **61.9%** (award); competitive share: **96.5%** (notice) vs **96.5%** (award). Max per-country gap: 35.3 pp (EU funding), 21.0 pp (competition).
  - **Why:** EU-funded notices average 1.52 awards per notice vs 1.46 for non-EU-funded ones, so the award-level EU share runs slightly higher. This is the reason award level is secondary.

## Distinct `Procedure Type Code` values → bucket

| Code | Bucket |
|---|---|
| `comp-dial` | competitive |
| `comp-tend` | competitive |
| `neg-w-call` | competitive |
| `neg-wo-call` | non-competitive |
| `open` | competitive |
| `oth-mult` | competitive |
| `oth-single` | non-competitive |
| `restricted` | competitive |

No procedure code in the data falls outside the competitive/non-competitive lists, so nothing is silently mis-bucketed.

## EU-funding share — **notice level (primary)**

| Country | EU-funded n | Non-EU-funded n | EU-funded % | Non-EU-funded % |
|---|---|---|---|---|
| AT | 0 | 8 | 0.0% | 100.0% |
| BE | 4 | 40 | 9.1% | 90.9% |
| BG | 27 | 4 | 87.1% | 12.9% |
| HR | 5 | 18 | 21.7% | 78.3% |
| CY | 2 | 2 | 50.0% | 50.0% |
| CZ | 444 | 118 | 79.0% | 21.0% |
| DK | 1 | 22 | 4.3% | 95.7% |
| EE | 0 | 8 | 0.0% | 100.0% |
| FI | 2 | 30 | 6.2% | 93.8% |
| FR | 4 | 61 | 6.2% | 93.8% |
| DE | 17 | 137 | 11.0% | 89.0% |
| EL | 12 | 33 | 26.7% | 73.3% |
| HU | 5 | 7 | 41.7% | 58.3% |
| IE | 1 | 2 | 33.3% | 66.7% |
| IT | 6 | 41 | 12.8% | 87.2% |
| LV | 36 | 20 | 64.3% | 35.7% |
| LT | 8 | 9 | 47.1% | 52.9% |
| LU | 0 | 19 | 0.0% | 100.0% |
| MT | 7 | 7 | 50.0% | 50.0% |
| NL | 2 | 185 | 1.1% | 98.9% |
| PL | 1049 | 254 | 80.5% | 19.5% |
| PT | 17 | 12 | 58.6% | 41.4% |
| RO | 23 | 18 | 56.1% | 43.9% |
| SK | 9 | 3 | 75.0% | 25.0% |
| SI | 56 | 9 | 86.2% | 13.8% |
| ES | 93 | 107 | 46.5% | 53.5% |
| SE | 0 | 11 | 0.0% | 100.0% |

## Competitive vs non-competitive — **notice level (primary)**

| Country | Competitive n | Non-competitive n | Unknown n | Competitive % | Non-competitive % |
|---|---|---|---|---|---|
| AT | 8 | 0 | 0 | 100.0% | 0.0% |
| BE | 43 | 1 | 0 | 97.7% | 2.3% |
| BG | 25 | 3 | 3 | 89.3% | 10.7% |
| HR | 14 | 0 | 9 | 100.0% | 0.0% |
| CY | 3 | 1 | 0 | 75.0% | 25.0% |
| CZ | 456 | 29 | 77 | 94.0% | 6.0% |
| DK | 22 | 1 | 0 | 95.7% | 4.3% |
| EE | 8 | 0 | 0 | 100.0% | 0.0% |
| FI | 31 | 1 | 0 | 96.9% | 3.1% |
| FR | 61 | 4 | 0 | 93.8% | 6.2% |
| DE | 131 | 21 | 2 | 86.2% | 13.8% |
| EL | 41 | 0 | 4 | 100.0% | 0.0% |
| HU | 10 | 1 | 1 | 90.9% | 9.1% |
| IE | 3 | 0 | 0 | 100.0% | 0.0% |
| IT | 46 | 0 | 1 | 100.0% | 0.0% |
| LV | 32 | 5 | 19 | 86.5% | 13.5% |
| LT | 17 | 0 | 0 | 100.0% | 0.0% |
| LU | 19 | 0 | 0 | 100.0% | 0.0% |
| MT | 14 | 0 | 0 | 100.0% | 0.0% |
| NL | 181 | 6 | 0 | 96.8% | 3.2% |
| PL | 1265 | 8 | 30 | 99.4% | 0.6% |
| PT | 26 | 0 | 3 | 100.0% | 0.0% |
| RO | 38 | 0 | 3 | 100.0% | 0.0% |
| SK | 11 | 1 | 0 | 91.7% | 8.3% |
| SI | 28 | 13 | 24 | 68.3% | 31.7% |
| ES | 179 | 5 | 16 | 97.3% | 2.7% |
| SE | 11 | 0 | 0 | 100.0% | 0.0% |

## EU-funding share — **award level (secondary)**

| Country | EU-funded n | Non-EU-funded n | EU-funded % | Non-EU-funded % |
|---|---|---|---|---|
| AT | 0 | 10 | 0.0% | 100.0% |
| BE | 4 | 71 | 5.3% | 94.7% |
| BG | 31 | 13 | 70.5% | 29.5% |
| HR | 7 | 26 | 21.2% | 78.8% |
| CY | 2 | 2 | 50.0% | 50.0% |
| CZ | 543 | 150 | 78.4% | 21.6% |
| DK | 1 | 40 | 2.4% | 97.6% |
| EE | 0 | 8 | 0.0% | 100.0% |
| FI | 2 | 30 | 6.2% | 93.8% |
| FR | 10 | 99 | 9.2% | 90.8% |
| DE | 46 | 196 | 19.0% | 81.0% |
| EL | 12 | 35 | 25.5% | 74.5% |
| HU | 6 | 10 | 37.5% | 62.5% |
| IE | 1 | 2 | 33.3% | 66.7% |
| IT | 12 | 47 | 20.3% | 79.7% |
| LV | 68 | 23 | 74.7% | 25.3% |
| LT | 42 | 9 | 82.4% | 17.6% |
| LU | 0 | 38 | 0.0% | 100.0% |
| MT | 7 | 7 | 50.0% | 50.0% |
| NL | 2 | 250 | 0.8% | 99.2% |
| PL | 1531 | 386 | 79.9% | 20.1% |
| PT | 83 | 12 | 87.4% | 12.6% |
| RO | 28 | 25 | 52.8% | 47.2% |
| SK | 11 | 7 | 61.1% | 38.9% |
| SI | 134 | 9 | 93.7% | 6.3% |
| ES | 190 | 186 | 50.5% | 49.5% |
| SE | 0 | 16 | 0.0% | 100.0% |

## Competitive vs non-competitive — **award level (secondary)**

| Country | Competitive n | Non-competitive n | Unknown n | Competitive % | Non-competitive % |
|---|---|---|---|---|---|
| AT | 10 | 0 | 0 | 100.0% | 0.0% |
| BE | 74 | 1 | 0 | 98.7% | 1.3% |
| BG | 28 | 13 | 3 | 68.3% | 31.7% |
| HR | 24 | 0 | 9 | 100.0% | 0.0% |
| CY | 3 | 1 | 0 | 75.0% | 25.0% |
| CZ | 566 | 33 | 94 | 94.5% | 5.5% |
| DK | 40 | 1 | 0 | 97.6% | 2.4% |
| EE | 8 | 0 | 0 | 100.0% | 0.0% |
| FI | 31 | 1 | 0 | 96.9% | 3.1% |
| FR | 105 | 4 | 0 | 96.3% | 3.7% |
| DE | 205 | 35 | 2 | 85.4% | 14.6% |
| EL | 43 | 0 | 4 | 100.0% | 0.0% |
| HU | 13 | 2 | 1 | 86.7% | 13.3% |
| IE | 3 | 0 | 0 | 100.0% | 0.0% |
| IT | 58 | 0 | 1 | 100.0% | 0.0% |
| LV | 67 | 5 | 19 | 93.1% | 6.9% |
| LT | 51 | 0 | 0 | 100.0% | 0.0% |
| LU | 38 | 0 | 0 | 100.0% | 0.0% |
| MT | 14 | 0 | 0 | 100.0% | 0.0% |
| NL | 246 | 6 | 0 | 97.6% | 2.4% |
| PL | 1859 | 14 | 44 | 99.3% | 0.7% |
| PT | 92 | 0 | 3 | 100.0% | 0.0% |
| RO | 50 | 0 | 3 | 100.0% | 0.0% |
| SK | 17 | 1 | 0 | 94.4% | 5.6% |
| SI | 64 | 25 | 54 | 71.9% | 28.1% |
| ES | 311 | 6 | 59 | 98.1% | 1.9% |
| SE | 16 | 0 | 0 | 100.0% | 0.0% |

**Unknown procedure type:** 296 awards (192 notices) across the EU-27 — the 324 NaN rows correspond to 302 distinct awards and 194 distinct notices.

## Non-EU countries present in the data (excluded from EU-27 shares)

| Country | Notice count | Award count |
|---|---:|---:|
| `BO` | 1 | 2 |
| `CA` | 1 | 1 |
| `CD` | 1 | 2 |
| `CH` | 42 | 42 |
| `GB` | 50 | 127 |
| `KE` | 1 | 1 |
| `MK` | 3 | 3 |
| `MX` | 1 | 1 |
| `NO` | 5 | 6 |
| `RS` | 2 | 2 |
| `TR` | 1 | 1 |

