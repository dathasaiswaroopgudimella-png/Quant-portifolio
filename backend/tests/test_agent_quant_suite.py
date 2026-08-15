import pytest
import math
from app.engine.quant_models import QuantModels
from app.engine.arbitrage_checker import ArbitrageChecker
from app.engine.stress_testing_agent import StressTestingAgent
from app.engine.multi_agent_system import MultiAgentQuantPipeline


def test_black_scholes_greeks():
    res = QuantModels.black_scholes(S=100.0, K=100.0, T=1.0, r=0.05, sigma=0.20, option_type="call")
    assert res["price"] > 10.0 and res["price"] < 11.0
    assert res["delta"] > 0.60 and res["delta"] < 0.65
    assert res["gamma"] > 0.015 and res["gamma"] < 0.025
    assert res["vega"] > 0.35 and res["vega"] < 0.40
    assert res["volga"] > 0.0
    assert res["vanna"] < 0.0


def test_garman_kohlhagen_fx():
    res = QuantModels.garman_kohlhagen(S=1.10, K=1.10, T=0.5, r_d=0.04, r_f=0.02, sigma=0.12, option_type="call")
    assert res["price"] > 0.03 and res["price"] < 0.05


def test_merton_jump_diffusion():
    price = QuantModels.merton_jump_diffusion(S=100.0, K=100.0, T=1.0, r=0.05, sigma=0.20, lam=0.75, gamma=-0.05, delta_j=0.15)
    assert price > 9.0 and price < 15.0


def test_heston_stochastic_vol():
    price = QuantModels.heston_stochastic_vol(S=100.0, K=100.0, T=1.0, r=0.05, v0=0.04, kappa=2.0, theta=0.04, xi=0.3, rho=-0.7)
    assert price > 8.0 and price < 13.0


def test_bjerksund_stensland_american():
    # American call with dividend yield >= European call
    am_price = QuantModels.bjerksund_stensland(S=100.0, K=100.0, T=1.0, r=0.05, sigma=0.20, q=0.03, option_type="call")
    eu_price = QuantModels.black_scholes(S=100.0, K=100.0, T=1.0, r=0.05, sigma=0.20, q=0.03, option_type="call")["price"]
    assert am_price >= eu_price - 1e-4


def test_corrado_su_skew_kurtosis():
    price = QuantModels.corrado_su(S=100.0, K=100.0, T=1.0, r=0.05, sigma=0.20, skewness=-0.5, kurtosis=4.0)
    assert price > 8.0 and price < 13.0


def test_bachelier_normal():
    price = QuantModels.bachelier(S=100.0, K=100.0, T=1.0, r=0.05, sigma_normal=20.0, option_type="call")
    assert price > 7.0 and price < 10.0


def test_sabr_vol_smile():
    vol_atm = QuantModels.sabr_implied_vol(F=100.0, K=100.0, T=1.0, alpha=0.2, beta=0.7, rho=-0.3, nu=0.4)
    vol_otm = QuantModels.sabr_implied_vol(F=100.0, K=120.0, T=1.0, alpha=0.2, beta=0.7, rho=-0.3, nu=0.4)
    assert vol_atm > 0.05
    assert vol_otm > 0.05


def test_arbitrage_checker_on_bs():
    def standard_bs(S, K, T, r, sigma):
        return QuantModels.black_scholes(S, K, T, r, sigma)["price"]

    audit = ArbitrageChecker.run_arbitrage_audit(pricer_fn=standard_bs, spot=100.0, strike=100.0, maturity=1.0, rate=0.05, volatility=0.20)
    assert audit["status"] == "NO_ARBITRAGE"
    assert audit["checks_passed"] == 5
    assert audit["arbitrage_score"] == 100.0


def test_stress_testing_agent():
    def standard_bs(S, K, T, r, sigma):
        return QuantModels.black_scholes(S, K, T, r, sigma)["price"]

    res = StressTestingAgent.run_stress_battery(pricer_fn=standard_bs, base_spot=100.0, base_strike=100.0, base_maturity=1.0, base_rate=0.05, base_vol=0.20)
    assert len(res["crisis_replays"]) == 5
    assert "var_99_10day" in res["tail_risk_metrics"]
    assert res["tail_risk_metrics"]["var_99_10day"] > 0


def test_multi_agent_pipeline():
    import asyncio
    bs_code = """def black_scholes_call(S, K, T, r, sigma):
    import math
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return 0.0
    d1 = (math.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*math.sqrt(T))
    d2 = d1 - sigma*math.sqrt(T)
    N = lambda x: 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
    return S * N(d1) - K * math.exp(-r*T) * N(d2)
"""
    res = asyncio.run(MultiAgentQuantPipeline.execute_full_validation_pipeline(
        model_name="BS Call Test",
        model_code=bs_code,
        spot=100.0,
        strike=100.0,
        maturity=1.0,
        rate=0.05,
        volatility=0.20
    ))
    assert "fragility_data" in res
    assert "arbitrage_audit" in res
    assert "stress_audit" in res
    assert "executive_summary" in res
    assert res["arbitrage_audit"]["status"] == "NO_ARBITRAGE"
