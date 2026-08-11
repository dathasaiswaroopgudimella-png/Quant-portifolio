import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.domain import FinancialModel

logger = logging.getLogger(__name__)

SEED_MODELS = [
    {
        "name": "Standard Black-Scholes Call",
        "description": "Baseline analytical European call option pricing function with constant volatility and interest rate assumptions.",
        "asset_class": "Equity Options",
        "code": """def black_scholes_call(S, K, T, r, sigma):
    import math
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return 0.0
    d1 = (math.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*math.sqrt(T))
    d2 = d1 - sigma*math.sqrt(T)
    N = lambda x: 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
    return S * N(d1) - K * math.exp(-r*T) * N(d2)
""",
    },
    {
        "name": "Garman-Kohlhagen Foreign Exchange (FX) Model",
        "description": "Analytical Garman-Kohlhagen FX option valuation model incorporating domestic risk-free rate r=4% and foreign risk-free rate rf=2%.",
        "asset_class": "FX Options",
        "code": """def garman_kohlhagen_fx(S, K, T, r, sigma):
    import math
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return 0.0
    rf = 0.02
    d1 = (math.log(S/K) + (r - rf + 0.5*sigma**2)*T) / (sigma*math.sqrt(T))
    d2 = d1 - sigma*math.sqrt(T)
    N = lambda x: 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
    return S * math.exp(-rf*T) * N(d1) - K * math.exp(-r*T) * N(d2)
""",
    }
]


async def seed_initial_data(db: AsyncSession) -> None:
    """
    Fast lightweight seed — inserts the 2 canonical option model rows only.
    Does NOT run heavy adversarial validation (that happens on user request).
    Safe for serverless cold-start environments.
    """
    try:
        result = await db.execute(select(FinancialModel))
        existing = result.scalars().all()
        if existing:
            logger.info(f"DB already has {len(existing)} models — seed skipped.")
            return

        logger.info("Seeding 2 canonical quantitative option models...")
        for spec in SEED_MODELS:
            model = FinancialModel(
                name=spec["name"],
                description=spec["description"],
                asset_class=spec["asset_class"],
                code=spec["code"],
            )
            db.add(model)

        await db.commit()
        logger.info("Seed complete: 2 models inserted.")
    except Exception as e:
        logger.warning(f"Seed notice: {e}")
        try:
            await db.rollback()
        except Exception:
            pass
