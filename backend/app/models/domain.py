import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    models: Mapped[List["FinancialModel"]] = relationship("FinancialModel", back_populates="owner", cascade="all, delete-orphan")


class FinancialModel(Base):
    __tablename__ = "financial_models"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    asset_class: Mapped[str] = mapped_column(String(100), default="Equity Options")
    code: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(String(50), default="1.0.0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    owner: Mapped[Optional["User"]] = relationship("User", back_populates="models")
    assumptions: Mapped[List["Assumption"]] = relationship("Assumption", back_populates="model", cascade="all, delete-orphan")
    validations: Mapped[List["ValidationRun"]] = relationship("ValidationRun", back_populates="model", cascade="all, delete-orphan")


class Assumption(Base):
    __tablename__ = "assumptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    model_id: Mapped[str] = mapped_column(String(36), ForeignKey("financial_models.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., Volatility, Rate, Distribution
    mathematical_form: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    is_violated_in_stress: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    model: Mapped["FinancialModel"] = relationship("FinancialModel", back_populates="assumptions")


class ValidationRun(Base):
    __tablename__ = "validation_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    model_id: Mapped[str] = mapped_column(String(36), ForeignKey("financial_models.id"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PENDING")  # PENDING, RUNNING, COMPLETED, FAILED
    fragility_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    classification: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # ROBUST, MODERATE, FRAGILE, CRITICAL
    max_pricing_error: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    breaking_parameters: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    greek_drifts: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    fragility_surface: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, default=lambda: datetime.now(timezone.utc))

    model: Mapped["FinancialModel"] = relationship("FinancialModel", back_populates="validations")
    report: Mapped[Optional["Report"]] = relationship("Report", back_populates="validation_run", uselist=False, cascade="all, delete-orphan")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("validation_runs.id"), index=True, nullable=False)
    executive_summary: Mapped[str] = mapped_column(Text, nullable=False)
    sr11_7_compliance: Mapped[dict] = mapped_column(JSON, nullable=False)
    report_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    validation_run: Mapped["ValidationRun"] = relationship("ValidationRun", back_populates="report")
