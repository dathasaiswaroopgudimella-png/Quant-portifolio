import asyncio
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.domain import FinancialModel, ValidationRun, Report, Assumption
from app.schemas.schemas import ValidationCreate, ValidationResponse, HexagonalScores
from app.engine.adversarial_engine import AdversarialEngine
from app.engine.fragility_scorer import FragilityScorer
from app.engine.expectations import ModelExpectationSuite
from app.services.report_ai import OpenRouterReportService

router = APIRouter(prefix="/validations", tags=["Validation Engine"])

@router.post("", response_model=ValidationResponse, status_code=status.HTTP_201_CREATED)
async def create_validation_run(
    req: ValidationCreate,
    db: AsyncSession = Depends(get_db)
):
    # Fetch target financial model
    result = await db.execute(select(FinancialModel).where(FinancialModel.id == req.model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Target financial model not found.")

    # Fetch model assumptions for baseline evaluation
    assumptions_res = await db.execute(select(Assumption).where(Assumption.model_id == model.id))
    assumptions_list = [
        {"name": a.name, "category": a.category, "mathematical_form": a.mathematical_form}
        for a in assumptions_res.scalars().all()
    ]

    # Step 1: Run SciPy Differential Evolution Adversarial Search in ThreadPool (Non-blocking async)
    loop = asyncio.get_event_loop()
    adv_res = await loop.run_in_executor(
        None,
        lambda: AdversarialEngine.run_adversarial_search(
            model_code=model.code,
            base_spot=req.spot_price,
            base_strike=req.strike_price,
            base_maturity=req.time_to_maturity,
            base_rate=req.risk_free_rate,
            base_volatility=req.volatility,
            option_type=req.option_type
        )
    )

    base_metrics = adv_res["base_metrics"]
    breaking_params = adv_res["breaking_parameters"]
    greek_drifts = adv_res.get("greek_drifts", {})
    surface = adv_res["fragility_surface"]

    # Step 2: Compute Fragility Index & Numerical Sensitivity Attribution
    fragility_data = FragilityScorer.calculate_fragility(
        base_error=base_metrics["base_error"],
        max_adversarial_error=breaking_params["absolute_error"],
        breaking_params=breaking_params,
        base_price=base_metrics["quantlib_price"],
        greek_drifts=greek_drifts
    )

    # Step 3: Compute Independent 6-axis Radar Metrics
    hex_scores = OpenRouterReportService.compute_hexagonal_scores(
        fragility_score=fragility_data["fragility_score"],
        pct_error=breaking_params.get("percentage_error", 0.0),
        greeks=base_metrics.get("base_greeks", {}),
        greek_drifts=greek_drifts,
        assumptions=assumptions_list,
        breaking_params=breaking_params
    )

    # Step 4: Run Formal Verification Expectation Suite
    expectations = ModelExpectationSuite.evaluate_expectations(
        user_price=base_metrics["user_price"],
        quantlib_price=base_metrics["quantlib_price"],
        greeks=base_metrics["base_greeks"],
        spot=req.spot_price,
        strike=req.strike_price,
        maturity=req.time_to_maturity,
        rate=req.risk_free_rate,
        option_type=req.option_type
    )

    # Step 5: Save ValidationRun
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

    # Step 6: Generate Executive Governance Summary
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
    await db.refresh(val_run)
    
    # Attach hex_scores dynamically to response
    res_data = ValidationResponse.model_validate(val_run)
    res_data.hexagonal_scores = HexagonalScores(**hex_scores)
    return res_data

@router.get("", response_model=List[ValidationResponse])
async def list_validations(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ValidationRun).order_by(ValidationRun.created_at.desc()))
    runs = result.scalars().all()
    if not runs:
        from app.db.seed import seed_initial_data
        await seed_initial_data(db)
        result = await db.execute(select(ValidationRun).order_by(ValidationRun.created_at.desc()))
        runs = result.scalars().all()

    res_list = []
    for r in runs:
        item = ValidationResponse.model_validate(r)
        hex_scores = OpenRouterReportService.compute_hexagonal_scores(
            fragility_score=r.fragility_score or 0.0,
            pct_error=r.breaking_parameters.get("percentage_error", 0.0) if r.breaking_parameters else 0.0,
            greeks=r.greek_drifts.get("base_greeks", {}) if r.greek_drifts else {},
            greek_drifts=r.greek_drifts or {},
            breaking_params=r.breaking_parameters or {}
        )
        item.hexagonal_scores = HexagonalScores(**hex_scores)
        res_list.append(item)
    return res_list

@router.get("/{validation_id}", response_model=ValidationResponse)
async def get_validation(validation_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ValidationRun).where(ValidationRun.id == validation_id))
    val_run = result.scalar_one_or_none()
    if not val_run:
        raise HTTPException(status_code=404, detail="Validation run not found.")
    item = ValidationResponse.model_validate(val_run)
    hex_scores = OpenRouterReportService.compute_hexagonal_scores(
        fragility_score=val_run.fragility_score or 0.0,
        pct_error=val_run.breaking_parameters.get("percentage_error", 0.0) if val_run.breaking_parameters else 0.0,
        greeks=val_run.greek_drifts.get("base_greeks", {}) if val_run.greek_drifts else {},
        greek_drifts=val_run.greek_drifts or {},
        breaking_params=val_run.breaking_parameters or {}
    )
    item.hexagonal_scores = HexagonalScores(**hex_scores)
    return item

@router.get("/{validation_id}/report")
async def get_validation_report(validation_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Report).where(Report.run_id == validation_id))
    rep = result.scalar_one_or_none()
    if not rep:
        raise HTTPException(status_code=404, detail="Report for validation run not found.")
    return rep
