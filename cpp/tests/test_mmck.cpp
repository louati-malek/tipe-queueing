// Checks the C++ simulator against closed-form M/M/c and M/M/c/K results.
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <vector>

#include "mmck.hpp"

namespace {

int failures = 0;

// Erlang C and M/M/c mean time in system
double mmc_W(double lam, double mu, int c) {
    const double a = lam / mu, rho = a / c;
    double term = 1.0, s = 1.0;
    for (int k = 1; k < c; ++k) { term *= a / k; s += term; }
    const double last = term * a / c / (1 - rho);
    const double pw = last / (s + last);
    return pw / (c * mu - lam) + 1 / mu;
}

// M/M/c/K blocking probability
double mmck_pblock(double lam, double mu, int c, int K) {
    const double a = lam / mu;
    std::vector<double> p{1.0};
    for (int n = 1; n <= K; ++n) p.push_back(p.back() * a / std::min(n, c));
    double z = 0;
    for (double x : p) z += x;
    return p[K] / z;
}

double mean_over(const queueing::Params& prm, int reps, double queueing::Result::*field) {
    double s = 0;
    for (int r = 0; r < reps; ++r) s += queueing::simulate(prm, 1000 + r).*field;
    return s / reps;
}

void check(const char* name, double sim, double theory, double rel_tol) {
    const double err = std::fabs(sim - theory) / theory;
    const bool ok = err <= rel_tol;
    std::printf("[%s] %-34s sim=%.6g theory=%.6g rel.err=%.2f%%\n", ok ? "PASS" : "FAIL", name, sim, theory, 100 * err);
    if (!ok) ++failures;
}

}  // namespace

int main() {
    const double mu = 1.0 / 300;
    queueing::Params p;
    p.horizon = 2e6; p.warmup = 5e4;

    p.lam = 1.0 / 450; p.c = 1;
    check("M/M/1 medium load, W", mean_over(p, 20, &queueing::Result::W), mmc_W(p.lam, mu, 1), 0.03);

    p.lam = 1.0 / 250; p.c = 3;
    check("M/M/3 saturated load, W", mean_over(p, 20, &queueing::Result::W), mmc_W(p.lam, mu, 3), 0.01);

    p.lam = 1.0 / 250; p.c = 1; p.K = 10;
    check("M/M/1/10 saturated, P(block)", mean_over(p, 20, &queueing::Result::p_block),
          mmck_pblock(p.lam, mu, 1, 10), 0.05);

    // Little's law inside one long run: L = lam_eff * W
    p.lam = 1.0 / 120; p.c = 3; p.K = -1; p.horizon = 1e7;
    const auto r = queueing::simulate(p, 7);
    check("Little's law L = lam W", r.L, p.lam * r.W, 0.02);

    std::printf("%s\n", failures ? "SOME TESTS FAILED" : "all tests passed");
    return failures ? 1 : 0;
}
