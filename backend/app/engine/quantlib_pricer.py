import math
from typing import Dict, Any

try:
    import QuantLib as ql
    HAS_QUANTLIB = True
except ImportError:
    ql = None
    HAS_QUANTLIB = False

class QuantLibPricer:
    """
    Ground-truth European option pricing engine backed by QuantLib C++ SWIG bindings,
    with exact analytical Black-Scholes pure-Python fallback for environments without native QuantLib binaries.
    """

    @staticmethod
    def _pure_python_price(
        spot: float,
        strike: float,
        maturity_years: float,
        risk_free_rate: float,
        volatility: float,
        dividend_yield: float = 0.0,
        option_type: str = "call"
    ) -> Dict[str, Any]:
        S = max(spot, 1e-8)
        K = max(strike, 1e-8)
        T = max(maturity_years, 1e-6)
        r = risk_free_rate
        q = dividend_yield
        sigma = max(volatility, 1e-6)
        is_call = option_type.lower() == "call"

        sqrt_T = math.sqrt(T)
        d1 = (math.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * sqrt_T)
        d2 = d1 - sigma * sqrt_T

        def norm_cdf(x: float) -> float:
            return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

        def norm_pdf(x: float) -> float:
            return (1.0 / math.sqrt(2.0 * math.pi)) * math.exp(-0.5 * x ** 2)

        N_d1 = norm_cdf(d1)
        N_d2 = norm_cdf(d2)
        n_d1 = norm_pdf(d1)

        disc_r = math.exp(-r * T)
        disc_q = math.exp(-q * T)

        if is_call:
            npv = S * disc_q * N_d1 - K * disc_r * N_d2
            delta = disc_q * N_d1
            theta_annual = - (S * sigma * disc_q * n_d1) / (2.0 * sqrt_T) - r * K * disc_r * N_d2 + q * S * disc_q * N_d1
            rho_1pct = (K * T * disc_r * N_d2) / 100.0
        else:
            N_neg_d1 = norm_cdf(-d1)
            N_neg_d2 = norm_cdf(-d2)
            npv = K * disc_r * N_neg_d2 - S * disc_q * N_neg_d1
            delta = -disc_q * N_neg_d1
            theta_annual = - (S * sigma * disc_q * n_d1) / (2.0 * sqrt_T) + r * K * disc_r * N_neg_d2 - q * S * disc_q * N_neg_d1
            rho_1pct = (-K * T * disc_r * N_neg_d2) / 100.0

        gamma = (disc_q * n_d1) / (S * sigma * sqrt_T)
        vega_unit = S * disc_q * n_d1 * sqrt_T
        vega_1pct = vega_unit / 100.0
        theta_1day = theta_annual / 365.0

        return {
            "price": max(float(npv), 0.0),
            "greeks": {
                "delta": float(delta),
                "gamma": float(gamma),
                "vega": float(vega_1pct),
                "vega_unit": float(vega_unit),
                "theta": float(theta_1day),
                "rho": float(rho_1pct),
            },
            "parameters": {
                "spot": spot,
                "strike": strike,
                "maturity_years": maturity_years,
                "risk_free_rate": risk_free_rate,
                "volatility": volatility,
                "dividend_yield": dividend_yield,
                "option_type": option_type.lower(),
            }
        }

    @staticmethod
    def price_european_option(
        spot: float,
        strike: float,
        maturity_years: float,
        risk_free_rate: float,
        volatility: float,
        dividend_yield: float = 0.0,
        option_type: str = "call"
    ) -> Dict[str, Any]:
        """
        Computes exact option NPV and analytical Greeks using QuantLib (or pure-Python analytical fallback).
        """
        if not HAS_QUANTLIB:
            return QuantLibPricer._pure_python_price(
                spot, strike, maturity_years, risk_free_rate, volatility, dividend_yield, option_type
            )

        try:
            today = ql.Date.todaysDate()
            ql.Settings.instance().evaluationDate = today

            calendar = ql.NullCalendar()
            day_count = ql.Actual365Fixed()

            maturity_days = max(int(round(maturity_years * 365.0)), 1)
            maturity_date = today + maturity_days

            spot_handle = ql.QuoteHandle(ql.SimpleQuote(spot))
            rate_handle = ql.YieldTermStructureHandle(
                ql.FlatForward(today, risk_free_rate, day_count)
            )
            dividend_handle = ql.YieldTermStructureHandle(
                ql.FlatForward(today, dividend_yield, day_count)
            )
            vol_handle = ql.BlackVolTermStructureHandle(
                ql.BlackConstantVol(today, calendar, volatility, day_count)
            )

            bsm_process = ql.BlackScholesMertonProcess(
                spot_handle, dividend_handle, rate_handle, vol_handle
            )

            ql_option_type = ql.Option.Call if option_type.lower() == "call" else ql.Option.Put
            payoff = ql.PlainVanillaPayoff(ql_option_type, strike)
            exercise = ql.EuropeanExercise(maturity_date)

            option = ql.EuropeanOption(payoff, exercise)
            engine = ql.AnalyticEuropeanEngine(bsm_process)
            option.setPricingEngine(engine)

            npv = float(option.NPV())

            try:
                delta = float(option.delta())
            except Exception:
                delta = 0.0

            try:
                gamma = float(option.gamma())
            except Exception:
                gamma = 0.0

            try:
                vega_unit = float(option.vega())
                vega_1pct = vega_unit / 100.0
            except Exception:
                vega_1pct = 0.0
                vega_unit = 0.0

            try:
                theta_1day = float(option.theta()) / 365.0
            except Exception:
                theta_1day = 0.0

            try:
                rho_1pct = float(option.rho()) / 100.0
            except Exception:
                rho_1pct = 0.0

            return {
                "price": npv,
                "greeks": {
                    "delta": delta,
                    "gamma": gamma,
                    "vega": vega_1pct,
                    "vega_unit": vega_unit,
                    "theta": theta_1day,
                    "rho": rho_1pct,
                },
                "parameters": {
                    "spot": spot,
                    "strike": strike,
                    "maturity_years": maturity_years,
                    "risk_free_rate": risk_free_rate,
                    "volatility": volatility,
                    "dividend_yield": dividend_yield,
                    "option_type": option_type.lower(),
                }
            }
        except Exception:
            return QuantLibPricer._pure_python_price(
                spot, strike, maturity_years, risk_free_rate, volatility, dividend_yield, option_type
            )
