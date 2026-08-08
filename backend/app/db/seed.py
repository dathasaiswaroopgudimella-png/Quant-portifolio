import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.domain import FinancialModel, ValidationRun, Report, Assumption
from app.engine.adversarial_engine import AdversarialEngine
from app.engine.fragility_scorer import FragilityScorer
from app.engine.expectations import ModelExpectationSuite
from app.engine.assumption_engine import AssumptionExtractor
from app.services.report_ai import OpenRouterReportService

logger = logging.getLogger(__name__)

SEED_MODELS = [
    {
        "name": "Standard Black-Scholes Call",
        "description": "Baseline analytical European call option pricing function with constant volatility and interest rate assumptions.",
        "asset_class": "Equity Options",
        "code": """def black_scholes_call(S, K, T, r, sigma):
    import math
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return 0.0
    d1 = (math.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*math.sqrt(T))
    d2 = d1 - sigma*math.sqrt(T)
    N = lambda x: 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
    return S * N(d1) - K * math.exp(-r*T) * N(d2)
""",
        "params": {
            "spot_price": 100.0,
            "strike_price": 100.0,
            "time_to_maturity": 1.0,
            "risk_free_rate": 0.05,
            "volatility": 0.20,
            "option_type": "call"
        }
    },
    {
        "name": "Garman-Kohlhagen Foreign Exchange (FX) Model",
        "description": "Analytical Garman-Kohlhagen FX option valuation model incorporating domestic risk-free rate r=4% and foreign risk-free rate rf=2%.",
        "asset_class": "FX Options",
        "code": """def garman_kohlhagen_fx(S, K, T, r, sigma):
    import math
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return 0.0
    rf = 0.02
    d1 = (math.log(S/K) + (r - rf + 0.5*sigma**2)*T) / (sigma*math.sqrt(T))
    d2 = d1 - sigma*math.sqrt(T)
    N = lambda x: 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
    return S * math.exp(-rf*T) * N(d1) - K * math.exp(-r*T) * N(d2)
""",
        "params": {
            "spot_price": 1.10,
            "strike_price": 1.10,
            "time_to_maturity": 0.5,
            "risk_free_rate": 0.04,
            "volatility": 0.12,
            "option_type": "call"
        }
    }
]

async def seed_initial_data(db: AsyncSession) -> None:
    """
    Seeds database with 2 real-world quantitative option models AND pre-calculates
    full adversarial validation runs with QuantLib ground truth, Greek drifts, 3D fragility surfaces,
    and SR 11-7 model risk reports.
    """
    result = await db.execute(select(FinancialModel))
    existing_models = result.scalars().all()
    if existing_models:
        logger.info(f"Database already contains {len(existing_models)} models. Seed skipped.")
        return

    logger.info("Seeding database with 2 real-world quantitative models and completed adversarial validation runs...")

    for spec in SEED_MODELS:
        model = FinancialModel(
            name=spec["name"],
            description=spec["description"],
            asset_class=spec["asset_class"],
            code=spec["code"]
        )
        db.add(model)
        await db.flush()

        # Extract symbolic AST assumptions
        extracted = AssumptionExtractor.extract_assumptions(spec["code"])
        assumptions_list = []
        for a in extracted:
            ass_obj = Assumption(
                model_id=model.id,
                name=a["name"],
                category=a["category"],
                mathematical_form=a["mathematical_form"],
                description=a["description"],
                is_violated_in_stress=a["is_violated_in_stress"]
            )
            db.add(ass_obj)
            assumptions_list.append(a)

        # Run real Adversarial DE Search & QuantLib validation
        p = spec["params"]
        adv_res = AdversarialEngine.run_adversarial_search(
            model_code=spec["code"],
            base_spot=p["spot_price"],
            base_strike=p["strike_price"],
            base_maturity=p["time_to_maturity"],
            base_rate=p["risk_free_rate"],
            base_volatility=p["volatility"],
            option_type=p["option_type"]
        )

        base_metrics = adv_res["base_metrics"]
        breaking_params = adv_res["breaking_parameters"]
        greek_drifts = adv_res.get("greek_drifts", {})
        surface = adv_res["fragility_surface"]

        fragility_data = FragilityScorer.calculate_fragility(
            base_error=base_metrics["base_error"],
            max_adversarial_error=breaking_params["absolute_error"],
            breaking_params=breaking_params,
            base_price=base_metrics["quantlib_price"],
            greek_drifts=greek_drifts
        )

        hex_scores = OpenRouterReportService.compute_hexagonal_scores(
            fragility_score=fragility_data["fragility_score"],
            pct_error=breaking_params.get("percentage_error", 0.0),
            greeks=base_metrics.get("base_greeks", {}),
            greek_drifts=greek_drifts,
            assumptions=assumptions_list,
            breaking_params=breaking_params
        )

        expectations = ModelExpectationSuite.evaluate_expectations(
            user_price=base_metrics["user_price"],
            quantlib_price=base_metrics["quantlib_price"],
            greeks=base_metrics["base_greeks"],
            spot=p["spot_price"],
            strike=p["strike_price"],
            maturity=p["time_to_maturity"],
            rate=p["risk_free_rate"],
            option_type=p["option_type"]
        )

        val_run = ValidationRun(
            model_id=model.id,
            status="COMPLETED",
            fragility_score=fragility_data["fragility_score"],
            classification=fragility_data["classification"],
            max_pricing_error=breaking_params["absolute_error"],
            breaking_parameters=breaking_params,
            greek_drifts=greek_drifts,
            fragility_surface=surface
        )
        db.add(val_run)
        await db.flush()

        exec_summary = await OpenRouterReportService.generate_executive_summary(
            model_name=model.name,
            fragility_score=fragility_data["fragility_score"],
            classification=fragility_data["classification"],
            breaking_params=breaking_params,
            assumptions=assumptions_list
        )

        sr11_7_payload = {
            "framework": "Federal Reserve SR 11-7 Aligned Model Validation Tooling",
            "model_name": model.name,
            "conceptual_soundness": "PASS" if fragility_data["fragility_score"] < 40.0 else "WARNING",
            "ongoing_monitoring": "REQUIRED",
            "sensitivity_analysis": "PASSED_DIFFERENTIAL_EVOLUTION_SEARCH",
            "actionable_recommendation": fragility_data["actionable_recommendation"],
            "expectations_suite": expectations
        }

        report_payload = {
            "summary": fragility_data["summary"],
            "actionable_recommendation": fragility_data["actionable_recommendation"],
            "risk_attribution": fragility_data["risk_attribution"],
            "base_metrics": base_metrics,
            "breaking_parameters": breaking_params,
            "expectations": expectations,
            "hexagonal_scores": hex_scores
        }

        report = Report(
            run_id=val_run.id,
            executive_summary=exec_summary,
            sr11_7_compliance=sr11_7_payload,
            report_data=report_payload
        )
        db.add(report)

    await db.commit()
    logger.info("Successfully seeded 2 real-world quantitative models and validation runs.")
