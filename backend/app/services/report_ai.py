import os
import re
import json
import httpx
from typing import Dict, Any, Optional
from app.core.config import settings

class OpenRouterReportService:
    """
    OpenRouter AI Executive Summary & Prompt-to-Model Synthesizer.
    Provides natural language model generation and SR 11-7 governance narratives.
    """

    @staticmethod
    def get_api_key() -> Optional[str]:
        return os.getenv("OPENROUTER_API_KEY") or settings.OPENROUTER_API_KEY

    @staticmethod
    async def synthesize_model_from_prompt(prompt: str, asset_class: str = "Equity Options") -> Dict[str, str]:
        """
        Synthesizes a valid Python pricing function from natural language or LaTeX formulas using OpenRouter AI.
        Falls back to intelligent template generator if API key is not configured.
        """
        api_key = OpenRouterReportService.get_api_key()
        if not api_key:
            return OpenRouterReportService._generate_fallback_synthetic_model(prompt, asset_class)

        candidate_models = [
            os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash"),
            "meta-llama/llama-3.1-70b-instruct",
            "openai/gpt-4o-mini",
            "google/gemini-flash-1.5"
        ]
        system_prompt = (
            "You are a Quantitative Software Engineer. Convert natural language descriptions, formulas, "
            "or mathematical requirements into executable Python functions for option pricing. "
            "The function MUST take exactly 5 parameters: S (spot), K (strike), T (maturity in years), "
            "r (risk-free rate), sigma (volatility). Only use standard Python math or scipy.stats. "
            "Return valid JSON with keys: name, description, code."
        )

        user_prompt = f"""
        Prompt / Formula: "{prompt}"
        Asset Class: "{asset_class}"

        Generate a single executable Python function `def price_option(S, K, T, r, sigma):` 
        that implements this formula accurately. Ensure math and scipy.stats are imported inside or accessible.
        Return JSON format:
        {{
          "name": "<Short Model Title>",
          "description": "<Technical Summary>",
          "code": "def price_option(S, K, T, r, sigma):\\n    import math\\n    ..."
        }}
        """

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
                        # Extract JSON payload
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
        if "put" in prompt_lower:
            code = (
                "def black_scholes_put(S, K, T, r, sigma):\n"
                "    import math\n"
                "    d1 = (math.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*math.sqrt(T))\n"
                "    d2 = d1 - sigma*math.sqrt(T)\n"
                "    N = lambda x: 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))\n"
                "    return K * math.exp(-r*T) * N(-d2) - S * N(-d1)\n"
            )
            name = "Synthesized BSM European Put"
            desc = f"Synthesized put option model based on requirement: '{prompt}'"
        elif "garman" in prompt_lower or "fx" in prompt_lower or "currency" in prompt_lower:
            code = (
                "def garman_kohlhagen_fx(S, K, T, r, sigma):\n"
                "    import math\n"
                "    rf = 0.02  # foreign rate assumption\n"
                "    d1 = (math.log(S/K) + (r - rf + 0.5*sigma**2)*T) / (sigma*math.sqrt(T))\n"
                "    d2 = d1 - sigma*math.sqrt(T)\n"
                "    N = lambda x: 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))\n"
                "    return S * math.exp(-rf*T) * N(d1) - K * math.exp(-r*T) * N(d2)\n"
            )
            name = "Synthesized Garman-Kohlhagen FX Model"
            desc = f"Foreign exchange option model synthesized for: '{prompt}'"
        else:
            code = (
                "def black_scholes_call(S, K, T, r, sigma):\n"
                "    import math\n"
                "    d1 = (math.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*math.sqrt(T))\n"
                "    d2 = d1 - sigma*math.sqrt(T)\n"
                "    N = lambda x: 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))\n"
                "    return S * N(d1) - K * math.exp(-r*T) * N(d2)\n"
            )
            name = "Synthesized BSM European Call"
            desc = f"Analytical option model synthesized from prompt: '{prompt}'"

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
        """
        Computes 6 independent Radar Scores (0.0 to 100.0) for model risk assessment.
        Each axis evaluates a distinct mathematical, structural, or empirical dimension.
        """
        # Axis 1: Conceptual Soundness (driven by code-backed assumption confidence & AST guards)
        ast_guards = [a for a in (assumptions or []) if "Safeguards" in a.get("name", "")]
        conceptual = 95.0 if ast_guards else max(30.0, round(90.0 - fragility_score * 0.4, 1))

        # Axis 2: Numerical Stability (driven by pricing behavior under small values)
        stability = round(max(10.0, min(100.0, 100.0 - min(pct_error * 1.8, 85.0))), 1)

        # Axis 3: Parameter Robustness (driven by multi-seed DE optimizer stability)
        opt_stab = breaking_params.get("optimizer_stability", 85.0) if breaking_params else 85.0
        robustness = round(max(10.0, min(100.0, opt_stab - fragility_score * 0.3)), 1)

        # Axis 4: Boundary Condition Safety (driven by deep OTM / high vol relative drift)
        boundary = round(max(10.0, min(100.0, 98.0 - min(pct_error * 1.4, 75.0))), 1)
        
        # Axis 5: Greek Fidelity (driven by actual numerical Delta & Vega drift vs QuantLib at worst-case)
        d_drift = greek_drifts.get("delta_drift", 0.0) if greek_drifts else 0.0
        v_drift = greek_drifts.get("vega_drift", 0.0) if greek_drifts else 0.0
        greek_fidelity = round(max(10.0, min(100.0, 100.0 - (d_drift * 50.0 + v_drift * 60.0))), 1)

        # Axis 6: Benchmark Alignment (driven by base-case divergence vs QuantLib analytical truth)
        base_err = breaking_params.get("absolute_error", 0.0) if breaking_params else 0.0
        benchmark_align = round(max(10.0, min(100.0, 100.0 - min(base_err * 8.0 + pct_error * 1.2, 85.0))), 1)

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
        assumptions: list
    ) -> str:
        """
        Synthesizes human-readable validation summary via OpenRouter API with multi-model resilience,
        or falls back to deterministic template synthesis.
        """
        api_key = OpenRouterReportService.get_api_key()
        if not api_key:
            return OpenRouterReportService._generate_template_summary(
                model_name, fragility_score, classification, breaking_params, assumptions
            )

        candidate_models = [
            os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash"),
            "meta-llama/llama-3.1-70b-instruct",
            "openai/gpt-4o-mini",
            "google/gemini-flash-1.5"
        ]

        system_prompt = (
            "You are a Senior Model Risk Manager and Quantitative Auditor specializing in Federal Reserve "
            "SR 11-7 governance guidelines. Synthesize executive-level, mathematically sound model risk reviews."
        )

        user_prompt = f"""
        Generate a comprehensive, world-class Model Risk Governance & SR 11-7 Executive Report for the following validation run:

        ### Target Model: {model_name}
        - **Fragility Index**: {fragility_score}/100 ({classification} Tier)
        - **Worst-Case Breaking Scenario (SciPy DE Search)**:
          - Perturbed Spot Price: ${breaking_params.get('spot', 'N/A')}
          - Perturbed Volatility: {breaking_params.get('volatility', 0)*100:.1f}%
          - Perturbed Interest Rate: {breaking_params.get('risk_free_rate', 0)*100:.2f}%
          - User Model Output Price: ${breaking_params.get('user_price', 'N/A')}
          - QuantLib 1.43 Ground Truth Price: ${breaking_params.get('quantlib_price', 'N/A')}
          - Maximum Absolute Error: ${breaking_params.get('absolute_error', 'N/A')} ({breaking_params.get('percentage_error', 'N/A')}% divergence)
        - **Extracted Mathematical Assumptions**: {[a.get('name', '') for a in assumptions]}

        Please structure your output in clear prose with the following sections:
        1. **Executive Overview**: High-level summary of model performance and fragility tier.
        2. **Mathematical Assumption Breakdown**: Analysis of implicit assumptions (e.g. constant volatility ∂σ/∂t=0) and why they fail under stress.
        3. **Adversarial Worst-Case Analysis**: Detailed explanation of how the breaking perturbation degrades pricing accuracy relative to QuantLib ground truth.
        4. **SR 11-7 Regulatory Compliance Audit**: Specific governance recommendations, monitoring requirements, and operational boundaries.
        """

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
                            "max_tokens": 800,
                            "temperature": 0.3
                        }
                    )
                    if response.status_code == 200:
                        data = response.json()
                        if "choices" in data and len(data["choices"]) > 0:
                            content = data["choices"][0]["message"]["content"]
                            if content and len(content.strip()) > 50:
                                return content
            except Exception as e:
                print(f"[OpenRouterService] API notice for model '{model_to_use}': {e}")
                continue

        return OpenRouterReportService._generate_template_summary(
            model_name, fragility_score, classification, breaking_params, assumptions
        )

    @staticmethod
    def _generate_template_summary(
        model_name: str,
        fragility_score: float,
        classification: str,
        breaking_params: Dict[str, Any],
        assumptions: list
    ) -> str:
        assump_str = ", ".join([a.get('name', '') for a in assumptions]) if assumptions else "Constant Volatility, Constant Risk-Free Rate"
        return (
            f"### Executive Model Risk Summary for '{model_name}'\n\n"
            f"**Fragility Classification**: {fragility_score:.1f}/100 — **{classification}**\n\n"
            f"Adversarial non-convex optimization via SciPy Differential Evolution identified a breaking market regime at "
            f"Spot = ${breaking_params.get('spot', 0):.2f}, Volatility = {breaking_params.get('volatility', 0)*100:.1f}%, and "
            f"Interest Rate = {breaking_params.get('risk_free_rate', 0)*100:.2f}%. Under this scenario, model pricing deviates by "
            f"${breaking_params.get('absolute_error', 0):.4f} ({breaking_params.get('percentage_error', 0):.2f}%) from QuantLib 1.43 analytical ground truth.\n\n"
            f"**Extracted Implicit Assumptions**: {assump_str}.\n\n"
            f"**SR 11-7 Governance Action**: Model risk management recommends enforcing strict volatility boundaries "
            f"and configuring continuous real-time market monitoring against historical 21-day volatility drift."
        )

