# Uncertainties

What was uncertain or unclear during the process, and how it was resolved.

## Public-tender research (2026-11-25)

The following are reported by the research sub-agents but **not yet verified
against primary sources** (EUR-Lex / Commission OJ). They must be checked before
any figure is used in published output. "⚠️" in `sources.md` marks these.

### Regulatory instruments (need EUR-Lex confirmation)
- **NZIA implementing regulations** and their numbers/dates: (EU) 2026/718
  (environmental-sustainability minimums, from 30 June 2026), (EU) 2025/1178
  (resilience list of products/components), (EU) 2025/1176 (auction non-price
  criteria). Verify titles, scope, and effective dates.
- **Guidance on NZIA Art. 25** (C/2026/4623, OJ 31.8.2026) and the
  non-price-criteria guidance (22 July 2026) — confirm publication.
- **Solar-glass trade measures**: Repeal of AD (Reg. (EU) 2026/2314) and CVD
  (Reg. (EU) 2026/2310) duties on Chinese solar glass, October 2026 — confirm.
- **Clean Industrial Deal State Aid Framework** (C/2025/3602, June 2025).
- **Industrial Accelerator Act (IAA)** — proposed March 2026; confirm status
  (proposal vs. adopted) and its "Made in EU" procurement provisions.
- **Forced Labour Regulation** (EU) 2024/3015 applicability date (14 Dec 2027)
  — reported via a secondary guide, not EUR-Lex.

### Figures and claims (need primary-source check)
- "Only six member states applying NZIA solar rules by Oct 2026; Italy 1.1 GW
  (FER-X) excluding Chinese cells/modules/inverters" (pv magazine).
- ESMC dumping/price figures: Chinese modules €0.109/Wp vs €0.159/Wp
  "sustainable European" price (~31–46% gap).
- China >95% of EU panel imports by value (ESMC; Bruegel cites 2022).
- EPBD Art. 10 phasing years for existing public buildings (2028/2029/2031 by
  size 2,000/750/250 m²).
- NZIA resilience trigger thresholds (>50% general; >85% for PV cells).
- ECA SR 09/2025 conclusion that the Commission "has not been able to draw
  sufficient assurance" on RRF procurement/state-aid compliance.

### Verified against primary sources (2026-11-28)
- **EPBD Art. 10 phasing for existing public buildings** — confirmed from
  Directive (EU) 2024/1275 Art. 10(3)(b): >2,000 m² by 31 Dec 2027, >750 m² by
  31 Dec 2028, >250 m² by 31 Dec 2030. (The "2028/2029/2031" figures are the
  "applies-from" dates, not the legal deadlines.)
- **Solar strategy targets** — confirmed from COM(2022) 221: >320 GW by 2025 and
  ~600 GW by 2030 (AC); the Commission now cites "at least 700 GW" by 2030.
- **REPowerEU financing** — confirmed: "close to €300 billion" mobilised with the
  RRF "at the heart"; ~€26bn additional solar-PV investment 2022–2027; RRF
  spending subject to DNSH (Reg. (EU) 2021/241 Art. 5) + state-aid/procurement
  rules.

### Data/logistics ambiguities
- Several sub-agent URLs are truncated (marked `…`) and need full canonical URLs
  before citing (ECA reports, Bruegel WP, ENTSO-E, Publications Office, OECD,
  World Bank, BridgeGap, Covenant of Mayors, Find-a-Tender notices).
- Whether "Source Country" vs "Buyer Country" differ meaningfully in our own
  dataset remains an open question from `ted-fields-reference.md` (Section 9).

## Dataset-level uncertainties (carried over from prior phases)
- `Value Eur` (EUR-normalised) empty for ~69% of rows; `Value Eur Real` empty
  for 100%. Any EUR total must use award-level de-duplication (exploded rows)
  and cannot be summed across currencies — see `csv-overview.md`.
