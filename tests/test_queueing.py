import math
import os
import subprocess
import sys
from pathlib import Path

import pytest

from queueing import (availability, erlang_c, mm1, mmc, mmck, outage_probability,
                      overload_probability, replicate, servers_needed, simulate)

MU = 1 / 300          # one dossier every 5 minutes per server, as in the original TIPE


def test_erlang_c_known_value():
    # c = 2 servers, offered load a = 1  ->  C = 1/3 (textbook value)
    assert erlang_c(2, 1.0) == pytest.approx(1 / 3)


def test_mmc_with_one_server_is_mm1_formula():
    lam = 1 / 450
    r = mm1(lam, MU)
    assert r["W"] == pytest.approx(1 / (MU - lam))
    assert r["Wq"] == pytest.approx(lam / (MU * (MU - lam)))


def test_littles_law_in_theory():
    for c in (1, 3, 6):
        r = mmc(1 / 250, MU, c) if 1 / 250 < c * MU else None
        if r:
            assert r["L"] == pytest.approx((1 / 250) * r["W"])


def test_unstable_queue_is_infinite():
    assert math.isinf(mm1(1 / 250, MU)["W"])            # rho = 1.2


def test_finite_capacity_converges_to_infinite_model():
    lam = 1 / 450
    assert mmck(lam, MU, 3, 200)["W"] == pytest.approx(mmc(lam, MU, 3)["W"], rel=1e-9)


@pytest.mark.parametrize("c", [1, 3])
def test_simulation_matches_theory(c):
    lam = 1 / 450 if c == 1 else 1 / 120
    th = mmc(lam, MU, c)
    sim = replicate(10, lam=lam, mu=MU, c=c, horizon=2e6, warmup=5e4, seed=10)
    for m in ("W", "Wq", "L"):
        mean, half = sim[m]
        assert abs(mean - th[m]) <= max(3 * half, 0.05 * th[m]), m


def test_simulated_blocking_matches_theory():
    lam, K = 1 / 250, 10                                  # original 'saturated' scenario, rho = 1.2
    th = mmck(lam, MU, 1, K)
    sim = replicate(10, lam=lam, mu=MU, c=1, K=K, horizon=2e6, warmup=5e4, seed=3)
    mean, half = sim["p_block"]
    assert abs(mean - th["p_block"]) <= max(3 * half, 0.01)


def test_zero_waits_are_recorded():
    r = simulate(1 / 900, MU, c=6, horizon=1e5, seed=0)
    assert (r.waits == 0).mean() > 0.9                   # with 6 servers almost nobody waits


def test_reliability():
    A = availability(500, 5)
    assert outage_probability(1, A) == pytest.approx(1 - A)
    assert outage_probability(6, A) == pytest.approx((1 - A) ** 6)
    assert overload_probability(0, MU, 3, A) == pytest.approx((1 - A) ** 3)  # only k=0 overloads


def test_servers_needed():
    assert servers_needed(1 / 250, MU, max_rho=0.8) == 2


def test_run_all_writes_utf8_summary():
    # Regression: on Windows the default encoding (cp1252) has no λ/ρ, so writing summary.md crashed
    # and left it empty. Run with UTF-8 mode off and stdout piped, as in VS Code or CI.
    root = Path(__file__).resolve().parents[1]
    env = {**os.environ, "PYTHONUTF8": "0", "MPLBACKEND": "Agg"}
    env.pop("PYTHONIOENCODING", None)
    proc = subprocess.run([sys.executable, "-m", "experiments.run_all"], cwd=root, env=env,
                          capture_output=True, timeout=300)
    assert proc.returncode == 0, proc.stderr.decode(errors="replace")
    summary = (root / "results" / "summary.md").read_text(encoding="utf-8")
    assert "λ" in summary and "## 6." in summary


def test_cpp_simulator_matches_theory():
    from queueing.cpp_bridge import find_binary, run_cpp, summarise
    if find_binary() is None:
        pytest.skip("C++ simulator not built (see cpp/README.md)")
    lam = 1 / 250
    rows = run_cpp(lam, MU, c=3, reps=20, seed=1)
    mean, half = summarise(rows, "W")
    assert abs(mean - mmc(lam, MU, 3)["W"]) <= max(3 * half, 0.02 * mean)
    rows = run_cpp(lam, MU, c=1, K=10, reps=20, seed=2)
    mean, half = summarise(rows, "p_block")
    assert abs(mean - mmck(lam, MU, 1, 10)["p_block"]) <= max(3 * half, 0.01)
