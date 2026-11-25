# Italy — insights and trends from the cleaned TED solar dataset

Analysis of `data/solar_power_clean.parquet`, filtered to `Buyer Country == "IT"`.
Run 2026-11-25. Source of the underlying data: EU TED (Tenders Electronic Daily)
contract-award notices filtered to solar CPV codes (see `sources.md` and
`csv-overview.md`). No new external source was used.

## Scope and caveats (recorded before interpreting)

- **Exploded dataset**: one row per *award × contractor*. Italy has **66 rows**
  but only **59 unique awards** (47 contracts / 47 Doc IDs, 44 distinct buyers,
  44 contractor names, 3 rows with no contractor). All value totals below are
  computed at **award level** (deduplicated on `Award ID`), never summed over
  rows.
- **`Source Country` == `Buyer Country` == `IT` for all 66 rows** — no provenance
  mismatch for Italy.
- **Value coverage**: 43 of 59 awards have a valid EUR awarded value; 16 awards
  have no published value. `Value Eur` (EUR-normalised) mirrors `Awarded Value`
  for Italy (43 non-null, identical sum). No `-1` sentinels and no `7,000,000,000`
  outlier occur in the Italy subset.
- **Anomalies to be aware of** (not corrected, only flagged):
  - One 2013 Cagliari ASL award is labelled `CYP` (Cypriot pound) though the
    buyer is Sardinian and the amount (384,420) is clearly EUR — a currency
    mislabel in the source.
  - `Autonome Provinz Bozen` publishes the same SS 12 project in German and
    Italian as two award IDs (633333 / 633334) with identical €564,097.78 value —
    a likely bilingual duplicate that over-counts the total by ~€0.56m.
  - One 2014 award (`Consorzio Obbligatorio Smaltimento Rifiuti (Cosmari)`) reports
    **98 tenders received** — implausible for a single solar award; treat as a
    data-entry outlier (it skews the mean tenders-received upward).

## Headline finding: two distinct waves, with a silent gap between

Italy's public-body solar awards in TED are **bimodal**, mirroring policy cycles:

| Era | Publication years | Awards | Awarded value (EUR) | Character |
|-----|-------------------|-------:|--------------------:|-----------|
| **Conto Energia era** | 2011–2015 (1 straggler 2017) | ~40 | ~€34.8m | municipality/utility-led single PV plants |
| **gap** | 2016, 2018–2021 | ~0 | — | near-total absence |
| **post-crisis / PNRR era** | 2022–2026 | ~18 | ~€18.4m | central-purchasing-body framework agreements + EPC |

- The **2011–2015 wave** coincides with the tail of the *Conto Energia* feed-in
  tariff (ended July 2013): 40 awards in 2011–2015, €29m in 2011 alone, led by
  *Comune di* municipalities, provinces, utilities (Trentino trasporti, San
  Donnino multiservizi, Toscana Energia) and one regional body (Regione
  Sardegna). Many are large single plants; several use project-finance
  "concessione" (e.g. AGAC/Reggio Emilia, art. 153).
- The **2016–2021 gap** is almost total (a single 2017 award). It tracks the end
  of the feed-in tariff and the absence of a successor incentive.
- The **2022–2026 revival** is led not by individual municipalities but by a
  **central purchasing body, Consorzio CEV** (Veneto), which in 2023 let two
  framework agreements — one for supply+installation (~€2.7m, 2 lots) and one
  **Energy Performance Contract** (~€8.1m, 4 lots) — worth ~€10.8m combined,
  each awarded to a single ATI/joint venture (EXPOFIN SRL + S.V.E.T.).

## Other patterns

- **Procedure type**: 60 of 66 rows are **open** procedure (91%); 5 negotiated
  *with* call; **zero** direct awards (`neg-wo-call`). Italian solar is almost
  entirely competitively tendered — a contrast worth highlighting.
