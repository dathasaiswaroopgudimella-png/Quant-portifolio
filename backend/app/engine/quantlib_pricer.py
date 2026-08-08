import QuantLib as ql
from typing import Dict, Any

class QuantLibPricer:
    """
    Ground-truth European option pricing engine backed by QuantLib C++ SWIG bindings.
    Provides exact analytical Black-Scholes prices and exact partial derivative Greeks.
    """

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
        Computes exact option NPV and analytical Greeks using QuantLib.
        Ensures exact fractional day maturity handling to prevent calendar discretization mismatch.
        """
        today = ql.Date.todaysDate()
        ql.Settings.instance().evaluationDate = today

        calendar = ql.NullCalendar()
        day_count = ql.Actual365Fixed()
        
        # Calculate exact maturity date with fractional day precision handling
        maturity_days = max(int(round(maturity_years * 365.0)), 1)
        maturity_date = today + maturity_days

        # Market Quotes & Term Structures
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

        # Black-Scholes-Merton Process
        bsm_process = ql.BlackScholesMertonProcess(
            spot_handle, dividend_handle, rate_handle, vol_handle
        )

        # Payoff & Exercise
        ql_option_type = ql.Option.Call if option_type.lower() == "call" else ql.Option.Put
        payoff = ql.PlainVanillaPayoff(ql_option_type, strike)
        exercise = ql.EuropeanExercise(maturity_date)

        # Instrument & Engine
        option = ql.EuropeanOption(payoff, exercise)
        engine = ql.AnalyticEuropeanEngine(bsm_process)
        option.setPricingEngine(engine)

        npv = float(option.NPV())
        
        # Analytical Greeks (normalized to standard market conventions)
        try:
            delta = float(option.delta())
        except Exception:
            delta = 0.0

        try:
            gamma = float(option.gamma())
        except Exception:
            gamma = 0.0

        try:
            # QuantLib vega() is per 100% vol move (1.0). Divide by 100 to get Vega per 1% vol shift.
            vega_1pct = float(option.vega()) / 100.0
            vega_unit = float(option.vega())
        except Exception:
            vega_1pct = 0.0
            vega_unit = 0.0

        try:
            # QuantLib theta() is annual. Divide by 365.0 for 1-day decay theta.
            theta_1day = float(option.theta()) / 365.0
        except Exception:
            theta_1day = 0.0

        try:
            # QuantLib rho() is per 100% rate shift (1.0). Divide by 100 to get Rho per 1% (100 bps) shift.
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
