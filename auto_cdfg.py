import ast
import inspect
from z3 import *
from cdfg_analyzer import CDFGNode, CDFGAnalyzer  # 确保 cdfg_analyzer.py 在同目录下

class AutoCDFG:
    def __init__(self):
        self.analyzer = CDFGAnalyzer()
        self.vars = {}

    def get_var(self, name):
        if name not in self.vars:
            self.vars[name] = Int(name)
        return self.vars[name]

    def parse_to_z3(self, node):
        """将 AST 表达式转换为 Z3 表达式"""
        if isinstance(node, ast.Compare):
            left = self.parse_to_z3(node.left)
            ops = node.ops[0]
            right = self.parse_to_z3(node.comparators[0])
            if isinstance(ops, ast.Gt): return left > right
            if isinstance(ops, ast.Lt): return left < right
            if isinstance(ops, ast.GtE): return left >= right
            if isinstance(ops, ast.LtE): return left <= right
        elif isinstance(node, ast.Name):
            return self.get_var(node.id)
        elif isinstance(node, ast.Constant):
            return node.value
        return True

    def build_from_func(self, func):
        source = inspect.getsource(func)
        tree = ast.parse(source)
        func_def = tree.body[0]

        # 初始节点
        entry = CDFGNode("Entry")
        self.analyzer.all_nodes.append(entry)
        
        # 模拟解析简单的 If-Else 结构
        current = entry
        for stmt in func_def.body:
            if isinstance(stmt, ast.If):
                # 提取判断条件
                z3_cond = self.parse_to_z3(stmt.test)
                
                # 创建分支节点
                if_node = CDFGNode(f"If_Check", [z3_cond])
                true_branch = CDFGNode("True_Path", is_exit=True)
                false_branch = CDFGNode("False_Path", is_exit=True)
                
                # 建立连接
                current.add_successor(if_node)
                if_node.add_successor(true_branch, z3_cond)
                if_node.add_successor(false_branch, Not(z3_cond))
                
                self.analyzer.all_nodes.extend([if_node, true_branch, false_branch])
                
        return entry

# ==========================================
# 2. 准备一个“真实”的业务逻辑函数进行测试
# ==========================================
def complex_business_logic(x):
    # 假设这是某个 RPA 流程中的判断逻辑
    if x > 10:
        if x < 5:
            return "Impossible"
        return "Normal"

if __name__ == "__main__":
    app = AutoCDFG()
    
    # 1. 自动解析函数并构建图
    entry_node = app.build_from_func(complex_business_logic)
    
    # 2. 执行 SMT 路径分析
    print("🚀 正在自动分析 Python 函数逻辑...")
    app.analyzer.find_paths(entry_node, None, [], [])
    
    # 3. 生成可视化图片
    app.analyzer.visualize('auto_parsed_cdfg')