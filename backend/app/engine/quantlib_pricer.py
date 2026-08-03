import QuantLib as ql
from typing import Dict, Any, Tuple

class QuantLibPricer:
    """
    Ground-truth European option pricing engine backed by QuantLib SWIG bindings.
    Provides exact analytical Black-Scholes prices and analytical Greeks.
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
        """
        # Set valuation date
        today = ql.Date.todaysDate()
        ql.Settings.instance().evaluationDate = today

        # Exercise date based on maturity in years
        calendar = ql.NullCalendar()
        day_count = ql.Actual365Fixed()
        
        # Add integer days corresponding to maturity
        maturity_days = max(int(round(maturity_years * 365)), 1)
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

        # Calculate Price & Greeks safely
        npv = float(option.NPV())
        
        # Calculate analytical Greeks safely
        try:
            delta = float(option.delta())
        except Exception:
            delta = 0.0

        try:
            gamma = float(option.gamma())
        except Exception:
            gamma = 0.0

        try:
            vega = float(option.vega()) / 100.0  # QuantLib returns Vega per 100% vol shift
        except Exception:
            vega = 0.0

        try:
            theta = float(option.theta()) / 365.0  # Daily theta
        except Exception:
            theta = 0.0

        try:
            rho = float(option.rho()) / 100.0  # QuantLib returns Rho per 100% rate shift
        except Exception:
            rho = 0.0

        return {
            "price": npv,
            "greeks": {
                "delta": delta,
                "gamma": gamma,
                "vega": vega,
                "theta": theta,
                "rho": rho,
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
