from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

# Authentication
class UserCreate(BaseModel):
    email: str
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# Model Registry
class ModelCreate(BaseModel):
    name: str = Field(..., example="Black-Scholes European Call")
    description: Optional[str] = "Standard analytical Black-Scholes option pricing formula"
    asset_class: str = "Equity Options"
    code: str = Field(..., example="def black_scholes_call(S, K, T, r, sigma):\n    import math\n    d1 = (math.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*math.sqrt(T))\n    d2 = d1 - sigma*math.sqrt(T)\n    # Normal CDF via math.erf\n    N = lambda x: 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))\n    return S * N(d1) - K * math.exp(-r*T) * N(d2)")

class ModelSynthesizeRequest(BaseModel):
    prompt: str = Field(..., description="Natural language description or mathematical formula of option pricing model")
    asset_class: Optional[str] = "Equity Options"

class ModelResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    asset_class: str
    code: str
    version: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Assumptions
class AssumptionResponse(BaseModel):
    id: str
    name: str
    category: str
    mathematical_form: str
    description: str
    is_violated_in_stress: bool
    model_config = ConfigDict(from_attributes=True)

# Validation Execution
class ValidationCreate(BaseModel):
    model_id: str
    spot_price: float = Field(default=100.0, gt=0)
    strike_price: float = Field(default=100.0, gt=0)
    time_to_maturity: float = Field(default=1.0, gt=0)
    risk_free_rate: float = Field(default=0.05, ge=0)
    volatility: float = Field(default=0.20, gt=0)
    dividend_yield: float = Field(default=0.0, ge=0)
    option_type: str = Field(default="call", pattern="^(call|put)$")

class HexagonalScores(BaseModel):
    conceptual_soundness: float = Field(..., description="Score 0-100")
    numerical_stability: float = Field(..., description="Score 0-100")
    parameter_robustness: float = Field(..., description="Score 0-100")
    boundary_condition_safety: float = Field(..., description="Score 0-100")
    greek_fidelity: float = Field(..., description="Score 0-100")
    benchmark_alignment: float = Field(..., description="Score 0-100")

class ValidationResponse(BaseModel):
    id: str
    model_id: str
    status: str
    fragility_score: Optional[float] = None
    classification: Optional[str] = None
    max_pricing_error: Optional[float] = None
    breaking_parameters: Optional[Dict[str, Any]] = None
    greek_drifts: Optional[Dict[str, Any]] = None
    fragility_surface: Optional[Dict[str, Any]] = None
    hexagonal_scores: Optional[HexagonalScores] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Reports
class ReportResponse(BaseModel):
    id: str
    run_id: str
    executive_summary: str
    sr11_7_compliance: Dict[str, Any]
    report_data: Dict[str, Any]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Market Data
class MarketQuote(BaseModel):
    ticker: str
    spot_price: float
    historical_volatility_21d: float
    risk_free_rate: float
    timestamp: str

