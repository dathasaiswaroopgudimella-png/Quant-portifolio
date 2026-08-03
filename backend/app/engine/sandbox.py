import math
import threading
import scipy.stats as stats
from typing import Dict, Any, Callable
from app.engine.ast_parser import parse_and_validate_model_code, ASTSecurityError

ALLOWED_SANDBOX_MODULES = {"math", "scipy", "scipy.stats", "numpy"}

def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name not in ALLOWED_SANDBOX_MODULES:
        raise ImportError(f"Security restriction: Importing module '{name}' is forbidden in sandbox environment.")
    return __import__(name, globals, locals, fromlist, level)

def _get_safe_globals() -> Dict[str, Any]:
    return {
        "__builtins__": {
            "__import__": safe_import,
            "abs": abs, "min": min, "max": max, "pow": pow, "range": range, "len": len,
            "float": float, "int": int, "bool": bool, "round": round
        },
        "math": math,
        "exp": math.exp,
        "log": math.log,
        "sqrt": math.sqrt,
        "erf": math.erf,
        "pi": math.pi,
        "norm_cdf": lambda x: stats.norm.cdf(x),
        "cdf": lambda x: stats.norm.cdf(x),
    }

class SandboxedModelEvaluator:
    """
    Thread-safe, process-compatible sandbox evaluator for user Black-Scholes pricing functions.
    Enforces AST static security inspection and restricted builtins environment.
    """

    @staticmethod
    def create_executable_callable(code: str) -> Callable[[float, float, float, float, float], float]:
        """
        1. Pre-execution static AST security check (blocks os, sys, subprocess, dangerous imports).
        2. Compiles code into a restricted execution environment.
        3. Returns high-performance, thread-safe function for SciPy optimization loops.
        """
        parsed_info = parse_and_validate_model_code(code)
        fn_name = parsed_info["function_name"]
        param_map = parsed_info["parameter_mapping"]

        safe_globals = _get_safe_globals()
        local_scope: Dict[str, Any] = {}

        compiled_code = compile(code, "<sandboxed_model>", "exec")
        exec(compiled_code, safe_globals, local_scope)

        if fn_name not in local_scope:
            raise ASTSecurityError(f"Function '{fn_name}' missing from compiled scope.")

        raw_fn = local_scope[fn_name]

        def _eval_func(spot: float, strike: float, maturity: float, rate: float, volatility: float) -> float:
            kwargs = {}
            if "spot" in param_map:
                kwargs[param_map["spot"]] = float(spot)
            if "strike" in param_map:
                kwargs[param_map["strike"]] = float(strike)
            if "maturity" in param_map:
                kwargs[param_map["maturity"]] = float(maturity)
            if "rate" in param_map:
                kwargs[param_map["rate"]] = float(rate)
            if "volatility" in param_map:
                kwargs[param_map["volatility"]] = float(volatility)

            if len(kwargs) < 5:
                params = parsed_info["parameters"]
                if len(params) >= 5:
                    kwargs = {
                        params[0]: float(spot),
                        params[1]: float(strike),
                        params[2]: float(maturity),
                        params[3]: float(rate),
                        params[4]: float(volatility)
                    }
                else:
                    raise ASTSecurityError(f"Pricing function requires 5 parameters (S, K, T, r, sigma). Got: {params}")

            return float(raw_fn(**kwargs))

        return _eval_func

    @staticmethod
    def evaluate(
        code: str,
        spot: float,
        strike: float,
        maturity: float,
        rate: float,
        volatility: float,
        timeout_seconds: float = 5.0
    ) -> float:
        """
        Evaluates user model code in a thread with a 5.0s hard timeout enforcement.
        """
        eval_fn = SandboxedModelEvaluator.create_executable_callable(code)
        result_holder = {}
        error_holder = {}

        def _worker():
            try:
                result_holder["res"] = eval_fn(spot, strike, maturity, rate, volatility)
            except Exception as e:
                error_holder["err"] = str(e)

        t = threading.Thread(target=_worker)
        t.start()
        t.join(timeout=timeout_seconds)

        if t.is_alive():
            raise RuntimeError(f"Sandboxed model execution timed out after {timeout_seconds}s limit.")

        if "err" in error_holder:
            raise RuntimeError(error_holder["err"])

        if "res" not in result_holder:
            raise RuntimeError("Sandboxed evaluation returned no result.")

        return float(result_holder["res"])
