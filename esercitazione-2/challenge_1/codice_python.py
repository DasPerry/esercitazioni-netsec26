import csv, statistics as st
import numpy as np
from collections import defaultdict

ANCHOR, HZ = 161, 250
rows = defaultdict(list)
with open("ts.csv") as f:
    for d in csv.DictReader(f):
        rows[int(d["tcp.stream"])].append(
            (float(d["frame.time_relative"]),
             int(d["tcp.options.timestamp.tsval"])))

off = {s: st.median(ts - HZ * t for t, ts in pts) for s, pts in rows.items()}
ref = off[ANCHOR]

# 1) gruppo provvisorio
group = [s for s, o in off.items() if abs(o - ref) < 50]
print("gruppo provvisorio:", len(group), "stream")

# 2) retta sui punti del gruppo: TSval = a*t + b
T = np.array([t for s in group for t, ts in rows[s]])
V = np.array([ts for s in group for t, ts in rows[s]], dtype=float)
a, b = np.polyfit(T, V, 1)
print(f"hz reale ~ {a:.4f}")

# 3) residui di TUTTI gli stream rispetto alla retta
res = {s: st.median(ts - (a * t + b) for t, ts in pts) for s, pts in rows.items()}
ordered = sorted((abs(r), s) for s, r in res.items())
for r, s in ordered[:40]:
    print(f"{r:>12.1f}  stream {s}")

final = sorted(s for r, s in ordered if r < 5)
print("\nstream finali:", len(final))
print(" ".join(map(str, final)))
