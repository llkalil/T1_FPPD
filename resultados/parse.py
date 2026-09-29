"""Uso: python parse.py <pasta com results.csv>  ->  <pasta>/summary.csv e <pasta>/summary.md"""
import csv, statistics as st, sys
from collections import defaultdict
from pathlib import Path

d = Path(sys.argv[1])
rows = [r for r in csv.reader((d / "results.csv").open(encoding="utf-8")) if r and r[0].startswith("V")]
g = defaultdict(list)
for v, n, status, tot, wavg, wmax, eat, cyc in rows:
    g[(v, int(n))].append((status, float(tot), float(wavg), float(wmax), int(eat), [int(c) for c in cyc.split(";")]))

def ms(xs):  # média, desvio, min, max
    return (st.mean(xs), st.stdev(xs) if len(xs) > 1 else 0.0, min(xs), max(xs))

hdr = ["versao", "n", "execucoes", "ok", "deadlocks", "total_ms_media", "total_ms_dp", "total_ms_min", "total_ms_max",
       "espera_media_ms", "espera_max_ms_pior", "max_comendo", "ciclos_min", "ciclos_max"]
out = []
for (v, n) in sorted(g):
    ok = [r for r in g[(v, n)] if r[0] == "OK"]
    dead = len(g[(v, n)]) - len(ok)
    row = [v, n, len(g[(v, n)]), len(ok), dead]
    if ok:
        t = ms([r[1] for r in ok])
        row += [f"{t[0]:.1f}", f"{t[1]:.1f}", f"{t[2]:.1f}", f"{t[3]:.1f}",
                f"{st.mean(r[2] for r in ok):.3f}", f"{max(r[3] for r in ok):.3f}", max(r[4] for r in ok),
                min(min(r[5]) for r in ok), max(max(r[5]) for r in ok)]
    else:  # só deadlocks: ciclos parciais no momento do travamento
        row += ["-"] * 7 + [min(min(r[5]) for r in g[(v, n)]), max(max(r[5]) for r in g[(v, n)])]
    out.append(row)

with (d / "summary.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(hdr); w.writerows(out)
with (d / "summary.md").open("w", encoding="utf-8") as f:
    f.write("| " + " | ".join(hdr) + " |\n|" + "---|" * len(hdr) + "\n")
    for r in out:
        f.write("| " + " | ".join(map(str, r)) + " |\n")
print((d / "summary.md").read_text(encoding="utf-8"))
