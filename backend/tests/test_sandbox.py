import pytest
from app.engine.sandbox import SandboxedModelEvaluator
from app.engine.ast_parser import parse_and_validate_model_code, ASTSecurityError

SAFE_BS_CODE = """def bs_call(S, K, T, r, sigma):
    import math
    d1 = (math.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*math.sqrt(T))
    d2 = d1 - sigma*math.sqrt(T)
    N = lambda x: 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
    return S * N(d1) - K * math.exp(-r*T) * N(d2)
"""

UNSAFE_MALICIOUS_CODE = """def malicious_call(S, K, T, r, sigma):
    import os
    os.system("echo hacked")
    return S - K
"""

def test_sandbox_evaluates_valid_code():
    res = SandboxedModelEvaluator.evaluate(
        code=SAFE_BS_CODE,
        spot=100.0,
        strike=100.0,
        maturity=1.0,
        rate=0.05,
        volatility=0.20
    )
    assert abs(res - 10.45058) < 1e-4

def test_sandbox_rejects_prohibited_imports():
    with pytest.raises(ASTSecurityError):
        parse_and_validate_model_code(UNSAFE_MALICIOUS_CODE)
