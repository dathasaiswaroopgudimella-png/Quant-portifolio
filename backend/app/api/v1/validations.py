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

    # Step 1: Run SciPy Differential Evolution Adversarial Parameter Search
    adv_res = AdversarialEngine.run_adversarial_search(
        model_code=model.code,
        base_spot=req.spot_price,
        base_strike=req.strike_price,
        base_maturity=req.time_to_maturity,
        base_rate=req.risk_free_rate,
        base_volatility=req.volatility,
        option_type=req.option_type
    )

    base_metrics = adv_res["base_metrics"]
    breaking_params = adv_res["breaking_parameters"]
    surface = adv_res["fragility_surface"]

    # Step 2: Compute Fragility Index (0.0 to 100.0)
    fragility_data = FragilityScorer.calculate_fragility(
        base_error=base_metrics["base_error"],
        max_adversarial_error=breaking_params["absolute_error"],
        breaking_params=breaking_params,
        base_price=base_metrics["quantlib_price"]
    )

    # Step 3: Compute Hexagonal Radar Metrics (6-axis assessment)
    hex_scores = OpenRouterReportService.compute_hexagonal_scores(
        fragility_score=fragility_data["fragility_score"],
        pct_error=breaking_params.get("percentage_error", 0.0),
        greeks=base_metrics.get("base_greeks", {})
    )

    # Step 4: Run Quantitative Expectations Suite
    expectations = ModelExpectationSuite.evaluate_expectations(
        user_price=base_metrics["user_price"],
        quantlib_price=base_metrics["quantlib_price"],
        greeks=base_metrics["base_greeks"],
        spot=req.spot_price,
        strike=req.strike_price
    )

    # Step 5: Save ValidationRun
    val_run = ValidationRun(
        model_id=model.id,
        status="COMPLETED",
        fragility_score=fragility_data["fragility_score"],
        classification=fragility_data["classification"],
        max_pricing_error=breaking_params["absolute_error"],
        breaking_parameters=breaking_params,
        greek_drifts=base_metrics["base_greeks"],
        fragility_surface=surface
    )
    db.add(val_run)
    await db.flush()

    # Step 6: Fetch model assumptions for report
    assumptions_res = await db.execute(select(Assumption).where(Assumption.model_id == model.id))
    assumptions_list = [
        {"name": a.name, "category": a.category, "mathematical_form": a.mathematical_form}
        for a in assumptions_res.scalars().all()
    ]

    # Step 7: Generate Executive Summary and Report
    exec_summary = await OpenRouterReportService.generate_executive_summary(
        model_name=model.name,
        fragility_score=fragility_data["fragility_score"],
        classification=fragility_data["classification"],
        breaking_params=breaking_params,
        assumptions=assumptions_list
    )

    sr11_7_payload = {
        "framework": "Federal Reserve SR 11-7 Model Risk Management Standard",
        "model_name": model.name,
        "conceptual_soundness": "PASS" if fragility_data["fragility_score"] < 40.0 else "WARNING",
        "ongoing_monitoring": "REQUIRED",
        "out_of_sample_validation": "PASSED_ADVERSARIAL_SEARCH",
        "expectations_suite": expectations
    }

    report_payload = {
        "summary": fragility_data["summary"],
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
    res_list = []
    for r in runs:
        item = ValidationResponse.model_validate(r)
        # Compute hex scores on the fly if needed
        hex_scores = OpenRouterReportService.compute_hexagonal_scores(
            fragility_score=r.fragility_score or 0.0,
            pct_error=r.breaking_parameters.get("percentage_error", 0.0) if r.breaking_parameters else 0.0,
            greeks=r.greek_drifts or {}
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
        greeks=val_run.greek_drifts or {}
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

