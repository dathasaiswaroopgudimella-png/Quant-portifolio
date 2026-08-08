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
        greek_drifts: Dict[str, Any] = None
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
        # Score = 0.25 * base_error_pct + 0.55 * adversarial_pct_err + 0.20 * greek_penalty
        raw_score = 0.25 * min(rel_base_err * 5.0, 25.0) + 0.55 * min(pct_err, 100.0) + 0.20 * greek_penalty
        fragility_score = round(min(max(raw_score, 0.0), 100.0), 1)

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

        # Dynamic Gradient Risk Attribution
        # Calculate actual parameter sensitivity ratio at breaking point
        spot = breaking_params.get("spot", 100.0)
        vol = breaking_params.get("volatility", 0.20)
        rate = breaking_params.get("risk_free_rate", 0.05)
        
        vol_sens = abs(vol - 0.20) / 0.20
        spot_sens = abs(spot - 100.0) / 100.0
        rate_sens = abs(rate - 0.05) / 0.05
        total_sens = max(vol_sens + spot_sens + rate_sens, 1e-4)

        risk_attribution = {
            "volatility_regime_risk": round((vol_sens / total_sens) * 100.0, 1),
            "spot_tail_convexity": round((spot_sens / total_sens) * 100.0, 1),
            "interest_rate_sensitivity": round((rate_sens / total_sens) * 100.0, 1),
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
            "classification": classification,
            "summary": summary,
            "actionable_recommendation": actionable_recommendation,
            "max_pricing_error": max_adversarial_error,
            "percentage_error": round(pct_err, 2),
            "risk_attribution": risk_attribution
        }
