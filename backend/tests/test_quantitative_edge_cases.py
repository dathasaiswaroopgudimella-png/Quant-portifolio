import math
import pytest
from app.engine.quantlib_pricer import QuantLibPricer
from app.engine.adversarial_engine import AdversarialEngine
from app.engine.expectations import ModelExpectationSuite

GARMAN_KOHLHAGEN_CODE = """def garman_kohlhagen_fx(S, K, T, r, sigma):
    import math
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return 0.0
    rf = 0.02
    d1 = (math.log(S/K) + (r - rf + 0.5*sigma**2)*T) / (sigma*math.sqrt(T))
    d2 = d1 - sigma*math.sqrt(T)
    N = lambda x: 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
    return S * math.exp(-rf*T) * N(d1) - K * math.exp(-r*T) * N(d2)
"""

def test_deep_itm_call_option():
    # S=200, K=100 (Deep ITM). Call price should approach S - K * exp(-rT)
    res = QuantLibPricer.price_european_option(
        spot=200.0, strike=100.0, maturity_years=1.0, risk_free_rate=0.05, volatility=0.20, option_type="call"
    )
    lower_bound = 200.0 - 100.0 * math.exp(-0.05)
    assert res["price"] >= lower_bound
    assert 0.95 <= res["greeks"]["delta"] <= 1.00

def test_deep_otm_call_option():
    # S=50, K=150 (Deep OTM). Call price should approach 0
    res = QuantLibPricer.price_european_option(
        spot=50.0, strike=150.0, maturity_years=1.0, risk_free_rate=0.05, volatility=0.20, option_type="call"
    )
    assert 0.0 <= res["price"] < 0.10
    assert 0.0 <= res["greeks"]["delta"] < 0.05

def test_near_expiry_option_gamma_behavior():
    # Near expiry T = 0.01 (3.6 days). Delta should be sharp, Gamma non-negative
    res = QuantLibPricer.price_european_option(
        spot=100.0, strike=100.0, maturity_years=0.01, risk_free_rate=0.05, volatility=0.20, option_type="call"
    )
    assert res["price"] > 0.0
    assert res["greeks"]["gamma"] > 0.0

def test_garman_kohlhagen_dividend_yield_alignment():
    adv_res = AdversarialEngine.run_adversarial_search(
        model_code=GARMAN_KOHLHAGEN_CODE,
        base_spot=1.10,
        base_strike=1.10,
        base_maturity=0.5,
        base_rate=0.04,
        base_volatility=0.12,
        dividend_yield=0.02,
        option_type="call"
    )
    # With dividend_yield=0.02 correctly passed, baseline pricing error should be negligible
    assert adv_res["base_metrics"]["base_error"] < 0.001

def test_put_call_parity_verification():
    call_res = QuantLibPricer.price_european_option(
        spot=100.0, strike=100.0, maturity_years=1.0, risk_free_rate=0.05, volatility=0.20, option_type="call"
    )
    put_res = QuantLibPricer.price_european_option(
        spot=100.0, strike=100.0, maturity_years=1.0, risk_free_rate=0.05, volatility=0.20, option_type="put"
    )
    parity_lhs = call_res["price"] - put_res["price"]
    parity_rhs = 100.0 - 100.0 * math.exp(-0.05)
    assert abs(parity_lhs - parity_rhs) < 1e-3
