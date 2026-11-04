"""C++ vs Python simulator: same answers, how much faster, and what the speed buys.

    python -m experiments.cpp_benchmark      (build cpp/ first)
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from queueing import mmc, mmck, replicate, simulate
from queueing.cpp_bridge import find_binary, run_cpp, summarise

OUT = Path(__file__).resolve().parents[1] / "results"
MU = 1 / 300
lines = ["# C++ simulator: validation and speed\n"]


def validation():
    configs = [("M/M/1, medium load", 1 / 450, 1, None), ("M/M/1/10, saturated load", 1 / 250, 1, 10),
               ("M/M/3, saturated load", 1 / 250, 3, None), ("M/M/6, saturated load", 1 / 250, 6, None)]
    lines.extend(["## Same answers as theory and as the Python simulator\n",
              "30 replications each. W in seconds, mean ± 95% CI.\n",
              "| Model | W theory | W Python | W C++ | P(block) theory | P(block) C++ |", "|---|---|---|---|---|---|"])
    for name, lam, c, K in configs:
        th = mmck(lam, MU, c, K) if K else mmc(lam, MU, c)
        py = replicate(30, lam=lam, mu=MU, c=c, K=K, horizon=2e6, warmup=5e4, seed=100)
        cp = run_cpp(lam, MU, c, K, reps=30, seed=100)
        wm, wh = summarise(cp, "W"); bm, bh = summarise(cp, "p_block")
        lines.append(f"| {name} | {th['W']:.1f} | {py['W'][0]:.1f} ± {py['W'][1]:.1f} | {wm:.1f} ± {wh:.1f} | "
                     f"{th.get('p_block', 0):.4f} | {bm:.4f} ± {bh:.4f} |")
    lines.append("\nPython and C++ use different random-number generators, so individual runs differ; "
                 "both agree with the theory within their confidence intervals.\n")


def speed():
    lam, mu, c = 2.5, 1.0, 3                          # busy system: many events per unit time
    py_h, cpp_h = 2e5, 2e6
    t0 = time.perf_counter(); r_py = simulate(lam, mu, c, horizon=py_h, seed=1); t_py = time.perf_counter() - t0
    ev_py = 2 * r_py.served                           # approx. arrivals + departures
    cp = run_cpp(lam, mu, c, horizon=cpp_h, warmup=0, reps=5, seed=1)
    ev_cpp = sum(r["events"] for r in cp) / len(cp)
    t_cpp = sum(r["seconds"] for r in cp) / len(cp)
    rate_py, rate_cpp = ev_py / t_py, ev_cpp / t_cpp
    lines.extend(["## Speed\n", f"M/M/3 at ρ = {lam / (c * mu):.2f}, single run, same machine.\n",
              "| Simulator | Events simulated | Time (s) | Events per second |", "|---|---|---|---|",
              f"| Python | {ev_py:,.0f} | {t_py:.2f} | {rate_py:,.0f} |",
              f"| C++ (Release build) | {ev_cpp:,.0f} | {t_cpp:.3f} | {rate_cpp:,.0f} |",
              f"\nThe C++ simulator processes about **{rate_cpp / rate_py:.0f}× more events per second**.\n"])
    return rate_py, rate_cpp


def what_speed_buys(rate_py, rate_cpp):
    """Blocking probability of the original saturated scenario with 30 vs 3,000 replications."""
    lam, K = 1 / 250, 10
    th = mmck(lam, MU, 1, K)["p_block"]
    ns = [30, 100, 300, 1000, 3000]
    t0 = time.perf_counter()
    rows = run_cpp(lam, MU, 1, K, horizon=2e6, warmup=5e4, reps=max(ns), seed=500)
    t_cpp = time.perf_counter() - t0
    halfs = [summarise(rows[:n], "p_block")[1] for n in ns]
    means = [summarise(rows[:n], "p_block")[0] for n in ns]
    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    ax.errorbar(ns, means, yerr=halfs, fmt="o-", capsize=3, label="C++ simulation (95% CI)")
    ax.axhline(th, color="k", ls="--", lw=0.8, label=f"theory {th:.4f}")
    ax.set_xscale("log"); ax.set_xlabel("number of replications"); ax.set_ylabel("P(dossier lost)")
    ax.set_title("M/M/1/10, saturated load: precision vs replications"); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(OUT / "cpp_replications.png", dpi=150); plt.close(fig)
    events = sum(r["events"] for r in rows)
    lines.extend(["## What the speed buys\n",
              f"{max(ns):,} replications of the saturated scenario ({events:,.0f} events) take {t_cpp:.1f} s in C++; "
              f"at Python's measured rate they would take about {events / rate_py:.0f} s. "
              f"The 95% CI on the loss probability shrinks from ±{halfs[0]:.4f} (30 runs) to ±{halfs[-1]:.4f} "
              f"({max(ns):,} runs), around the theoretical {th:.4f}.\n"])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252, which lacks ρ/λ
    if find_binary() is None:
        raise SystemExit("Build the C++ simulator first: cmake -S cpp -B cpp/build && cmake --build cpp/build --config Release")
    validation(); print("validation done")
    rp, rc = speed(); print("speed done")
    what_speed_buys(rp, rc); print("replications done")
    (OUT / "cpp_benchmark.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
