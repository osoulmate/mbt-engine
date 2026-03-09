from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from graphviz import Digraph
from z3 import BoolVal, Solver, sat


@dataclass
class CDFGNode:
    name: str
    instructions: List[Any] = field(default_factory=list)
    is_exit: bool = False
    successors: List[Tuple["CDFGNode", Any]] = field(default_factory=list)

    def add_successor(self, node: "CDFGNode", condition: Any = True) -> None:
        self.successors.append((node, condition))


class CDFGAnalyzer:
    def __init__(self) -> None:
        self.all_feasible_paths: List[List[str]] = []
        self.all_nodes: List[CDFGNode] = []
        self.generated_models: List[Dict[str, str]] = []
        self.unsat_paths: List[str] = []

    def find_paths(
        self,
        current_node: CDFGNode,
        target_node: Optional[CDFGNode],
        constraints: List[Any],
        current_path: List[str],
    ) -> None:
        new_constraints = constraints + current_node.instructions
        current_path.append(current_node.name)

        if current_node.is_exit or (target_node and current_node is target_node):
            self._record_sat_path(current_path, new_constraints)
            return

        if not current_node.successors:
            self._record_sat_path(current_path, new_constraints)
            return

        for next_node, branch_cond in current_node.successors:
            combined_constraints = list(new_constraints)
            if branch_cond is not True:
                combined_constraints.append(branch_cond)

            solver = Solver()
            solver.add(combined_constraints)
            if solver.check() == sat:
                self.find_paths(next_node, target_node, combined_constraints, list(current_path))
            else:
                blocked = f"{' -> '.join(current_path)} -> {next_node.name}"
                self.unsat_paths.append(blocked)

    def _record_sat_path(self, current_path: List[str], constraints: List[Any]) -> None:
        path_str = " -> ".join(current_path)
        solver = Solver()
        solver.add(constraints)
        if solver.check() != sat:
            return

        self.all_feasible_paths.append(list(current_path))
        model = solver.model()
        model_data = ", ".join([f"{d} = {model[d]}" for d in model.decls()])
        self.generated_models.append(
            {
                "path": path_str,
                "inputs": f"[{model_data}]" if model_data else "[No Params Needed]",
            }
        )

    def visualize(self, filename: str = "cdfg_result") -> None:
        dot = Digraph(comment="CDFG Analyzer Output")
        dot.attr(rankdir="TB", size="10,8")
        dot.attr("node", shape="box", style="filled", fontname="Arial")

        for node in self.all_nodes:
            instr_str = "<br/>".join(
                [str(i).replace(">", "&gt;").replace("<", "&lt;") for i in node.instructions]
            )
            label = f'<<table border="0" cellborder="0"><tr><td><b>{node.name}</b></td></tr>'
            if instr_str:
                label += f"<tr><td><i>{instr_str}</i></td></tr>"
            label += "</table>>"

            color = "lavender"
            for path in self.all_feasible_paths:
                if node.name in path:
                    color = "gold"
                    break
            dot.node(node.name, label, fillcolor=color)

        for node in self.all_nodes:
            for next_node, cond in node.successors:
                edge_label = "" if cond is True else str(cond).replace(">", "&gt;").replace("<", "&lt;")
                edge_color = "black"
                penwidth = "1.0"
                for path in self.all_feasible_paths:
                    if node.name in path and next_node.name in path:
                        idx = path.index(node.name)
                        if idx < len(path) - 1 and path[idx + 1] == next_node.name:
                            edge_color = "red"
                            penwidth = "2.5"
                            break
                dot.edge(node.name, next_node.name, label=edge_label, color=edge_color, penwidth=penwidth)

        dot.render(filename, format="png", view=False)
