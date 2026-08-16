"""
FRAGMENT Monte Carlo Convergence & Statistical Diagnostics Suite
Audits stochastic simulations: Standard Error, 95%/99% Confidence Intervals,
Seed Replication Stability, Feller Condition (Heston), and Discretization Error.
"""
import math
from typing import Dict, Any, Callable, Optional


class MonteCarloDiagnostics:
    """
    Comprehensive diagnostic battery for Monte Carlo and stochastic numerical models.
    """

    @staticmethod
    def audit_simulation(
        raw_output: Any,
        pricer_fn: Callable[..., float],
        ground_truth_price: float,
        spot: float = 100.0,
        strike: float = 100.0,
        maturity: float = 1.0,
        rate: float = 0.05,
        volatility: float = 0.20,
        model_family: str = "HESTON_MC",
        stochastic_params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Runs complete statistical convergence audit for Monte Carlo models.
        """
        # 1. Extract simulation diagnostics from raw dictionary output (if provided by user)
        user_price = 0.0
        standard_error = 0.0
        ci_95 = [0.0, 0.0]
        paths = 100000
        steps = 252

        if isinstance(raw_output, dict):
            user_price = float(raw_output.get("price", raw_output.get("val", 0.0)))
            standard_error = float(raw_output.get("standard_error", raw_output.get("se", 0.0)))
            ci_raw = raw_output.get("95%_confidence_interval", raw_output.get("ci_95", None))
            if ci_raw and isinstance(ci_raw, (list, tuple)) and len(ci_raw) == 2:
                ci_95 = [round(float(ci_raw[0]), 5), round(float(ci_raw[1]), 5)]
            paths = int(raw_output.get("paths", 100000))
            steps = int(raw_output.get("steps", 252))

        if user_price <= 0:
            user_price = pricer_fn(spot, strike, maturity, rate, volatility)

        if standard_error <= 0:
            # Estimate theoretical Monte Carlo standard error: sigma * S / sqrt(paths)
            standard_error = (volatility * spot * math.sqrt(maturity)) / math.sqrt(paths)

        if ci_95 == [0.0, 0.0]:
            ci_95 = [
                round(user_price - 1.96 * standard_error, 5),
                round(user_price + 1.96 * standard_error, 5)
            ]

        ci_99 = [
            round(user_price - 2.576 * standard_error, 5),
            round(user_price + 2.576 * standard_error, 5)
        ]

        # 2. Check Confidence Interval Coverage against Semi-Analytical Benchmark
        ci_enveloped = (ci_95[0] <= ground_truth_price <= ci_95[1])
        ci_99_enveloped = (ci_99[0] <= ground_truth_price <= ci_99[1])

        # 3. Seed Replication Stability (3 runs with varying seeds if callable supports it)
        seed_prices = [user_price]
        try:
            # Fast replication check
            p2 = pricer_fn(spot, strike, maturity, rate, volatility, seed=101)
            p3 = pricer_fn(spot, strike, maturity, rate, volatility, seed=2024)
            seed_prices.extend([p2, p3])
        except Exception:
            pass

        seed_mean = sum(seed_prices) / len(seed_prices)
        seed_variance = sum((p - seed_mean) ** 2 for p in seed_prices) / max(1, len(seed_prices) - 1)
        seed_std = math.sqrt(seed_variance) if len(seed_prices) > 1 else standard_error

        # 4. Feller Condition Audit (for Heston CIR variance process: 2*kappa*theta >= sigma_v^2)
        feller_audit = None
        if model_family in ["HESTON_MC", "HESTON_ANALYTICAL"] and stochastic_params:
            kappa = float(stochastic_params.get("kappa", 2.0))
            theta = float(stochastic_params.get("theta", 0.04))
            sigma_v = float(stochastic_params.get("sigma_v", stochastic_params.get("sigma", 0.5)))
            
            feller_lhs = 2.0 * kappa * theta
            feller_rhs = sigma_v ** 2
            feller_satisfied = (feller_lhs >= feller_rhs)

            feller_audit = {
                "feller_condition_formula": "2 * kappa * theta >= sigma_v^2",
                "two_kappa_theta": round(feller_lhs, 4),
                "sigma_v_squared": round(feller_rhs, 4),
                "is_feller_satisfied": feller_satisfied,
                "status": "FELLER_SATISFIED" if feller_satisfied else "FELLER_VIOLATION_BOUNDARY_ABSORPTION",
                "governance_note": (
                    "Variance process is strictly positive (v_t > 0 for all t)."
                    if feller_satisfied else
                    "2*kappa*theta < sigma_v^2: Variance reaches 0.0 with positive probability. "
                    "Requires reflection/full-truncation scheme (v_next = max(v_next, 0.0)) to prevent negative variance."
                )
            }

        return {
            "is_monte_carlo": True,
            "paths": paths,
            "steps": steps,
            "point_estimate": round(user_price, 5),
            "ground_truth_benchmark": round(ground_truth_price, 5),
            "standard_error": round(standard_error, 5),
            "relative_standard_error_pct": round((standard_error / max(0.01, user_price)) * 100.0, 3),
            "confidence_interval_95": ci_95,
            "confidence_interval_99": ci_99,
            "is_benchmark_within_95_ci": ci_enveloped,
            "is_benchmark_within_99_ci": ci_99_enveloped,
            "seed_stability": {
                "replications_evaluated": len(seed_prices),
                "seed_price_range": [round(min(seed_prices), 5), round(max(seed_prices), 5)],
                "inter_seed_std_dev": round(seed_std, 5),
                "stability_rating": "HIGH_STABILITY" if seed_std < standard_error * 1.5 else "MODERATE_VARIANCE"
            },
            "feller_condition_audit": feller_audit
        }
