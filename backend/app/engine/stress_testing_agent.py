"""
FRAGMENT Stress Testing & Crisis Replay Agent (Inspired by AgentQuant)
Executes historical tail-risk scenario replays and computes Value-at-Risk (VaR) / Expected Shortfall (CVaR).
"""
import math
from typing import Dict, Any, List, Callable

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None  # type: ignore
    HAS_NUMPY = False

try:
    from scipy.stats import norm as _norm
    def _norm_pdf(x: float) -> float:
        return float(_norm.pdf(x))
except ImportError:
    def _norm_pdf(x: float) -> float:
        return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)


class StressTestingAgent:
    """
    Simulates catastrophic tail-risk shocks, non-linear volatility spikes, and liquidity breakdowns.
    """

    HISTORICAL_SCENARIOS = [
        {
            "name": "2008 Global Financial Crisis (Lehman Collapse)",
            "date": "September 2008",
            "spot_shock": -0.38,      # -38% equity collapse
            "vol_shock": +2.10,       # +210% VIX explosion (VIX peaked at 89.5)
            "rate_shock": -0.035,     # -350 bps Fed rate cut
            "description": "Systemic banking liquidity freeze, massive volatility spike, and severe flight to quality."
        },
        {
            "name": "2020 COVID-19 Liquidity Shock",
            "date": "March 2020",
            "spot_shock": -0.34,      # -34% in 22 trading days (fastest bear market in history)
            "vol_shock": +1.95,       # +195% volatility surge
            "rate_shock": -0.015,     # -150 bps emergency cuts
            "description": "Global economic shutdown, extreme gamma squeeze, and unprecedented cross-asset correlations."
        },
        {
            "name": "1987 Black Monday Crash",
            "date": "October 19, 1987",
            "spot_shock": -0.226,     # -22.6% single-day collapse (Dow Jones)
            "vol_shock": +3.20,       # Implied volatility exceeded 150%
            "rate_shock": -0.010,     # Rate cut
            "description": "Portfolio insurance cascading automated sell orders and market maker liquidity withdrawal."
        },
        {
            "name": "2023 SVB Regional Banking Stress",
            "date": "March 2023",
            "spot_shock": -0.12,      # Regional bank index down 35%, broader market -12%
            "vol_shock": +0.65,       # +65% MOVE & VIX surge
            "rate_shock": -0.011,     # -110 bps 2Y Treasury yield plummet (biggest 3-day drop since 1987)
            "description": "Unrealized HTM securities losses, digital deposit runs, and sharp yield curve recalibration."
        },
        {
            "name": "2010 Flash Crash (High-Frequency Microstructure)",
            "date": "May 6, 2010",
            "spot_shock": -0.09,      # -9% intra-day plunge
            "vol_shock": +1.40,       # Spurious quote stuffing and order book exhaustion
            "rate_shock": 0.0,
            "description": "Spoofing algorithm triggered cascade of automated stop-loss orders in E-mini S&P futures."
        }
    ]

    @staticmethod
    def run_stress_battery(
        pricer_fn: Callable[[float, float, float, float, float], float],
        base_spot: float = 100.0,
        base_strike: float = 100.0,
        base_maturity: float = 1.0,
        base_rate: float = 0.05,
        base_vol: float = 0.20,
        notional: float = 1000000.0  # $1,000,000 reference portfolio notional
    ) -> Dict[str, Any]:
        """
        Replays 5 major financial crises through the target pricing model.
        Calculates Value-at-Risk (95%, 99% VaR) and Expected Shortfall (CVaR).
        """
        base_price = pricer_fn(base_spot, base_strike, base_maturity, base_rate, base_vol)
        scenario_results = []
        losses = []

        for scen in StressTestingAgent.HISTORICAL_SCENARIOS:
            stressed_spot = max(1.0, base_spot * (1.0 + scen["spot_shock"]))
            stressed_vol = max(0.01, base_vol * (1.0 + scen["vol_shock"]))
            stressed_rate = max(0.0001, base_rate + scen["rate_shock"])

            stressed_price = pricer_fn(stressed_spot, base_strike, base_maturity, stressed_rate, stressed_vol)
            pnl_per_contract = stressed_price - base_price
            pnl_pct = (pnl_per_contract / max(1e-5, base_price)) * 100.0
            dollar_pnl = (pnl_per_contract / base_spot) * notional

            losses.append(-dollar_pnl if dollar_pnl < 0 else 0.0)

            scenario_results.append({
                "scenario": scen["name"],
                "date": scen["date"],
                "stressed_spot": round(stressed_spot, 2),
                "stressed_vol": round(stressed_vol * 100.0, 1),
                "stressed_rate": round(stressed_rate * 100.0, 2),
                "stressed_price": round(stressed_price, 4),
                "pnl_per_contract": round(pnl_per_contract, 4),
                "pnl_percentage": round(pnl_pct, 2),
                "portfolio_dollar_pnl": round(dollar_pnl, 2),
                "description": scen["description"]
            })

        # Parametric & Historical VaR calculation (10-day 99% VaR)
        daily_vol = base_vol / math.sqrt(252)
        var_95_1d = notional * 1.645 * daily_vol
        var_99_1d = notional * 2.326 * daily_vol
        cvar_99_1d = notional * (_norm_pdf(2.326) / 0.01) * daily_vol  # Expected Shortfall

        if HAS_NUMPY and np is not None:
            var_99_10day = round(var_99_1d * float(np.sqrt(10)), 2)
        else:
            var_99_10day = round(var_99_1d * math.sqrt(10), 2)

        max_historical_loss = max(losses) if losses else 0.0

        return {
            "base_valuation": {
                "spot": base_spot,
                "strike": base_strike,
                "volatility": base_vol,
                "rate": base_rate,
                "price": round(base_price, 4),
                "portfolio_notional": notional
            },
            "crisis_replays": scenario_results,
            "tail_risk_metrics": {
                "var_95_1day": round(var_95_1d, 2),
                "var_99_1day": round(var_99_1d, 2),
                "var_99_10day": var_99_10day,
                "cvar_expected_shortfall_99": round(cvar_99_1d, 2),
                "worst_case_historical_loss": round(max_historical_loss, 2),
                "stress_resilience_rating": "HIGH_RESILIENCE" if max_historical_loss < notional * 0.25 else "MODERATE_RESILIENCE" if max_historical_loss < notional * 0.50 else "SEVERE_VULNERABILITY"
            }
        }
