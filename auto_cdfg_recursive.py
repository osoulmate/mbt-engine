import ast
import inspect
from z3 import *
from cdfg_analyzer import CDFGNode, CDFGAnalyzer

class RecursiveAutoCDFG:
    def __init__(self):
        self.analyzer = CDFGAnalyzer()
        self.vars = {}

    def get_var(self, name):
        if name not in self.vars:
            self.vars[name] = Int(name)
        return self.vars[name]

    def parse_expr(self, node):
        """递归解析 AST 表达式为 Z3 表达式"""
        if isinstance(node, ast.Compare):
            left = self.parse_expr(node.left)
            ops = node.ops[0]
            right = self.parse_expr(node.comparators[0])
            if isinstance(ops, ast.Gt): return left > right
            if isinstance(ops, ast.Lt): return left < right
            if isinstance(ops, ast.GtE): return left >= right
            if isinstance(ops, ast.LtE): return left <= right
            if isinstance(ops, ast.Eq): return left == right
        elif isinstance(node, ast.Name):
            return self.get_var(node.id)
        elif isinstance(node, ast.Constant):
            return node.value
        return True

    def build_recursive(self, stmts, parent_node):
        """核心递归函数：解析语句列表并挂载到父节点"""
        current = parent_node
        
        for i, stmt in enumerate(stmts):
            if isinstance(stmt, ast.If):
                # 1. 提取判断条件
                z3_cond = self.parse_expr(stmt.test)
                
                # 2. 创建分支判断节点
                check_node = CDFGNode(f"If_Check_{id(stmt)%1000}", [z3_cond])
                self.analyzer.all_nodes.append(check_node)
                current.add_successor(check_node)
                
                # 3. 递归解析 True 分支
                true_entry = CDFGNode(f"True_Path_{id(stmt)%1000}")
                self.analyzer.all_nodes.append(true_entry)
                check_node.add_successor(true_entry, z3_cond)
                self.build_recursive(stmt.body, true_entry)
                
                # 4. 递归解析 False 分支 (Else)
                false_entry = CDFGNode(f"False_Path_{id(stmt)%1000}")
                self.analyzer.all_nodes.append(false_entry)
                check_node.add_successor(false_entry, Not(z3_cond))
                if stmt.orelse:
                    self.build_recursive(stmt.orelse, false_entry)
                
                # 嵌套后的逻辑通常会汇合，此处简化处理为分支末端
                return 

            elif isinstance(stmt, ast.Return):
                # 标记退出节点
                exit_node = CDFGNode(f"Exit_{id(stmt)%1000}", is_exit=True)
                self.analyzer.all_nodes.append(exit_node)
                current.add_successor(exit_node)
def nested_logic_demo(x):
    if x > 5:
        if x < 2:  # 这是一个深层嵌套的矛盾点
            return "Impossible"
        else:
            return "Greater than 5"
    return "Less or equal to 5"

if __name__ == "__main__":
    app = RecursiveAutoCDFG()
    source = inspect.getsource(nested_logic_demo)
    tree = ast.parse(source)
    
    # 从函数体开始递归构建
    entry = CDFGNode("Start")
    app.analyzer.all_nodes.append(entry)
    app.build_recursive(tree.body[0].body, entry)
    
    print("🚀 正在分析复杂嵌套逻辑...")
    app.analyzer.find_paths(entry, None, [], [])
    app.analyzer.visualize('nested_cdfg_result')