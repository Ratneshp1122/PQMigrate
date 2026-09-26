import ast
from pqc_migration_tool.schema.models import CryptoIR, ProtocolContext

class ContextInferenceEngine:
    """
    D6: Context Inference Engine.
    Examines AST to link explicit operation, algorithm, and key variable 
    via bounded same-function dataflow.
    """
    def __init__(self, source_code: str):
        self.source_code = source_code
        try:
            self.tree = ast.parse(source_code)
        except Exception:
            self.tree = None

    def infer_context(self, finding: CryptoIR) -> CryptoIR:
        """
        Enhances the CryptoIR with context and evidence.
        """
        if not self.tree:
            finding.protocol_context = ProtocolContext.UNKNOWN
            finding.context_evidence = "AST parsing failed."
            return finding
            
        line_no = finding.location.line_number
        
        # Check if the node is inside a function or script scope
        enclosing_func = self._get_enclosing_function(line_no)
        if enclosing_func:
            jwt_context = self._check_jwt_in_scope(enclosing_func, line_no)
            if jwt_context:
                finding.protocol_context = ProtocolContext.JWT
                finding.context_evidence = "Explicit jwt.encode/decode found in same function."
                return finding
                
            ssh_context = self._check_ssh_in_scope(enclosing_func, line_no)
            if ssh_context:
                finding.protocol_context = ProtocolContext.SSH
                finding.context_evidence = "Paramiko/SSH usage detected in same function."
                return finding

        # If not matched, we abstain from assigning a protocol.
        finding.protocol_context = ProtocolContext.UNKNOWN
        finding.context_evidence = "No explicit protocol dataflow linked to this usage."
        return finding

    def _get_enclosing_function(self, line_no: int) -> ast.FunctionDef:
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                if node.lineno <= line_no and getattr(node, 'end_lineno', float('inf')) >= line_no:
                    return node
        return None

    def _check_jwt_in_scope(self, func_node: ast.FunctionDef, line_no: int) -> bool:
        """
        Looks for `jwt.encode(..., algorithm=...)` in the same function.
        """
        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                elif isinstance(node.func, ast.Name):
                    func_name = node.func.id
                
                if func_name in ['encode', 'decode']:
                    # Heuristically check if this is likely a jwt call
                    # (e.g., checks for kwargs 'algorithm' or 'key')
                    for kw in getattr(node, 'keywords', []):
                        if kw.arg in ['algorithm', 'algorithms']:
                            return True
        return False

    def _check_ssh_in_scope(self, func_node: ast.FunctionDef, line_no: int) -> bool:
        """
        Looks for paramiko or ssh client usage.
        """
        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                    
                if func_name in ['connect', 'SSHClient']:
                    return True
        return False
