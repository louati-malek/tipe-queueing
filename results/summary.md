# Results

## 1. Simulation vs theory

30 replications of 2e+06 s each (warm-up 5e+04 s). Simulated values are mean ± 95% CI.

| Model | rho | W theory (s) | W simulated (s) | Wq theory (s) | Wq simulated (s) | P(block) theory | P(block) simulated |
|---|---|---|---|---|---|---|---|
| M/M/1, medium load | 0.67 | 900 | 896.5 ± 23 | 600 | 596.1 ± 22 | 0.0000 | 0 ± 0 |
| M/M/1/10, saturated load | 1.20 | 2078 | 2097 ± 26 | 1778 | 1796 ± 24 | 0.1926 | 0.1963 ± 0.0046 |
| M/M/3, saturated load | 0.40 | 323.5 | 323.8 ± 1.8 | 23.53 | 23.2 ± 0.78 | 0.0000 | 0 ± 0 |
| M/M/6, saturated load | 0.20 | 300.1 | 301.2 ± 1.3 | 0.09758 | 0.08063 ± 0.027 | 0.0000 | 0 ± 0 |

## 2. One simulated day is not enough

Medium load gives about 64 dossiers per day. Over 2,000 independent one-day runs, the daily mean waiting time ranges from 2.5 to 19.4 min (5th–95th percentile), around a theoretical value of 10.0 min. A single run, as in the original TIPE, cannot estimate the mean.

## 3. Same demand, 1 vs 3 vs 6 servers

| Scenario | λ (dossiers/h) | W M/M/1 (min) | W M/M/3 (min) | W M/M/6 (min) |
|---|---|---|---|---|
| low | 4.0 | 7.5 | 5.0 | 5.0 |
| medium | 8.0 | 15.0 | 5.1 | 5.0 |
| saturated | 14.4 | unstable | 5.4 | 5.0 |

This is the comparison made in the TIPE. The gain is real, but it comes from adding capacity: 3 servers can process 3 times more dossiers.

## 4. Fair comparison: same total capacity

At utilisation 0.8 with the same total capacity (6 dossiers per 5 min): one fast server gives W = 4.2 min, 6 parallel servers give W = 7.2 min. Queueing time is lower with parallel servers (Wq 2.2 vs 3.3 min), but each dossier is served more slowly, so the total time is higher. Decentralising does not reduce delay by itself; its advantage is resilience (next section).

## 5. Resilience under server failures

Illustrative values: each server fails on average every 720 h and takes 8 h to repair (availability 0.9890).

| Architecture | P(total outage) | Expected hours of total outage per year |
|---|---|---|
| Centralised (1 server) | 1.10e-02 | 96.3 |
| Decentralised (6 servers) | 1.76e-12 | 1.54e-08 |

With the same total capacity, total outages practically disappear, and partial failures only reduce capacity. This is the real argument for decentralisation. The figure shows the limit: above 60 arrivals per hour, losing any one of the 6 servers already causes overload, so the decentralised system becomes *more* fragile than the centralised one. Decentralisation only pays off with spare capacity (N+1 redundancy).

## 6. Sizing: how many servers for a given volume?

Hypothetical daily volumes over an 8-hour day, keeping ρ ≤ 0.8. These are not measurements.

| Daily volume | λ (per h) | servers at 300 s | servers at 30 s | servers at 1 s |
|---|---|---|---|---|
| 115/day (TIPE 'saturated') | 14.4 | 2 | 1 | 1 |
| 1,000/day | 125.0 | 14 | 2 | 1 |
| 10,000/day | 1,250.0 | 131 | 14 | 1 |

The TIPE scenarios were not calibrated against measured traffic. The required number of servers scales with volume × processing time, so both must be measured before drawing conclusions about a real platform.
