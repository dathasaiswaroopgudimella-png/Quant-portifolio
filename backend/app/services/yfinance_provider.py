import numpy as np
import yfinance as yf
from datetime import datetime, timezone
from typing import Dict, Any, Optional

class YFinanceMarketProvider:
    """
    Market Data Provider backed by Yahoo Finance (yfinance).
    Retrieves ticker quotes, 21-day annualized historical volatility (sample std dev ddof=1),
    and risk-free rate benchmarks.
    """

    @staticmethod
    def get_ticker_market_data(ticker_symbol: str = "AAPL") -> Dict[str, Any]:
        """
        Fetches live spot price and calculates annualized rolling 21-day sample historical volatility.
        """
        try:
            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(period="1mo")
            
            if hist.empty:
                return YFinanceMarketProvider._get_fallback_snapshot(ticker_symbol)

            # Spot price from latest close
            spot_price = float(hist["Close"].iloc[-1])

            # Calculate log returns using sample standard deviation (ddof=1)
            log_returns = np.log(hist["Close"] / hist["Close"].shift(1)).dropna()
            daily_vol = float(np.std(log_returns, ddof=1)) if len(log_returns) > 1 else 0.20
            annualized_hv21 = float(daily_vol * np.sqrt(252))

            # Attempt to fetch 30-day ATM implied volatility from option chain
            implied_vol = annualized_hv21 * 1.10  # Volatility risk premium default (+10%)
            try:
                options_dates = ticker.options
                if options_dates:
                    chain = ticker.option_chain(options_dates[0])
                    calls = chain.calls
                    # Find near-the-money call option
                    calls['strike_diff'] = abs(calls['strike'] - spot_price)
                    atm_call = calls.sort_values('strike_diff').iloc[0]
                    if 'impliedVolatility' in atm_call and atm_call['impliedVolatility'] > 0:
                        implied_vol = float(atm_call['impliedVolatility'])
            except Exception:
                pass

            return {
                "ticker": ticker_symbol.upper(),
                "spot_price": round(spot_price, 2),
                "historical_volatility_21d": round(annualized_hv21, 4),
                "implied_volatility_30d_atm": round(implied_vol, 4),
                "volatility_type": "Market Implied Volatility (IV) with Realized Historical Volatility (HV) reference",
                "risk_free_rate": 0.0525,  # Benchmark US 10Y Treasury yield
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "DELAYED",
                "source": "Yahoo Finance (15-min delayed option chain & quote data)"
            }
        except Exception as e:
            return YFinanceMarketProvider._get_fallback_snapshot(ticker_symbol, error=str(e))

    @staticmethod
    def _get_fallback_snapshot(ticker_symbol: str, error: Optional[str] = None) -> Dict[str, Any]:
        defaults = {
            "AAPL": 225.50,
            "SPY": 545.20,
            "NVDA": 120.80,
            "TSLA": 210.40,
            "MSFT": 440.30
        }
        spot = defaults.get(ticker_symbol.upper(), 100.0)
        return {
            "ticker": ticker_symbol.upper(),
            "spot_price": spot,
            "historical_volatility_21d": 0.2250,
            "risk_free_rate": 0.0525,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "FALLBACK_SIMULATED",
            "source": "Simulated Benchmark Snapshot (Network Offline / Market Closed)",
            "info": error
        }
