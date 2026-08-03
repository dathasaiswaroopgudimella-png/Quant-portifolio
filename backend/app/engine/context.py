from typing import Dict, Any, Optional
from datetime import datetime, timezone

class PricingContext:
    """
    GS-Quant inspired Pricing Context Manager.
    Provides structured market state, valuation parameters, and execution scoping.
    """

    def __init__(
        self,
        valuation_date: Optional[datetime] = None,
        pricing_engine: str = "QuantLib",
        risk_free_rate: float = 0.05,
        volatility_surface: str = "FlatConstant"
    ):
        self.valuation_date = valuation_date or datetime.now(timezone.utc)
        self.pricing_engine = pricing_engine
        self.risk_free_rate = risk_free_rate
        self.volatility_surface = volatility_surface

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valuation_date": self.valuation_date.isoformat(),
            "pricing_engine": self.pricing_engine,
            "risk_free_rate": self.risk_free_rate,
            "volatility_surface": self.volatility_surface
        }
