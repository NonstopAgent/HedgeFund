"""Compare candidate score formulas on the labeled feature rows (no re-download)."""
import json, statistics
from pathlib import Path

rows = json.loads(Path(".data/feature_rows.json").read_text())


def clip(x, lo=0.0, hi=10.0):
    return max(lo, min(hi, x))


def v2(r):
    mom = 0.5 * r["r5"] + 0.3 * r["r10"] + 0.2 * r["r20"]
    m = clip(5 + mom * 40)
    ext = 0.5 * r["ext50"] + 0.5 * r["ext200"]
    t = clip(5 + ext * 40)
    return 0.6 * m + 0.4 * t


def quint(rows, keyfn):
    vals = sorted(rows, key=keyfn)
    n = len(vals); q = max(1, n // 5); out = []
    for b in range(5):
        seg = vals[b * q:(b + 1) * q] if b < 4 else vals[4 * q:]
        out.append((sum(x["win"] for x in seg) / len(seg),
                    statistics.mean(x["pnl"] for x in seg)))
    return out


for name, fn in [("v1 (current)", lambda r: r["score"]), ("v2 (mom+trend)", v2)]:
    qs = quint(rows, fn)
    print(name + ":")
    for i, (w, a) in enumerate(qs):
        print(f"  Q{i+1} win {w:4.0%}  avg {a:+5.2%}")
    print(f"  top-minus-bottom avg-pnl spread = {qs[-1][1]-qs[0][1]:+.2%}\n")
