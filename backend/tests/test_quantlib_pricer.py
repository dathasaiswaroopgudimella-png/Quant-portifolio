import pytest
from app.engine.quantlib_pricer import QuantLibPricer

def test_quantlib_pricer_call_option():
    # Benchmark Black-Scholes values for S=100, K=100, T=1.0, r=0.05, sigma=0.20
    res = QuantLibPricer.price_european_option(
        spot=100.0,
        strike=100.0,
        maturity_years=1.0,
        risk_free_rate=0.05,
        volatility=0.20,
        option_type="call"
    )
    assert "price" in res
    assert abs(res["price"] - 10.45058) < 1e-4
    assert "greeks" in res
    assert 0.60 < res["greeks"]["delta"] < 0.67
    assert res["greeks"]["vega"] > 0.0

def test_quantlib_pricer_put_option():
    res = QuantLibPricer.price_european_option(
        spot=100.0,
        strike=100.0,
        maturity_years=1.0,
        risk_free_rate=0.05,
        volatility=0.20,
        option_type="put"
    )
    # Put-Call parity check: C - P = S - K * exp(-r*T)
    # 10.45058 - Put = 100 - 100*exp(-0.05) => Put = 10.45058 - (100 - 95.12294) = 5.5735
    assert abs(res["price"] - 5.5735) < 1e-3
    assert -0.40 < res["greeks"]["delta"] < -0.30
