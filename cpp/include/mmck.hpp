// Discrete-event simulator for an M/M/c/K queue (FIFO), C++17.
// Same logic as queueing/simulation.py: every served customer's wait is recorded (including 0),
// queue length is time-averaged, blocked arrivals are counted, and a warm-up period is discarded.
#pragma once

#include <cstdint>
#include <limits>

namespace queueing {

struct Params {
    double lam = 1.0 / 450;      // arrival rate (per second)
    double mu = 1.0 / 300;       // service rate per server
    int c = 1;                   // number of servers
    int K = -1;                  // max customers in system (waiting + in service); -1 = unlimited
    double horizon = 2e6;        // simulated time
    double warmup = 5e4;         // initial period excluded from statistics
};

struct Result {
    double Wq = 0;               // mean waiting time in queue (all served customers)
    double W = 0;                // mean time in system
    double L = 0;                // time-average number in system
    double Lq = 0;               // time-average number in queue
    double p_block = 0;          // fraction of arrivals lost because the system was full
    std::uint64_t served = 0;
    std::uint64_t events = 0;    // arrivals + departures processed (for speed measurements)
};

Result simulate(const Params& p, std::uint64_t seed);

}  // namespace queueing
