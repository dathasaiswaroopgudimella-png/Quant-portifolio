import ast
from typing import Dict, Any, List, Set

class ASTSecurityError(Exception):
    """Raised when uploaded Python model code contains prohibited AST nodes."""
    pass

class BlackScholesASTVisitor(ast.NodeVisitor):
    """
    AST Security Inspector and Quantitative Function Parameter Extractor.
    Validates code against dangerous imports, global mutations, or reflection.
    """
    ALLOWED_NODE_TYPES: Set[type] = {
        ast.Module,
        ast.FunctionDef,
        ast.AsyncFunctionDef,
        ast.arguments,
        ast.arg,
        ast.keyword,
        ast.Return,
        ast.Assign,
        ast.AugAssign,
        ast.AnnAssign,
        ast.Name,
        ast.Load,
        ast.Store,
        ast.Constant,
        ast.BinOp,
        ast.UnaryOp,
        ast.Compare,
        ast.If,
        ast.IfExp,
        ast.BoolOp,
        ast.Or,
        ast.And,
        ast.Call,
        ast.Lambda,
        ast.Expr,
        ast.Import,
        ast.ImportFrom,
        ast.alias,
        ast.For,
        ast.While,
        ast.List,
        ast.Tuple,
        ast.Dict,
        ast.Set,
        ast.ListComp,
        ast.DictComp,
        ast.SetComp,
        ast.GeneratorExp,
        ast.comprehension,
        ast.Subscript,
        ast.Slice,
        ast.Starred,
        ast.Pass,
        ast.Break,
        ast.Continue,
        ast.FormattedValue,
        ast.JoinedStr,
        ast.Try,
        ast.ExceptHandler,
        # Arithmetic & Bitwise
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod, ast.FloorDiv,
        ast.USub, ast.UAdd, ast.Not, ast.Invert,
        ast.BitOr, ast.BitAnd, ast.BitXor, ast.LShift, ast.RShift, ast.MatMult,
        # Comparisons
        ast.Gt, ast.GtE, ast.Lt, ast.LtE, ast.Eq, ast.NotEq,
        ast.In, ast.NotIn, ast.Is, ast.IsNot,
        ast.Attribute,
    }

    PROHIBITED_ATTRIBUTES: Set[str] = {
        "__class__", "__subclasses__", "__globals__", "__code__",
        "__builtins__", "__import__", "eval", "exec", "subprocess", "socket",
        "system", "popen", "os", "__bases__", "__mro__", "__init__",
        "__dict__", "__module__", "__getattribute__", "shutil", "builtins"
    }

    ALLOWED_MODULES: Set[str] = {
        "math", "cmath", "scipy", "scipy.stats", "scipy.optimize", "scipy.integrate",
        "scipy.interpolate", "numpy", "numpy.random", "typing", "collections", "dataclasses"
    }

    def __init__(self):
        self.function_name: str = ""
        self.parameters: List[str] = []
        self.default_args: Dict[str, Any] = {}
        self.local_definitions: Set[str] = set()
        self.is_valid: bool = True
        self.security_violations: List[str] = []

    def visit(self, node: ast.AST):
        node_type = type(node)
        if node_type not in self.ALLOWED_NODE_TYPES:
            err = f"Prohibited syntax element: '{node_type.__name__}' is not allowed in sandboxed models."
            self.security_violations.append(err)
            self.is_valid = False
        
        super().visit(node)

    def visit_Assign(self, node: ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.local_definitions.add(target.id)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if not self.function_name:
            self.function_name = node.name
            self.parameters = [arg.arg for arg in node.args.args]
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        for alias_item in node.names:
            base_mod = alias_item.name.split(".")[0]
            if base_mod not in self.ALLOWED_MODULES and alias_item.name not in self.ALLOWED_MODULES:
                self.security_violations.append(f"Prohibited import module '{alias_item.name}'.")
                self.is_valid = False
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            base_mod = node.module.split(".")[0]
            if base_mod not in self.ALLOWED_MODULES and node.module not in self.ALLOWED_MODULES:
                self.security_violations.append(f"Prohibited import module '{node.module}'.")
                self.is_valid = False
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        if node.attr in self.PROHIBITED_ATTRIBUTES:
            self.security_violations.append(f"Prohibited attribute access '{node.attr}'.")
            self.is_valid = False
        self.generic_visit(node)

def parse_and_validate_model_code(code: str) -> Dict[str, Any]:
    """
    Parses uploaded code into an AST tree and asserts AST security rules.
    Returns function signature and parameter mappings.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise ASTSecurityError(f"Syntax error in uploaded model code: {e.msg} at line {e.lineno}")

    visitor = BlackScholesASTVisitor()
    visitor.visit(tree)

    if not visitor.is_valid:
        raise ASTSecurityError("Security violation: " + "; ".join(visitor.security_violations))

    if not visitor.function_name:
        raise ASTSecurityError("No top-level pricing function found in code.")

    param_map = {}
    has_v0 = False
    has_sigma = False

    for p in visitor.parameters:
        p_lower = p.lower()
        if p_lower in ["s", "spot", "spot_price", "price", "underlying", "s0", "stock"]:
            param_map["spot"] = p
        elif p_lower in ["k", "strike", "strike_price", "k_strike"]:
            param_map["strike"] = p
        elif p_lower in ["t", "maturity", "tenor", "time_to_maturity", "time", "expiry", "texp"]:
            param_map["maturity"] = p
        elif p_lower in ["r", "rate", "risk_free_rate", "rf", "interest_rate"]:
            param_map["rate"] = p
        elif p_lower in ["v0", "var0", "variance0", "initial_variance"]:
            has_v0 = True
            param_map["v0"] = p
        elif p_lower in ["sigma", "vol", "volatility", "v", "sigma_v", "sig"]:
            has_sigma = True
            param_map["sigma"] = p
        elif p_lower in ["q", "dividend", "div", "dividend_yield", "yield_rate"]:
            param_map["dividend_yield"] = p
        elif p_lower in ["paths", "n_paths", "num_paths", "npaths", "mc_paths", "simulations"]:
            param_map["paths"] = p
        elif p_lower in ["steps", "n_steps", "num_steps", "nsteps", "timesteps"]:
            param_map["steps"] = p

    # Volatility resolution:
    # If both v0 and sigma are present (e.g. Heston stochastic vol model),
    # v0 represents initial variance (vol^2), while sigma represents vol-of-vol.
    if has_v0 and has_sigma:
        param_map["variance"] = param_map.get("v0")
        param_map["vol_of_vol"] = param_map.get("sigma")
        param_map["volatility"] = param_map.get("v0")  # will receive volatility**2
    elif has_sigma:
        param_map["volatility"] = param_map.get("sigma")
    elif has_v0:
        param_map["volatility"] = param_map.get("v0")

    return {
        "function_name": visitor.function_name,
        "parameters": visitor.parameters,
        "parameter_mapping": param_map,
        "is_stochastic_variance": has_v0 and has_sigma
    }
