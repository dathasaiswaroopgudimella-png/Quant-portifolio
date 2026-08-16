import asyncio
import pytest
from app.engine.multi_agent_system import MultiAgentQuantPipeline
from app.engine.sandbox import SandboxedModelEvaluator
from app.engine.ast_parser import parse_and_validate_model_code

HESTON_MC_CODE = '''def heston_monte_carlo_call(S, K, T, r, v0=0.04, kappa=2.0, theta=0.04, sigma=0.5, rho=-0.7, q=0.0, paths=10000, steps=100, seed=42):

    import numpy as np

    if S <= 0 or K <= 0 or T <= 0:
        return 0.0

    if v0 < 0 or theta < 0 or kappa <= 0 or sigma <= 0:
        return 0.0

    if abs(rho) >= 1 or paths <= 0 or steps <= 0:
        return 0.0

    rng = np.random.default_rng(seed)

    dt = T / steps
    sqrt_dt = np.sqrt(dt)

    S_paths = np.full(paths, S, dtype=float)
    v_paths = np.full(paths, v0, dtype=float)

    for _ in range(steps):

        z1 = rng.standard_normal(paths)
        z2 = rng.standard_normal(paths)

        dW_S = z1
        dW_v = rho * z1 + np.sqrt(1.0 - rho**2) * z2

        v = np.maximum(v_paths, 0.0)

        v_next = (
            v
            + kappa * (theta - v) * dt
            + sigma * np.sqrt(v) * sqrt_dt * dW_v
        )

        v_next = np.maximum(v_next, 0.0)

        S_paths *= np.exp(
            (r - q - 0.5 * v) * dt
            + np.sqrt(v) * sqrt_dt * dW_S
        )

        v_paths = v_next

    payoff = np.maximum(S_paths - K, 0.0)

    discounted_payoff = np.exp(-r * T) * payoff

    price = np.mean(discounted_payoff)

    standard_error = (
        np.std(discounted_payoff, ddof=1)
        / np.sqrt(paths)
    )

    confidence_low = price - 1.96 * standard_error
    confidence_high = price + 1.96 * standard_error

    return {
        "price": float(price),
        "standard_error": float(standard_error),
        "95%_confidence_interval": (
            float(confidence_low),
            float(confidence_high)
        ),
        "paths": paths,
        "steps": steps,
        "initial_variance": v0,
        "long_run_variance": theta,
        "mean_reversion": kappa,
        "vol_of_vol": sigma,
        "correlation": rho
    }
'''

def test_heston_ast_parsing():
    info = parse_and_validate_model_code(HESTON_MC_CODE)
    assert info["function_name"] == "heston_monte_carlo_call"
    assert "spot" in info["parameter_mapping"]
    assert "strike" in info["parameter_mapping"]
    assert "maturity" in info["parameter_mapping"]
    assert "rate" in info["parameter_mapping"]
    assert info["is_stochastic_variance"] is True

def test_heston_sandbox_dict_extraction():
    fn = SandboxedModelEvaluator.create_executable_callable(HESTON_MC_CODE)
    price = fn(spot=100.0, strike=100.0, maturity=1.0, rate=0.05, volatility=0.20)
    assert isinstance(price, float)
    # Heston ATM European Call price for S=100, K=100, T=1, r=0.05, v0=0.04 (vol=20%) is ~10.40 - 10.50
    assert 9.0 <= price <= 12.0
    print(f"Heston MC evaluated price: {price:.4f}")

def test_heston_full_pipeline():
    res = asyncio.run(MultiAgentQuantPipeline.execute_full_validation_pipeline(
        model_name="Heston Monte Carlo Call",
        model_code=HESTON_MC_CODE,
        spot=100.0,
        strike=100.0,
        maturity=1.0,
        rate=0.05,
        volatility=0.20
    ))
    assert "fragility_data" in res
    assert "base_metrics" in res
    user_p = res["base_metrics"]["user_price"]
    ql_p = res["base_metrics"]["quantlib_price"]
    assert abs(user_p - ql_p) < 1.0  # Monte Carlo matches Black-Scholes benchmark closely
    assert res["fragility_data"]["fragility_score"] >= 0.0
    assert res["arbitrage_audit"]["status"] in ["NO_ARBITRAGE", "PASS", "WARNING"]
    print(f"Pipeline finished! User Price: {user_p}, QuantLib: {ql_p}, Fragility Score: {res['fragility_data']['fragility_score']}")
