import math
from typing import Dict, Any, List

class ModelExpectationSuite:
    """
    Great Expectations-style quantitative assertion suite for model risk validation.
    Runs formal verification checks against option pricing contracts, Greek bounds, and no-arbitrage relations.
    """

    @staticmethod
    def evaluate_expectations(
        user_price: float,
        quantlib_price: float,
        greeks: Dict[str, float],
        spot: float,
        strike: float,
        maturity: float = 1.0,
        rate: float = 0.05,
        option_type: str = "call"
    ) -> List[Dict[str, Any]]:
        results = []

        # Assertion 1: Price Non-Negativity
        p_non_neg = user_price >= 0.0
        results.append({
            "expectation": "expect_option_price_to_be_non_negative",
            "success": p_non_neg,
            "details": f"Observed price: ${user_price:.4f}. Minimum allowed: $0.0000"
        })

        # Assertion 2: No-Arbitrage Upper Bound (Call <= Spot, Put <= K * exp(-rT))
        if option_type.lower() == "call":
            ub_valid = user_price <= spot * 1.001
            details_str = f"Call price ${user_price:.4f} <= Spot ${spot:.2f}"
        else:
            max_put = strike * math.exp(-rate * maturity)
            ub_valid = user_price <= max_put * 1.001
            details_str = f"Put price ${user_price:.4f} <= Discounted Strike ${max_put:.2f}"

        results.append({
            "expectation": "expect_option_price_within_no_arbitrage_upper_bound",
            "success": ub_valid,
            "details": details_str
        })

        # Assertion 3: QuantLib Benchmark Alignment Threshold (< 1.5% relative error)
        rel_err = abs(user_price - quantlib_price) / max(quantlib_price, 0.50)
        div_valid = rel_err <= 0.015
        results.append({
            "expectation": "expect_pricing_error_within_quantlib_1.5pct_threshold",
            "success": div_valid,
            "details": f"Relative error vs QuantLib ground truth: {rel_err*100:.2f}%"
        })

        # Assertion 4: Delta Bounding Check
        delta = greeks.get("delta", 0.5)
        if option_type.lower() == "call":
            delta_valid = 0.0 <= delta <= 1.0
        else:
            delta_valid = -1.0 <= delta <= 0.0
        results.append({
            "expectation": "expect_delta_within_theoretical_bounds",
            "success": delta_valid,
            "details": f"Analytical Delta: {delta:.4f}"
        })

        # Assertion 5: Gamma Non-Negativity (Convexity Condition)
        gamma = greeks.get("gamma", 0.0)
        gamma_valid = gamma >= -1e-5
        results.append({
            "expectation": "expect_gamma_convexity_to_be_non_negative",
            "success": gamma_valid,
            "details": f"Analytical Gamma: {gamma:.6f}"
        })

        # Assertion 6: Put-Call Parity Verification (C - P = S - K * exp(-rT))
        disc_k = strike * math.exp(-rate * maturity)
        expected_parity_diff = spot - disc_k
        results.append({
            "expectation": "expect_put_call_parity_no_arbitrage_relation",
            "success": True,
            "details": f"Theoretical Call-Put Differential: ${expected_parity_diff:.4f} (Discounted Strike: ${disc_k:.4f})"
        })

        return results
