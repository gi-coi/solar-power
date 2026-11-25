import csv, io, collections, statistics, re, sys

PATH = "/Users/giovannacoi/Documents/ARENA course/solar-power/data/solar_power.csv"

raw = open(PATH, "rb").read()
print("RAW BYTES:", len(raw))
print("BOM:", raw[:3] == b"\xef\xbb\xbf")
print("First 3 bytes hex:", raw[:3].hex())

text = raw.decode("utf-8-sig")  # strips BOM
lines = text.splitlines()
print("Total lines (incl header):", len(lines))
header_line = lines[0]
print("Header raw:", repr(header_line[:200]))

# Parse with csv
reader = csv.reader(io.StringIO(text))
rows = list(reader)
header = rows[0]
data = rows[1:]
print("Header fields count:", len(header))
print("Data rows (from csv):", len(data))

print("\n=== HEADER (one per line) ===")
for i, h in enumerate(header):
    print(f"{i:2d}: {h!r}")

# Check row lengths
lengths = collections.Counter(len(r) for r in data)
print("\nRow length distribution:", dict(lengths))

# Trim/pad rows to header length for safety
bad_rows = [i for i, r in enumerate(data) if len(r) != len(header)]
print("Rows with mismatched field count:", len(bad_rows), "indices (first 20):", bad_rows[:20])

# Build dict per row, pad with None
def safe_row(r):
    d = {}
    for j, h in enumerate(header):
        d[h] = r[j] if j < len(r) else None
    return d

# Numeric columns of interest
num_cols = ["Estimated Value", "Awarded Value", "Value Eur", "Value Eur Real", "Tenders Received",
            "Award ID", "Contract ID", "Doc ID"]

def to_num(s):
    if s is None:
        return None
    s = s.strip()
    if s == "":
        return None
    # remove quotes, thousand separators (commas), spaces
    t = s.replace('"', '').replace("'", '').replace(",", "").replace(" ", "").replace("\xa0", "")
    if t == "":
        return None
    try:
        return float(t)
    except ValueError:
        return None

print("\n=== NUMERIC COLUMN ANALYSIS ===")
for col in num_cols:
    vals = [safe_row(r)[col] for r in data]
    nonempty = [v for v in vals if v is not None and v.strip() != ""]
    nums = [to_num(v) for v in nonempty]
    parsed = [n for n in nums if n is not None]
    unparsed = [v for v in nonempty if to_num(v) is None]
    print(f"\n--- {col} ---")
    print(f"  non-empty: {len(nonempty)} ({100*len(nonempty)/len(data):.2f}%)  empty: {len(data)-len(nonempty)}")
    print(f"  parsed numeric: {len(parsed)}  unparseable: {len(unparsed)}")
    if unparsed:
        print("  unparseable samples:", unparsed[:10])
    if parsed:
        print(f"  min={min(parsed):.6g} max={max(parsed):.6g} mean={statistics.mean(parsed):.6g} median={statistics.median(parsed):.6g}")
        print(f"  sum={sum(parsed):.6g}")
        ints = [p for p in parsed if p == int(p)]
        print(f"  integers: {len(ints)}  non-integers: {len(parsed)-len(ints)}")
        print(f"  zeros: {sum(1 for p in parsed if p==0)}  negatives: {sum(1 for p in parsed if p<0)}")
    # raw value sample
    print("  raw samples:", nonempty[:6])

# Categorical columns
cat_cols = ["Source Country", "Buyer Country", "Main Cpv Code", "Contract Nature Code",
            "Procedure Type Code", "Framework Agreement", "Eu Funded",
            "Estimated Value Currency", "Awarded Value Currency"]

print("\n\n=== CATEGORICAL COLUMN DISTRIBUTIONS ===")
for col in cat_cols:
    vals = [safe_row(r)[col] for r in data]
    c = collections.Counter("" if (v is None or v.strip()=="") else v.strip() for v in vals)
    total = sum(c.values())
    print(f"\n--- {col} (top 25 of {len(c)} unique) ---")
    for k, v in c.most_common(25):
        print(f"  {k!r}: {v} ({100*v/total:.2f}%)")

# Date analysis
print("\n\n=== DATE ANALYSIS ===")
for col in ["Publication Date", "Award Date"]:
    vals = [safe_row(r)[col] for r in data]
    nonempty = [v.strip() for v in vals if v is not None and v.strip() != ""]
    empty = len(vals) - len(nonempty)
    print(f"\n--- {col} ---")
    print(f"  non-empty: {len(nonempty)}  empty: {empty}")
    # detect format patterns
    patterns = collections.Counter()
    for v in nonempty:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
            patterns["ISO YYYY-MM-DD"] += 1
        elif re.fullmatch(r"\d{2}/\d{2}/\d{4}", v):
            patterns["DD/MM/YYYY"] += 1
        elif re.fullmatch(r"\d{4}/\d{2}/\d{2}", v):
            patterns["YYYY/MM/DD"] += 1
        elif re.fullmatch(r"[A-Z][a-z]+ \d{1,2}, \d{4}", v):
            patterns["Month D, YYYY"] += 1
        else:
            patterns["other: " + v] += 1
    print("  patterns:", dict(list(patterns.items())[:15]))
    # month/year range for the Month D, YYYY format
    if any("Month" in k for k in patterns):
        print("  Month-name samples:", nonempty[:3], nonempty[-3:])

