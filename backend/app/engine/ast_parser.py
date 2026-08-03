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
        ast.IfExp,
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
        "__builtins__", "__import__", "eval", "exec", "subprocess", "socket", "system", "popen", "os"
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
        # Track locally assigned variable and lambda names
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.local_definitions.add(target.id)
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            if alias.name not in self.ALLOWED_MODULES:
                err = f"Security violation: Import of module '{alias.name}' is prohibited. Allowed: {self.ALLOWED_MODULES}"
                self.security_violations.append(err)
                self.is_valid = False
            self.local_definitions.add(alias.asname or alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module not in self.ALLOWED_MODULES:
            err = f"Security violation: Import from module '{node.module}' is prohibited. Allowed: {self.ALLOWED_MODULES}"
            self.security_violations.append(err)
            self.is_valid = False
        for alias in node.names:
            self.local_definitions.add(alias.asname or alias.name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if not self.function_name:
            self.function_name = node.name
            self.parameters = [arg.arg for arg in node.args.args]
        self.local_definitions.add(node.name)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        if node.attr in self.PROHIBITED_ATTRIBUTES:
            err = f"Security violation: Attribute access to '{node.attr}' is prohibited."
            self.security_violations.append(err)
            self.is_valid = False
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        func_name = ""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        
        if func_name:
            if func_name not in self.ALLOWED_FUNCTIONS and func_name not in self.local_definitions:
                err = f"Unauthorized function call: '{func_name}' is not in the whitelist or local definitions."
                self.security_violations.append(err)
                self.is_valid = False
        self.generic_visit(node)


def parse_and_validate_model_code(code: str) -> Dict[str, Any]:
    """
    Parses uploaded Python code, inspects security rules, and returns parameter mapping.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise ASTSecurityError(f"Syntax error in model code: {e.msg} at line {e.lineno}")

    visitor = BlackScholesASTVisitor()
    visitor.visit(tree)

    if not visitor.is_valid:
        raise ASTSecurityError("; ".join(visitor.security_violations))

    if not visitor.function_name:
        raise ASTSecurityError("No valid pricing function definition found in model code.")

    # Validate standard Black-Scholes parameter map
    params = visitor.parameters
    param_map = {}
    for p in params:
        p_lower = p.lower()
        if p_lower in ["s", "spot", "stock_price", "underlying"]:
            param_map["spot"] = p
        elif p_lower in ["k", "strike", "strike_price"]:
            param_map["strike"] = p
        elif p_lower in ["t", "maturity", "time", "tenor", "time_to_maturity"]:
            param_map["maturity"] = p
        elif p_lower in ["r", "rate", "risk_free_rate", "interest_rate"]:
            param_map["rate"] = p
        elif p_lower in ["sigma", "vol", "volatility"]:
            param_map["volatility"] = p

    return {
        "function_name": visitor.function_name,
        "parameters": visitor.parameters,
        "parameter_mapping": param_map,
        "is_secure": True,
        "ast_tree": ast.dump(tree)
    }
