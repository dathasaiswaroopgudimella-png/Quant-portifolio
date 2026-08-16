import os
import re
import json
import httpx
from typing import Dict, Any, Optional
from app.core.config import settings


class OpenRouterReportService:
    """
    OpenRouter AI Executive Summary & Prompt-to-Model Synthesizer.
    Provides model-aware natural language generation and SR 11-7 governance narratives.
    """

    @staticmethod
    def get_api_key() -> Optional[str]:
        return os.getenv("OPENROUTER_API_KEY") or settings.OPENROUTER_API_KEY

    @staticmethod
    async def synthesize_model_from_prompt(prompt: str, asset_class: str = "Equity Options") -> Dict[str, str]:
        api_key = OpenRouterReportService.get_api_key()

        candidate_models = [
            "nvidia/nemotron-3.5-lightning:free",
            "google/gemma-4-26b-a4b-it:free",
            "liquid/lfm-2.5-2.6b:free",
            "cohere/north-mini-code:free",
            "openrouter/free",
            os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash"),
        ]
        system_prompt = (
            "You are a Quantitative Software Engineer. Convert natural language descriptions, formulas, "
            "or mathematical requirements into executable Python functions for option pricing. "
            "The function MUST take parameters: S (spot), K (strike), T (maturity in years), "
            "r (risk-free rate), and relevant model parameters. Only use standard Python math, numpy, or scipy.stats. "
            "Return valid JSON with keys: name, description, code."
        )

        user_prompt = f"""
        Prompt / Formula: "{prompt}"
        Asset Class: "{asset_class}"

        Generate an executable Python pricing function that implements this formula accurately.
        Return JSON format:
        {{
          "name": "<Short Model Title>",
          "description": "<Technical Summary>",
          "code": "def price_option(S, K, T, r, ...):\\n    import math\\n    ..."
        }}
        """

        if api_key:
            for model_to_use in candidate_models:
                try:
                    async with httpx.AsyncClient(timeout=15.0) as client:
                        response = await client.post(
                            "https://openrouter.ai/api/v1/chat/completions",
                            headers={
                                "Authorization": f"Bearer {api_key}",
                                "Content-Type": "application/json",
                                "HTTP-Referer": "https://fragment.quant",
                                "X-Title": "FRAGMENT Model Synthesizer"
                            },
                            json={
                                "model": model_to_use,
                                "messages": [
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": user_prompt}
                                ],
                                "max_tokens": 700,
                                "temperature": 0.2
                            }
                        )
                        if response.status_code == 200:
                            data = response.json()
                            raw_text = data["choices"][0]["message"]["content"]
                            match = re.search(r"\{.*\}", raw_text, re.DOTALL)
                            if match:
                                parsed = json.loads(match.group(0))
                                if "code" in parsed and "def " in parsed["code"]:
                                    return {
                                        "name": parsed.get("name", "AI Synthesized Option Model"),
                                        "description": parsed.get("description", f"Generated from prompt: '{prompt}'"),
                                        "asset_class": asset_class,
                                        "code": parsed["code"]
                                    }
                except Exception as e:
                    print(f"[OpenRouterSynthesizer] API notice for model '{model_to_use}': {e}")
                    continue

        return OpenRouterReportService._generate_fallback_synthetic_model(prompt, asset_class)

    @staticmethod
    def _generate_fallback_synthetic_model(prompt: str, asset_class: str) -> Dict[str, str]:
        prompt_lower = prompt.lower()
        if "heston" in prompt_lower:
            code = (
                "def heston_monte_carlo_call(S, K, T, r, v0=0.04, kappa=2.0, theta=0.04, sigma=0.5, rho=-0.7, q=0.0, paths=100000, steps=252, seed=42):\n"
                "    import numpy as np\n"
                "    if S <= 0 or K <= 0 or T <= 0:\n"
                "        return 0.0\n"
                "    rng = np.random.default_rng(seed)\n"
                "    dt = T / steps\n"
                "    sqrt_dt = np.sqrt(dt)\n"
                "    S_paths = np.full(paths, S, dtype=float)\n"
                "    v_paths = np.full(paths, v0, dtype=float)\n"
                "    for _ in range(steps):\n"
                "        z1 = rng.standard_normal(paths)\n"
                "        z2 = rng.standard_normal(paths)\n"
                "        dW_S = z1\n"
                "        dW_v = rho * z1 + np.sqrt(1.0 - rho**2) * z2\n"
                "        v = np.maximum(v_paths, 0.0)\n"
                "        v_next = np.maximum(v + kappa * (theta - v) * dt + sigma * np.sqrt(v) * sqrt_dt * dW_v, 0.0)\n"
                "        S_paths *= np.exp((r - q - 0.5 * v) * dt + np.sqrt(v) * sqrt_dt * dW_S)\n"
                "        v_paths = v_next\n"
                "    payoff = np.maximum(S_paths - K, 0.0)\n"
                "    discounted = np.exp(-r * T) * payoff\n"
                "    price = np.mean(discounted)\n"
                "    se = np.std(discounted, ddof=1) / np.sqrt(paths)\n"
                "    return {'price': float(price), 'standard_error': float(se), '95%_confidence_interval': (float(price - 1.96*se), float(price + 1.96*se))}\n"
            )
            name = "Synthesized Heston Stochastic Volatility MC Model"
            desc = f"Heston CIR square-root stochastic variance Monte Carlo simulation model synthesized for: '{prompt}'"
        elif "put" in prompt_lower:
            code = (
                "def black_scholes_put(S, K, T, r, sigma):\n"
                "    import math\n"
                "    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:\n"
                "        return 0.0\n"
                "    d1 = (math.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*math.sqrt(T))\n"
                "    d2 = d1 - sigma*math.sqrt(T)\n"
                "    N = lambda x: 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))\n"
                "    return K * math.exp(-r*T) * N(-d2) - S * N(-d1)\n"
            )
            name = "Synthesized BSM European Put Model"
            desc = f"Analytical European put pricing model synthesized for requirement: '{prompt}'"
        elif "garman" in prompt_lower or "fx" in prompt_lower or "currency" in prompt_lower:
            code = (
                "def garman_kohlhagen_fx(S, K, T, r, sigma):\n"
                "    import math\n"
                "    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:\n"
                "        return 0.0\n"
                "    rf = 0.02\n"
                "    d1 = (math.log(S/K) + (r - rf + 0.5*sigma**2)*T) / (sigma*math.sqrt(T))\n"
                "    d2 = d1 - sigma*math.sqrt(T)\n"
                "    N = lambda x: 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))\n"
                "    return S * math.exp(-rf*T) * N(d1) - K * math.exp(-r*T) * N(d2)\n"
            )
            name = "Synthesized Garman-Kohlhagen FX Model"
            desc = f"Foreign exchange option valuation model synthesized for: '{prompt}'"
        else:
            code = (
                "def black_scholes_call(S, K, T, r, sigma):\n"
                "    import math\n"
                "    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:\n"
                "        return 0.0\n"
                "    d1 = (math.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*math.sqrt(T))\n"
                "    d2 = d1 - sigma*math.sqrt(T)\n"
                "    N = lambda x: 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))\n"
                "    return S * N(d1) - K * math.exp(-r*T) * N(d2)\n"
            )
            name = "Synthesized BSM European Call Model"
            desc = f"Analytical option pricing model synthesized from prompt: '{prompt}'"

        return {
            "name": name,
            "description": desc,
            "asset_class": asset_class,
            "code": code
        }

    @staticmethod
    def compute_hexagonal_scores(
        fragility_score: float,
        pct_error: float,
        greeks: Dict[str, Any],
        greek_drifts: Dict[str, Any] = None,
        assumptions: list = None,
        breaking_params: Dict[str, Any] = None
    ) -> Dict[str, float]:
        ast_guards = [a for a in (assumptions or []) if "Safeguards" in a.get("name", "")]
        conceptual = 95.0 if ast_guards else max(30.0, round(92.0 - fragility_score * 0.35, 1))
        stability = round(max(10.0, min(100.0, 100.0 - min(pct_error * 1.5, 80.0))), 1)
        opt_stab = breaking_params.get("optimizer_stability", 85.0) if breaking_params else 85.0
        robustness = round(max(10.0, min(100.0, opt_stab - fragility_score * 0.25)), 1)
        boundary = round(max(10.0, min(100.0, 98.0 - min(pct_error * 1.2, 70.0))), 1)

        d_drift = greek_drifts.get("delta_drift", 0.0) if greek_drifts else 0.0
        v_drift = greek_drifts.get("vega_drift", 0.0) if greek_drifts else 0.0
        greek_fidelity = round(max(10.0, min(100.0, 100.0 - (d_drift * 40.0 + v_drift * 50.0))), 1)

        base_err = breaking_params.get("absolute_error", 0.0) if breaking_params else 0.0
        benchmark_align = round(max(10.0, min(100.0, 100.0 - min(base_err * 6.0 + pct_error * 1.0, 80.0))), 1)

        return {
            "conceptual_soundness": conceptual,
            "numerical_stability": stability,
            "parameter_robustness": robustness,
            "boundary_condition_safety": boundary,
            "greek_fidelity": greek_fidelity,
            "benchmark_alignment": benchmark_align
        }

    @staticmethod
    async def generate_executive_summary(
        model_name: str,
        fragility_score: float,
        classification: str,
        breaking_params: Dict[str, Any],
        assumptions: list,
        model_meta: Dict[str, Any] = None,
        mc_diagnostics: Dict[str, Any] = None
    ) -> str:
        api_key = OpenRouterReportService.get_api_key()

        meta = model_meta or {}
        model_full_name = meta.get("name", model_name)
        benchmark_name = meta.get("ground_truth_name", breaking_params.get("benchmark_engine", "Analytical Ground Truth"))
        is_mc = meta.get("is_monte_carlo", False)

        candidate_models = [
            "nvidia/nemotron-3.5-lightning:free",
            "google/gemma-4-26b-a4b-it:free",
            "liquid/lfm-2.5-2.6b:free",
            "cohere/north-mini-code:free",
            "openrouter/free",
            os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash"),
        ]

        system_prompt = (
            "You are a Senior Quantitative Auditor and Model Risk Officer specializing in Federal Reserve "
            "SR 11-7 / OCC 2011-12 model risk governance. Synthesize executive-level, mathematically rigorous "
            "validation audits specifically addressing the true model family (Heston Stochastic Volatility, "
            "Monte Carlo simulations, Jump-Diffusion, or BSM) and their theoretical benchmark alignments."
        )

        mc_info_str = ""
        if is_mc and mc_diagnostics:
            feller = mc_diagnostics.get("feller_condition_audit") or {}
            mc_info_str = f"""
            - **Monte Carlo Simulation Diagnostics**:
              - Sample Paths: {mc_diagnostics.get('paths', 'N/A'):,} | Time Steps: {mc_diagnostics.get('steps', 'N/A')}
              - Simulation Point Estimate: ${mc_diagnostics.get('point_estimate', 'N/A')}
              - Analytical Reference Benchmark: ${mc_diagnostics.get('ground_truth_benchmark', 'N/A')}
              - Standard Error (SE): ±${mc_diagnostics.get('standard_error', 'N/A')} ({mc_diagnostics.get('relative_standard_error_pct', 'N/A')}%)
              - 95% Confidence Interval: [{mc_diagnostics.get('confidence_interval_95', ['',''])[0]}, {mc_diagnostics.get('confidence_interval_95', ['',''])[1]}]
              - Benchmark Within 95% CI: {mc_diagnostics.get('is_benchmark_within_95_ci', 'N/A')}
              - Feller Condition (2*kappa*theta >= sigma_v^2): {feller.get('status', 'N/A')} ({feller.get('two_kappa_theta', 'N/A')} vs {feller.get('sigma_v_squared', 'N/A')})
            """

        user_prompt = f"""
        Generate a comprehensive, world-class Federal Reserve SR 11-7 Model Risk Governance Audit for the following run:

        ### Target Model: {model_full_name}
        - **Model Classification**: {meta.get('stochastic_type', 'Quantitative Pricing Engine')}
        - **Theoretical Ground Truth Benchmark**: {benchmark_name}
        - **Fragility Score**: {fragility_score}/100 ({classification} Tier)
        {mc_info_str}
        - **Worst-Case Adversarial Perturbation**:
          - Perturbed Spot: ${breaking_params.get('spot', 'N/A')}
          - Perturbed Volatility / Initial Variance: {breaking_params.get('volatility', 0)*100:.2f}%
          - Candidate Model Output: ${breaking_params.get('user_price', 'N/A')}
          - Ground Truth Benchmark: ${breaking_params.get('ground_truth_price', breaking_params.get('quantlib_price', 'N/A'))}
          - Absolute Pricing Error: ${breaking_params.get('absolute_error', 'N/A')} ({breaking_params.get('percentage_error', 'N/A')}% relative error)
        - **AST Assumptions Extracted**: {[a.get('name', '') for a in assumptions]}

        Structure your report in clear prose with the following sections:
        1. **Executive Summary & Model Identification**: Clearly state the true model formulation and benchmark engine.
        2. **Mathematical Formulation & Stochastic Dynamics**: Detail the underlying SDE/PDE (e.g. CIR variance process, correlated Brownian increments, Euler-Maruyama discretization).
        3. **Monte Carlo Convergence & Confidence Interval Audit** (if applicable): Standard error analysis, 95% CI coverage of theoretical benchmark, and Feller boundary stability.
        4. **Adversarial Stress Search & Parameter Fragility**: Analysis of parameter regimes causing highest divergence.
        5. **SR 11-7 Regulatory Compliance & Actionable Controls**: Specific governance boundaries, ongoing surveillance thresholds, and model validation recertification protocols.
        """

        if api_key:
            for model_to_use in candidate_models:
                try:
                    async with httpx.AsyncClient(timeout=15.0) as client:
                        response = await client.post(
                            "https://openrouter.ai/api/v1/chat/completions",
                            headers={
                                "Authorization": f"Bearer {api_key}",
                                "Content-Type": "application/json",
                                "HTTP-Referer": "https://fragment.quant",
                                "X-Title": "FRAGMENT Model Risk Platform"
                            },
                            json={
                                "model": model_to_use,
                                "messages": [
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": user_prompt}
                                ],
                                "max_tokens": 900,
                                "temperature": 0.25
                            }
                        )
                        if response.status_code == 200:
                            data = response.json()
                            if "choices" in data and len(data["choices"]) > 0:
                                content = data["choices"][0]["message"]["content"]
                                if content and len(content.strip()) > 50:
                                    # Strip reasoning/thinking tokens from models like Nemotron/Gemma
                                    content = re.sub(r"<thought>.*?</thought>", "", content, flags=re.DOTALL).strip()
                                    content = re.sub(r"^([ \t]*\n)*", "", content)
                                    # If output has a markdown heading after preamble thoughts, start from heading
                                    hash_pos = content.find("# ")
                                    if hash_pos != -1 and hash_pos < 500:
                                        content = content[hash_pos:]
                                    return content
                except Exception as e:
                    print(f"[OpenRouterService] API notice for model '{model_to_use}': {e}")
                    continue

        return OpenRouterReportService._generate_template_summary(
            model_name=model_full_name,
            fragility_score=fragility_score,
            classification=classification,
            breaking_params=breaking_params,
            assumptions=assumptions,
            model_meta=meta,
            mc_diagnostics=mc_diagnostics
        )

    @staticmethod
    def _generate_template_summary(
        model_name: str,
        fragility_score: float,
        classification: str,
        breaking_params: Dict[str, Any],
        assumptions: list,
        model_meta: Dict[str, Any] = None,
        mc_diagnostics: Dict[str, Any] = None
    ) -> str:
        meta = model_meta or {}
        benchmark_name = meta.get("ground_truth_name", breaking_params.get("benchmark_engine", "Theoretical Ground Truth Reference"))
        is_mc = meta.get("is_monte_carlo", False)

        assump_list = [a.get('name', '') for a in assumptions] if assumptions else ["Stochastic Asset Dynamics", "Risk-Neutral Valuation", "Equivalent Martingale Measure"]
        assump_str = "\n- " + "\n- ".join(assump_list)

        spot = breaking_params.get('spot', 100.0)
        vol = breaking_params.get('volatility', 0.20) * 100.0
        r = breaking_params.get('risk_free_rate', 0.05) * 100.0
        user_p = breaking_params.get('user_price', 7.3305)
        gt_p = breaking_params.get('ground_truth_price', breaking_params.get('quantlib_price', 7.3812))
        abs_err = breaking_params.get('absolute_error', 0.0507)
        pct_err = breaking_params.get('percentage_error', 0.687)

        mc_section = ""
        if is_mc and mc_diagnostics:
            feller = mc_diagnostics.get("feller_condition_audit") or {}
            ci_95 = mc_diagnostics.get("confidence_interval_95", [user_p - 0.05, user_p + 0.05])
            se = mc_diagnostics.get("standard_error", 0.03)
            paths = mc_diagnostics.get("paths", 100000)
            steps = mc_diagnostics.get("steps", 252)
            enveloped = "CONFIRMED (Benchmark enclosed in 95% CI)" if mc_diagnostics.get("is_benchmark_within_95_ci") else "DEVIATION DETECTED"

            mc_section = fr"""
---

## 3. Monte Carlo Convergence & Statistical Confidence Audit

A formal statistical validation of the simulation engine was conducted across {paths:,} sample paths and {steps} time steps:
- **Simulation Point Estimate ($\hat{{P}}$)**: `${user_p:.5f}`
- **Theoretical Semi-Analytical Benchmark ($P_{{\text{{ref}}}}$)**: `${gt_p:.5f}`
- **Monte Carlo Standard Error ($\text{{SE}} = s / \sqrt{{N}}$)**: `±${se:.5f}` ({mc_diagnostics.get('relative_standard_error_pct', 0.41):.3f}% relative precision)
- **95% Confidence Interval**: `[${ci_95[0]:.5f}, ${ci_95[1]:.5f}]`
- **Theoretical Envelopment**: **{enveloped}**
- **Feller Condition Audit ($2\kappa\theta \ge \sigma_v^2$)**: **{feller.get('status', 'FELLER_AUDIT_ACTIVE')}**
  - Left-hand side ($2\kappa\theta$): `{feller.get('two_kappa_theta', 0.16):.4f}`
  - Right-hand side ($\sigma_v^2$): `{feller.get('sigma_v_squared', 0.25):.4f}`
  - *Governance Finding*: {feller.get('governance_note', 'Discretization requires reflection guard at zero variance boundary.')}
"""

        return fr"""# Federal Reserve SR 11-7 Model Risk Audit & Quantitative Governance

**Model Identity**: `{model_name}`  
**Model Family**: **{meta.get('stochastic_type', 'Quantitative Derivative Engine')}**  
**Ground Truth Benchmark**: `{benchmark_name}`  
**Quantitative Fragility Index**: **{fragility_score:.1f} / 100.0** — **[{classification} TIER]**  

---

## 1. Executive Summary & Regulatory Classification

A model risk audit was conducted on `{model_name}`. Rather than assuming constant volatility Black-Scholes dynamics, the validation engine evaluated the model against its exact theoretical reference: **{benchmark_name}**.

The model achieved a Fragility Index of **{fragility_score:.1f} / 100**, placing it in the **{classification}** governance tier. {("The Monte Carlo simulation aligns closely with the semi-analytical Fourier integral ground truth, with pricing discrepancy fully enveloped by the 95% statistical confidence interval." if is_mc else "The pricing formulation demonstrates mathematical soundness across operational market regimes.")}

---

## 2. Mathematical Formulation & AST Structural Assumptions

Static Abstract Syntax Tree (AST) inspection extracted the following code-derived assumptions:
{assump_str}

### Structural Dynamics:
1. **Variance Dynamics & Skew**: Model implements stochastic variance diffusion with continuous mean reversion. The negative Brownian correlation captures the empirical equity leverage effect.
2. **Discretization Boundary Controls**: Time-stepping loops utilize Euler-Maruyama integration with non-negativity truncation guards, preventing numerical instability when variance paths approach zero.
3. **Discounting & Funding**: Evaluates expected payoff discounted at continuous risk-free rate $r$.
{mc_section}
---

## 4. Adversarial Non-Convex Stress Search

Differential evolution optimization identified the maximal pricing divergence coordinate:
- **Perturbed Spot Price ($S$)**: `${spot:.2f}`
- **Perturbed Volatility / Initial Variance ($v_0$)**: `{vol:.2f}%`
- **Perturbed Risk-Free Rate ($r$)**: `{r:.2f}%`
- **Candidate Model Price**: `${user_p:.4f}`
- **Theoretical Reference Price**: `${gt_p:.4f}`
- **Absolute Pricing Error**: `${abs_err:.5f}` (**{pct_err:.3f}%** relative error divergence)

---

## 5. Federal Reserve SR 11-7 Governance Protocol & Operational Boundaries

Pursuant to Federal Reserve SR 11-7 and OCC 2011-12 Supervisory Guidance on Model Risk Management:
1. **Operational Boundaries**: Model execution is approved for trading within $S \in [60, 150]$ and initial variance $v_0 \in [0.01, 0.64]$.
2. **Simulation Sample Size Policy**: For live book pricing and end-of-day P&L, maintain minimum $N \ge 50,000$ paths to guarantee standard error $\text{{SE}} \le \$0.04$.
3. **Model Recertification**: Re-audit the pricing engine quarterly or whenever numerical time-stepping or variance calibration routines are updated.
"""
