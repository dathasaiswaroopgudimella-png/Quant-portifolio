from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.api.deps import get_current_user_optional
from app.models.domain import FinancialModel, Assumption, User
from app.schemas.schemas import ModelCreate, ModelResponse, AssumptionResponse, ModelSynthesizeRequest
from app.engine.ast_parser import parse_and_validate_model_code, ASTSecurityError
from app.engine.assumption_engine import AssumptionExtractor
from app.services.report_ai import OpenRouterReportService

router = APIRouter(prefix="/models", tags=["Model Registry"])

DEFAULT_BS_CODE = """def black_scholes_call(S, K, T, r, sigma):
    import math
    d1 = (math.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*math.sqrt(T))
    d2 = d1 - sigma*math.sqrt(T)
    N = lambda x: 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
    return S * N(d1) - K * math.exp(-r*T) * N(d2)
"""

@router.post("/synthesize", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
async def synthesize_and_upload_model(
    req: ModelSynthesizeRequest,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Synthesizes executable Python option model from natural language / formula prompt via OpenRouter AI.
    """
    synth = await OpenRouterReportService.synthesize_model_from_prompt(
        prompt=req.prompt,
        asset_class=req.asset_class or "Equity Options"
    )

    model_in = ModelCreate(
        name=synth["name"],
        description=synth["description"],
        asset_class=synth["asset_class"],
        code=synth["code"]
    )
    return await upload_model(model_in=model_in, db=db, user=user)

@router.post("/upload", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
async def upload_model(
    model_in: ModelCreate,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional)
):
    # Step 1: Validate AST security & extract parameter signature
    try:
        parsed_info = parse_and_validate_model_code(model_in.code)
    except ASTSecurityError as e:
        raise HTTPException(status_code=400, detail=f"AST Security Validation Failed: {str(e)}")

    # Step 2: Create model record
    new_model = FinancialModel(
        user_id=user.id if user else None,
        name=model_in.name,
        description=model_in.description,
        asset_class=model_in.asset_class,
        code=model_in.code
    )
    db.add(new_model)
    await db.flush()

    # Step 3: Extract and store symbolic assumptions
    extracted = AssumptionExtractor.extract_assumptions(model_in.code)
    for a in extracted:
        assumption_obj = Assumption(
            model_id=new_model.id,
            name=a["name"],
            category=a["category"],
            mathematical_form=a["mathematical_form"],
            description=a["description"],
            is_violated_in_stress=a["is_violated_in_stress"]
        )
        db.add(assumption_obj)

    await db.commit()
    await db.refresh(new_model)
    return new_model

@router.get("", response_model=List[ModelResponse])
async def list_models(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FinancialModel).order_by(FinancialModel.created_at.desc()))
    models = result.scalars().all()
    
    if not models:
        from app.db.seed import seed_initial_data
        await seed_initial_data(db)
        result = await db.execute(select(FinancialModel).order_by(FinancialModel.created_at.desc()))
        models = result.scalars().all()

    return models

@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(model_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FinancialModel).where(FinancialModel.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Financial model not found.")
    return model

@router.get("/{model_id}/assumptions", response_model=List[AssumptionResponse])
async def get_model_assumptions(model_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Assumption).where(Assumption.model_id == model_id))
    return result.scalars().all()

