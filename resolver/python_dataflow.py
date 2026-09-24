import ast
from typing import Dict, List, Set, Tuple

class PythonDataflowResolver(ast.NodeVisitor):
    """
    Lightweight AST Dataflow Resolver.
    Tracks imports (e.g., 'from cryptography.hazmat... import rsa')
    and looks for specific method calls (e.g., '.sign', '.encrypt') on those modules.
    """
    def __init__(self):
        self.tracked_names: Dict[str, str] = {} # local_name -> full_module_path
        self.resolved_operations: List[Tuple[str, str, ast.Call]] = [] # (module_path, operation_verb, node)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            local_name = alias.asname or alias.name
            self.tracked_names[local_name] = alias.name
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        module = node.module or ""
        for alias in node.names:
            local_name = alias.asname or alias.name
            full_path = f"{module}.{alias.name}" if module else alias.name
            self.tracked_names[local_name] = full_path
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        # Look for obj.method() calls
        if isinstance(node.func, ast.Attribute):
            method_name = node.func.attr
            # Simple heuristic: if the method is a crypto operation
            op_verbs = {'sign', 'verify', 'encrypt', 'decrypt', 'generate_private_key', 'exchange', 'derive'}
            if method_name in op_verbs:
                # Try to resolve the base object name
                base_name = self._get_base_name(node.func.value)
                if base_name in self.tracked_names:
                    module_path = self.tracked_names[base_name]
                    self.resolved_operations.append((module_path, method_name, node))
                elif base_name: 
                    # Even if we didn't track the import directly, record the base name + operation
                    self.resolved_operations.append((base_name, method_name, node))

        self.generic_visit(node)

    def _get_base_name(self, node: ast.AST) -> str:
        """Attempt to extract the root variable name from an AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return self._get_base_name(node.value)
        elif isinstance(node, ast.Call):
            return self._get_base_name(node.func)
        return ""

def resolve_file(filepath: str) -> 'PythonDataflowResolver':
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    tree = ast.parse(source, filename=filepath)
    resolver = PythonDataflowResolver()
    resolver.visit(tree)
    return resolver
