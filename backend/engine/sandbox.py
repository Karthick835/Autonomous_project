import ast
import json
import os
import sys
import subprocess
import tempfile
import time
from typing import Dict, Any, List, Tuple, Optional

FORBIDDEN_AST_NODES = {
    'import_modules': {'os', 'subprocess', 'shutil', 'socket', 'urllib', 'http', 'requests', 'ctypes', 'winreg'},
    'function_calls': {'eval', 'exec', 'system', 'popen', 'spawn', 'rmdir', 'remove', 'unlink'}
}

class ASTSecurityVisitor(ast.NodeVisitor):
    def __init__(self):
        self.violations: List[str] = []

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            base_mod = alias.name.split('.')[0]
            if base_mod in FORBIDDEN_AST_NODES['import_modules']:
                self.violations.append(f"Forbidden module import: '{alias.name}'")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            base_mod = node.module.split('.')[0]
            if base_mod in FORBIDDEN_AST_NODES['import_modules']:
                self.violations.append(f"Forbidden module import: '{node.module}'")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name):
            if node.func.id in FORBIDDEN_AST_NODES['function_calls']:
                self.violations.append(f"Forbidden function call: '{node.func.id}()'")
        elif isinstance(node.func, ast.Attribute):
            if node.func.attr in FORBIDDEN_AST_NODES['function_calls']:
                self.violations.append(f"Forbidden function attribute call: '.{node.func.attr}()'")
        self.generic_visit(node)

def validate_code_safety(code_str: str) -> Tuple[bool, List[str]]:
    """Statically inspect code for disallowed syntax or unsafe imports."""
    try:
        parsed_ast = ast.parse(code_str)
        visitor = ASTSecurityVisitor()
        visitor.visit(parsed_ast)
        if visitor.violations:
            return False, visitor.violations
        return True, []
    except SyntaxError as se:
        return False, [f"Syntax error in code: {se}"]
    except Exception as e:
        return False, [f"AST Parsing error: {str(e)}"]

class PythonSandbox:
    """Isolated Python execution sandbox with timeout and security AST validation."""

    def __init__(self, working_dir: Optional[str] = None, timeout_seconds: int = 15):
        self.working_dir = working_dir or os.getcwd()
        self.timeout_seconds = timeout_seconds

    def execute_script(self, code_str: str, csv_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes a script safely and returns structured output.
        """
        is_safe, violations = validate_code_safety(code_str)
        if not is_safe:
            return {
                "success": False,
                "output": "",
                "error": f"Security Validation Failed:\n" + "\n".join(violations),
                "execution_time_sec": 0.0,
                "parsed_result": None
            }

        # Inject standard setup header if csv_path is provided
        script_content = []
        if csv_path:
            norm_csv = os.path.abspath(csv_path).replace("\\", "/")
            script_content.append("import pandas as pd")
            script_content.append("import numpy as np")
            script_content.append("import scipy.stats as stats")
            script_content.append("import json")
            script_content.append(f"df = pd.read_csv('{norm_csv}')")
        
        script_content.append(code_str)
        full_code = "\n".join(script_content)

        # Write to a temporary file in working directory
        temp_file_path = os.path.join(self.working_dir, f"_temp_exec_{int(time.time()*1000)}.py")
        try:
            with open(temp_file_path, "w", encoding="utf-8") as f:
                f.write(full_code)

            start_time = time.time()
            proc = subprocess.run(
                [sys.executable, temp_file_path],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds
            )
            exec_time = time.time() - start_time

            stdout = proc.stdout.strip()
            stderr = proc.stderr.strip()

            parsed_result = None
            # Attempt to parse json from stdout if printed
            if stdout:
                for line in reversed(stdout.splitlines()):
                    line_str = line.strip()
                    if line_str.startswith("{") and line_str.endswith("}"):
                        try:
                            parsed_result = json.loads(line_str)
                            break
                        except Exception:
                            pass

            return {
                "success": proc.returncode == 0,
                "output": stdout,
                "error": stderr if proc.returncode != 0 else "",
                "execution_time_sec": round(exec_time, 3),
                "parsed_result": parsed_result
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": f"Execution timed out after {self.timeout_seconds} seconds.",
                "execution_time_sec": float(self.timeout_seconds),
                "parsed_result": None
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"Sandbox Exception: {str(e)}",
                "execution_time_sec": 0.0,
                "parsed_result": None
            }
        finally:
            if os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except Exception:
                    pass
