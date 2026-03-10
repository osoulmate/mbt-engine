from __future__ import annotations

import ast
from typing import Any, List, Optional, Tuple

from z3 import And, ArithRef, BoolRef, BoolVal, If as Z3If, Int, IntVal, Not, Or

from cdfg_analyzer import CDFGAnalyzer, CDFGNode


class RecursiveAutoCDFG:
    def __init__(self) -> None:
        self.analyzer = CDFGAnalyzer()
        self.vars = {}
        self.warnings: List[str] = []
        self._node_counter = 0

    def get_var(self, name: str) -> ArithRef:
        if name not in self.vars:
            self.vars[name] = Int(name)
        return self.vars[name]

    def _new_name(self, prefix: str, node: Optional[ast.AST] = None) -> str:
        self._node_counter += 1
        if node is not None and hasattr(node, "lineno"):
            return f"{prefix}_{node.lineno}_{getattr(node, 'col_offset', 0)}_{self._node_counter}"
        return f"{prefix}_{self._node_counter}"

    def _to_int_expr(self, expr: Any) -> Any:
        if isinstance(expr, bool):
            return IntVal(int(expr))
        if isinstance(expr, BoolRef):
            return Z3If(expr, IntVal(1), IntVal(0))
        return expr

    def parse_expr(self, node: ast.AST) -> Tuple[Any, bool]:
        if isinstance(node, ast.Compare):
            left, lok = self.parse_expr(node.left)
            right, rok = self.parse_expr(node.comparators[0])
            op = node.ops[0]
            ok = lok and rok
            if isinstance(op, ast.Gt):
                return left > right, ok
            if isinstance(op, ast.Lt):
                return left < right, ok
            if isinstance(op, ast.GtE):
                return left >= right, ok
            if isinstance(op, ast.LtE):
                return left <= right, ok
            if isinstance(op, ast.Eq):
                return left == right, ok
            if isinstance(op, ast.NotEq):
                return left != right, ok
        elif isinstance(node, ast.BoolOp):
            values = [self.parse_expr(v) for v in node.values]
            exprs = [v[0] for v in values]
            ok = all(v[1] for v in values)
            if isinstance(node.op, ast.And):
                return And(*exprs), ok
            if isinstance(node.op, ast.Or):
                return Or(*exprs), ok
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            expr, ok = self.parse_expr(node.operand)
            return Not(expr), ok
        elif isinstance(node, ast.BinOp):
            left, lok = self.parse_expr(node.left)
            right, rok = self.parse_expr(node.right)
            ok = lok and rok
            left = self._to_int_expr(left)
            right = self._to_int_expr(right)
            if isinstance(node.op, ast.Add):
                return left + right, ok
            if isinstance(node.op, ast.Sub):
                return left - right, ok
            if isinstance(node.op, ast.Mult):
                return left * right, ok
            if isinstance(node.op, ast.FloorDiv):
                return left / right, ok
        elif isinstance(node, ast.Name):
            return self.get_var(node.id), True
        elif isinstance(node, ast.Constant):
            if isinstance(node.value, bool):
                return BoolVal(node.value), True
            if isinstance(node.value, int):
                return IntVal(node.value), True
            self.warnings.append(f"Unsupported constant type: {type(node.value).__name__}")
            return BoolVal(True), False
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            expr, ok = self.parse_expr(node.operand)
            return -self._to_int_expr(expr), ok

        self.warnings.append(f"Unsupported expression: {type(node).__name__}")
        return BoolVal(True), False

    def _collect_assignment_constraints(self, stmt: ast.Assign) -> Tuple[List[Any], bool]:
        value_expr, value_ok = self.parse_expr(stmt.value)
        constraints: List[Any] = []
        ok = value_ok
        for target in stmt.targets:
            if isinstance(target, ast.Name):
                constraints.append(self.get_var(target.id) == self._to_int_expr(value_expr))
            else:
                self.warnings.append(
                    f"Unsupported assignment target at line {stmt.lineno}: {type(target).__name__}"
                )
                ok = False
        return constraints, ok

    def build_recursive(self, stmts: List[ast.stmt], parent_node: CDFGNode) -> CDFGNode:
        current = parent_node
        for stmt in stmts:
            if isinstance(stmt, ast.Assign):
                constraints, ok = self._collect_assignment_constraints(stmt)
                assign_node = CDFGNode(self._new_name("Assign", stmt), constraints)
                self.analyzer.all_nodes.append(assign_node)
                current.add_successor(assign_node)
                current = assign_node
                if not ok:
                    self.warnings.append(f"Fallback assignment handling at line {stmt.lineno}")
                continue

            if isinstance(stmt, ast.AugAssign):
                self.warnings.append(
                    f"Unsupported augmented assignment at line {stmt.lineno}: {type(stmt.op).__name__}"
                )
                passthrough_node = CDFGNode(self._new_name("AugAssign", stmt))
                self.analyzer.all_nodes.append(passthrough_node)
                current.add_successor(passthrough_node)
                current = passthrough_node
                continue

            if isinstance(stmt, ast.If):
                z3_cond, cond_ok = self.parse_expr(stmt.test)
                if not cond_ok:
                    self.warnings.append(
                        f"Fallback on True for conditional expression at line {stmt.lineno}"
                    )

                check_node = CDFGNode(self._new_name("If_Check", stmt), [z3_cond])
                self.analyzer.all_nodes.append(check_node)
                current.add_successor(check_node)

                true_entry = CDFGNode(self._new_name("True_Path", stmt))
                false_entry = CDFGNode(self._new_name("False_Path", stmt))
                join_node = CDFGNode(self._new_name("Join", stmt))
                self.analyzer.all_nodes.extend([true_entry, false_entry, join_node])

                check_node.add_successor(true_entry, z3_cond)
                check_node.add_successor(false_entry, Not(z3_cond))

                true_tail = self.build_recursive(stmt.body, true_entry)
                false_tail = self.build_recursive(stmt.orelse, false_entry) if stmt.orelse else false_entry

                if not true_tail.is_exit:
                    true_tail.add_successor(join_node)
                if not false_tail.is_exit:
                    false_tail.add_successor(join_node)

                current = join_node
                continue

            if isinstance(stmt, ast.Assert):
                assert_expr, ok = self.parse_expr(stmt.test)
                assert_node = CDFGNode(self._new_name("Assert", stmt), [assert_expr])
                self.analyzer.all_nodes.append(assert_node)
                current.add_successor(assert_node)
                current = assert_node
                if not ok:
                    self.warnings.append(f"Fallback assert handling at line {stmt.lineno}")
                continue

            if isinstance(stmt, ast.Return):
                exit_node = CDFGNode(self._new_name("Exit", stmt), is_exit=True)
                self.analyzer.all_nodes.append(exit_node)
                current.add_successor(exit_node)
                current = exit_node
                continue

            if isinstance(stmt, (ast.Pass, ast.Expr)):
                passthrough_node = CDFGNode(self._new_name(type(stmt).__name__, stmt))
                self.analyzer.all_nodes.append(passthrough_node)
                current.add_successor(passthrough_node)
                current = passthrough_node
                continue

            self.warnings.append(
                f"Unsupported statement at line {getattr(stmt, 'lineno', '?')}: {type(stmt).__name__}"
            )

        return current
