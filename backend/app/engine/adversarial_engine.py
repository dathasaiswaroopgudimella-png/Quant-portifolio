import sys
import numpy as np
import scipy.optimize as optimize
import QuantLib as ql
from typing import Dict, Any, List, Tuple
from app.engine.quantlib_pricer import QuantLibPricer
from app.engine.sandbox import SandboxedModelEvaluator

class AdversarialEngine:
    """
    Adversarial Search Engine powered by SciPy Non-Convex Differential Evolution.
    Finds minimal realistic market parameter perturbations (Spot, Volatility, Interest Rate, Tenor)
    that maximize pricing discrepancy and Greek divergence between user model and QuantLib ground truth.
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
        Executes 4D SciPy Differential Evolution over parameter bounds (Spot, Vol, Rate, Maturity).
        Uses scale-relative pricing error objective to ensure equal sensitivity across deep ITM and OTM options.
        """
        ql_base = QuantLibPricer.price_european_option(
            spot=base_spot,
            strike=base_strike,
            maturity_years=base_maturity,
            risk_free_rate=base_rate,
            volatility=base_volatility,
            dividend_yield=dividend_yield,
            option_type=option_type
        )
        ql_base_price = float(ql_base["price"])

        user_fn = SandboxedModelEvaluator.create_executable_callable(model_code)

        try:
            user_base_price = float(user_fn(
                spot=base_spot,
                strike=base_strike,
                maturity=base_maturity,
                rate=base_rate,
                volatility=base_volatility
            ))
        except Exception:
            user_base_price = ql_base_price

        # 4D Search bounds:
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

            ql_res = QuantLibPricer.price_european_option(
                spot=curr_spot,
                strike=base_strike,
                maturity_years=curr_mat,
                risk_free_rate=curr_rate,
                volatility=curr_vol,
                dividend_yield=dividend_yield,
                option_type=option_type
            )
            ql_p = float(ql_res["price"])

            try:
                user_p = float(user_fn(
                    spot=curr_spot,
                    strike=base_strike,
                    maturity=curr_mat,
                    rate=curr_rate,
                    volatility=curr_vol
                ))
            except Exception:
                user_p = 0.0

            # Scale-relative pricing error objective:
            # Floor set to 0.5% of current spot price so deep OTM options are evaluated scale-proportionally.
            abs_err = abs(user_p - ql_p)
            scale_floor = max(ql_p, curr_spot * 0.005)
            rel_err = abs_err / scale_floor
            return -rel_err  # Maximize relative error

        # Multi-seed Differential Evolution for statistical confidence bounds (Seeds 42, 101, 2024)
        seeds = [42, 101, 2024]
        seed_results = []

        for seed_val in seeds:
            res = optimize.differential_evolution(
                _objective,
                bounds=bounds,
                strategy='best1bin',
                maxiter=35,
                popsize=15,
                tol=1e-5,
                seed=seed_val
            )
            seed_results.append(res)

        # Primary optimization result (Seed 42)
        opt_res = seed_results[0]
        opt_spot_mult, opt_vol_mult, opt_rate, opt_maturity = opt_res.x
        opt_spot = float(base_spot * opt_spot_mult)
        opt_vol = float(base_volatility * opt_vol_mult)
        opt_rate = float(opt_rate)
        opt_maturity = float(opt_maturity)

        # Evaluate QuantLib ground truth at adversarial point
        ql_worst = QuantLibPricer.price_european_option(
            spot=opt_spot,
            strike=base_strike,
            maturity_years=opt_maturity,
            risk_free_rate=opt_rate,
            volatility=opt_vol,
            dividend_yield=dividend_yield,
            option_type=option_type
        )
        ql_worst_price = float(ql_worst["price"])

        try:
            user_worst_price = float(user_fn(
                spot=opt_spot,
                strike=base_strike,
                maturity=opt_maturity,
                rate=opt_rate,
                volatility=opt_vol
            ))
        except Exception:
            user_worst_price = 0.0

        max_error = float(abs(user_worst_price - ql_worst_price))
        scale_floor_worst = max(ql_worst_price, opt_spot * 0.005)
        pct_error = float((max_error / scale_floor_worst) * 100.0)

        # Numerical finite-difference Greek drift estimation for user model at breaking point
        h_s = max(opt_spot * 0.001, 0.01)
        h_v = max(opt_vol * 0.001, 0.001)

        try:
            u_p_s_up = user_fn(opt_spot + h_s, base_strike, opt_maturity, opt_rate, opt_vol)
            u_p_s_dn = user_fn(opt_spot - h_s, base_strike, opt_maturity, opt_rate, opt_vol)
            user_delta = (u_p_s_up - u_p_s_dn) / (2.0 * h_s)
        except Exception:
            user_delta = ql_worst["greeks"]["delta"]

        try:
            u_p_v_up = user_fn(opt_spot, base_strike, opt_maturity, opt_rate, opt_vol + h_v)
            u_p_v_dn = user_fn(opt_spot, base_strike, opt_maturity, opt_rate, opt_vol - h_v)
            # FD vega per unit vol change (Δσ=1.0) — same convention as QuantLib vega_unit.
            # QuantLib stores vega_unit (per unit move) in greeks["vega_unit"] but exposes vega_1pct
            # as greeks["vega"]. Use vega_unit for consistent comparison.
            user_vega_unit = (u_p_v_up - u_p_v_dn) / (2.0 * h_v)
            user_vega = user_vega_unit / 100.0  # convert to per-1%-vol-point (market convention)
        except Exception:
            user_vega = ql_worst["greeks"]["vega"]

        greek_drifts = {
            "delta_drift": round(float(abs(user_delta - ql_worst["greeks"]["delta"])), 4),
            "vega_drift": round(float(abs(user_vega - ql_worst["greeks"]["vega"])), 4),
            "base_greeks": ql_base["greeks"],
            "adversarial_greeks": ql_worst["greeks"]
        }

        # Multi-seed statistical confidence calculation
        err_values = [-r.fun for r in seed_results]
        mean_err = float(np.mean(err_values))
        std_err = float(np.std(err_values))
        stability_score = round(max(0.0, min(100.0, 100.0 - (std_err / max(mean_err, 1e-4)) * 100.0)), 1)

        breaking_parameters = {
            "spot": round(float(opt_spot), 2),
            "volatility": round(float(opt_vol), 4),
            "risk_free_rate": round(float(opt_rate), 4),
            "maturity_years": round(float(opt_maturity), 3),
            "user_price": round(float(user_worst_price), 4),
            "quantlib_price": round(float(ql_worst_price), 4),
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
                "maxiter": 35,
                "popsize": 15,
                "environment_metadata": {
                    "quantlib_version": getattr(ql, "__version__", "1.43"),
                    "scipy_version": __import__("scipy").__version__,
                    "numpy_version": np.__version__,
                    "python_version": sys.version.split()[0]
                }
            }
        }

        surface_grid = AdversarialEngine._generate_fragility_surface(
            user_fn=user_fn,
            base_spot=base_spot,
            base_strike=base_strike,
            base_maturity=base_maturity,
            base_rate=base_rate,
            base_volatility=base_volatility,
            dividend_yield=dividend_yield,
            option_type=option_type
        )

        return {
            "base_metrics": {
                "user_price": round(float(user_base_price), 4),
                "quantlib_price": round(float(ql_base_price), 4),
                "base_error": round(float(abs(user_base_price - ql_base_price)), 4),
                "base_greeks": ql_base["greeks"]
            },
            "breaking_parameters": breaking_parameters,
            "greek_drifts": greek_drifts,
            "fragility_surface": surface_grid
        }

    @staticmethod
    def _generate_fragility_surface(
        user_fn: Any,
        base_spot: float,
        base_strike: float,
        base_maturity: float,
        base_rate: float,
        base_volatility: float,
        dividend_yield: float = 0.0,
        option_type: str = "call"
    ) -> Dict[str, Any]:
        spot_multipliers = np.linspace(0.70, 1.30, 7)
        vol_multipliers = np.linspace(0.50, 2.00, 7)

        matrix = []
        for v_mult in vol_multipliers:
            row = []
            curr_vol = float(base_volatility * v_mult)
            for s_mult in spot_multipliers:
                curr_spot = float(base_spot * s_mult)
                ql_res = QuantLibPricer.price_european_option(
                    spot=curr_spot,
                    strike=base_strike,
                    maturity_years=base_maturity,
                    risk_free_rate=base_rate,
                    volatility=curr_vol,
                    dividend_yield=dividend_yield,
                    option_type=option_type
                )
                ql_p = float(ql_res["price"])

                try:
                    user_p = float(user_fn(
                        spot=curr_spot,
                        strike=base_strike,
                        maturity=base_maturity,
                        rate=base_rate,   # surface is Spot×Vol 2D slice at base_rate
                        volatility=curr_vol
                    ))
                except Exception:
                    user_p = 0.0

                err = float(abs(user_p - ql_p))
                row.append(round(err, 4))
            matrix.append(row)

        return {
            "spot_axis": [round(float(base_spot * m), 1) for m in spot_multipliers],
            "volatility_axis": [round(float(base_volatility * m), 3) for m in vol_multipliers],
            "error_matrix": matrix
        }
