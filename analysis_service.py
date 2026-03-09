from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Dict

from auto_cdfg_recursive import RecursiveAutoCDFG
from cdfg_analyzer import CDFGNode


class AnalysisError(Exception):
    pass


class AnalysisService:
    def __init__(self, static_image_dir: Path):
        self.static_image_dir = static_image_dir

    def analyze_file(self, file_path: Path, output_name: str = "analysis_result") -> Dict[str, Any]:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        if not tree.body:
            raise AnalysisError("文件为空，无法进行分析。")

        first_node = tree.body[0]
        if not isinstance(first_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            raise AnalysisError("请上传包含函数定义的 Python 文件。")

        app_logic = RecursiveAutoCDFG()
        entry = CDFGNode("Start")
        app_logic.analyzer.all_nodes.append(entry)
        tail = app_logic.build_recursive(first_node.body, entry)

        if not tail.is_exit:
            implicit_exit = CDFGNode("Implicit_Exit", is_exit=True)
            app_logic.analyzer.all_nodes.append(implicit_exit)
            tail.add_successor(implicit_exit)

        app_logic.analyzer.find_paths(entry, None, [], [])
        output_path = self.static_image_dir / output_name
        app_logic.analyzer.visualize(str(output_path))

        return {
            "test_cases": app_logic.analyzer.generated_models,
            "warnings": app_logic.warnings,
            "blocked_paths": app_logic.analyzer.unsat_paths,
            "output_filename": f"images/{output_name}.png",
        }
