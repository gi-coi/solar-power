# TED (Tenders Electronic Daily) CSV — Field Reference

A reference for interpreting a CSV export of EU public-procurement award notices, filtered to solar-power awards.

**Scope note / uncertainty:** the export you are reading uses human-readable column names (e.g. "Doc ID", "Value Eur", "Value Eur Real", "Source Country"). These are not the raw column names of the official "TED CSV subset" (`ted-csv`), which uses names such as `ID_NOTICE_CAN`, `VALUE_EURO_FIN_1`, `ISO_COUNTRY_CODE`, `NUMBER_OFFERS`. Your export is either a derivative/normalised version of that subset, the TED website's CSV export, or an OCDS-flavoured export. This document explains the underlying TED concepts and maps your likely column names to the official fields. Where a mapping is an interpretation rather than a certainty it is flagged.

---

## 1. What TED is, what its CSV/OCDS exports contain, and the "Doc ID"

**TED (Tenders Electronic Daily)** is the online version of the "Supplement to the Official Journal of the European Union" (the OJ S series). It is the EU-wide portal, run by the Publications Office of the EU, where public bodies ("contracting authorities") publish their procurement notices: calls for competition (mainly *contract notices*, CN), *contract award notices* (CAN), and *voluntary ex-ante transparency notices* (VEAT).

- A **contract notice (CN)** announces a *future* purchase ("The ministry would like to buy furniture").
- A **contract award notice (CAN)** announces the *result* ("The ministry has bought furniture from company X"). Award notices are the form relevant to solar-power **awards**.
- The data mostly covers tenders **above the EU procurement thresholds**, though below-threshold notices are sometimes published voluntarily.

**What the CSV/OCDS exports contain.** The official "TED CSV subset" (dataset `ted-csv` on data.europa.eu) is a flat-file export of "the most important fields" from contract-notice and contract-award-notice standard forms — "who bought what from whom, for how much, and which procedure and award criteria were used." TED also publishes full notices in **XML** (eForms since 14 Nov 2022, and the older "TED schema" forms), and an **OCDS** (Open Contracting Data Standard) mapping exists for eForms. CSV is a *lossy subset*: free-text descriptions and some fields are omitted to keep files manageable.

**What a row in an award-notice export represents.** A single CAN can describe several **lots** and several **contract awards (CA)**, with a many-to-many relationship between them. In the flat CSV, this is "flattened" by duplication: **each row = one combination of notice + lot + contract award**. Notice-level fields (e.g. procedure type) are repeated on every row for the same notice. To count *notices*, de-duplicate on the notice identifier; to count *awards*, de-duplicate on the award identifier.

**"Doc ID" / notice publication number format (e.g. `00006377-2025`).** This is the notice's unique publication number, assigned by the Publications Office when the notice is published. Format: an **8-digit sequential number (zero-padded) + hyphen + 4-digit year** — `00006377-2025` = notice number 6377 of 2025.

- The **number** is a running sequence assigned in order of publication within the OJ S series for that **year**; the **year** is the year the notice was published (not necessarily the year of award).
- The same number appears in the OJ S reference (`2025/S ...`) and as the eForms XML file name (`00006377_2025.xml`). eForms XML packages name files as "8 digits + year", matching this format.

---

## 2. CPV (Common Procurement Vocabulary) codes — solar

**CPV** is the EU's single classification system for describing the subject of a public contract (supplies, works or services). It is mandatory for EU notices since 1 Feb 2006; the current version is **CPV 2008**, in force since 17 September 2008 (Regulation (EC) No 213/2008). A CPV code is 8 digits plus a 9th **check digit** (e.g. `09330000-1`); TED publishes the 8 digits without the check digit.

**Structure.** The 8-digit code is hierarchical:
- first 2 digits = **division** (`XX000000-Y`)
- first 3 digits = **group** (`XXX00000-Y`)
- first 4 digits = **class** (`XXXX0000-Y`)
- first 5 digits = **category** (`XXXXX000-Y`)

