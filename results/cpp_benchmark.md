# C++ simulator: validation and speed

## Same answers as theory and as the Python simulator

30 replications each. W in seconds, mean ± 95% CI.

| Model | W theory | W Python | W C++ | P(block) theory | P(block) C++ |
|---|---|---|---|---|---|
| M/M/1, medium load | 900.0 | 896.5 ± 23.1 | 894.2 ± 19.5 | 0.0000 | 0.0000 ± 0.0000 |
| M/M/1/10, saturated load | 2077.8 | 2096.9 ± 26.0 | 2068.5 ± 26.2 | 0.1926 | 0.1897 ± 0.0049 |
| M/M/3, saturated load | 323.5 | 323.8 ± 1.8 | 324.9 ± 1.8 | 0.0000 | 0.0000 ± 0.0000 |
| M/M/6, saturated load | 300.1 | 301.2 ± 1.3 | 300.6 ± 1.3 | 0.0000 | 0.0000 ± 0.0000 |

Python and C++ use different random-number generators, so individual runs differ; both agree with the theory within their confidence intervals.

## Speed

M/M/3 at ρ = 0.83, single run, same machine.

| Simulator | Events simulated | Time (s) | Events per second |
|---|---|---|---|
| Python | 999,672 | 0.98 | 1,021,014 |
| C++ (Release build) | 9,999,705 | 0.503 | 19,893,964 |

The C++ simulator processes about **19× more events per second**.

## What the speed buys

3,000 replications of the saturated scenario (43,385,880 events) take 1.8 s in C++; at Python's measured rate they would take about 42 s. The 95% CI on the loss probability shrinks from ±0.0042 (30 runs) to ±0.0004 (3,000 runs), around the theoretical 0.1926.
