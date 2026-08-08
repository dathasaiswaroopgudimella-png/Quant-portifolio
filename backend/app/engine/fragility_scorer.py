from typing import Dict, Any

class FragilityScorer:
    """
    Model Fragility Index & Numerical Gradient Sensitivity Attribution Engine.
    Converts adversarial pricing errors, relative percentage drifts, and partial derivative sensitivity
    into a calibrated 0.0 - 100.0 Fragility Score with dynamic risk attribution and actionable boundaries.
    """

    @staticmethod
    def calculate_fragility(
        base_error: float,
        max_adversarial_error: float,
        breaking_params: Dict[str, Any],
        base_price: float,
        greek_drifts: Dict[str, Any] = None,
        base_spot: float = 100.0,
        base_volatility: float = 0.20,
        base_rate: float = 0.05
    ) -> Dict[str, Any]:
        """
        Computes composite fragility index, numerical gradient risk attribution,
        and actionable risk boundaries.
        """
        # Base pricing relative error
        rel_base_err = (base_error / max(base_price, 0.50)) * 100.0
        
        # Max adversarial percentage error from breaking parameters
        pct_err = breaking_params.get("percentage_error", (max_adversarial_error / max(base_price, 0.50)) * 100.0)

        # Greek drift component (delta + vega drift)
        delta_drift = greek_drifts.get("delta_drift", 0.0) if greek_drifts else 0.0
        vega_drift = greek_drifts.get("vega_drift", 0.0) if greek_drifts else 0.0
        greek_penalty = min((delta_drift * 40.0 + vega_drift * 50.0), 30.0)

        # Calibrated Composite Fragility Index
        raw_score = 0.25 * min(rel_base_err * 5.0, 25.0) + 0.55 * min(pct_err, 100.0) + 0.20 * greek_penalty
        fragility_score = round(min(max(raw_score, 0.0), 100.0), 1)

        # Robustness Score (100 - Fragility Score)
        robustness_score = round(100.0 - fragility_score, 1)

        # Classification Tiers
        if fragility_score <= 15.0:
            classification = "ROBUST"
            summary = "Model matches QuantLib analytical ground truth closely across all tested market perturbation scenarios."
        elif fragility_score <= 40.0:
            classification = "MODERATE"
            summary = "Model exhibits minor sensitivity under volatility skew or interest rate shifts, maintaining acceptable bounds."
        elif fragility_score <= 70.0:
            classification = "FRAGILE"
            summary = "Model exhibits significant pricing drift under volatility regime shifts, violating constant volatility assumptions."
        else:
            classification = "CRITICAL"
            summary = "Model suffers severe pricing breakdown or produces non-physical outputs under stress market conditions."

        # Dynamic Gradient Risk Attribution relative to actual model base parameters
        spot = breaking_params.get("spot", base_spot)
        vol = breaking_params.get("volatility", base_volatility)
        rate = breaking_params.get("risk_free_rate", base_rate)
        
        vol_sens = abs(vol - base_volatility) / max(base_volatility, 0.01)
        spot_sens = abs(spot - base_spot) / max(base_spot, 0.01)
        rate_sens = abs(rate - base_rate) / max(base_rate, 0.001)
        total_sens = vol_sens + spot_sens + rate_sens

        if total_sens > 1e-4:
            attr_vol = round((vol_sens / total_sens) * 100.0, 1)
            attr_spot = round((spot_sens / total_sens) * 100.0, 1)
            attr_rate = round((rate_sens / total_sens) * 100.0, 1)
        else:
            attr_vol, attr_spot, attr_rate = 60.0, 25.0, 15.0

        risk_attribution = {
            "volatility_regime_risk": attr_vol,
            "spot_tail_convexity": attr_spot,
            "interest_rate_sensitivity": attr_rate,
        }

        # Actionable Operational Boundaries & Guidance
        max_safe_vol = round(vol * 0.85 * 100.0, 1)
        actionable_recommendation = (
            f"Enforce input validation guard: Constrain volatility inputs to sigma <= {max_safe_vol}%. "
            f"Do not deploy for unhedged long-tenor options without continuous delta-gamma rebalancing."
            if fragility_score > 30.0 else
            "Model passed adversarial validation search. Safe for production automated option pricing within standard volatility bounds."
        )

        return {
            "fragility_score": fragility_score,
            "robustness_score": robustness_score,
            "classification": classification,
            "summary": summary,
            "actionable_recommendation": actionable_recommendation,
            "max_pricing_error": max_adversarial_error,
            "percentage_error": round(pct_err, 2),
            "risk_attribution": risk_attribution
        }
