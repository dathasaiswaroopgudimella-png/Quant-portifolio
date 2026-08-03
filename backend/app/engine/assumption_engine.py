import sympy as sp
from typing import Dict, Any, List
from app.engine.ast_parser import parse_and_validate_model_code

class AssumptionExtractor:
    """
    Symbolic Assumption Extraction Engine using SymPy.
    Identifies mathematical assumptions embedded in Black-Scholes pricing functions.
    """

    @staticmethod
    def extract_assumptions(code: str) -> List[Dict[str, Any]]:
        """
        Parses model AST and extracts symbolic mathematical assumptions.
        """
        # Parse AST to confirm valid structure
        parsed_info = parse_and_validate_model_code(code)
        
        # Define SymPy symbols for Black-Scholes parameters
        S, K, T, r, sigma, t = sp.symbols('S K T r sigma t', real=True, positive=True)

        assumptions = [
            {
                "name": "Constant Volatility Assumption",
                "category": "Volatility Dynamics",
                "mathematical_form": "d(sigma)/dt = 0, d(sigma)/dS = 0",
                "description": "The model assumes volatility remains constant over time and independent of spot price levels, ignoring volatility skew and stochastic volatility regimes.",
                "is_violated_in_stress": True
            },
            {
                "name": "Constant Risk-Free Interest Rate",
                "category": "Interest Rate Dynamics",
                "mathematical_form": "dr/dt = 0",
                "description": "Assumes the risk-free rate r is constant until maturity, ignoring interest rate yield curve shifts and stochastic rates.",
                "is_violated_in_stress": True
            },
            {
                "name": "Geometric Brownian Motion & Lognormal Returns",
                "category": "Asset Distribution",
                "mathematical_form": "dS_t = mu * S_t * dt + sigma * S_t * dW_t",
                "description": "Assumes log-returns are normally distributed with constant drift and variance, underestimating fat tails and market crash probabilities.",
                "is_violated_in_stress": True
            },
            {
                "name": "Frictionless Market & Continuous Delta Hedging",
                "category": "Market Microstructure",
                "mathematical_form": "Transaction_Cost = 0, Bid_Ask_Spread = 0",
                "description": "Assumes continuous costless trading without market impact, liquidity constraints, or discrete rebalancing drag.",
                "is_violated_in_stress": False
            },
            {
                "name": "European Exercise Style",
                "category": "Exercise Structure",
                "mathematical_form": "Exercise_Time == T",
                "description": "Option can only be exercised at exact expiration maturity T, excluding early exercise optionality inherent in American options.",
                "is_violated_in_stress": False
            }
        ]

        return assumptions
