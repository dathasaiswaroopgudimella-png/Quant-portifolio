"""
FRAGMENT Quantitative Models Suite (Inspired by awesome-quant)
Industrial-grade closed-form and semi-analytical valuation models with exact Greeks.
"""
import math
from typing import Dict, Any, Optional, Tuple

try:
    import numpy as np
    from scipy.stats import norm as _norm
    def _N(x: float) -> float:
        return float(_norm.cdf(x))
    def _n(x: float) -> float:
        return float(_norm.pdf(x))
except ImportError:
    np = None  # type: ignore
    def _N(x: float) -> float:
        """Standard normal CDF via Horner-form minimax approximation (Abramowitz & Stegun 26.2.17)."""
        if x < -8.0: return 0.0
        if x > 8.0: return 1.0
        k = 1.0 / (1.0 + 0.2316419 * abs(x))
        poly = k * (0.319381530 + k * (-0.356563782 + k * (1.781477937 + k * (-1.821255978 + k * 1.330274429))))
        result = 1.0 - (1.0 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * x * x) * poly
        return result if x >= 0 else 1.0 - result
    def _n(x: float) -> float:
        """Standard normal PDF."""
        return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)


class QuantModels:
    """Collection of canonical option pricing models and Greek calculators."""

    # ── 1. Black-Scholes-Merton (1973) ──────────────────────────────────────
    @staticmethod
    def black_scholes(S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0, option_type: str = "call") -> Dict[str, float]:
        """
        Vanilla European Black-Scholes-Merton pricer with continuous dividend yield q
        and analytical first/second-order Greeks.
        """
        if T <= 1e-7 or sigma <= 1e-7 or S <= 1e-7 or K <= 1e-7:
            intrinsic = max(0.0, S - K) if option_type.lower() == "call" else max(0.0, K - S)
            return {
                "price": intrinsic, "delta": 1.0 if (option_type.lower() == "call" and S > K) else 0.0,
                "gamma": 0.0, "vega": 0.0, "theta": 0.0, "rho": 0.0,
                "vanna": 0.0, "volga": 0.0, "charm": 0.0, "speed": 0.0
            }

        sqrt_T = math.sqrt(T)
        d1 = (math.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * sqrt_T)
        d2 = d1 - sigma * sqrt_T

        pdf_d1 = _n(d1)
        cdf_d1 = _N(d1)
        cdf_d2 = _N(d2)
        cdf_neg_d1 = _N(-d1)
        cdf_neg_d2 = _N(-d2)

        exp_neg_qT = math.exp(-q * T)
        exp_neg_rT = math.exp(-r * T)

        is_call = option_type.lower() == "call"
        if is_call:
            price = S * exp_neg_qT * cdf_d1 - K * exp_neg_rT * cdf_d2
            delta = exp_neg_qT * cdf_d1
            theta = (- (S * sigma * exp_neg_qT * pdf_d1) / (2.0 * sqrt_T)
                     - r * K * exp_neg_rT * cdf_d2
                     + q * S * exp_neg_qT * cdf_d1) / 365.0
            rho = (K * T * exp_neg_rT * cdf_d2) / 100.0
        else:
            price = K * exp_neg_rT * cdf_neg_d2 - S * exp_neg_qT * cdf_neg_d1
            delta = -exp_neg_qT * cdf_neg_d1
            theta = (- (S * sigma * exp_neg_qT * pdf_d1) / (2.0 * sqrt_T)
                     + r * K * exp_neg_rT * cdf_neg_d2
                     - q * S * exp_neg_qT * cdf_neg_d1) / 365.0
            rho = (-K * T * exp_neg_rT * cdf_neg_d2) / 100.0

        gamma = (exp_neg_qT * pdf_d1) / (S * sigma * sqrt_T)
        vega = (S * exp_neg_qT * pdf_d1 * sqrt_T) / 100.0
        vanna = (-exp_neg_qT * pdf_d1 * d2 / sigma) / 100.0
        volga = (vega * d1 * d2 / sigma)
        charm = (q * exp_neg_qT * (cdf_d1 if is_call else -cdf_neg_d1)
                 - exp_neg_qT * pdf_d1 * (2 * (r - q) * T - d2 * sigma * sqrt_T) / (2 * T * sigma * sqrt_T)) / 365.0
        speed = (-gamma / S) * (d1 / (sigma * sqrt_T) + 1.0)

        return {
            "price": max(0.0, price),
            "delta": delta,
            "gamma": gamma,
            "vega": vega,
            "theta": theta,
            "rho": rho,
            "vanna": vanna,
            "volga": volga,
            "charm": charm,
            "speed": speed
        }

    # ── 2. Garman-Kohlhagen (1983) FX Model ─────────────────────────────────
    @staticmethod
    def garman_kohlhagen(S: float, K: float, T: float, r_d: float, r_f: float, sigma: float, option_type: str = "call") -> Dict[str, float]:
        """
        FX currency option model with domestic interest rate r_d and foreign risk-free rate r_f.
        """
        return QuantModels.black_scholes(S=S, K=K, T=T, r=r_d, sigma=sigma, q=r_f, option_type=option_type)

    # ── 3. Merton (1976) Jump-Diffusion Model ───────────────────────────────
    @staticmethod
    def merton_jump_diffusion(
        S: float, K: float, T: float, r: float, sigma: float,
        lam: float = 0.75,      # Jump intensity (expected jumps per year)
        gamma: float = -0.05,   # Mean jump size (log return shock)
        delta_j: float = 0.15,  # Jump volatility
        n_max: int = 40,
        option_type: str = "call"
    ) -> float:
        """
        Merton (1976) Poisson Jump-Diffusion European option pricing model.
        Superimposes log-normal jump shocks onto continuous geometric Brownian motion.
        """
        if T <= 1e-7 or S <= 1e-7 or K <= 1e-7:
            return max(0.0, S - K) if option_type.lower() == "call" else max(0.0, K - S)

        k = math.exp(gamma + 0.5 * delta_j ** 2) - 1.0
        lam_prime = lam * (1.0 + k)
        total_price = 0.0

        for n in range(n_max):
            p_n = (math.exp(-lam_prime * T) * (lam_prime * T) ** n) / math.factorial(n)
            sigma_n = math.sqrt(sigma ** 2 + n * (delta_j ** 2) / T)
            r_n = r - lam * k + n * math.log(1.0 + k) / T
            bs_res = QuantModels.black_scholes(S=S, K=K, T=T, r=r_n, sigma=sigma_n, option_type=option_type)
            total_price += p_n * bs_res["price"]

        return max(0.0, total_price)

    # ── 4. Heston (1993) Stochastic Volatility (Carr-Madan Fourier Inversion) 
    @staticmethod
    def heston_stochastic_vol(
        S: float, K: float, T: float, r: float,
        v0: float = 0.04,     # Initial variance (sigma^2)
        kappa: float = 2.0,   # Mean reversion speed
        theta: float = 0.04,  # Long-term variance
        xi: float = 0.3,      # Vol-of-vol
        rho: float = -0.7,    # Correlation between asset and variance
        option_type: str = "call"
    ) -> float:
        """
        Heston (1993) stochastic volatility model solved via numerical quadrature
        of the characteristic function (Carr-Madan Fourier transform).
        """
        if T <= 1e-7 or S <= 1e-7 or K <= 1e-7:
            return max(0.0, S - K) if option_type.lower() == "call" else max(0.0, K - S)

        def heston_char_func(u, j):
            # j = 1 or 2
            u_c = complex(u, 0)
            if j == 1:
                u_term = complex(0.5, u)
                b = kappa - rho * xi
            else:
                u_term = complex(-0.5, u)
                b = kappa

            d = np.sqrt((rho * xi * complex(0, 1) * u - b) ** 2 - xi ** 2 * (2 * complex(0, 1) * u_term - u ** 2))
            g = (b - rho * xi * complex(0, 1) * u + d) / (b - rho * xi * complex(0, 1) * u - d)
            
            exp_dT = np.exp(d * T)
            C = (r * complex(0, 1) * u * T + (kappa * theta / (xi ** 2)) *
                 ((b - rho * xi * complex(0, 1) * u + d) * T - 2 * np.log((1 - g * exp_dT) / (1 - g))))
            D = ((b - rho * xi * complex(0, 1) * u + d) / (xi ** 2)) * ((1 - exp_dT) / (1 - g * exp_dT))
            
            return np.exp(C + D * v0 + complex(0, 1) * u * np.log(S))

        # Gauss-Legendre numerical integration over frequency domain u in [0, 100]
        u_nodes, u_weights = np.polynomial.legendre.leggauss(64)
        u_pts = 0.5 * 100.0 * (u_nodes + 1.0)
        w_pts = 0.5 * 100.0 * u_weights

        int1 = 0.0
        int2 = 0.0
        log_K = math.log(K)

        for u, w in zip(u_pts, w_pts):
            cf1 = heston_char_func(u, 1)
            cf2 = heston_char_func(u, 2)
            
            term1 = (np.exp(-complex(0, 1) * u * log_K) * cf1 / (complex(0, 1) * u)).real
            term2 = (np.exp(-complex(0, 1) * u * log_K) * cf2 / (complex(0, 1) * u)).real
            
            int1 += w * term1
            int2 += w * term2

        P1 = 0.5 + (1.0 / math.pi) * int1
        P2 = 0.5 + (1.0 / math.pi) * int2

        call_price = S * P1 - K * math.exp(-r * T) * P2
        if option_type.lower() == "call":
            return max(0.0, float(call_price))
        else:
            # Put-Call parity
            put_price = call_price - S + K * math.exp(-r * T)
            return max(0.0, float(put_price))

    # ── 5. Bjerksund-Stensland (2002) American Option Approximation ─────────
    @staticmethod
    def bjerksund_stensland(S: float, K: float, T: float, r: float, sigma: float, q: float = 0.0, option_type: str = "call") -> float:
        """
        Bjerksund-Stensland (2002) closed-form analytical approximation for American option pricing.
        Accounts for early exercise boundary.
        """
        if option_type.lower() == "put":
            # Transform American put into American call via symmetry: S <-> K, r <-> q
            return QuantModels.bjerksund_stensland(S=K, K=S, T=T, r=q, sigma=sigma, q=r, option_type="call")

        if T <= 1e-7 or S <= 1e-7 or K <= 1e-7:
            return max(0.0, S - K)

        if q >= r:
            # Early exercise of call option never optimal when q <= 0; matches European Black-Scholes
            return QuantModels.black_scholes(S=S, K=K, T=T, r=r, sigma=sigma, q=q, option_type="call")["price"]

        b = r - q
        beta = (0.5 - b / (sigma ** 2)) + math.sqrt((b / (sigma ** 2) - 0.5) ** 2 + 2 * r / (sigma ** 2))
        B_infinity = (beta / (beta - 1.0)) * K
        B_0 = max(K, (r / (r - b)) * K)
        h_t = -(b * T + 2 * sigma * math.sqrt(T)) * (B_0 / (B_infinity - B_0))
        I = B_0 + (B_infinity - B_0) * (1.0 - math.exp(h_t))

        if S >= I:
            return S - K

        def phi(S_in, T_in, gamma_in, H_in, I_in):
            lambda_val = (-r + gamma_in * b + 0.5 * gamma_in * (gamma_in - 1.0) * (sigma ** 2)) * T_in
            d_val = -(math.log(S_in / H_in) + (b + (gamma_in - 0.5) * (sigma ** 2)) * T_in) / (sigma * math.sqrt(T_in))
            kappa_val = (2.0 * b / (sigma ** 2)) + (2.0 * gamma_in - 1.0)
            return (math.exp(lambda_val) * (S_in ** gamma_in) *
                    (_N(d_val) - ((I_in / S_in) ** kappa_val) *
                     _N(d_val - 2.0 * math.log(I_in / S_in) / (sigma * math.sqrt(T_in)))))

        alpha = (I - K) * (I ** (-beta))
        bs_price = QuantModels.black_scholes(S=S, K=K, T=T, r=r, sigma=sigma, q=q, option_type="call")["price"]
        am_call = (alpha * (S ** beta) - alpha * phi(S, T, beta, I, I) +
                   phi(S, T, 1.0, I, I) - phi(S, T, 1.0, K, I) -
                   K * phi(S, T, 0.0, I, I) + K * phi(S, T, 0.0, K, I))
        return max(bs_price, float(am_call))

    # ── 6. Corrado-Su (1996) Gram-Charlier Skewness & Kurtosis Expansion ────
    @staticmethod
    def corrado_su(S: float, K: float, T: float, r: float, sigma: float, skewness: float = -0.5, kurtosis: float = 3.8, option_type: str = "call") -> float:
        """
        Corrado-Su (1996) Gram-Charlier expansion adjusting Black-Scholes for non-Gaussian
        skewness (gamma_1) and excess kurtosis (gamma_2).
        """
        bs_data = QuantModels.black_scholes(S=S, K=K, T=T, r=r, sigma=sigma, option_type="call")
        c_bs = bs_data["price"]
        
        if T <= 1e-7 or sigma <= 1e-7:
            return max(0.0, S - K) if option_type.lower() == "call" else max(0.0, K - S)

        sqrt_T = math.sqrt(T)
        d = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt_T)
        
        n_d = _n(d)
        mu3 = skewness
        mu4 = kurtosis - 3.0  # Excess kurtosis

        # Corrado-Su higher-moment correction terms
        Q3 = (1.0 / 6.0) * S * sqrt_T * (2 * sigma * sqrt_T - d) * n_d
        Q4 = (1.0 / 24.0) * S * sqrt_T * (d ** 2 - 1.0 - 3 * d * sigma * sqrt_T + 3 * (sigma * sqrt_T) ** 2) * n_d

        c_cs = c_bs + mu3 * Q3 + mu4 * Q4
        c_cs = max(max(0.0, S - K * math.exp(-r * T)), c_cs)

        if option_type.lower() == "call":
            return float(c_cs)
        else:
            p_cs = c_cs - S + K * math.exp(-r * T)
            return max(0.0, float(p_cs))

    # ── 7. SABR Volatility Smile Model (Hagan et al. 2002) ───────────────────
    @staticmethod
    def sabr_implied_vol(F: float, K: float, T: float, alpha: float = 0.2, beta: float = 0.7, rho: float = -0.3, nu: float = 0.4) -> float:
        """
        Hagan et al. (2002) SABR model asymptotic formula for Black-76 implied volatility smile.
        F: Forward price, K: Strike, T: Tenor, alpha: Initial vol, beta: CEV exponent, rho: Correlation, nu: Vol-of-vol.
        """
        if abs(F - K) < 1e-6:
            # ATM asymptotic formula
            f_mid = F
            term1 = alpha / (f_mid ** (1.0 - beta))
            term2 = 1.0 + (((1.0 - beta) ** 2 / 24.0) * (alpha ** 2 / (f_mid ** (2 - 2 * beta)))
                           + (rho * beta * nu * alpha / (4.0 * (f_mid ** (1 - beta))))
                           + ((2.0 - 3.0 * rho ** 2) / 24.0) * (nu ** 2)) * T
            return float(term1 * term2)

        log_FK = math.log(F / K)
        fk_beta = (F * K) ** ((1.0 - beta) / 2.0)
        z = (nu / alpha) * fk_beta * log_FK
        x_z = math.log((math.sqrt(1.0 - 2.0 * rho * z + z ** 2) + z - rho) / (1.0 - rho))

        num = alpha * (1.0 + (((1.0 - beta) ** 2 / 24.0) * (alpha ** 2 / (fk_beta ** 2))
                              + (rho * beta * nu * alpha / (4.0 * fk_beta))
                              + ((2.0 - 3.0 * rho ** 2) / 24.0) * (nu ** 2)) * T)
        den = fk_beta * (1.0 + ((1.0 - beta) ** 2 / 24.0) * (log_FK ** 2) + ((1.0 - beta) ** 4 / 1920.0) * (log_FK ** 4))

        sigma_sabr = (num / den) * (z / x_z)
        return max(0.01, float(sigma_sabr))

    # ── 8. Bachelier Normal Model (1900) ────────────────────────────────────
    @staticmethod
    def bachelier(S: float, K: float, T: float, r: float, sigma_normal: float, option_type: str = "call") -> float:
        """
        Bachelier (1900) arithmetic Brownian motion normal option model (supports negative strikes & spot).
        """
        if T <= 1e-7 or sigma_normal <= 1e-7:
            return max(0.0, S - K) if option_type.lower() == "call" else max(0.0, K - S)

        d = (S - K) / (sigma_normal * math.sqrt(T))
        disc = math.exp(-r * T)
        
        if option_type.lower() == "call":
            price = disc * ((S - K) * _N(d) + sigma_normal * math.sqrt(T) * _n(d))
        else:
            price = disc * ((K - S) * _N(-d) + sigma_normal * math.sqrt(T) * _n(d))

        return max(0.0, float(price))

    # ── 9. Asian Option Turnbull-Wakeman Average Rate Model ─────────────────
    @staticmethod
    def asian_geometric_average(S: float, K: float, T: float, r: float, sigma: float, n_steps: int = 12, option_type: str = "call") -> float:
        """
        Turnbull-Wakeman exact analytical pricing for Geometric Continuous/Discrete Asian Options.
        """
        if T <= 1e-7 or sigma <= 1e-7:
            return max(0.0, S - K) if option_type.lower() == "call" else max(0.0, K - S)

        # Adjusted volatility and drift for geometric average asset price
        sigma_adj = sigma * math.sqrt((2.0 * n_steps + 1.0) / (6.0 * (n_steps + 1.0)))
        b_adj = 0.5 * (r - 0.5 * sigma ** 2 + sigma_adj ** 2)
        q_adj = r - b_adj

        return QuantModels.black_scholes(S=S, K=K, T=T, r=r, sigma=sigma_adj, q=q_adj, option_type=option_type)["price"]

    # ── 10. Barrier Option Analytical Pricing (Down-and-Out Call) ────────────
    @staticmethod
    def barrier_down_and_out_call(S: float, K: float, H: float, T: float, r: float, sigma: float) -> float:
        """
        Reiner-Rubinstein (1991) analytical closed-form for European Down-and-Out Call Option.
        H: Lower barrier level (H < S).
        """
        if S <= H:
            return 0.0  # Knocked out instantly
        if H >= K:
            # When H >= K, option pays if asset stays above H
            mu = (r - 0.5 * sigma ** 2) / (sigma ** 2)
            lam = math.sqrt(mu ** 2 + 2 * r / (sigma ** 2))
            
            d1 = (math.log(S / H) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
            d2 = d1 - sigma * math.sqrt(T)
            
            y1 = (math.log(H / S) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
            y2 = y1 - sigma * math.sqrt(T)
            
            c_vanilla = QuantModels.black_scholes(S=S, K=H, T=T, r=r, sigma=sigma, option_type="call")["price"]
            c_knock_out = c_vanilla - (S * _N(d1) - H * math.exp(-r * T) * _N(d2)) + \
                          ((H / S) ** (2 * mu)) * (H * _N(y1) - S * math.exp(-r * T) * _N(y2))
            return max(0.0, float(c_knock_out))
        else:
            # H < K standard down-and-out
            c_std = QuantModels.black_scholes(S=S, K=K, T=T, r=r, sigma=sigma, option_type="call")["price"]
            c_di = ((H / S) ** (2 * (r - 0.5 * sigma ** 2) / (sigma ** 2))) * \
                   QuantModels.black_scholes(S=(H ** 2) / S, K=K, T=T, r=r, sigma=sigma, option_type="call")["price"]
            return max(0.0, float(c_std - c_di))
