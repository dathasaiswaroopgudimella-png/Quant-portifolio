from app.engine.adversarial_engine import AdversarialEngine

SAFE_BS_CODE = """def bs_call(S, K, T, r, sigma):
    import math
    d1 = (math.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*math.sqrt(T))
    d2 = d1 - sigma*math.sqrt(T)
    N = lambda x: 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
    return S * N(d1) - K * math.exp(-r*T) * N(d2)
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
    assert "fragility_surface" in adv_res
    assert adv_res["breaking_parameters"]["spot"] > 0.0
    assert len(adv_res["fragility_surface"]["error_matrix"]) == 7
