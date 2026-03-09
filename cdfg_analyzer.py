import os
from z3 import *
from graphviz import Digraph

# ==========================================
# 1. 核心数据结构：CDFG 节点
# ==========================================
class CDFGNode:
    def __init__(self, name, instructions=None, is_exit=False):
        self.name = name
        self.instructions = instructions if instructions else [] # 存储 Z3 表达式
        self.is_exit = is_exit
        self.successors = [] # 存储格式: (next_node, condition_expr)

    def add_successor(self, node, condition=True):
        self.successors.append((node, condition))

# ==========================================
# 2. 核心算法：带 SMT 约束检查的路径搜索
# ==========================================
class CDFGAnalyzer:
    def __init__(self):
        self.all_feasible_paths = []    # 存储路径节点列表
        self.all_nodes = []             # 存储图中所有节点
        self.generated_models = []      # 用于存储 Web 端展示的测试数据

    def find_paths(self, current_node, target_node, constraints, current_path):
        """
        深度优先搜索 + SMT 约束检查
        """
        # 1. 累加当前节点的指令到路径约束中
        new_constraints = constraints + current_node.instructions
        current_path.append(current_node.name)

        # 2. 终止条件：到达退出节点
        if current_node.is_exit:
            path_str = " -> ".join(current_path)
            self.all_feasible_paths.append(list(current_path))
            
            # --- 核心：利用 Z3 生成模型数据 ---
            s = Solver()
            s.add(new_constraints)
            if s.check() == sat:
                model = s.model()
                # 遍历所有变量并格式化输出
                model_data = ", ".join([f"{d} = {model[d]}" for d in model.decls()])
                
                # 存入列表，供 Flask 渲染展示
                self.generated_models.append({
                    "path": path_str,
                    "inputs": f"[{model_data}]" if model_data else "[No Params Needed]"
                })
            return

        # 3. 递归遍历子节点
        for next_node, branch_cond in current_node.successors:
            # 只有 branch_cond 不为 True（即有实际判断条件）时才加入约束
            combined_constraints = new_constraints
            if branch_cond is not True:
                combined_constraints = combined_constraints + [branch_cond]
            
            s = Solver()
            s.add(combined_constraints)
            
            if s.check() == sat:
                # 逻辑成立才继续向下搜索
                self.find_paths(next_node, target_node, combined_constraints, list(current_path))
            else:
                # 逻辑矛盾则在终端打印拦截信息
                print(f"❌ 逻辑审计：路径 {' -> '.join(current_path)} -> {next_node.name} 已拦截（约束冲突）")
    def _print_model(self, constraints):
        """打印能触发该路径的输入示例"""
        s = Solver()
        s.add(constraints)
        if s.check() == sat:
            print(f"   [测试数据生成] 推荐输入: {s.model()}\n")

    # ==========================================
    # 3. 可视化模块
    # ==========================================
    def visualize(self, filename='cdfg_result'):
            dot = Digraph(comment='CDFG Analyzer Output')
            dot.attr(rankdir='TB', size='10,8')
            dot.attr('node', shape='box', style='filled', fontname='Arial')
    
            # 绘制节点
            for node in self.all_nodes:
                # --- 修复核心：转义 HTML 特殊字符 ---
                instr_str = "<br/>".join([
                    str(i).replace('>', '&gt;').replace('<', '&lt;') 
                    for i in node.instructions
                ])
                
                # 使用 HTML 格式的 label
                label = f'<<table border="0" cellborder="0"><tr><td><b>{node.name}</b></td></tr>'
                if instr_str:
                    label += f'<tr><td><i>{instr_str}</i></td></tr>'
                label += '</table>>'
                
                color = 'lavender'
                for path in self.all_feasible_paths:
                    if node.name in path:
                        color = 'gold'
                        break
                dot.node(node.name, label, fillcolor=color)
    
            # 绘制边
            for node in self.all_nodes:
                for next_node, cond in node.successors:
                    # --- 修复核心：边上的标签也需要转义 ---
                    edge_label = str(cond).replace('>', '&gt;').replace('<', '&lt;') if cond is not True else ""
                    
                    edge_color = 'black'
                    penwidth = '1.0'
                    for path in self.all_feasible_paths:
                        if node.name in path and next_node.name in path:
                            idx = path.index(node.name)
                            if idx < len(path)-1 and path[idx+1] == next_node.name:
                                edge_color = 'red'
                                penwidth = '2.5'
                    
                    dot.edge(node.name, next_node.name, label=edge_label, color=edge_color, penwidth=penwidth)
    
            # 注意：在服务器环境建议 view=False，避免弹窗报错
            dot.render(filename, format='png', view=False)
            print(f"📊 图形已成功生成至: {filename}.png")
# ==========================================
# 4. 模拟运行：测试一个带矛盾逻辑的代码段
# ==========================================
if __name__ == "__main__":
    # 定义符号变量
    x = Int('x')
    y = Int('y')

    # 构造节点
    # 模拟场景：
    # entry: a = x + 5
    # branch: if a > 10 -> check_y
    #         else -> fail
    # check_y: if x < 2 -> win (此路径逻辑矛盾：x+5 > 10 则 x > 5，与 x < 2 冲突)
    
    entry = CDFGNode("Entry", [x > 0]) # 假设输入 x 必须大于 0
    check_y = CDFGNode("Check_Y", [y == x * 2])
    win = CDFGNode("Win_Path", [y > 20], is_exit=True)
    fail = CDFGNode("Fail_Path", [], is_exit=True)

    # 建立拓扑关系
    entry.add_successor(check_y, x > 5)   # 条件1: x > 5
    entry.add_successor(fail, x <= 5)
    
    check_y.add_successor(win, x < 2)    # 条件2: x < 2 (这里会与条件1冲突)
    check_y.add_successor(fail, x >= 2)

    # 执行分析
    analyzer = CDFGAnalyzer()
    analyzer.all_nodes = [entry, check_y, win, fail]
    
    print("🚀 开始 CDFG 路径自动化分析...\n")
    analyzer.find_paths(entry, None, [], [])
    
    # 渲染可视化结果
    analyzer.visualize('my_project_cdfg')