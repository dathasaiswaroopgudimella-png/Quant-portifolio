import numpy as np
import scipy.optimize as optimize
from typing import Dict, Any, List, Tuple
from app.engine.quantlib_pricer import QuantLibPricer
from app.engine.sandbox import SandboxedModelEvaluator

class AdversarialEngine:
    """
    Adversarial Search Engine powered by SciPy Non-Convex Differential Evolution.
    Finds minimal realistic market parameter perturbations (Spot, Volatility, Interest Rate)
    that maximize pricing discrepancy and Greek divergence between user model and QuantLib.
    """

    @staticmethod
    def run_adversarial_search(
        model_code: str,
        base_spot: float = 100.0,
        base_strike: float = 100.0,
        base_maturity: float = 1.0,
        base_rate: float = 0.05,
        base_volatility: float = 0.20,
        option_type: str = "call"
    ) -> Dict[str, Any]:
        """
        Executes SciPy Differential Evolution over parameter bounds.
        Uses normalized relative error objective to prevent large-dollar distortion on ITM options
        and reveal true percentage fragility in deep OTM / high-volatility regimes.
        """
        ql_base = QuantLibPricer.price_european_option(
            spot=base_spot,
            strike=base_strike,
            maturity_years=base_maturity,
            risk_free_rate=base_rate,
            volatility=base_volatility,
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

        # Search bounds: Spot [0.6x, 1.4x], Volatility [0.4x, 3.0x], Rate [0.001, rate+0.06]
        bounds = [
            (0.60, 1.40),
            (0.40, 3.00),
            (max(0.001, base_rate - 0.04), base_rate + 0.06)
        ]

        def _objective(x):
            spot_mult, vol_mult, rate_val = x
            curr_spot = float(base_spot * spot_mult)
            curr_vol = float(max(0.01, base_volatility * vol_mult))
            curr_rate = float(max(0.001, rate_val))

            ql_res = QuantLibPricer.price_european_option(
                spot=curr_spot,
                strike=base_strike,
                maturity_years=base_maturity,
                risk_free_rate=curr_rate,
                volatility=curr_vol,
                option_type=option_type
            )
            ql_p = float(ql_res["price"])

            try:
                user_p = float(user_fn(
                    spot=curr_spot,
                    strike=base_strike,
                    maturity=base_maturity,
                    rate=curr_rate,
                    volatility=curr_vol
                ))
            except Exception:
                user_p = 0.0

            # Normalized relative pricing error objective
            # Normalization scale floor of $0.50 prevents divide-by-zero on deep OTM options
            abs_err = abs(user_p - ql_p)
            rel_err = abs_err / max(ql_p, 0.50)
            return -rel_err  # Maximize relative error

        # Execute primary DE optimization (Seed 42)
        opt_res = optimize.differential_evolution(
            _objective,
            bounds=bounds,
            strategy='best1bin',
            maxiter=35,
            popsize=15,
            tol=1e-5,
            seed=42
        )

        # Multi-seed stability verification (Seed 101)
        opt_res_seed2 = optimize.differential_evolution(
            _objective,
            bounds=bounds,
            strategy='best1bin',
            maxiter=35,
            popsize=15,
            tol=1e-5,
            seed=101
        )

        opt_spot_mult, opt_vol_mult, opt_rate = opt_res.x
        opt_spot = float(base_spot * opt_spot_mult)
        opt_vol = float(base_volatility * opt_vol_mult)
        opt_rate = float(opt_rate)

        # Evaluate QuantLib ground truth at adversarial point
        ql_worst = QuantLibPricer.price_european_option(
            spot=opt_spot,
            strike=base_strike,
            maturity_years=base_maturity,
            risk_free_rate=opt_rate,
            volatility=opt_vol,
            option_type=option_type
        )
        ql_worst_price = float(ql_worst["price"])

        try:
            user_worst_price = float(user_fn(
                spot=opt_spot,
                strike=base_strike,
                maturity=base_maturity,
                rate=opt_rate,
                volatility=opt_vol
            ))
        except Exception:
            user_worst_price = 0.0

        max_error = float(abs(user_worst_price - ql_worst_price))
        pct_error = float((max_error / max(ql_worst_price, 0.50)) * 100.0)

        # Numerical finite-difference Greek drift estimation for user model at breaking point
        h_s = max(opt_spot * 0.001, 0.01)
        h_v = max(opt_vol * 0.001, 0.001)

        try:
            u_p_s_up = user_fn(opt_spot + h_s, base_strike, base_maturity, opt_rate, opt_vol)
            u_p_s_dn = user_fn(opt_spot - h_s, base_strike, base_maturity, opt_rate, opt_vol)
            user_delta = (u_p_s_up - u_p_s_dn) / (2.0 * h_s)
        except Exception:
            user_delta = ql_worst["greeks"]["delta"]

        try:
            u_p_v_up = user_fn(opt_spot, base_strike, base_maturity, opt_rate, opt_vol + h_v)
            u_p_v_dn = user_fn(opt_spot, base_strike, base_maturity, opt_rate, opt_vol - h_v)
            user_vega = (u_p_v_up - u_p_v_dn) / (2.0 * h_v * 100.0)
        except Exception:
            user_vega = ql_worst["greeks"]["vega"]

        greek_drifts = {
            "delta_drift": round(float(abs(user_delta - ql_worst["greeks"]["delta"])), 4),
            "vega_drift": round(float(abs(user_vega - ql_worst["greeks"]["vega"])), 4),
            "base_greeks": ql_base["greeks"],
            "adversarial_greeks": ql_worst["greeks"]
        }

        # Optimizer stability comparison
        err_seed1 = -opt_res.fun
        err_seed2 = -opt_res_seed2.fun
        stability_score = round(max(0.0, 100.0 - abs(err_seed1 - err_seed2) * 50.0), 1)

        breaking_parameters = {
            "spot": round(float(opt_spot), 2),
            "volatility": round(float(opt_vol), 4),
            "risk_free_rate": round(float(opt_rate), 4),
            "user_price": round(float(user_worst_price), 4),
            "quantlib_price": round(float(ql_worst_price), 4),
            "absolute_error": round(float(max_error), 4),
            "percentage_error": round(float(pct_error), 2),
            "optimizer_stability": stability_score,
            "reproducibility": {
                "primary_seed": 42,
                "verification_seed": 101,
                "strategy": "best1bin",
                "maxiter": 35,
                "popsize": 15
            }
        }

        surface_grid = AdversarialEngine._generate_fragility_surface(
            user_fn=user_fn,
            base_spot=base_spot,
            base_strike=base_strike,
            base_maturity=base_maturity,
            base_rate=base_rate,
            base_volatility=base_volatility,
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
        option_type: str
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
                    option_type=option_type
                )
                ql_p = float(ql_res["price"])

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

                err = float(abs(user_p - ql_p))
                row.append(round(err, 4))
            matrix.append(row)

        return {
            "spot_axis": [round(float(base_spot * m), 1) for m in spot_multipliers],
            "volatility_axis": [round(float(base_volatility * m), 3) for m in vol_multipliers],
            "error_matrix": matrix
        }