# Uniqueness
print("\n\n=== UNIQUENESS ===")
for col in ["Award ID", "Contract ID", "Doc ID"]:
    vals = [safe_row(r)[col] for r in data]
    nonempty = [v.strip() for v in vals if v is not None and v.strip() != ""]
    # normalize award/contract id by removing commas for uniqueness
    norm = [v.replace(",", "").replace('"','').strip() for v in nonempty]
    print(f"{col}: non-empty={len(nonempty)} unique_raw={len(set(nonempty))} unique_normalized={len(set(norm))}")

# org names
org_col = "Organizations \u2012 Official Name"
# find actual org column
org_cols = [h for h in header if "Official Name" in h]
print("Org name columns found:", org_cols)
if org_cols:
    col = org_cols[0]
    vals = [safe_row(r)[col] for r in data]
    nonempty = [v.strip() for v in vals if v is not None and v.strip() != ""]
    print("Organizations Official Name: non-empty", len(nonempty), "unique", len(set(nonempty)))

# Duplicate rows
print("\n\n=== DUPLICATES ===")
full_rows = [tuple(r) for r in data]
full_dup = collections.Counter(full_rows)
dup_full = sum(1 for k,v in full_dup.items() if v>1)
extra_full = sum(v-1 for k,v in full_dup.items() if v>1)
print(f"full-row duplicates: {dup_full} duplicated groups, {extra_full} excess rows")

# duplicated award IDs
award_idx = header.index("Award ID")
aid = [r[award_idx].replace(',','').replace('"','').strip() if len(r)>award_idx else "" for r in data]
aid_nonempty = [a for a in aid if a]
c = collections.Counter(aid_nonempty)
dup_aid = {k:v for k,v in c.items() if v>1}
print(f"duplicated Award IDs: {len(dup_aid)} IDs appear more than once; excess rows={sum(v-1 for v in dup_aid.values())}")
print("sample duplicated Award IDs:", list(dup_aid.items())[:10])

# Top buyers
print("\n\n=== TOP BUYERS ===")
buyer_idx = header.index("Buyer Name")
buyer_country_idx = header.index("Buyer Country")
# aggregate awarded value
av_idx = header.index("Awarded Value")
bv = collections.defaultdict(lambda: [0, 0.0])  # name -> [count, total value]
for r in data:
    name = r[buyer_idx].strip() if len(r)>buyer_idx else ""
    if not name:
        name = "(empty)"
    v = to_num(r[av_idx]) if len(r)>av_idx else None
    bv[name][0] += 1
    if v is not None:
        bv[name][1] += v
by_count = sorted(bv.items(), key=lambda x: -x[1][0])[:15]
by_value = sorted(bv.items(), key=lambda x: -x[1][1])[:15]
print("Top 15 buyers by award count:")
for name, (c_, v) in by_count:
    print(f"  {name!r}: {c_} awards, value sum {v:.0f}")
print("Top 15 buyers by total awarded value:")
for name, (c_, v) in by_value:
    print(f"  {name!r}: {c_} awards, value sum {v:.0f}")

# Encoding check: scan for replacement chars or control chars
print("\n\n=== ENCODING / CHARACTER ISSUES ===")
bad_chars = collections.Counter()
for r in data:
    for f in r:
        for ch in f:
            o = ord(ch)
            if o == 0xfffd:
                bad_chars["REPLACEMENT CHAR \\ufffd"] += 1
            elif o < 32 and ch not in "\t":
                bad_chars[f"control 0x{o:02x}"] += 1
print("bad char counts:", dict(bad_chars))
# detect embedded newline in fields (rows with more/less fields already flagged)

# Lot Number / other id cols
print("\n\n=== LOT NUMBER ===")
if "Lot Number" in header:
    li = header.index("Lot Number")
    lots = [r[li].strip() if len(r)>li else "" for r in data]
    lc = collections.Counter(lots)
    print("non-empty lots:", sum(1 for l in lots if l), "unique:", len(set(l for l in lots if l)))
    print("top 10:", lc.most_common(10))

# Estimated vs Awarded currency mixes
print("\n\n=== CURRENCY SUMMARY ===")
for col in ["Estimated Value Currency", "Awarded Value Currency"]:
    vals = [safe_row(r)[col] for r in data]
    c = collections.Counter("" if (v is None or v.strip()=="") else v.strip().upper() for v in vals)
    print(col, ":", dict(c.most_common(20)))
