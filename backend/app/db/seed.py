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
    },
    {
        "name": "Merton (1976) Jump-Diffusion Pricing Engine",
        "description": "Superimposes Poisson-distributed discontinuous jump shocks onto continuous geometric Brownian motion to price fat-tailed market regimes.",
        "asset_class": "Equity Options",
        "code": """def merton_jump_diffusion(S, K, T, r, sigma):
    import math
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return 0.0
    lam = 0.75       # Jump intensity (frequency per year)
    gamma_j = -0.05  # Mean jump size
    delta_j = 0.15   # Jump volatility
    
    k = math.exp(gamma_j + 0.5 * delta_j**2) - 1.0
    lam_prime = lam * (1.0 + k)
    total_price = 0.0
    N = lambda x: 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
    
    for n in range(25):
        p_n = (math.exp(-lam_prime * T) * (lam_prime * T)**n) / math.factorial(n)
        sigma_n = math.sqrt(sigma**2 + n * (delta_j**2) / T)
        r_n = r - lam * k + n * math.log(1.0 + k) / T
        d1 = (math.log(S/K) + (r_n + 0.5 * sigma_n**2) * T) / (sigma_n * math.sqrt(T))
        d2 = d1 - sigma_n * math.sqrt(T)
        bs_n = S * N(d1) - K * math.exp(-r_n * T) * N(d2)
        total_price += p_n * max(0.0, bs_n)
    return total_price
""",
    },
    {
        "name": "Bjerksund-Stensland (2002) American Option Model",
        "description": "High-precision closed-form analytical approximation for early-exercise American options on dividend-paying equities.",
        "asset_class": "American Options",
        "code": """def bjerksund_stensland_american(S, K, T, r, sigma):
    import math
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return max(0.0, S - K)
    q = 0.01  # Dividend yield
    b = r - q
    N = lambda x: 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
    
    # European Black-Scholes baseline
    d1 = (math.log(S/K) + (b + 0.5*sigma**2)*T) / (sigma*math.sqrt(T))
    d2 = d1 - sigma*math.sqrt(T)
    bs_call = S * math.exp(-q*T) * N(d1) - K * math.exp(-r*T) * N(d2)
    
    # Early exercise trigger boundary
    beta = (0.5 - b / sigma**2) + math.sqrt((b / sigma**2 - 0.5)**2 + 2 * r / sigma**2)
    B_inf = (beta / (beta - 1.0)) * K
    B_0 = max(K, (r / (r - b)) * K) if r != b else K
    h_t = -(b * T + 2 * sigma * math.sqrt(T)) * (B_0 / (B_inf - B_0))
    I = B_0 + (B_inf - B_0) * (1.0 - math.exp(h_t))
    
    if S >= I:
        return S - K
    return max(bs_call, bs_call + (I - K) * ((S / I) ** beta) * (1.0 - math.exp(-r*T)))
""",
    },
    {
        "name": "Corrado-Su Gram-Charlier Skewness & Kurtosis Model",
        "description": "Analytical Gram-Charlier series expansion adjusting Black-Scholes for observed non-Gaussian skewness and excess kurtosis.",
        "asset_class": "Index Options",
        "code": """def corrado_su_skew_kurtosis(S, K, T, r, sigma):
    import math
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return 0.0
    skewness = -0.65  # Negative equity index skew
    kurtosis = 3.90   # Fat-tailed excess kurtosis
    
    sqrt_T = math.sqrt(T)
    d = (math.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*sqrt_T)
    d2 = d - sigma*sqrt_T
    
    N = lambda x: 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
    n_d = (1.0 / math.sqrt(2.0 * math.pi)) * math.exp(-0.5 * d**2)
    
    c_bs = S * N(d) - K * math.exp(-r*T) * N(d2)
    mu3 = skewness
    mu4 = kurtosis - 3.0
    
    Q3 = (1.0 / 6.0) * S * sqrt_T * (2 * sigma * sqrt_T - d) * n_d
    Q4 = (1.0 / 24.0) * S * sqrt_T * (d**2 - 1.0 - 3*d*sigma*sqrt_T + 3*(sigma*sqrt_T)**2) * n_d
    
    return max(0.0, c_bs + mu3 * Q3 + mu4 * Q4)
""",
    },
    {
        "name": "Bachelier (1900) Normal Spread & Negative Rate Model",
        "description": "Bachelier arithmetic Brownian motion model with normal volatility, supporting zero and negative interest rate regimes.",
        "asset_class": "Commodity / Spread",
        "code": """def bachelier_normal_pricer(S, K, T, r, sigma):
    import math
    if T <= 0 or sigma <= 0:
        return max(0.0, S - K)
    sigma_normal = sigma * S  # Convert relative vol to absolute normal vol ($)
    sqrt_T = math.sqrt(T)
    d = (S - K) / (sigma_normal * sqrt_T)
    N = lambda x: 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
    n_d = (1.0 / math.sqrt(2.0 * math.pi)) * math.exp(-0.5 * d**2)
    disc = math.exp(-r * T)
    return max(0.0, disc * ((S - K) * N(d) + sigma_normal * sqrt_T * n_d))
""",
    }
]


async def seed_initial_data(db: AsyncSession) -> None:
    """
    Seeds quantitative model inventory from awesome-quant library.
    Safe for serverless cold-start environments.
    """
    try:
        result = await db.execute(select(FinancialModel))
        existing = result.scalars().all()
        if existing:
            logger.info(f"DB already has {len(existing)} models — seed skipped.")
            return

        logger.info(f"Seeding {len(SEED_MODELS)} institutional quantitative option models...")
        for spec in SEED_MODELS:
            model = FinancialModel(
                name=spec["name"],
                description=spec["description"],
                asset_class=spec["asset_class"],
                code=spec["code"],
            )
            db.add(model)

        await db.commit()
        logger.info(f"Seed complete: {len(SEED_MODELS)} models inserted.")
    except Exception as e:
        logger.warning(f"Seed notice: {e}")
        try:
            await db.rollback()
        except Exception:
            pass
