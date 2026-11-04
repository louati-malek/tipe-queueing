"""Resilience of centralised vs decentralised architectures under server failures.

Each server alternates between 'up' and 'down' with mean time between failures MTBF and
mean time to repair MTTR (independent servers). Availability of one server:
    A = MTBF / (MTBF + MTTR)
With c independent servers, the number of servers up follows Binomial(c, A).
Quasi-static approximation: failures are much slower than arrivals, so while k servers are
up the system behaves like an M/M/k queue.
"""
from __future__ import annotations

from math import comb


def availability(mtbf: float, mttr: float) -> float:
    return mtbf / (mtbf + mttr)


def up_distribution(c: int, A: float) -> list[float]:
    return [comb(c, k) * A ** k * (1 - A) ** (c - k) for k in range(c + 1)]


def outage_probability(c: int, A: float) -> float:
    """Probability that every server is down at the same time (total outage)."""
    return (1 - A) ** c


def overload_probability(lam: float, mu: float, c: int, A: float) -> float:
    """Probability that the servers currently up cannot keep up with demand (k*mu <= lam)."""
    return sum(p for k, p in enumerate(up_distribution(c, A)) if k * mu <= lam)
