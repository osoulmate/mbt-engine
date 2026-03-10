from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Dict, List

from auto_cdfg_recursive import RecursiveAutoCDFG
from cdfg_analyzer import CDFGNode


class AnalysisError(Exception):
    pass


class AnalysisService:
    def __init__(self, static_image_dir: Path):
        self.static_image_dir = static_image_dir

    def _analyze_function(self, func_node: ast.AST, output_name: str | None = None) -> Dict[str, Any]:
        app_logic = RecursiveAutoCDFG()
        entry = CDFGNode(f"Start_{getattr(func_node, 'name', 'function')}")
        app_logic.analyzer.all_nodes.append(entry)
        tail = app_logic.build_recursive(func_node.body, entry)

        if not tail.is_exit:
            implicit_exit = CDFGNode("Implicit_Exit", is_exit=True)
            app_logic.analyzer.all_nodes.append(implicit_exit)
            tail.add_successor(implicit_exit)

        app_logic.analyzer.find_paths(entry, None, [], [])

        output_filename = None
        if output_name:
            output_path = self.static_image_dir / output_name
            app_logic.analyzer.visualize(str(output_path))
            output_filename = f"images/{output_name}.png"

        return {
            "function_name": getattr(func_node, "name", "<anonymous>"),
            "test_cases": app_logic.analyzer.generated_models,
            "warnings": app_logic.warnings,
            "blocked_paths": app_logic.analyzer.unsat_paths,
            "output_filename": output_filename,
        }

    def analyze_file(self, file_path: Path, output_name: str = "analysis_result") -> Dict[str, Any]:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        if not tree.body:
            raise AnalysisError("文件为空，无法进行分析。")

        function_nodes: List[ast.AST] = [
            node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        if not function_nodes:
            raise AnalysisError("请上传包含至少一个函数定义的 Python 文件。")

        test_cases: List[Dict[str, str]] = []
        warnings: List[str] = []
        blocked_paths: List[str] = []

        for i, func_node in enumerate(function_nodes):
            func_result = self._analyze_function(
                func_node,
                output_name=output_name if i == 0 else None,
            )
            function_name = func_result["function_name"]
            for case in func_result["test_cases"]:
                test_cases.append({"function": function_name, **case})
            warnings.extend([f"[{function_name}] {w}" for w in func_result["warnings"]])
            blocked_paths.extend([f"[{function_name}] {p}" for p in func_result["blocked_paths"]])

        return {
            "test_cases": test_cases,
            "warnings": warnings,
            "blocked_paths": blocked_paths,
            "output_filename": f"images/{output_name}.png",
        }
