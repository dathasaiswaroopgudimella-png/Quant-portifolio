import ast
from typing import Dict, Any, List, Set

class ASTSecurityError(Exception):
    """Raised when uploaded Python model code contains prohibited AST nodes."""
    pass

class BlackScholesASTVisitor(ast.NodeVisitor):
    """
    AST Security Inspector and Black-Scholes function parameter extractor.
    Validates code against dangerous imports, global mutations, or reflection.
    """
    ALLOWED_NODE_TYPES: Set[type] = {
        ast.Module,
        ast.FunctionDef,
        ast.arguments,
        ast.arg,
        ast.Return,
        ast.Assign,
        ast.AugAssign,
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
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod, ast.FloorDiv,
        ast.USub, ast.UAdd,
        ast.Gt, ast.GtE, ast.Lt, ast.LtE, ast.Eq, ast.NotEq,
        ast.Attribute,
    }

    PROHIBITED_ATTRIBUTES: Set[str] = {
        "__class__", "__subclasses__", "__globals__", "__code__",
        "__builtins__", "__import__", "eval", "exec", "subprocess", "socket", "system", "popen", "os",
        "__bases__", "__mro__", "__init__", "__dict__", "__module__", "__getattribute__"
    }

    ALLOWED_MODULES: Set[str] = {
        "math", "scipy", "scipy.stats", "numpy", "typing"
    }

    ALLOWED_FUNCTIONS: Set[str] = {
        "log", "exp", "sqrt", "erf", "pi", "abs", "min", "max", "norm_cdf", "cdf", "pow", "norm"
    }

    def __init__(self):
        self.function_name: str = ""
        self.parameters: List[str] = []
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
            if alias_item.name not in self.ALLOWED_MODULES:
                self.security_violations.append(f"Prohibited import module '{alias_item.name}'.")
                self.is_valid = False
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module and node.module not in self.ALLOWED_MODULES:
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
    Returns function signature and parameters.
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
    for p in visitor.parameters:
        p_lower = p.lower()
        if p_lower in ["s", "spot", "spot_price", "price"]:
            param_map[p] = "spot"
        elif p_lower in ["k", "strike", "strike_price"]:
            param_map[p] = "strike"
        elif p_lower in ["t", "maturity", "tenor", "time_to_maturity", "time"]:
            param_map[p] = "maturity"
        elif p_lower in ["r", "rate", "risk_free_rate", "rf"]:
            param_map[p] = "rate"
        elif p_lower in ["vol", "sigma", "volatility", "v"]:
            param_map[p] = "volatility"

    return {
        "function_name": visitor.function_name,
        "parameters": visitor.parameters,
        "parameter_mapping": param_map
    }
