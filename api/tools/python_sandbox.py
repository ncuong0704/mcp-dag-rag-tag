import ast
import threading
from typing import Any

FORBIDDEN_NAMES = {"os", "subprocess", "sys", "open", "eval", "exec", "__import__", "builtins"}
ALLOWED_IMPORTS = {"math", "statistics", "json", "datetime"}


class SandboxError(Exception):
    pass


def validate_code(code: str) -> None:
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root not in ALLOWED_IMPORTS:
                    raise SandboxError(f"Import không cho phép: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root = node.module.split(".")[0]
                if root not in ALLOWED_IMPORTS:
                    raise SandboxError(f"Import không cho phép: {node.module}")
        elif isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            raise SandboxError(f"Biến/hàm không cho phép: {node.id}")
        elif isinstance(node, ast.Attribute) and node.attr in {"system", "popen"}:
            raise SandboxError(f"Thuộc tính không cho phép: {node.attr}")


def _run_code(code: str, local_vars: dict[str, Any], error_box: list[str]) -> None:
    try:
        safe_builtins = {
            "abs": abs,
            "min": min,
            "max": max,
            "sum": sum,
            "len": len,
            "round": round,
            "range": range,
            "float": float,
            "int": int,
            "str": str,
            "list": list,
            "dict": dict,
            "tuple": tuple,
            "print": print,
        }
        exec(compile(code, "<sandbox>", "exec"), {"__builtins__": safe_builtins}, local_vars)
    except Exception as exc:
        error_box.append(str(exc))


def execute_python(code: str, timeout: int = 10) -> dict:
    validate_code(code)
    local_vars: dict[str, Any] = {}
    error_box: list[str] = []

    thread = threading.Thread(target=_run_code, args=(code, local_vars, error_box))
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        return {"success": False, "error": "Timeout: vượt quá 10 giây"}
    if error_box:
        return {"success": False, "error": error_box[0]}

    result = local_vars.get("result", local_vars.get("ket_qua"))
    return {"success": True, "result": result, "stdout": str(result)}
