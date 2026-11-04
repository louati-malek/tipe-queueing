"""Closed-form steady-state results for M/M/1, M/M/c and M/M/c/K queues.

Notation: arrival rate lam, service rate mu per server, c servers, a = lam/mu (offered load),
rho = lam/(c*mu) (utilisation). K is the maximum number of customers in the system
(waiting + in service); arrivals that find K customers are lost (blocked).
All returned dicts contain: rho, L, Lq, W, Wq, and for finite K also p_block, lam_eff.
"""
from __future__ import annotations

import math

INF = float("inf")


def _unstable(rho: float) -> dict:
    return {"rho": rho, "L": INF, "Lq": INF, "W": INF, "Wq": INF, "p_wait": 1.0}


def erlang_c(c: int, a: float) -> float:
    """Probability that an arrival has to wait in an M/M/c queue (Erlang C formula)."""
    rho = a / c
    if rho >= 1:
        return 1.0
    # sum_{k<c} a^k/k! computed iteratively for numerical stability
    term, s = 1.0, 1.0
    for k in range(1, c):
        term *= a / k
        s += term
    last = term * a / c / (1 - rho)          # a^c / (c! (1 - rho))
    return last / (s + last)


def mmc(lam: float, mu: float, c: int) -> dict:
    rho = lam / (c * mu)
    if rho >= 1:
        return _unstable(rho)
    a = lam / mu
    pw = erlang_c(c, a)
    wq = pw / (c * mu - lam)
    w = wq + 1 / mu
    return {"rho": rho, "L": lam * w, "Lq": lam * wq, "W": w, "Wq": wq, "p_wait": pw}


def mm1(lam: float, mu: float) -> dict:
    """M/M/1 is the special case c = 1: W = 1/(mu - lam), Wq = lam/(mu (mu - lam))."""
    return mmc(lam, mu, 1)


def mmck(lam: float, mu: float, c: int, K: int) -> dict:
    """Finite-capacity queue: stable for any load; a fraction p_block of arrivals is lost."""
    if K < c:
        raise ValueError("K must be >= c")
    a = lam / mu
    # unnormalised p_n
    p = [1.0]
    for n in range(1, K + 1):
        p.append(p[-1] * a / min(n, c))
    z = sum(p)
    p = [x / z for x in p]
    L = sum(n * pn for n, pn in enumerate(p))
    Lq = sum((n - c) * pn for n, pn in enumerate(p) if n > c)
    p_block = p[K]
    lam_eff = lam * (1 - p_block)
    return {"rho": lam / (c * mu), "L": L, "Lq": Lq, "W": L / lam_eff, "Wq": Lq / lam_eff,
            "p_block": p_block, "lam_eff": lam_eff, "p": p}


def servers_needed(lam: float, mu: float, max_rho: float = 0.8) -> int:
    """Smallest c with utilisation lam/(c mu) <= max_rho."""
    return max(1, math.ceil(lam / (mu * max_rho)))
