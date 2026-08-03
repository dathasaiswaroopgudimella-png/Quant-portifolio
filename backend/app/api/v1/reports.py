from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.domain import Report
from app.schemas.schemas import ReportResponse

router = APIRouter(prefix="/reports", tags=["Validation Reports"])

@router.get("/{run_id}", response_model=ReportResponse)
async def get_report_by_run_id(run_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Report).where(Report.run_id == run_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Validation report not found for given run ID.")
    return report
