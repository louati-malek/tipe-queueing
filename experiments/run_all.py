"""Run every experiment and write figures + tables to results/.

    python -m experiments.run_all          (from the project root)

Takes about 1–2 minutes.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from queueing import (availability, mm1, mmc, mmck, outage_probability, overload_probability,
                      replicate, servers_needed, simulate)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results"
OUT.mkdir(exist_ok=True)

MU = 1 / 300                      # service rate per server: 5 min per dossier (original assumption)
DAY = 8 * 3600                    # 8-hour working day (original assumption)
SCENARIOS = {"low": 1 / 900, "medium": 1 / 450, "saturated": 1 / 250}   # original arrival rates (1/s)
K_ORIG = 10                       # original capacity limit (server + queue)
REPS, HORIZON, WARMUP = 30, 2e6, 5e4
COLORS = {1: "tab:red", 3: "tab:blue", 6: "tab:green"}
lines: list[str] = []             # markdown summary


def save(fig, name):
    fig.tight_layout()
    fig.savefig(OUT / name, dpi=150)
    plt.close(fig)


def fmt(m, h):
    return f"{m:.4g} ± {h:.2g}"


# ---------------------------------------------------------------- 1. validation
def validation():
    configs = [
        ("M/M/1, medium load", SCENARIOS["medium"], 1, None),
        ("M/M/1/10, saturated load", SCENARIOS["saturated"], 1, K_ORIG),
        ("M/M/3, saturated load", SCENARIOS["saturated"], 3, None),
        ("M/M/6, saturated load", SCENARIOS["saturated"], 6, None),
    ]
    lines.append("## 1. Simulation vs theory\n")
    lines.append(f"{REPS} replications of {HORIZON:.0e} s each (warm-up {WARMUP:.0e} s). Simulated values are mean ± 95% CI.\n")
    lines.append("| Model | rho | W theory (s) | W simulated (s) | Wq theory (s) | Wq simulated (s) | P(block) theory | P(block) simulated |")
    lines.append("|---|---|---|---|---|---|---|---|")
    rows = []
    for name, lam, c, K in configs:
        th = mmck(lam, MU, c, K) if K else mmc(lam, MU, c)
        sim = replicate(REPS, lam=lam, mu=MU, c=c, K=K, horizon=HORIZON, warmup=WARMUP, seed=100)
        pb = th.get("p_block", 0.0)
        lines.append(f"| {name} | {lam / (c * MU):.2f} | {th['W']:.4g} | {fmt(*sim['W'])} | {th['Wq']:.4g} | "
                     f"{fmt(*sim['Wq'])} | {pb:.4f} | {fmt(*sim['p_block'])} |")
        rows.append([name, th["W"], *sim["W"], th["Wq"], *sim["Wq"], pb, *sim["p_block"]])
    with open(OUT / "validation.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["model", "W_theory", "W_sim", "W_ci", "Wq_theory", "Wq_sim", "Wq_ci",
                    "pblock_theory", "pblock_sim", "pblock_ci"])
        w.writerows(rows)
    lines.append("")


# ------------------------------------------------- 2. why one 8-hour run is not enough
def single_day_noise():
    lam = SCENARIOS["medium"]
    th = mm1(lam, MU)["Wq"]
    daily = np.array([simulate(lam, MU, 1, horizon=DAY, seed=s).Wq for s in range(2000)])
    daily = daily[~np.isnan(daily)]
    lo, hi = np.percentile(daily, [5, 95])
    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    ax.hist(daily / 60, bins=60, color="tab:blue", alpha=0.75)
    ax.axvline(th / 60, color="k", ls="--", label=f"theory: {th / 60:.0f} min")
    ax.set_xlabel("mean waiting time over one 8-hour day (min)")
    ax.set_ylabel("number of simulated days")
    ax.set_title("M/M/1, medium load: 2,000 independent single-day runs")
    ax.legend()
    save(fig, "single_day_noise.png")
    lines.append("## 2. One simulated day is not enough\n")
    lines.append(f"Medium load gives about {lam * DAY:.0f} dossiers per day. Over 2,000 independent one-day runs, the daily "
                 f"mean waiting time ranges from {lo / 60:.1f} to {hi / 60:.1f} min (5th–95th percentile), around a "
                 f"theoretical value of {th / 60:.1f} min. A single run, as in the original TIPE, cannot estimate the mean.\n")


# ------------------------------------------------ 3. same demand, more servers
def same_demand():
    lam_grid = np.linspace(1e-5, 0.0175, 400)               # arrivals per second
    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    for c in (1, 3, 6):
        W = [mmc(l, MU, c)["W"] / 60 for l in lam_grid]
        ax.plot(lam_grid * 3600, W, color=COLORS[c], label=f"M/M/{c} (theory)")
    for name, lam in SCENARIOS.items():
        for c in (1, 3, 6):
            if lam < c * MU:
                m, h = replicate(10, lam=lam, mu=MU, c=c, horizon=HORIZON, warmup=WARMUP, seed=7)["W"]
                ax.errorbar(lam * 3600, m / 60, yerr=h / 60, fmt="o", color=COLORS[c], ms=4, capsize=2)
        ax.axvline(lam * 3600, color="grey", lw=0.6, ls=":")
        ax.text(lam * 3600, 58, name, rotation=90, fontsize=7, va="top", ha="right", color="grey")
    ax.set_ylim(0, 60)
    ax.set_xlabel("arrivals per hour (λ)")
    ax.set_ylabel("mean time in system W (min)")
    ax.set_title("Same demand, more servers (μ = 12 dossiers/h per server)")
    ax.legend(fontsize=8)
    save(fig, "same_demand.png")
    lines.append("## 3. Same demand, 1 vs 3 vs 6 servers\n")
    lines.append("| Scenario | λ (dossiers/h) | W M/M/1 (min) | W M/M/3 (min) | W M/M/6 (min) |")
    lines.append("|---|---|---|---|---|")
    for name, lam in SCENARIOS.items():
        ws = [mmc(lam, MU, c)["W"] / 60 for c in (1, 3, 6)]
        lines.append(f"| {name} | {lam * 3600:.1f} | " + " | ".join("unstable" if np.isinf(w) else f"{w:.1f}" for w in ws) + " |")
    lines.append("\nThis is the comparison made in the TIPE. The gain is real, but it comes from adding capacity: "
                 "3 servers can process 3 times more dossiers.\n")


# ------------------------------------------- 4. same total capacity (fair comparison)
def equal_capacity(c=6):
    rho = np.linspace(0.05, 0.97, 300)
    lam = rho * c * MU
    W_fast = np.array([mm1(l, c * MU)["W"] for l in lam])
    W_dec = np.array([mmc(l, MU, c)["W"] for l in lam])
    Wq_fast = np.array([mm1(l, c * MU)["Wq"] for l in lam])
    Wq_dec = np.array([mmc(l, MU, c)["Wq"] for l in lam])
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
    axes[0].plot(rho, W_fast / 60, "tab:red", label=f"1 server, {c}× faster")
    axes[0].plot(rho, W_dec / 60, "tab:green", label=f"{c} servers in parallel")
    axes[0].set_title("Mean time in system W")
    axes[1].plot(rho, Wq_fast / 60, "tab:red", label=f"1 server, {c}× faster")
    axes[1].plot(rho, Wq_dec / 60, "tab:green", label=f"{c} servers in parallel")
    axes[1].set_title("Mean waiting time in queue Wq")
    for ax in axes:
        ax.set_xlabel("utilisation ρ (same total capacity)")
        ax.set_ylabel("minutes"); ax.set_ylim(0, 30); ax.legend(fontsize=8)
    save(fig, "equal_capacity.png")
    i = np.argmin(abs(rho - 0.8))
    lines.append("## 4. Fair comparison: same total capacity\n")
    lines.append(f"At utilisation 0.8 with the same total capacity ({c} dossiers per 5 min): one fast server gives "
                 f"W = {W_fast[i] / 60:.1f} min, {c} parallel servers give W = {W_dec[i] / 60:.1f} min. "
                 f"Queueing time is lower with parallel servers (Wq {Wq_dec[i] / 60:.1f} vs {Wq_fast[i] / 60:.1f} min), "
                 "but each dossier is served more slowly, so the total time is higher. Decentralising does not reduce "
                 "delay by itself; its advantage is resilience (next section).\n")


# --------------------------------------------------------------- 5. resilience
def resilience(c=6, mtbf_h=720.0, mttr_h=8.0):
    A = availability(mtbf_h, mttr_h)
    lam_grid = np.linspace(0.0005, c * MU * 0.99, 300)
    p_central = [overload_probability(l, c * MU, 1, A) for l in lam_grid]   # one big server
    p_dec = [overload_probability(l, MU, c, A) for l in lam_grid]           # c small servers
    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    ax.semilogy(lam_grid * 3600, p_central, "tab:red", label="centralised: 1 server, 6× faster")
    ax.semilogy(lam_grid * 3600, np.maximum(p_dec, 1e-14), "tab:green", label="decentralised: 6 servers")
    ax.set_xlabel("arrivals per hour (λ)")
    ax.set_ylabel("P(capacity up < demand)")
    ax.set_title(f"Probability of overload under failures (MTBF {mtbf_h:.0f} h, MTTR {mttr_h:.0f} h)")
    ax.legend(fontsize=8)
    save(fig, "resilience.png")
    out_c, out_d = outage_probability(1, A), outage_probability(c, A)
    lines.append("## 5. Resilience under server failures\n")
    lines.append(f"Illustrative values: each server fails on average every {mtbf_h:.0f} h and takes {mttr_h:.0f} h to repair "
                 f"(availability {A:.4f}).\n")
    lines.append("| Architecture | P(total outage) | Expected hours of total outage per year |")
    lines.append("|---|---|---|")
    lines.append(f"| Centralised (1 server) | {out_c:.2e} | {out_c * 8760:.1f} |")
    lines.append(f"| Decentralised ({c} servers) | {out_d:.2e} | {out_d * 8760:.2e} |")
    lines.append("\nWith the same total capacity, total outages practically disappear, and partial failures only "
                 "reduce capacity. This is the real argument for decentralisation. The figure shows the limit: above "
                 f"{(c - 1) * MU * 3600:.0f} arrivals per hour, losing any one of the {c} servers already causes overload, "
                 "so the decentralised system becomes *more* fragile than the centralised one. Decentralisation "
                 "only pays off with spare capacity (N+1 redundancy).\n")


# ---------------------------------------------------------------- 6. sizing
def sizing():
    """Servers needed for rho <= 0.8 as a function of processing time, for hypothetical daily volumes."""
    volumes = {f"{SCENARIOS['saturated'] * DAY:.0f}/day (TIPE 'saturated')": SCENARIOS["saturated"] * DAY,
               "1,000/day": 1000.0, "10,000/day": 10000.0}
    service = np.logspace(np.log10(0.5), np.log10(300), 200)
    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    for (label, vol), col in zip(volumes.items(), ("tab:red", "tab:blue", "tab:purple")):
        ax.loglog(service, [servers_needed(vol / DAY, 1 / s, 0.8) for s in service], color=col, label=label)
    ax.axvline(300, color="grey", ls=":"); ax.text(290, 1.2, "TIPE assumption\n(300 s)", fontsize=7, ha="right")
    ax.set_xlabel("mean processing time per dossier (s)")
    ax.set_ylabel("servers needed for ρ ≤ 0.8")
    ax.set_title("Sizing: servers needed vs processing time (8-hour day)")
    ax.legend(fontsize=8)
    save(fig, "sizing.png")
    lines.append("## 6. Sizing: how many servers for a given volume?\n")
    lines.append("Hypothetical daily volumes over an 8-hour day, keeping ρ ≤ 0.8. These are not measurements.\n")
    lines.append("| Daily volume | λ (per h) | servers at 300 s | servers at 30 s | servers at 1 s |")
    lines.append("|---|---|---|---|---|")
    for label, vol in volumes.items():
        lam = vol / DAY
        lines.append(f"| {label} | {lam * 3600:,.1f} | " +
                     " | ".join(str(servers_needed(lam, 1 / s, 0.8)) for s in (300, 30, 1)) + " |")
    lines.append("\nThe TIPE scenarios were not calibrated against measured traffic. The required number of servers "
                 "scales with volume × processing time, so both must be measured before drawing conclusions about a "
                 "real platform.\n")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252, which lacks ρ/λ
    lines.append("# Results\n")
    validation(); print("1 validation done")
    single_day_noise(); print("2 single-day done")
    same_demand(); print("3 same demand done")
    equal_capacity(); print("4 equal capacity done")
    resilience(); print("5 resilience done")
    sizing(); print("6 sizing done")
    (OUT / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
