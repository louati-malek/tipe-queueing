"""Run the C++ simulator (cpp/) from Python and read its CSV output.

Build it first:  cmake -S cpp -B cpp/build  &&  cmake --build cpp/build --config Release
"""
from __future__ import annotations

import csv
import io
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = [
    ROOT / "cpp" / "build" / "mmck_sim",
    ROOT / "cpp" / "build" / "mmck_sim.exe",
    ROOT / "cpp" / "build" / "Release" / "mmck_sim.exe",     # Visual Studio generator
    ROOT / "cpp" / "build" / "Debug" / "mmck_sim.exe",
]


def find_binary() -> Path | None:
    return next((p for p in CANDIDATES if p.exists()), None)


def run_cpp(lam: float, mu: float, c: int = 1, K: int | None = None, horizon: float = 2e6,
            warmup: float = 5e4, reps: int = 30, seed: int = 0) -> list[dict]:
    exe = find_binary()
    if exe is None:
        raise FileNotFoundError("C++ simulator not built: see cpp/README.md")
    args = [str(exe), "--lam", repr(lam), "--mu", repr(mu), "--c", str(c), "--K", str(K if K else -1),
            "--horizon", repr(horizon), "--warmup", repr(warmup), "--reps", str(reps), "--seed", str(seed)]
    out = subprocess.run(args, capture_output=True, text=True, check=True).stdout
    return [{k: float(v) for k, v in row.items()} for row in csv.DictReader(io.StringIO(out))]


def summarise(rows: list[dict], metric: str) -> tuple[float, float]:
    """Mean and 95% CI half-width over replications."""
    x = [r[metric] for r in rows]
    n = len(x)
    m = sum(x) / n
    if n < 2:
        return m, float("nan")
    sd = math.sqrt(sum((v - m) ** 2 for v in x) / (n - 1))
    try:
        from scipy.stats import t
        q = float(t.ppf(0.975, n - 1))
    except ImportError:
        q = 1.96
    return m, q * sd / math.sqrt(n)
