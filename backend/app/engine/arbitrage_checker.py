"""
FRAGMENT No-Arbitrage & Boundary Condition Integrity Engine
Performs rigorous structural mathematical consistency checks on candidate pricing models.
"""
from typing import Dict, Any, List, Callable
import math
from app.engine.quant_models import QuantModels


class ArbitrageChecker:
    """
    Validates economic no-arbitrage boundary conditions and partial derivative inequalities.
    """

    @staticmethod
    def run_arbitrage_audit(
        pricer_fn: Callable[[float, float, float, float, float], float],
        spot: float = 100.0,
        strike: float = 100.0,
        maturity: float = 1.0,
        rate: float = 0.05,
        volatility: float = 0.20
    ) -> Dict[str, Any]:
        """
        Executes 5 fundamental No-Arbitrage stress tests across the parameter neighborhood.
        """
        violations = []
        checks_passed = 0
        total_checks = 5

        # 1. Monotonicity with respect to Strike (dC/dK <= 0)
        # Higher strike call options MUST be strictly cheaper or equal in price
        k_down = max(1.0, strike * 0.95)
        k_up = strike * 1.05
        p_k_down = pricer_fn(spot, k_down, maturity, rate, volatility)
        p_k_mid = pricer_fn(spot, strike, maturity, rate, volatility)
        p_k_up = pricer_fn(spot, k_up, maturity, rate, volatility)

        strike_monotonic = (p_k_down >= p_k_mid - 1e-4) and (p_k_mid >= p_k_up - 1e-4)
        if strike_monotonic:
            checks_passed += 1
        else:
            violations.append({
                "test": "Strike Monotonicity (∂C/∂K ≤ 0)",
                "detail": f"Call price increased with strike: P(K={k_down:.1f})={p_k_down:.4f}, P(K={strike:.1f})={p_k_mid:.4f}, P(K={k_up:.1f})={p_k_up:.4f}",
                "severity": "CRITICAL"
            })

        # 2. Convexity / Butterfly Spread Arbitrage (d²C/dK² >= 0)
        # Breeden-Litzenberger risk-neutral density requirement
        butterfly_spread = p_k_down - 2 * p_k_mid + p_k_up
        convexity_valid = butterfly_spread >= -1e-4
        if convexity_valid:
            checks_passed += 1
        else:
            violations.append({
                "test": "Convexity / Butterfly Arbitrage (∂²C/∂K² ≥ 0)",
                "detail": f"Negative butterfly spread payoff ({butterfly_spread:.6f}) creates riskless static arbitrage.",
                "severity": "CRITICAL"
            })

        # 3. Calendar Spread Arbitrage (dC/dT >= 0 for European calls with q=0)
        t_short = max(0.01, maturity * 0.7)
        t_long = maturity * 1.3
        p_t_short = pricer_fn(spot, strike, t_short, rate, volatility)
        p_t_long = pricer_fn(spot, strike, t_long, rate, volatility)

        calendar_valid = p_t_long >= p_t_short - 1e-4
        if calendar_valid:
            checks_passed += 1
        else:
            violations.append({
                "test": "Calendar Spread Arbitrage (∂C/∂T ≥ 0)",
                "detail": f"Longer tenor option is cheaper than shorter tenor: P(T={t_short:.2f})={p_t_short:.4f}, P(T={t_long:.2f})={p_t_long:.4f}",
                "severity": "HIGH"
            })

        # 4. Intrinsic Payoff Lower & Upper Bounds (max(0, S - K*e^-rT) <= C <= S)
        disc_k = strike * math.exp(-rate * maturity)
        lower_bound = max(0.0, spot - disc_k)
        upper_bound = spot
        
        bounds_valid = (p_k_mid >= lower_bound - 1e-4) and (p_k_mid <= upper_bound + 1e-4)
        if bounds_valid:
            checks_passed += 1
        else:
            violations.append({
                "test": "Boundary Envelope (max(0, S - Ke^-rT) ≤ C ≤ S)",
                "detail": f"Price ${p_k_mid:.4f} violated theoretical bounds [${lower_bound:.4f}, ${upper_bound:.4f}]",
                "severity": "HIGH"
            })

        # 5. Volatility Smile Positive Variance Check
        # Ensure prices scale monotonically with implied volatility (Vega >= 0)
        vol_low = max(0.02, volatility * 0.8)
        vol_high = volatility * 1.2
        p_vol_low = pricer_fn(spot, strike, maturity, rate, vol_low)
        p_vol_high = pricer_fn(spot, strike, maturity, rate, vol_high)

        vega_valid = p_vol_high >= p_vol_low - 1e-4
        if vega_valid:
            checks_passed += 1
        else:
            violations.append({
                "test": "Volatility Monotonicity / Vega Positivity (∂C/∂σ ≥ 0)",
                "detail": f"Higher volatility resulted in lower call price: P(σ={vol_low*100:.1f}%)={p_vol_low:.4f}, P(σ={vol_high*100:.1f}%)={p_vol_high:.4f}",
                "severity": "MEDIUM"
            })

        arbitrage_score = round((checks_passed / total_checks) * 100.0, 1)
        status = "NO_ARBITRAGE" if checks_passed == total_checks else "ARBITRAGE_DETECTED" if checks_passed < 3 else "CONDITIONAL_VALID"

        return {
            "arbitrage_score": arbitrage_score,
            "status": status,
            "checks_passed": checks_passed,
            "total_checks": total_checks,
            "violations": violations,
            "tests_summary": {
                "strike_monotonicity": "PASS" if strike_monotonic else "FAIL",
                "convexity_butterfly": "PASS" if convexity_valid else "FAIL",
                "calendar_spread": "PASS" if calendar_valid else "FAIL",
                "boundary_envelope": "PASS" if bounds_valid else "FAIL",
                "vega_positivity": "PASS" if vega_valid else "FAIL"
            }
        }