- The `7,000,000,000` CZK outlier (ČEZ framework ceiling) and `-1` sentinels
  must be excluded before aggregation.
- TED under-covers below-threshold municipal contracts — a structural bias to
  flag in any visualisation headline.


## EU funding & competition shares (2026-11-25)

Computed by `scripts/eu_funding_competition.py`.

- **(a) Unknown procedure type:** excluded from the competitive/non-competitive denominator but reported per country — includes the 324 rows with a missing code (302 distinct awards / 194 notices) plus the rows coded `oth-single`/`oth-mult` (undefined in the codelist).
- **(b) Non-EU countries excluded from the EU-27 scope:** BO, CA, CD, CH, GB, KE, MK, MX, NO, RS, TR are present in the data and excluded from the EU-27 share tables (counts reported separately).
- **(c) "EU funded" is a buyer self-declaration** (TED field `BT-60`), not a verified funding record.
- **(d) Primary unit = the notice** (de-duplicated on `Contract ID`), with the award level kept as a secondary/sensitivity measure. **Reason:** both flags are notice-level, so we cannot prove an individual award is genuinely EU-funded rather than merely inheriting the flag from its parent notice — counting awards would risk overstating EU funding for multi-lot frameworks (e.g. GB: 50 notices but 127 awards). Award-level figures are reported alongside for transparency but are not the headline.
- **(e) `oth-single`/`oth-mult` reclassified to unknown (2026-11-28).** The `procurement-procedure-type` codelist gives these two codes no definition, so rather than guess competitive vs non-competitive we exclude them from the split. Competitive is now `open`/`restricted`/`neg-w-call`/`comp-dial`/`comp-tend`; non-competitive is `neg-wo-call` only.

## EU funding & beneficiaries research (2026-11-28)

Unresolved points from the funding/beneficiary research note
(`eu-funding-solar-tenders.md`). Sources numbered #84+ in `sources.md`.

- **No solar-specific Cohesion figure.** DG ENER gives €43.7bn for *all* cohesion
  "energy priorities" (2021–2027); the renewables-only ERDF/CF figure (~€8bn) comes from
  a single academic paper (Nigohosyan 2026, source #103) quoting the Scoreboard/Cohesion
  platform, and could not be confirmed against a primary Commission table. The
  *solar-only* share is not published anywhere we found.
- **Grant-vs-tender split unknown.** How much EU-funded solar money reaches TED-published
  public procurement (vs. household/firm grants and CfD auctions) is not quantified by
  any primary source. Our TED "EU-funded" flag (BT-60) is a buyer self-declaration, so it
  cannot be used to size this split.
- **"Who wins" is unquantified.** No TED-derived ranking of companies winning EU-funded
  solar tenders exists — the ECA-flagged missing common supplier ID (SR 28/2023) blocks
  ownership/cross-border analysis. Company names (Ameresco/Sunel, GES, LONGi, Shanghai
  Electric, inverter vendors) are illustrative, not a systematic beneficiary list.
- **Modernisation Fund solar share.** The €23.2bn total disbursement is firm (portal);
  the solar-specific share is only visible through individual national calls (e.g.
  Romania's €500m public-entities solar+storage call) and is not summed EU-wide.
- **Innovation Fund exact solar € total.** €4.8bn (2023) / €3.4bn (2025) / €7.1bn
  committed are call-level totals, not solar-only; the three named solar projects are a
  sample of the project list, not an exhaustive solar tally.
- **ECA SR 21/2026 allocation table currency/dates.** Annex II figures (Oct 2025, in
  euro) come from the PDF annexes; the report body uses slightly different rounding
  (€54.3bn committed). Treat Poland €24.5bn/37.8% as the headline but note grants/loans
  mix varies by member state.
- **Secondary sources for 2025–2026 IF/LIFE round figures** (Renewables Now, Evolution
  Europe, EUbusiness) were not checked against CINEA's official award announcements.
