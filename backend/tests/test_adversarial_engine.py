import pytest
from app.engine.adversarial_engine import AdversarialEngine
from app.engine.ast_parser import parse_and_validate_model_code, ASTSecurityError
from app.engine.assumption_engine import AssumptionExtractor
from app.engine.quantlib_pricer import QuantLibPricer
from app.engine.expectations import ModelExpectationSuite

SAFE_BS_CODE = """def bs_call(S, K, T, r, sigma):
    import math
    d1 = (math.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*math.sqrt(T))
    d2 = d1 - sigma*math.sqrt(T)
    N = lambda x: 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
    return S * N(d1) - K * math.exp(-r*T) * N(d2)
"""

LOCAL_VOL_CODE = """def local_vol_call(S, K, T, r, sigma):
    import math
    adj_sigma = sigma * (1.0 + 0.1 * (S - K) / K)
    adj_sigma = max(0.01, adj_sigma)
    d1 = (math.log(S/K) + (r + 0.5*adj_sigma**2)*T) / (adj_sigma*math.sqrt(T))
    d2 = d1 - adj_sigma*math.sqrt(T)
    N = lambda x: 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
    return S * N(d1) - K * math.exp(-r*T) * N(d2)
"""

DANGEROUS_CODE = """def malicious_model(S, K, T, r, sigma):
    import os
    os.system("echo hacked")
    return S - K
"""

def test_adversarial_search_execution():
    adv_res = AdversarialEngine.run_adversarial_search(
        model_code=SAFE_BS_CODE,
        base_spot=100.0,
        base_strike=100.0,
        base_maturity=1.0,
        base_rate=0.05,
        base_volatility=0.20
    )
    assert "base_metrics" in adv_res
    assert "breaking_parameters" in adv_res
    assert "greek_drifts" in adv_res
    assert "fragility_surface" in adv_res
    assert adv_res["breaking_parameters"]["spot"] > 0.0
    assert adv_res["breaking_parameters"]["optimizer_stability"] >= 0.0
    assert len(adv_res["fragility_surface"]["error_matrix"]) == 7

def test_ast_security_sandbox_blocking():
    with pytest.raises(ASTSecurityError) as exc_info:
        parse_and_validate_model_code(DANGEROUS_CODE)
    assert "Security violation" in str(exc_info.value) or "Import of module 'os' is prohibited" in str(exc_info.value)

def test_dynamic_ast_assumption_extraction():
    safe_assumptions = AssumptionExtractor.extract_assumptions(SAFE_BS_CODE)
    local_vol_assumptions = AssumptionExtractor.extract_assumptions(LOCAL_VOL_CODE)

    # Standard BS should be tagged with Constant Volatility
    assert any("Constant Volatility" in a["name"] for a in safe_assumptions)

    # Local vol code should be dynamically tagged with Local Volatility Skew
    assert any("Local Volatility" in a["name"] for a in local_vol_assumptions)

def test_quantlib_pricer_accuracy():
    res = QuantLibPricer.price_european_option(
        spot=100.0,
        strike=100.0,
        maturity_years=1.0,
        risk_free_rate=0.05,
        volatility=0.20,
        option_type="call"
    )
    # Exact analytical BSM call price for S=100, K=100, T=1, r=0.05, vol=0.20 is ~10.4506
    assert abs(res["price"] - 10.4506) < 0.1
    assert 0.5 <= res["greeks"]["delta"] <= 0.7
    assert res["greeks"]["gamma"] > 0.0

def test_model_expectation_suite():
    expectations = ModelExpectationSuite.evaluate_expectations(
        user_price=10.45,
        quantlib_price=10.45,
        greeks={"delta": 0.63, "gamma": 0.018},
        spot=100.0,
        strike=100.0,
        maturity=1.0,
        rate=0.05
    )
    assert len(expectations) >= 5
    assert all(e["success"] for e in expectations)
