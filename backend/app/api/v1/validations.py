import asyncio
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.domain import FinancialModel, ValidationRun, Report, Assumption
from app.schemas.schemas import ValidationCreate, ValidationResponse, HexagonalScores
from app.engine.multi_agent_system import MultiAgentQuantPipeline
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

    # Execute complete multi-agent pipeline
    loop = asyncio.get_running_loop()
    pipeline_res = await loop.run_in_executor(
        None,
        lambda: asyncio.run(
            MultiAgentQuantPipeline.execute_full_validation_pipeline(
                model_name=model.name,
                model_code=model.code,
                spot=req.spot_price,
                strike=req.strike_price,
                maturity=req.time_to_maturity,
                rate=req.risk_free_rate,
                volatility=req.volatility,
                dividend_yield=req.dividend_yield,
                option_type=req.option_type
            )
        )
    )

    fragility_data = pipeline_res["fragility_data"]
    breaking_params = pipeline_res["breaking_parameters"]
    greek_drifts = pipeline_res["greek_drifts"]
    surface = pipeline_res["fragility_surface"]
    hex_scores = pipeline_res["hexagonal_scores"]
    exec_summary = pipeline_res["executive_summary"]
    sr11_7_payload = pipeline_res["sr11_7_payload"]
    report_payload = pipeline_res["report_payload"]

    # Save ValidationRun
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

    report = Report(
        run_id=val_run.id,
        executive_summary=exec_summary,
        sr11_7_compliance=sr11_7_payload,
        report_data=report_payload
    )
    db.add(report)

    await db.commit()
    await db.refresh(val_run)

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