- **Competition**: median 2 tenders; a long tail of highly competitive tenders
  (Trentino trasporti 31, Calabria beni culturali 25, Villaricca 18). The 2023
  CEV frameworks, by contrast, recorded only **1 tender** each (single bidder).
- **EU funding is low for Italy (~20%)** vs ~60.9% across the whole dataset:
  53 rows self-funded, 13 EU-funded — the EU-funded ones cluster in 2013
  (FESR 2007–2013 in South Tyrol/Alto Adige and Sardinia).
- **Contract nature skews to supplies** (49/66): Italy mostly buys PV
  modules/panels (`09331200` 31, `09331000` 9) rather than "solar energy"
  (`09330000` 17) or installation (`09332000` 8) as the main CPV.
- **Top buyers** (award-level): Consorzio CEV (~€10.8m, 6 awards), Provincia di
  Modena (€4.2m, 1), Trentino trasporti (€3.5m, 1), ASL Cagliari (~€1.9m across
  6 lots), San Donnino multiservizi (€3.0m, 1), Regione Sardegna (€1.8m, 1).
- **Top contractors**: EXPOFIN SRL & S.V.E.T. (6 rows each — the CEV framework
  joint venture), Sunerg Solar Srl (6 — Cagliari ASL's supplier), Parolux Srl,
  Obrist GmbH/Srl, ORSATTI Elettrotecnica (2 each).

## Sardinia (drill-down)

Filtered to `Contract Nuts Code` starting `ITG2*` (place of performance in
Sardegna). This is a **very thin slice**: **3 contracts** in the whole dataset.

- **8 rows = 8 awards, but only 3 contracts** (3 Doc IDs, 3 buyers, 3
  contractors). No multi-contractor rows; the `Lot Number` field is empty even
  where the notice describes lots.
- **No Sardinian award has appeared since 2013** — a harder stop than the
  national pattern (Italy revives 2022–2026, Sardinia does not).

The three contracts (all **supplies**, all **open** procedure):

| Year | Buyer | Doc ID | Awards | Value (EUR) | Bidders | Contractor (HQ) | EU-funded |
|------|-------|--------|-------:|------------:|--------:|------------------|:---------:|
| 2011 | Comune di Terralba | 120796-2011 | 1 | 361,528 | 5 | ATI Casu Antonino (Guspini, IT) | no |
| 2011 | Regione Sardegna | 197603-2011 | 1 | 1,785,664 | 12 | TEPOR SpA (Cagliari, IT) | no |
| 2013 | ASL Cagliari | 073219-2013 | 6 (lots) | ~1,889,605* | 2/lot | Sunerg Solar Srl (Città di Castello, IT) | yes (FESR) |

\* ASL Cagliari total includes one lot mislabelled `CYP` (€384,420, actually
EUR); the EUR-labelled lots sum to €1,505,185.

- **Buyer mix**: one small municipality, one regional government, one health
  authority. The ASL Cagliari tender was explicitly **"six lots, separately
  awarded"** for the authority's hospitals (e.g. lot shown for "P.O. Binaghi").
- **2 of 3 contracts went to Sardinian firms** (TEPOR, Casu Antonino); the
  largest — the six-lot hospital panel supply — went to **Sunerg Solar Srl**,
  based in **Umbria**, not Sardinia.
- **Competition**: 12 bidders for the Regione Sardegna roof plant, 5 for
  Terralba, 2 per lot for the ASL supply.
- **EU funding**: only the 2013 ASL Cagliari contract is EU-funded; the two 2011
  contracts are self-funded.

Same caveat as nationally: TED under-covers below-threshold municipal jobs, so
"nothing since 2013" is a *TED-visible* absence, not proof that no Sardinian
public body has bought solar since.

## What this does not show

TED only reliably covers **above-threshold** notices, so this under-represents
the many small municipal solar jobs published on national platforms (MEPA/
Consip). The apparent 2016–2021 gap and the low count overall should be read as
a *TED-visible* trend, not a full census of Italian public-body solar.
