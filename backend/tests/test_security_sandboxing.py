import pytest
from app.engine.ast_parser import parse_and_validate_model_code, ASTSecurityError
from app.engine.sandbox import SandboxedModelEvaluator

BASES_BREAKOUT_CODE = """def price(S, K, T, r, sigma):
    x = (1).__class__.__bases__
    return S
"""

MRO_BREAKOUT_CODE = """def price(S, K, T, r, sigma):
    x = (1).__class__.__mro__
    return S
"""

INIT_BREAKOUT_CODE = """def price(S, K, T, r, sigma):
    x = (1).__init__
    return S
"""

DICT_BREAKOUT_CODE = """def price(S, K, T, r, sigma):
    x = (1).__dict__
    return S
"""

SUBPROCESS_CODE = """def price(S, K, T, r, sigma):
    import subprocess
    return S
"""

def test_ast_blocks_bases_attribute():
    with pytest.raises(ASTSecurityError) as exc:
        parse_and_validate_model_code(BASES_BREAKOUT_CODE)
    assert "Prohibited attribute access '__bases__'" in str(exc.value)

def test_ast_blocks_mro_attribute():
    with pytest.raises(ASTSecurityError) as exc:
        parse_and_validate_model_code(MRO_BREAKOUT_CODE)
    assert "Prohibited attribute access '__mro__'" in str(exc.value)

def test_ast_blocks_init_attribute():
    with pytest.raises(ASTSecurityError) as exc:
        parse_and_validate_model_code(INIT_BREAKOUT_CODE)
    assert "Prohibited attribute access '__init__'" in str(exc.value)

def test_ast_blocks_dict_attribute():
    with pytest.raises(ASTSecurityError) as exc:
        parse_and_validate_model_code(DICT_BREAKOUT_CODE)
    assert "Prohibited attribute access '__dict__'" in str(exc.value)

def test_ast_blocks_subprocess():
    with pytest.raises(ASTSecurityError) as exc:
        parse_and_validate_model_code(SUBPROCESS_CODE)
    assert "Prohibited import module 'subprocess'" in str(exc.value)
