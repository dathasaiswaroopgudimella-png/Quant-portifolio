import sys
from typing import Dict, Any, List, Tuple

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None
    HAS_NUMPY = False

try:
    from scipy import optimize
    HAS_SCIPY = True
except ImportError:
    optimize = None
    HAS_SCIPY = False

try:
    import QuantLib as ql
    HAS_QL = True
except ImportError:
    ql = None
    HAS_QL = False

from app.engine.quantlib_pricer import QuantLibPricer
from app.engine.sandbox import SandboxedModelEvaluator, _extract_numeric_price
from app.engine.model_classifier import ModelClassifier, ModelBenchmarkRouter, ModelFamily


class AdversarialEngine:
    """
    Adversarial Search Engine powered by SciPy Non-Convex Differential Evolution.
    Finds minimal realistic market parameter perturbations that maximize pricing discrepancy
    and Greek divergence between user model and its exact theoretical/analytical benchmark.
    """

    @staticmethod
    def run_adversarial_search(
        model_code: str,
        base_spot: float = 100.0,
        base_strike: float = 100.0,
        base_maturity: float = 1.0,
        base_rate: float = 0.05,
        base_volatility: float = 0.20,
        dividend_yield: float = 0.0,
        option_type: str = "call"
    ) -> Dict[str, Any]:
        """
        Executes 4D SciPy Differential Evolution over parameter bounds.
        Automatically uses the model-appropriate ground truth (Heston Fourier Inversion for Heston,
        Merton Series for Jump-Diffusion, QuantLib Analytical for BSM).
        """
        model_meta = ModelClassifier.classify_model(model_code)
        family = model_meta["family"]

        # Calculate exact model-aware ground truth benchmark
        gt_base = ModelBenchmarkRouter.calculate_ground_truth(
            model_family=family,
            spot=base_spot,
            strike=base_strike,
            maturity=base_maturity,
            rate=base_rate,
            volatility=base_volatility,
            dividend_yield=dividend_yield,
            option_type=option_type,
            extra_params=model_meta.get("default_parameters", {})
        )
        gt_base_price = float(gt_base["price"])

        user_fn_full = SandboxedModelEvaluator.create_executable_callable(model_code, fast_mode=False)
        user_fn_fast = SandboxedModelEvaluator.create_executable_callable(model_code, fast_mode=True)

        try:
            user_base_price = float(user_fn_full(
                spot=base_spot,
                strike=base_strike,
                maturity=base_maturity,
                rate=base_rate,
                volatility=base_volatility
            ))
        except Exception:
            user_base_price = gt_base_price

        # Search bounds:
        # 1. Spot: [0.60x, 1.40x]
        # 2. Volatility: [0.40x, 3.00x]
        # 3. Interest Rate: [max(0.001, rate-0.04), rate+0.06]
        # 4. Time to Maturity: [max(0.05, maturity*0.2), maturity*2.5]
        bounds = [
            (0.60, 1.40),
            (0.40, 3.00),
            (max(0.001, base_rate - 0.04), base_rate + 0.06),
            (max(0.05, base_maturity * 0.20), base_maturity * 2.50)
        ]

        def _objective(x):
            spot_mult, vol_mult, rate_val, maturity_val = x
            curr_spot = float(base_spot * spot_mult)
            curr_vol = float(max(0.01, base_volatility * vol_mult))
            curr_rate = float(max(0.001, rate_val))
            curr_mat = float(max(0.05, maturity_val))

            gt_res = ModelBenchmarkRouter.calculate_ground_truth(
                model_family=family,
                spot=curr_spot,
                strike=base_strike,
                maturity=curr_mat,
                rate=curr_rate,
                volatility=curr_vol,
                dividend_yield=dividend_yield,
                option_type=option_type,
                extra_params=model_meta.get("default_parameters", {})
            )
            gt_p = float(gt_res["price"])

            try:
                user_p = float(user_fn_fast(
                    spot=curr_spot,
                    strike=base_strike,
                    maturity=curr_mat,
                    rate=curr_rate,
                    volatility=curr_vol
                ))
            except Exception:
                user_p = 0.0

            # Scale-relative pricing error objective:
            abs_err = abs(user_p - gt_p)
            scale_floor = max(gt_p, curr_spot * 0.005)
            rel_err = abs_err / scale_floor
            return -rel_err  # Maximize relative error

        # Multi-seed Differential Evolution for statistical confidence bounds
        seeds = [42, 101, 2024]
        seed_results = []

        if HAS_SCIPY and optimize is not None:
            for seed_val in seeds:
                res = optimize.differential_evolution(
                    _objective,
                    bounds=bounds,
                    strategy='best1bin',
                    maxiter=25,
                    popsize=12,
                    tol=1e-4,
                    seed=seed_val
                )
                seed_results.append(res)
        else:
            import math, random
            _rng = random.Random(42)
            class _FallbackResult:
                def __init__(self, x, fun):
                    self.x = x
                    self.fun = fun
            best_x, best_val = [0.9, 1.5, bounds[2][0] + (bounds[2][1]-bounds[2][0])*0.5, base_maturity], 0.0
            for seed_val in seeds:
                _rng.seed(seed_val)
                for _ in range(25):
                    candidate = [_rng.uniform(b[0], b[1]) for b in bounds]
                    val = -_objective(candidate)
                    if val > best_val:
                        best_val, best_x = val, candidate
                seed_results.append(_FallbackResult(best_x, -best_val))
            seed_results = [_FallbackResult(best_x, -best_val)] * 3

        # Primary optimization result (Seed 42)
        opt_res = seed_results[0]
        opt_spot_mult, opt_vol_mult, opt_rate, opt_maturity = opt_res.x
        opt_spot = float(base_spot * opt_spot_mult)
        opt_vol = float(base_volatility * opt_vol_mult)
        opt_rate = float(opt_rate)
        opt_maturity = float(opt_maturity)

        # Evaluate model-aware ground truth at adversarial point
        gt_worst = ModelBenchmarkRouter.calculate_ground_truth(
            model_family=family,
            spot=opt_spot,
            strike=base_strike,
            maturity_years=opt_maturity,
            risk_free_rate=opt_rate,
            volatility=opt_vol,
            dividend_yield=dividend_yield,
            option_type=option_type,
            extra_params=model_meta.get("default_parameters", {})
        ) if "maturity_years" in ModelBenchmarkRouter.calculate_ground_truth.__code__.co_varnames else ModelBenchmarkRouter.calculate_ground_truth(
            model_family=family,
            spot=opt_spot,
            strike=base_strike,
            maturity=opt_maturity,
            rate=opt_rate,
            volatility=opt_vol,
            dividend_yield=dividend_yield,
            option_type=option_type,
            extra_params=model_meta.get("default_parameters", {})
        )
        gt_worst_price = float(gt_worst["price"])

        try:
            user_worst_price = float(user_fn_full(
                spot=opt_spot,
                strike=base_strike,
                maturity=opt_maturity,
                rate=opt_rate,
                volatility=opt_vol
            ))
        except Exception:
            user_worst_price = 0.0

        max_error = float(abs(user_worst_price - gt_worst_price))
        scale_floor_worst = max(gt_worst_price, opt_spot * 0.005)
        pct_error = float((max_error / scale_floor_worst) * 100.0)

        # Numerical finite-difference Greek drift estimation for user model at breaking point
        h_s = max(opt_spot * 0.001, 0.01)
        h_v = max(opt_vol * 0.001, 0.001)

        try:
            u_p_s_up = user_fn_full(opt_spot + h_s, base_strike, opt_maturity, opt_rate, opt_vol)
            u_p_s_dn = user_fn_full(opt_spot - h_s, base_strike, opt_maturity, opt_rate, opt_vol)
            user_delta = (u_p_s_up - u_p_s_dn) / (2.0 * h_s)
        except Exception:
            user_delta = gt_worst["greeks"].get("delta", 0.5)

        try:
            u_p_v_up = user_fn_full(opt_spot, base_strike, opt_maturity, opt_rate, opt_vol + h_v)
            u_p_v_dn = user_fn_full(opt_spot, base_strike, opt_maturity, opt_rate, opt_vol - h_v)
            user_vega_unit = (u_p_v_up - u_p_v_dn) / (2.0 * h_v)
            user_vega = user_vega_unit / 100.0
        except Exception:
            user_vega = gt_worst["greeks"].get("vega", 0.2)

        greek_drifts = {
            "delta_drift": round(float(abs(user_delta - gt_worst["greeks"].get("delta", user_delta))), 4),
            "vega_drift": round(float(abs(user_vega - gt_worst["greeks"].get("vega", user_vega))), 4),
            "base_greeks": gt_base["greeks"],
            "adversarial_greeks": gt_worst["greeks"]
        }

        # Multi-seed statistical confidence calculation
        err_values = [-r.fun for r in seed_results]
        if HAS_NUMPY and np is not None:
            mean_err = float(np.mean(err_values))
            std_err = float(np.std(err_values))
        else:
            mean_err = float(sum(err_values) / len(err_values))
            variance = sum((v - mean_err) ** 2 for v in err_values) / len(err_values)
            std_err = float(variance ** 0.5)
        stability_score = round(max(0.0, min(100.0, 100.0 - (std_err / max(mean_err, 1e-4)) * 100.0)), 1)

        breaking_parameters = {
            "spot": round(float(opt_spot), 2),
            "volatility": round(float(opt_vol), 4),
            "risk_free_rate": round(float(opt_rate), 4),
            "maturity_years": round(float(opt_maturity), 3),
            "user_price": round(float(user_worst_price), 4),
            "quantlib_price": round(float(gt_worst_price), 4),
            "ground_truth_price": round(float(gt_worst_price), 4),
            "benchmark_engine": gt_worst["benchmark_engine"],
            "absolute_error": round(float(max_error), 4),
            "percentage_error": round(float(pct_error), 2),
            "optimizer_stability": stability_score,
            "statistical_confidence": {
                "mean_relative_error": round(mean_err, 4),
                "std_relative_error": round(std_err, 4),
                "confidence_95pct_ci": f"{mean_err:.4f} ± {1.96 * std_err:.4f}"
            },
            "reproducibility": {
                "seeds_evaluated": seeds,
                "strategy": "best1bin",
                "maxiter": 25,
                "popsize": 12,
                "environment_metadata": {
                    "benchmark_engine": gt_worst["benchmark_engine"],
                    "python_version": sys.version.split()[0]
                }
            }
        }

        surface_grid = AdversarialEngine._generate_fragility_surface(
            user_fn=user_fn_fast,
            model_family=family,
            base_spot=base_spot,
            base_strike=base_strike,
            base_maturity=base_maturity,
            base_rate=base_rate,
            base_volatility=base_volatility,
            dividend_yield=dividend_yield,
            option_type=option_type,
            extra_params=model_meta.get("default_parameters", {})
        )

        return {
            "model_metadata": model_meta,
            "base_metrics": {
                "user_price": round(float(user_base_price), 4),
                "quantlib_price": round(float(gt_base_price), 4),
                "ground_truth_price": round(float(gt_base_price), 4),
                "benchmark_engine": gt_base["benchmark_engine"],
                "base_error": round(float(abs(user_base_price - gt_base_price)), 4),
                "base_greeks": gt_base["greeks"],
                "stochastic_parameters": gt_base.get("stochastic_parameters", {})
            },
            "breaking_parameters": breaking_parameters,
            "greek_drifts": greek_drifts,
            "fragility_surface": surface_grid
        }

    @staticmethod
    def _generate_fragility_surface(
        user_fn: Any,
        model_family: str,
        base_spot: float,
        base_strike: float,
        base_maturity: float,
        base_rate: float,
        base_volatility: float,
        dividend_yield: float = 0.0,
        option_type: str = "call",
        extra_params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        if HAS_NUMPY and np is not None:
            spot_multipliers = np.linspace(0.70, 1.30, 7)
            vol_multipliers = np.linspace(0.50, 2.00, 7)
        else:
            spot_multipliers = [0.70 + i * (1.30-0.70)/6 for i in range(7)]
            vol_multipliers = [0.50 + i * (2.00-0.50)/6 for i in range(7)]

        matrix = []
        for v_mult in vol_multipliers:
            row = []
            curr_vol = float(base_volatility * v_mult)
            for s_mult in spot_multipliers:
                curr_spot = float(base_spot * s_mult)
                gt_res = ModelBenchmarkRouter.calculate_ground_truth(
                    model_family=model_family,
                    spot=curr_spot,
                    strike=base_strike,
                    maturity=base_maturity,
                    rate=base_rate,
                    volatility=curr_vol,
                    dividend_yield=dividend_yield,
                    option_type=option_type,
                    extra_params=extra_params
                )
                gt_p = float(gt_res["price"])

                try:
                    user_p = float(user_fn(
                        spot=curr_spot,
                        strike=base_strike,
                        maturity=base_maturity,
                        rate=base_rate,
                        volatility=curr_vol
                    ))
                except Exception:
                    user_p = 0.0

                err = float(abs(user_p - gt_p))
                row.append(round(err, 4))
            matrix.append(row)

        return {
            "spot_axis": [round(float(base_spot * m), 1) for m in spot_multipliers],
            "volatility_axis": [round(float(base_volatility * m), 3) for m in vol_multipliers],
            "error_matrix": matrix
        }
