"""Discrete-event simulation of an M/M/c/K queue (FIFO), with warm-up and replications.

Corrections compared with the original TIPE simulator:
  * every served customer's waiting time is recorded, including those served immediately
    (wait = 0); the original only recorded customers who actually queued, which biases
    the waiting-time distribution;
  * queue length is averaged over *time*, not over events (events are not equally spaced);
  * blocked arrivals (system full) are counted and returned, so the blocking probability
    can be compared with theory;
  * a warm-up period is discarded and results are averaged over independent replications
    with a confidence interval, instead of a single 8-hour run.
"""
from __future__ import annotations

import heapq
import math
import random
from collections import deque
from dataclasses import dataclass, field

import numpy as np


@dataclass
class SimResult:
    Wq: float          # mean waiting time in queue (all served customers)
    W: float           # mean time in system
    L: float           # time-average number in system
    Lq: float          # time-average number in queue
    p_block: float     # fraction of arrivals lost because the system was full
    served: int
    waits: np.ndarray = field(repr=False)
    trace_t: np.ndarray = field(repr=False)      # times of state changes
    trace_q: np.ndarray = field(repr=False)      # queue length after each change


def simulate(lam: float, mu: float, c: int = 1, K: int | None = None, horizon: float = 1e6,
             warmup: float = 0.0, seed: int | None = None, keep_trace: bool = False) -> SimResult:
    rng = random.Random(seed)
    t = 0.0
    queue: deque[float] = deque()               # arrival times of waiting customers
    busy: list[tuple[float, float]] = []        # heap of (departure time, arrival time) per busy server
    next_arr = rng.expovariate(lam)
    waits, sojourns = [], []
    area_n = area_q = 0.0
    arrivals = blocked = 0
    tr_t, tr_q = [0.0], [0]

    while True:
        next_dep = busy[0][0] if busy else math.inf
        t_next = min(next_arr, next_dep)
        if t_next > horizon:
            t_next = horizon
        # integrate state over [t, t_next] (only the part after warm-up)
        lo = max(t, warmup)
        if t_next > lo:
            area_n += (len(queue) + len(busy)) * (t_next - lo)
            area_q += len(queue) * (t_next - lo)
        t = t_next
        if t >= horizon:
            break

        if next_arr <= next_dep:                                   # arrival
            counted = t >= warmup
            arrivals += counted
            if K is not None and len(queue) + len(busy) >= K:
                blocked += counted
            elif len(busy) < c:
                heapq.heappush(busy, (t + rng.expovariate(mu), t))
                if counted:
                    waits.append(0.0)
            else:
                queue.append(t)
            next_arr = t + rng.expovariate(lam)
        else:                                                       # departure
            _, arr = heapq.heappop(busy)
            if arr >= warmup:
                sojourns.append(t - arr)
            if queue:
                a = queue.popleft()
                if a >= warmup:
                    waits.append(t - a)
                heapq.heappush(busy, (t + rng.expovariate(mu), a))
        if keep_trace:
            tr_t.append(t); tr_q.append(len(queue))

    span = horizon - warmup
    return SimResult(
        Wq=float(np.mean(waits)) if waits else float("nan"),
        W=float(np.mean(sojourns)) if sojourns else float("nan"),
        L=area_n / span, Lq=area_q / span,
        p_block=blocked / arrivals if arrivals else 0.0,
        served=len(sojourns), waits=np.array(waits),
        trace_t=np.array(tr_t), trace_q=np.array(tr_q),
    )


def replicate(n_reps: int, **kwargs) -> dict:
    """Run independent replications; return mean and 95% CI half-width for each metric."""
    seed0 = kwargs.pop("seed", 0)
    runs = [simulate(seed=seed0 + r, **kwargs) for r in range(n_reps)]
    out = {}
    try:
        from scipy.stats import t as student
        tq = float(student.ppf(0.975, n_reps - 1))
    except ImportError:                      # normal approximation if SciPy is missing
        tq = 1.96
    for m in ("Wq", "W", "L", "Lq", "p_block"):
        x = np.array([getattr(r, m) for r in runs], dtype=float)
        x = x[~np.isnan(x)]
        out[m] = (float(x.mean()), float(tq * x.std(ddof=1) / math.sqrt(len(x))) if len(x) > 1 else float("nan"))
    return out
