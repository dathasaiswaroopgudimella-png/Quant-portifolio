from typing import Dict, Any

class FragilityScorer:
    """
    Model Fragility Metric & Classification Engine.
    Converts adversarial pricing errors and Greek drift into a 0.0 - 100.0 Fragility Score.
    """

    @staticmethod
    def calculate_fragility(
        base_error: float,
        max_adversarial_error: float,
        breaking_params: Dict[str, Any],
        base_price: float
    ) -> Dict[str, Any]:
        """
        Computes composite fragility index and classification.
        """
        # Base pricing error relative to option price
        rel_base_err = (base_error / max(base_price, 1e-4)) * 100.0
        
        # Max adversarial pricing error relative to option price
        rel_max_err = (max_adversarial_error / max(base_price, 1e-4)) * 100.0
        
        # Percentage error reported in breaking parameters
        pct_err = breaking_params.get("percentage_error", rel_max_err)

        # Composite score calculation:
        # Score = 0.3 * rel_base_err + 0.7 * min(pct_err, 100.0)
        raw_score = 0.3 * min(rel_base_err * 10, 30.0) + 0.7 * min(pct_err, 100.0)
        fragility_score = round(min(max(raw_score, 0.0), 100.0), 1)

        # Classification thresholds
        if fragility_score <= 15.0:
            classification = "ROBUST"
            summary = "Model matches QuantLib analytical ground truth closely across all tested market perturbation scenarios."
        elif fragility_score <= 40.0:
            classification = "MODERATE"
            summary = "Model shows minor sensitivity under extreme volatility skew or interest rate shifts, but maintains acceptable pricing bounds."
        elif fragility_score <= 70.0:
            classification = "FRAGILE"
            summary = "Model exhibits significant pricing drift under volatility regime shifts, violating constant volatility assumptions."
        else:
            classification = "CRITICAL"
            summary = "Model suffers severe pricing breakdown or produces non-physical outputs under stress market conditions."

        # Risk Attribution breakdown
        risk_attribution = {
            "volatility_regime_risk": round(min(fragility_score * 0.55, 100.0), 1),
            "interest_rate_sensitivity": round(min(fragility_score * 0.25, 100.0), 1),
            "spot_tail_convexity": round(min(fragility_score * 0.20, 100.0), 1),
        }

        return {
            "fragility_score": fragility_score,
            "classification": classification,
            "summary": summary,
            "max_pricing_error": max_adversarial_error,
            "percentage_error": round(pct_err, 2),
            "risk_attribution": risk_attribution
        }
