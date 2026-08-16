import math
import threading
from typing import Dict, Any, Callable, Optional
import scipy.stats as stats

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None
    HAS_NUMPY = False

from app.engine.ast_parser import parse_and_validate_model_code, ASTSecurityError

ALLOWED_SANDBOX_MODULES = {
    "math", "cmath", "scipy", "scipy.stats", "scipy.optimize",
    "scipy.integrate", "scipy.interpolate", "numpy", "numpy.random",
    "typing", "collections", "dataclasses"
}

def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    base_name = name.split(".")[0]
    if base_name not in ALLOWED_SANDBOX_MODULES and name not in ALLOWED_SANDBOX_MODULES:
        raise ImportError(f"Security restriction: Importing module '{name}' is forbidden in sandbox environment.")
    return __import__(name, globals, locals, fromlist, level)

def _get_safe_globals() -> Dict[str, Any]:
    safe_dict = {
        "__builtins__": {
            "__import__": safe_import,
            "abs": abs, "min": min, "max": max, "pow": pow, "range": range, "len": len,
            "float": float, "int": int, "bool": bool, "round": round, "str": str,
            "dict": dict, "list": list, "tuple": tuple, "set": set,
            "sum": sum, "zip": zip, "enumerate": enumerate, "reversed": reversed,
            "isinstance": isinstance, "issubclass": issubclass, "callable": callable,
            "Exception": Exception, "ValueError": ValueError, "TypeError": TypeError,
            "RuntimeError": RuntimeError, "ZeroDivisionError": ZeroDivisionError,
            "ArithmeticError": ArithmeticError, "OverflowError": OverflowError,
            "print": lambda *args, **kwargs: None  # silent print
        },
        "math": math,
        "exp": math.exp,
        "log": math.log,
        "sqrt": math.sqrt,
        "erf": math.erf,
        "pi": math.pi,
        "norm_cdf": lambda x: float(stats.norm.cdf(x)),
        "cdf": lambda x: float(stats.norm.cdf(x)),
    }
    if HAS_NUMPY and np is not None:
        safe_dict["numpy"] = np
        safe_dict["np"] = np
    return safe_dict

def _extract_numeric_price(raw_output: Any) -> float:
    """
    Intelligently extracts the scalar pricing value from any quantitative model output:
    - Pure scalar (float, int, np.floating)
    - Diagnostic dictionary ({"price": 10.45, "standard_error": 0.02, ...})
    - Confidence interval tuple / list ((price, se) or [price, delta])
    - Numpy array / tensor
    """
    if raw_output is None:
        return 0.0

    if isinstance(raw_output, (int, float)):
        return float(raw_output)

    if isinstance(raw_output, dict):
        # Look for standard quant keys in prioritized order
        for key in ["price", "val", "value", "option_price", "pv", "call", "put",
                    "premium", "fair_value", "mean", "npv", "spot_price"]:
            if key in raw_output and isinstance(raw_output[key], (int, float)):
                return float(raw_output[key])
        # Fall back to first numeric value
        for v in raw_output.values():
            if isinstance(v, (int, float)):
                return float(v)

    if isinstance(raw_output, (list, tuple)):
        if len(raw_output) > 0 and isinstance(raw_output[0], (int, float)):
            return float(raw_output[0])

    if hasattr(raw_output, "item"):
        try:
            return float(raw_output.item())
        except Exception:
            pass

    try:
        return float(raw_output)
    except Exception as e:
        raise ValueError(f"Could not convert model output of type '{type(raw_output).__name__}' to numeric price: {raw_output}")


class SandboxedModelEvaluator:
    """
    Thread-safe, process-compatible sandbox evaluator for user pricing functions.
    Enforces AST static security inspection, restricted builtins, and adaptive parameter binding.
    """

    @staticmethod
    def create_executable_callable(code: str, fast_mode: bool = False) -> Callable[..., float]:
        """
        1. Pre-execution static AST security check.
        2. Compiles code into a restricted execution environment.
        3. Returns high-performance, thread-safe function for SciPy optimization and validation runs.
        """
        parsed_info = parse_and_validate_model_code(code)
        fn_name = parsed_info["function_name"]
        param_map = parsed_info["parameter_mapping"]
        all_params = parsed_info["parameters"]
        is_stochastic = parsed_info.get("is_stochastic_variance", False)

        safe_globals = _get_safe_globals()
        local_scope: Dict[str, Any] = {}

        compiled_code = compile(code, "<sandboxed_model>", "exec")
        exec(compiled_code, safe_globals, local_scope)

        if fn_name not in local_scope:
            raise ASTSecurityError(f"Function '{fn_name}' missing from compiled scope.")

        raw_fn = local_scope[fn_name]

        def _eval_func(
            spot: float,
            strike: float,
            maturity: float,
            rate: float,
            volatility: float,
            **override_kwargs
        ) -> float:
            kwargs = {}

            # Map standard 5 parameters
            if "spot" in param_map:
                kwargs[param_map["spot"]] = float(spot)
            if "strike" in param_map:
                kwargs[param_map["strike"]] = float(strike)
            if "maturity" in param_map:
                kwargs[param_map["maturity"]] = float(maturity)
            if "rate" in param_map:
                kwargs[param_map["rate"]] = float(rate)

            # Volatility / Variance handling
            if is_stochastic:
                # In Heston/stochastic vol models, v0 is initial variance (sigma^2)
                if "v0" in param_map:
                    kwargs[param_map["v0"]] = float(volatility ** 2)
            else:
                if "volatility" in param_map:
                    kwargs[param_map["volatility"]] = float(volatility)

            # Monte Carlo optimization scaling (prevents 100k paths from timing out during DE search)
            if fast_mode:
                if "paths" in param_map:
                    kwargs[param_map["paths"]] = 2000
                if "steps" in param_map:
                    kwargs[param_map["steps"]] = 30

            # Apply any explicit overrides
            kwargs.update(override_kwargs)

            # Fallback for standard 5-arg positional functions if mapping couldn't match keywords
            if len(kwargs) < 5 and len(all_params) >= 5 and not any(p in kwargs for p in all_params[:5]):
                kwargs = {
                    all_params[0]: float(spot),
                    all_params[1]: float(strike),
                    all_params[2]: float(maturity),
                    all_params[3]: float(rate),
                    all_params[4]: float(volatility)
                }

            raw_res = raw_fn(**kwargs)
            return _extract_numeric_price(raw_res)

        return _eval_func

    @staticmethod
    def evaluate(
        code: str,
        spot: float,
        strike: float,
        maturity: float,
        rate: float,
        volatility: float,
        timeout_seconds: float = 10.0
    ) -> float:
        """
        Evaluates user model code in a thread with a hard timeout enforcement.
        """
        eval_fn = SandboxedModelEvaluator.create_executable_callable(code)
        result_holder = {}
        error_holder = {}

        def _worker():
            try:
                result_holder["res"] = eval_fn(spot, strike, maturity, rate, volatility)
            except Exception as e:
                error_holder["err"] = str(e)

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        t.join(timeout=timeout_seconds)

        if t.is_alive():
            raise RuntimeError(f"Sandboxed model execution timed out after {timeout_seconds}s limit.")

        if "err" in error_holder:
            raise RuntimeError(error_holder["err"])

        if "res" not in result_holder:
            raise RuntimeError("Sandboxed evaluation returned no result.")

        return float(result_holder["res"])
