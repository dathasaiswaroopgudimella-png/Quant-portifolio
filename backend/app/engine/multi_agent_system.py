"""
FRAGMENT Multi-Agent Autonomous Quantitative System (Inspired by AgentQuant)
Orchestrates specialized sub-agents into a unified, institutional model risk validation pipeline.
"""
from typing import Dict, Any, List
import numpy as np

from app.engine.sandbox import SandboxedModelEvaluator
from app.engine.model_classifier import ModelClassifier, ModelBenchmarkRouter
from app.engine.monte_carlo_diagnostics import MonteCarloDiagnostics
from app.engine.adversarial_engine import AdversarialEngine
from app.engine.arbitrage_checker import ArbitrageChecker
from app.engine.stress_testing_agent import StressTestingAgent
from app.engine.assumption_engine import AssumptionExtractor
from app.engine.fragility_scorer import FragilityScorer
from app.engine.expectations import ModelExpectationSuite
from app.services.report_ai import OpenRouterReportService


class MultiAgentQuantPipeline:
    """
    Coordinator agent managing the 6 specialized quant sub-agents:
    1. Model Classifier & Ground Truth Router
    2. Monte Carlo & Statistical Convergence Auditor
    3. AST Assumption Extraction Agent
    4. Adversarial Parameter Search Agent (SciPy DE)
    5. No-Arbitrage Integrity Agent
    6. Stress Testing & Tail Risk Agent
    7. Federal Reserve SR 11-7 Regulatory Governance Agent
    """

    @staticmethod
    async def execute_full_validation_pipeline(
        model_name: str,
        model_code: str,
        spot: float = 100.0,
        strike: float = 100.0,
        maturity: float = 1.0,
        rate: float = 0.05,
        volatility: float = 0.20,
        dividend_yield: float = 0.0,
        option_type: str = "call"
    ) -> Dict[str, Any]:
        """
        Runs the comprehensive multi-agent validation pipeline.
        """
        # ── Agent 1: Model Classification ────────────────────────────────────
        model_meta = ModelClassifier.classify_model(model_code)
        family = model_meta["family"]
        is_mc = model_meta["is_monte_carlo"]

        # Create sandboxed callable functions
        target_pricer_full = SandboxedModelEvaluator.create_executable_callable(model_code, fast_mode=False)
        target_pricer_fast = SandboxedModelEvaluator.create_executable_callable(model_code, fast_mode=True)

        # ── Agent 2: AST Assumption Extraction ──────────────────────────────
        extracted_assumptions = AssumptionExtractor.extract_assumptions(model_code)

        # ── Agent 3: Adversarial Auditor (SciPy DE Global Search) ───────────
        adv_res = AdversarialEngine.run_adversarial_search(
            model_code=model_code,
            base_spot=spot,
            base_strike=strike,
            base_maturity=maturity,
            base_rate=rate,
            base_volatility=volatility,
            dividend_yield=dividend_yield,
            option_type=option_type
        )
        base_metrics = adv_res["base_metrics"]
        breaking_params = adv_res["breaking_parameters"]
        greek_drifts = adv_res.get("greek_drifts", {})
        surface = adv_res["fragility_surface"]

        # ── Agent 4: Monte Carlo Convergence Diagnostics ───────────────────
        mc_diagnostics = None
        if is_mc:
            # Evaluate raw output for metadata extraction
            try:
                # Compile raw function to get dict
                safe_scope: Dict[str, Any] = {}
                compiled = compile(model_code, "<mc_diag>", "exec")
                from app.engine.sandbox import _get_safe_globals
                exec(compiled, _get_safe_globals(), safe_scope)
                raw_callable = safe_scope.get(model_meta.get("function_name", list(safe_scope.keys())[-1]))
                # Call with base parameters
                raw_out = raw_callable(spot, strike, maturity, rate) if callable(raw_callable) else {}
            except Exception:
                raw_out = {}

            mc_diagnostics = MonteCarloDiagnostics.audit_simulation(
                raw_output=raw_out,
                pricer_fn=target_pricer_full,
                ground_truth_price=base_metrics["quantlib_price"],
                spot=spot,
                strike=strike,
                maturity=maturity,
                rate=rate,
                volatility=volatility,
                model_family=family,
                stochastic_params=base_metrics.get("stochastic_parameters", {})
            )

        # ── Agent 5: No-Arbitrage Integrity Agent ───────────────────────────
        arbitrage_audit = ArbitrageChecker.run_arbitrage_audit(
            pricer_fn=target_pricer_fast,
            spot=spot,
            strike=strike,
            maturity=maturity,
            rate=rate,
            volatility=volatility
        )

        # ── Agent 6: Stress Testing & Crisis Replay Agent ───────────────────
        stress_audit = StressTestingAgent.run_stress_battery(
            pricer_fn=target_pricer_fast,
            base_spot=spot,
            base_strike=strike,
            base_maturity=maturity,
            base_rate=rate,
            base_vol=volatility
        )

        # ── Agent 7: Fragility & Hexagonal Radar Scoring ────────────────────
        fragility_data = FragilityScorer.calculate_fragility(
            base_error=base_metrics["base_error"],
            max_adversarial_error=breaking_params["absolute_error"],
            breaking_params=breaking_params,
            base_price=base_metrics["quantlib_price"],
            greek_drifts=greek_drifts
        )

        hex_scores = OpenRouterReportService.compute_hexagonal_scores(
            fragility_score=fragility_data["fragility_score"],
            pct_error=breaking_params.get("percentage_error", 0.0),
            greeks=base_metrics.get("base_greeks", {}),
            greek_drifts=greek_drifts,
            assumptions=extracted_assumptions,
            breaking_params=breaking_params
        )

        expectations = ModelExpectationSuite.evaluate_expectations(
            user_price=base_metrics["user_price"],
            quantlib_price=base_metrics["quantlib_price"],
            greeks=base_metrics["base_greeks"],
            spot=spot,
            strike=strike,
            maturity=maturity,
            rate=rate,
            option_type=option_type
        )

        # ── Agent 8: Federal Reserve SR 11-7 Executive Synthesis ───────────
        effective_name = model_name if model_name and "Financial Model" not in model_name else model_meta["name"]
        exec_summary = await OpenRouterReportService.generate_executive_summary(
            model_name=effective_name,
            fragility_score=fragility_data["fragility_score"],
            classification=fragility_data["classification"],
            breaking_params=breaking_params,
            assumptions=extracted_assumptions,
            model_meta=model_meta,
            mc_diagnostics=mc_diagnostics
        )

        sr11_7_payload = {
            "framework": "Federal Reserve SR 11-7 / OCC 2011-12 Aligned Model Governance",
            "model_name": effective_name,
            "model_family": family,
            "ground_truth_engine": base_metrics["benchmark_engine"],
            "conceptual_soundness": "PASS" if fragility_data["fragility_score"] < 40.0 else "WARNING",
            "ongoing_monitoring": "REQUIRED",
            "sensitivity_analysis": "PASSED_DIFFERENTIAL_EVOLUTION_SEARCH",
            "arbitrage_integrity": arbitrage_audit["status"],
            "stress_resilience": stress_audit["tail_risk_metrics"]["stress_resilience_rating"],
            "actionable_recommendation": fragility_data["actionable_recommendation"],
            "expectations_suite": expectations,
            "monte_carlo_diagnostics": mc_diagnostics
        }

        report_payload = {
            "summary": fragility_data["summary"],
            "actionable_recommendation": fragility_data["actionable_recommendation"],
            "risk_attribution": fragility_data["risk_attribution"],
            "model_metadata": model_meta,
            "base_metrics": base_metrics,
            "breaking_parameters": breaking_params,
            "expectations": expectations,
            "hexagonal_scores": hex_scores,
            "arbitrage_audit": arbitrage_audit,
            "stress_audit": stress_audit,
            "monte_carlo_diagnostics": mc_diagnostics
        }

        return {
            "model_metadata": model_meta,
            "fragility_data": fragility_data,
            "base_metrics": base_metrics,
            "breaking_parameters": breaking_params,
            "greek_drifts": greek_drifts,
            "fragility_surface": surface,
            "hexagonal_scores": hex_scores,
            "arbitrage_audit": arbitrage_audit,
            "stress_audit": stress_audit,
            "monte_carlo_diagnostics": mc_diagnostics,
            "executive_summary": exec_summary,
            "sr11_7_payload": sr11_7_payload,
            "report_payload": report_payload
        }
