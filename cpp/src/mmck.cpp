#include "mmck.hpp"

#include <algorithm>
#include <deque>
#include <functional>
#include <queue>
#include <random>
#include <utility>
#include <vector>

namespace queueing {

Result simulate(const Params& p, std::uint64_t seed) {
    std::mt19937_64 rng(seed);
    std::exponential_distribution<double> inter_arrival(p.lam);
    std::exponential_distribution<double> service(p.mu);
    const double INF = std::numeric_limits<double>::infinity();

    // busy servers: min-heap of (departure time, arrival time of the customer in service)
    using Job = std::pair<double, double>;
    std::priority_queue<Job, std::vector<Job>, std::greater<Job>> busy;
    std::deque<double> waiting;                       // arrival times of queued customers

    double t = 0.0, next_arr = inter_arrival(rng);
    double sum_wait = 0, sum_sojourn = 0, area_n = 0, area_q = 0;
    std::uint64_t n_wait = 0, n_sojourn = 0, arrivals = 0, blocked = 0, events = 0;

    while (true) {
        const double next_dep = busy.empty() ? INF : busy.top().first;
        double t_next = std::min(next_arr, next_dep);
        if (t_next > p.horizon) t_next = p.horizon;

        // integrate the state over [t, t_next], counting only the part after warm-up
        const double lo = std::max(t, p.warmup);
        if (t_next > lo) {
            area_n += static_cast<double>(waiting.size() + busy.size()) * (t_next - lo);
            area_q += static_cast<double>(waiting.size()) * (t_next - lo);
        }
        t = t_next;
        if (t >= p.horizon) break;
        ++events;

        if (next_arr <= next_dep) {                                    // arrival
            const bool counted = t >= p.warmup;
            arrivals += counted;
            const auto in_system = waiting.size() + busy.size();
            if (p.K >= 0 && in_system >= static_cast<std::size_t>(p.K)) {
                blocked += counted;
            } else if (busy.size() < static_cast<std::size_t>(p.c)) {
                busy.emplace(t + service(rng), t);
                if (counted) ++n_wait;                                 // waited 0
            } else {
                waiting.push_back(t);
            }
            next_arr = t + inter_arrival(rng);
        } else {                                                       // departure
            const double arr = busy.top().second;
            busy.pop();
            if (arr >= p.warmup) { sum_sojourn += t - arr; ++n_sojourn; }
            if (!waiting.empty()) {
                const double a = waiting.front();
                waiting.pop_front();
                if (a >= p.warmup) { sum_wait += t - a; ++n_wait; }
                busy.emplace(t + service(rng), a);
            }
        }
    }

    const double span = p.horizon - p.warmup;
    Result r;
    r.Wq = n_wait ? sum_wait / n_wait : 0.0;
    r.W = n_sojourn ? sum_sojourn / n_sojourn : 0.0;
    r.L = area_n / span;
    r.Lq = area_q / span;
    r.p_block = arrivals ? static_cast<double>(blocked) / arrivals : 0.0;
    r.served = n_sojourn;
    r.events = events;
    return r;
}

}  // namespace queueing
