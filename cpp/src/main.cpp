// Command-line front end: runs independent replications and prints one CSV row per replication.
//
//   mmck_sim --lam 0.0040 --mu 0.003333 --c 3 --K 10 --horizon 2e6 --warmup 5e4 --reps 30 --seed 100
//
// Output (stdout): rep,Wq,W,L,Lq,p_block,served,events,seconds
#include <chrono>
#include <cstdlib>
#include <iostream>
#include <string>

#include "mmck.hpp"

int main(int argc, char** argv) {
    queueing::Params p;
    int reps = 30;
    std::uint64_t seed = 0;
    for (int i = 1; i + 1 < argc; i += 2) {
        const std::string k = argv[i];
        const char* v = argv[i + 1];
        if (k == "--lam") p.lam = std::atof(v);
        else if (k == "--mu") p.mu = std::atof(v);
        else if (k == "--c") p.c = std::atoi(v);
        else if (k == "--K") p.K = std::atoi(v);
        else if (k == "--horizon") p.horizon = std::atof(v);
        else if (k == "--warmup") p.warmup = std::atof(v);
        else if (k == "--reps") reps = std::atoi(v);
        else if (k == "--seed") seed = std::strtoull(v, nullptr, 10);
        else { std::cerr << "unknown option " << k << "\n"; return 2; }
    }
    if (p.lam <= 0 || p.mu <= 0 || p.c < 1 || (p.K >= 0 && p.K < p.c) || p.warmup >= p.horizon) {
        std::cerr << "invalid parameters\n";
        return 2;
    }
    std::cout << "rep,Wq,W,L,Lq,p_block,served,events,seconds\n";
    std::cout.precision(10);
    for (int r = 0; r < reps; ++r) {
        const auto t0 = std::chrono::steady_clock::now();
        const auto res = queueing::simulate(p, seed + r);
        const double sec = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
        std::cout << r << ',' << res.Wq << ',' << res.W << ',' << res.L << ',' << res.Lq << ','
                  << res.p_block << ',' << res.served << ',' << res.events << ',' << sec << '\n';
    }
    return 0;
}
