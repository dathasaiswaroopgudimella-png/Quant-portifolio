from fastapi import APIRouter, Query
from app.schemas.schemas import MarketQuote
from app.services.yfinance_provider import YFinanceMarketProvider

router = APIRouter(prefix="/market-data", tags=["Market Data"])

@router.get("/{ticker}", response_model=MarketQuote)
async def get_market_quote(ticker: str):
    data = YFinanceMarketProvider.get_ticker_market_data(ticker)
    return MarketQuote(
        ticker=data["ticker"],
        spot_price=data["spot_price"],
        historical_volatility_21d=data["historical_volatility_21d"],
        risk_free_rate=data["risk_free_rate"],
        timestamp=data["timestamp"]
    )