**Division 09 context.** Division `09` is **"Petroleum products, fuel, electricity and other sources of energy"**. Within it, class `09300000` is **"Electricity, heating, solar and nuclear energy"**, which contains the solar codes below.

| CPV code | Official wording |
|---|---|
| `09300000` | Electricity, heating, solar and nuclear energy |
| `09310000` | Electricity |
| `09320000` | Steam, hot water and associated products |
| `09330000` | **Solar energy** |
| `09331000` | **Solar panels** |
| `09331100` | Solar collectors for heat production |
| `09331200` | **Solar photovoltaic modules** |
| `09332000` | **Solar installation** |

**Interpretation for your solar filter:**
- `09330000` ("Solar energy") is the broad class — a "parent" code. Many notices tag it as the *main* CPV code even when the real subject is more specific.
- `09331000` ("Solar panels") and `09331200` ("Solar photovoltaic modules") are progressively more specific *supplies* codes (PV modules are the actual panels; `09331100` is for solar *thermal* collectors).
- `09332000` ("Solar installation") is the *works/installation* code — relevant when the contract is to *install* solar systems rather than just supply panels.
- Because `09331200` is a leaf code, an award tagged `09331200` is more precisely a PV-module supply than one tagged only `09330000`. A notice can carry **one main CPV code plus additional CPV codes** (often several solar codes listed together).

---

## 3. Contract Nature Code ("supplies" / "works" / "services")

This is the **type of contract** (`BT-...` / the `contract-nature` codelist, formerly `TYPE_OF_CONTRACT` in the CSV subset). It classifies what is being procured:

| Code | Meaning |
|---|---|
| `supplies` | Purchase/lease of **goods** (e.g. solar panels) |
| `works` | **Construction / civil-engineering works** (e.g. installing a solar array on a building) |
| `services` | Provision of **services** (e.g. design, maintenance, a power-purchase agreement) |

In the official CSV subset the values are the words `works`, `supplies`, `services` (not codes). Solar awards can be any of the three: buying panels = supplies; installing them = works; operating/maintaining or a PPA = services.

---

## 4. Procedure Type Code ("open", "neg-wo-call", …)

