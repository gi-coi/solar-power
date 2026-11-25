"""Extract a small, representative sample of data/solar_power.csv for human review.

Reads the full file with the csv module (handles BOM + embedded newlines) and
selects a handful of rows that together illustrate the main data features and
issues: the different CPV codes, currencies, contract natures, procedure types,
a multi-contractor award, the -1 sentinel, the 7bn-CZK framework outlier,
embedded newlines, and missing values.

Writes data/solar_power_sample.csv and prints a compact legend of what each
selected row illustrates.
"""

import csv
from collections import Counter

SRC = "data/solar_power.csv"
OUT = "data/solar_power_sample.csv"

with open(SRC, encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

chosen: set[int] = set()
features: dict[int, list[str]] = {}  # row index -> list of feature labels


def add(i: int, feature: str) -> None:
    chosen.add(i)
    features.setdefault(i, []).append(feature)


def add_first(pred, feature: str, n: int = 1) -> None:
    found = 0
    for i, r in enumerate(rows):
        if pred(r) and i not in chosen:
            add(i, feature)
            found += 1
            if found >= n:
                break


# 1. One row per Main CPV code (there are 5).
seen_cpv = set()
for i, r in enumerate(rows):
    c = r["Main Cpv Code"]
    if c and c not in seen_cpv:
        seen_cpv.add(c)
        add(i, f"CPV {c}")

# 2. One row per currency (first 10 distinct).
seen_cur = set()
for i, r in enumerate(rows):
    c = r["Awarded Value Currency"]
    if c and c not in seen_cur:
        seen_cur.add(c)
        add(i, f"currency {c}")
        if len(seen_cur) >= 10:
            break

# 3. Contract nature variety (beyond the dominant "supplies").
add_first(lambda r: r["Contract Nature Code"] == "works", "nature works")
add_first(lambda r: r["Contract Nature Code"] == "services", "nature services")

# 4. Procedure variety (beyond the dominant "open").
add_first(lambda r: r["Procedure Type Code"] == "restricted", "procedure restricted")
add_first(lambda r: r["Procedure Type Code"] == "neg-wo-call", "procedure neg-wo-call")

# 5. A full multi-contractor award (Award ID on 4+ rows) to show denormalisation.
aid_counts = Counter(r["Award ID"] for r in rows)
multi_id = next((a for a, c in aid_counts.items() if c >= 4), None)
if multi_id:
    for i, r in enumerate(rows):
        if r["Award ID"] == multi_id:
            add(i, f"multi-contractor award ({aid_counts[multi_id]} rows)")

# 6. Specific data quirks.
add_first(lambda r: r["Awarded Value"] == "-1", "-1 sentinel (not disclosed)")
add_first(lambda r: r["Framework Agreement"].lower() == "true", "framework = true")
add_first(lambda r: r["Awarded Value"] == "7,000,000,000", "7bn CZK outlier")
add_first(lambda r: "\n" in r["Contract Title"], "embedded newline in title")
add_first(lambda r: r["Awarded Value"] == "", "awarded value empty")
add_first(lambda r: r["Tenders Received"] == "0", "0 tenders received")
add_first(lambda r: r["Award Date"] == "", "award date empty")

# 7. The very first row (Slovenian multi-lot example).
add(0, "first row")

ordered = sorted(chosen)

with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for i in ordered:
        w.writerow(rows[i])

print(f"Wrote {OUT} with {len(ordered)} rows.")
print()
print("Legend (row -> why it was picked):")
for i in ordered:
    label = " | ".join(features[i])
    r = rows[i]
    print(
        f"  #{i:>4}  {r['Doc ID']:<15} {r['Buyer Country']:<3} "
        f"{r['Main Cpv Code']:<8} {r['Procedure Type Code'] or '-':<11} "
        f"{r['Awarded Value Currency'] or '-':<4} {r['Awarded Value'] or '-':>14}  [{label}]"
    )