This describes the **procurement procedure** used. In eForms the field is **`BT-105`** (`cbc:ProcedureCode`, list name `procurement-procedure-type`). The authoritative code + label set is the TED eForms SDK [`procurement-procedure-type` codelist](https://docs.ted.europa.eu/eforms/latest/reference/code-lists/procurement-procedure-type.html) (version 20250924-0, accessed 2026-11-28), issued by the Publications Office as the EU Vocabularies authority table `http://publications.europa.eu/resource/authority/procurement-procedure-type`. The quoted descriptions below come from the OCDS for eForms profile's [`procurement-procedure-type` codelist mapping](https://standard.open-contracting.org/profiles/eforms/latest/en/codelists/procurement-procedure-type/) (accessed 2026-11-28).

| Code | Authoritative label (TED SDK codelist) | Description (OCDS-for-eForms, quoted) |
|---|---|---|
| `open` | Open | "In open procedures any interested economic operator may submit a tender in response to a call for competition." |
| `restricted` | Restricted | "In restricted procedures, any economic operator may submit a request to participate in response to a call for competition by providing the information for qualitative selection that is requested by the contracting entity." |
| `neg-w-call` | Negotiated with prior publication of a call for competition / competitive with negotiation | "In negotiated procedures with prior call for competition, any economic operator may submit a request to participate in response to a call for competition by providing the information for qualitative selection that is requested by the contracting entity." |
| `neg-wo-call` | Negotiated without prior call for competition | "Contracting entities may use a negotiated procedure without prior call for competition in the following cases: Based on Directive 2014/25/EU, Article 50: (a) where no tenders or no suitable tenders or no requests to participate or no suitable requests to participate have been submitted […]; (b) where a contract is purely for the purpose of research, experiment, study or development […]; (c) where the works, supplies or services can be supplied only by a particular economic operator […]; (d) … extreme urgency …; (e) … additional deliveries by the original supplier …; (f) … repetition of similar works or services …; (g) supplies quoted and purchased on a commodity market; (h) bargain purchases …; (i) … particularly advantageous conditions …; (j) … follows a design contest …; OR Based on Regulation (EC) No 1370/2007, Article 5." |
| `comp-dial` | Competitive dialogue | "In competitive dialogues, any economic operator may submit a request to participate in response to a call for competition in accordance with points (b) and (c) of Article 44(4) by providing the information for qualitative selection that is requested by the contracting entity." |
| `comp-tend` | Competitive tendering (article 5(3) of Regulation 1370/2007) | "A competitive tendering procedure is open to any interested economic operator, is fair and observes the principles of transparency and non-discrimination. Such a procedure does not rule out negotiations (in order to determine how best to meet specific or complex requirements) provided they comply with the same principles." |
| `innovation` | Innovation partnership | "In innovation partnerships, any economic operator may submit a request to participate in response to a call for competition in accordance with points (b) and (c) of Article 44(4) by providing the information for qualitative selection that is requested by the contracting entity." |
| `oth-single` | Other single stage procedure | *No description — the codelist gives only this terse label, and the code is absent from the OCDS-for-eForms mapping.* |
| `oth-mult` | Other multiple stage procedure | *No description — the codelist gives only this terse label, and the code is absent from the OCDS-for-eForms mapping.* |
| `exp-int-rail` | Request for expression of interest – only for rail (article 5(3b) of Regulation 1370/2007) | "Based on Article 5(3b) of Regulation (EC) No 1370/2007, competent authorities may make public their intentions to award a public service contract for public passenger transport services by rail by publishing an information notice in the Official Journal of the European Union." |

**Field level (BT-105).** Procedure-level, **cardinality 1** (mandatory and unique): "It is marked for the whole Procedure with the `cbc:ProcedureCode` element" ([TED eForms schema, "Procedure Type (BT-105)"](https://docs.ted.europa.eu/eforms/latest/schema/procedure-lot-part-information.html), accessed 2026-11-28). It is *not* repeated per lot/part, so it is constant across every award in a notice.

**Codelist vs. competitive/non-competitive aggregation — two distinct things:**

- The **codelist** above is authoritative and lists *procedure types* (10 codes and their labels). It contains **no "competitive / non-competitive" flag** — that split is **not** a codelist field; it is an *analytical* convention we apply for this project.
- Our **aggregation** (`scripts/eu_funding_competition.py`) buckets:
  - **competitive** = `open`, `restricted`, `neg-w-call`, `comp-dial`, `comp-tend`, `oth-mult`
  - **non-competitive** = `neg-wo-call`, `oth-single`

**Judgment calls in that rule:**
- `neg-w-call` → competitive follows the **"prior call ⇒ competitive"** convention: its label is literally "negotiated **with prior publication of a call for competition** / competitive with negotiation", and the OCDS-for-eForms mapping assigns it to OCDS `selective` ("Only qualified suppliers are invited to submit a tender").
- `neg-wo-call` → non-competitive: "negotiated **without prior** call for competition"; the OCDS-for-eForms mapping assigns it to OCDS `limited` ("The procuring entity contacts a number of suppliers of its choice"), i.e. a direct award.
- `oth-single` / `oth-mult` are **genuinely vague** in the codelist ("other single / multiple stage procedure", with no definition). Assigning `oth-mult` → competitive and `oth-single` → non-competitive is *our* choice (single-stage ≈ no separate shortlisting/selection stage); the codelist does not state it.

**Interpretation:** a solar award with `neg-wo-call` is a *direct award* (no open competition), whereas `open` means a fully competitive tender. `neg-wo-call` awards are common for small, urgent, or sole-supplier solar work and typically show very few or zero competing tenders.

---

## 5. NUTS codes (e.g. SI038, CZ051, DE712, PL418)

**NUTS** = *Nomenclature of Territorial Units for Statistics*, the EU/Eurostat hierarchical classification of regions (Regulation (EC) No 1059/2003). It is used in notices to state *where the work will be performed / goods delivered* ("place of performance").

**Structure (3 levels):**

| Level | Meaning | Population band |
|---|---|---|
| NUTS 1 | major socio-economic regions | 3–7 million |
| NUTS 2 | basic regions (regional policy) | 800k–3 million |
| NUTS 3 | small regions (local analyses) | 150k–800k |

A NUTS code = **2-letter country code (ISO 3166-1 alpha-2) + digits/letters for each level**. More characters = deeper level.

**Your examples (all are NUTS 3):**
- `SI038` → Slovenia, NUTS 3 "Primorsko-notranjska" (SI0 = Slovenija; SI03 = Vzhodna Slovenija; SI038 = Primorsko-notranjska).
- `CZ051` → Czechia, NUTS 3 "Liberecký kraj" (CZ0 = Česko; CZ05 = Severovýchod; CZ051 = Liberecký kraj).
- `DE712` → Germany, NUTS 3 "Frankfurt am Main, Kreisfreie Stadt" (DE7 = Hessen; DE71 = Darmstadt; DE712 = Frankfurt).
- `PL418` → Poland, NUTS 3 "Poznański" (PL4 = Makroregion północno-zachodni; PL41 = Wielkopolskie; PL418 = Poznański).

**Notes:** in small countries the whole country may occupy several levels (e.g. LU0 / LU00 / LU000). "Extra-Regio" codes end in Z/ZZ/ZZZ for territories not attachable to a region. The NUTS **version** matters: the classification is revised periodically (NUTS 2021, 2024, 2027); a code's meaning can change slightly between versions, and older notices use older NUTS versions. For solar notices, the NUTS code tells you **where the panels were installed**, not necessarily where the buyer is based.

---

## 6. Framework Agreement flag and EU Funded flag

**Framework Agreement flag** (CSV: `B_FRA_AGREEMENT` = Y/N; eForms `BT-765` framework / `BT-766` dynamic purchasing system / `BT-768` "contract awarded within a framework").
- `true` (Y) = the notice involves the **establishment of a framework agreement** (an agreement with one or more operators setting terms for future call-offs), or (for an award) that the contract was **awarded within a framework agreement**.
- `false` (N) = no framework agreement.
- A framework award's reported "value" is often an *estimated/ceiling* value rather than money definitely spent, because actual call-offs come later.

**EU Funded flag** (CSV: `B_EU_FUNDS` = Y/N; eForms `BT-60`, codelist `eu-funded` with values `eu-funds` / `no-eu-funds`).
- `true` (Y / `eu-funds`) = the contract is related to a project **partly financed by EU funds** (e.g. ERDF, Recovery/cohesion funds — common for public-body solar programmes).
- `false` (N / `no-eu-funds`) = no EU funds foreseen.
- This is a **declaration by the buyer**, not a verified funding record.

---

## 7. Value fields — Estimated vs Awarded vs "Value Eur" vs "Value Eur Real"

All values in the official TED CSV subset are in **EUR and exclude VAT** (non-EUR notices are converted; see the codebook Annex I).

**Canonical TED CSV value fields:**

| Official field | Meaning | Level |
|---|---|---|
| `VALUE_EURO` | Estimated (or reported) value of the contract/notice, as filled in by the buyer, EUR ex-VAT. | notice (older) / lot (2.0.9) |
| `VALUE_EURO_FIN_1` | **"Final"/cleaned** value: if the value is missing, it is imputed from other fields per Annex I. `[ADDED]` by the EC. | notice / lot |
| `AWARD_EST_VALUE_EURO` | **Estimated** value of the *contract award*, EUR ex-VAT. | contract award |
| `AWARD_VALUE_EURO` | **Total final** value of the *contract award*; if not present, the **lowest bid** is used. | contract award |
| `AWARD_VALUE_EURO_FIN_1` | **"Final"/cleaned** award value (imputed per Annex I if missing). `[ADDED]` | contract award |

**How to read your columns (interpretation — verify against your source):**
- **"Estimated Value"** ≈ `VALUE_EURO_FIN_1` (or `AWARD_EST_VALUE_EURO` at award level): the buyer's *pre-procurement estimate* of what the contract will cost.
- **"Awarded Value"** ≈ `AWARD_VALUE_EURO` / `AWARD_VALUE_EURO_FIN_1`: the **actual final value** of the awarded contract (the sum actually awarded to the winner).
- **"Value Eur"** ≈ the *raw* reported value (what the buyer typed, possibly `VALUE_EURO` or `AWARD_VALUE_EURO`).
- **"Value Eur Real"** ≈ the *cleaned/imputed* "final" value (the `*_FIN_1` concept): the EC's best-available value after filling gaps. In an award export this is the most reliable single figure to use, because it has been reconstructed when the raw value was missing.

**What it means when a value is empty or 0:**
- **Estimated value empty** — the buyer did not report an estimate. Common; the estimate is an optional field. It does *not* mean the contract had no value.
- **Awarded value 0 or empty** — the value was not published (or was marked confidential), or genuinely no award was made. In the CSV subset, if the award value is missing the codebook's imputation falls back to *lowest bid → highest bid → initial estimated value → 0*; a **0** in the cleaned field therefore often means "no usable value reported", not "a €0 contract". The `INFO_ON_NON_AWARD` field flags awards where **no contract was awarded** ("no tenders received or all rejected", or procedure discontinued) — in that case there is legitimately no value.
- **Framework agreements**: the "value" is the *maximum/estimated* value of the framework, not necessarily money spent.

**Multi-lot contracts (Lot Number, e.g. `LOT-0001`).** A notice divided into lots has one row per lot (and per award). The **Lot Number** (`ID_LOT` / "Lot No", e.g. `LOT-0001`, `LOT-0002`…) identifies which lot the row describes. In a lot, the **value** may be stated at lot level (each lot's own value) or only at notice level (total for all lots). When summing values, be careful not to double-count: sum **award-level** values once per award, and treat notice-level values as totals, not per-lot, unless the notice states them per lot.

---

## 8. "Tenders Received" (NUMBER_OFFERS)

- It counts the **"Number of tenders received"** for that contract award — i.e. how many bids/offers the buyer received for that award (not requests to participate).
- It is a **contract-award-level** field: in a multi-lot/multi-award notice, each award row has its own count.
- **Empty / blank** — the buyer did not report the figure. This is very common (an external study of French TED award notices found ~30% of `NUMBER_OFFERS` values missing). Blank = *unknown*, not zero.
- **0** — zero tenders received, or the field was not populated for a direct award. A `neg-wo-call` (negotiated without call) award legitimately has no competitive tenders, so expect 0, 1, or blank there.
- Related fields (in the CSV subset) split the count: `NUMBER_TENDERS_SME`, `NUMBER_TENDERS_OTHER_EU`, `NUMBER_TENDERS_NON_EU`, `NUMBER_OFFERS_ELECTR` (offers received electronically).

---

## 9. "Buyer Country" vs "Source Country"

- **Buyer Country** = the **country of the contracting authority** (the public body making the purchase). In the official CSV subset this is `ISO_COUNTRY_CODE` ("Country" of the first-listed contracting authority; `WIN_COUNTRY_CODE` is the *winner's* country — not the buyer). For a solar award this is where the buying public body is based.
- **Source Country** = *interpretation — flagged as uncertain.* The official `ted-csv` subset has **no** "source country" column; the nearest concepts are:
  - `ISO_COUNTRY_CODE_GPA` — the *legal* (as opposed to geographical) country of the authority, mainly for embassies and WTO Government Procurement Agreement reporting.
  - In derivative/aggregated exports, "source country" usually means the country **from which the notice was published/collected** (the originating feed or the buyer's country as recorded in the OJ S series). For the vast majority of EU procurement notices this is **identical to the buyer country**; it can differ for EU-institution notices, cross-border joint procurement, or when an aggregator labels the data source.
  - Practical advice: treat "Buyer Country" as authoritative for analysis (the buyer's country), and use "Source Country" only to trace provenance. If they differ for a given row, investigate that row specifically (e.g. an EU-institution buyer or a cross-border case).

---

## Sources

All accessed **2026-11-25**.

1. TED CSV subset — dataset page (DG Internal Market, Industry, Entrepreneurship and SMEs), data.europa.eu: https://data.europa.eu/data/datasets/ted-csv?locale=en
2. TED CSV open data — Notes & Codebook v3.6 (2024-01-18) [authoritative field codebook]: https://data.europa.eu/data-management/store/api/legacy/data/ted-csv-data-information-v3-6.pdf/ (mirror: https://data.europa.eu/euodp/repository/ec/dg-grow/mapps/TED(csv)_data_information.pdf)
3. TED advanced notes on methodology (framework agreements/DPS, indicators): https://data.europa.eu/euodp/en/data/storage/f/2022-02-14T122830/TED_advanced_notes_vers_0.92.pdf
4. TED Developers' corner (bulk download, eForms vs TED schema, XML numbering): https://ted.europa.eu/en/simap/developers-corner-for-reusers
5. TED Help — data reuse: https://ted.europa.eu/en/help/data-reuse
6. CPV — Regulation (EC) No 213/2008 (CPV 2008, structure + 09/093 solar codes), EUR-Lex: https://eur-lex.europa.eu/eli/reg/2008/213/oj/eng
7. TED SIMAP — What is the CPV: https://ted.europa.eu/en/simap/cpv
8. TED Developer Docs — `cpv` codelist (eForms): https://docs.ted.europa.eu/eforms/latest/reference/code-lists/cpv.html
9. Contract-nature and procedure-type listIDs — PEPPOL Pre-Award (T011): https://docs.peppol.eu/pracc/transactions/T011/index.html
10. `procurement-procedure-type` codelist — OCDS for eForms (authoritative eForms labels for open/restricted/neg-w-call/neg-wo-call/etc.): https://standard.open-contracting.org/profiles/eforms/latest/en/codelists/procurement-procedure-type/
11. TED Developer Docs — eForms schema, Procedure Type (BT-105) and Tendering Process: https://docs.ted.europa.eu/eforms/latest/schema/procedure-lot-part-information.html
12. TED Developer Docs — eForms schema, EU Funds (BT-60) and Framework Agreement fields: https://docs.ted.europa.eu/eforms/latest/schema/procedure-lot-part-information.html and Competition Results (BT-768): https://docs.ted.europa.eu/eforms/latest/schema/competition-results.html
13. Eurostat — NUTS overview: https://ec.europa.eu/eurostat/web/nuts
14. TED SIMAP — NUTS (how codes are structured): https://ted.europa.eu/en/simap/nuts
15. TED Developer Docs — `nuts` codelist (eForms): https://docs.ted.europa.eu/eforms/latest/reference/code-lists/nuts.html
16. NUTS — Regulation (EC) No 1059/2003, EUR-Lex: https://eur-lex.europa.eu/eli/reg/2003/1059/oj/eng
17. NUTS 2027 amendment — Commission Delegated Regulation (EU) 2026/195, EUR-Lex: https://eur-lex.europa.eu/eli/reg_del/2026/195/oj/eng
18. FOPPA report (French TED award notices; `NUMBER_OFFERS` missing-rate ~30.7%): https://hal.science/hal-03796734v2/file/FOPPA_report.pdf
