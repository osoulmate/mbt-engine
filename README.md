# 项目背景

![Image](https://www.cs.toronto.edu/~david/course-notes/csc110-111/17-graphs/images/one-iteration-simple.svg)

## Control Data Flow Graph

控制数据流图（Control Data Flow Graph，简称 CDFG）是一种统一的图形化程序表示形式，同时刻画程序的控制流（语句执行顺序）与数据流（变量定义与使用之间的依赖关系）。它被广泛应用于程序静态分析、编译优化、自动修复以及硬件综合等领域，为理解和改进程序结构提供系统化依据。([Emergent Mind][1])

### 关键特征

* **图结构**：有向图 ( G = (V, E_C, E_D) )，其中节点 (V) 表示程序元素。
* **控制边 (E_C)**：表示允许的执行顺序（如顺序、分支、循环、调用）。
* **数据边 (E_D)**：表示“定义–使用”关系，即变量值的产生与消费路径。
* **统一性**：兼容纯控制流图（CFG）与数据流图（DFG）的特性。

### 结构与构造

在构建 CDFG 时，编译器或分析器会先识别程序的基本块，再分析控制转移（顺序、分支、调用等）形成控制流边，并提取变量定义与使用的对应关系形成数据流边。
生成的图通常以不同样式的边区分控制与数据依赖：例如细箭头表示控制流，粗曲线表示数据流。该图可由源代码、中间表示或硬件描述自动提取。

### 主要应用

CDFG 在软件与硬件领域均具有核心作用：

* **静态分析与验证**：支持路径覆盖、故障定位、正确性验证等精细分析。
* **优化与并行化**：显式表示控制与数据依赖，利于循环展开、指令调度与代码迁移。
* **自动错误分类与修复**：通过比较边的差异识别控制流或数据流错误。
* **机器学习建模**：为图神经网络与 Transformer 模型提供结构化输入，用于代码检索、算法分类和硬件质量预测。
* **硬件综合与质量估计**：在寄存器传输级（RTL）设计中，CDFG 支持面积、延迟等指标的早期估算。

### 挑战与发展

合并控制和数据信息会导致图规模庞大、异质性强，从而增加计算复杂度。研究者通过类型化边、分层子图、结构采样等方法提高可扩展性。近年发展出的流类型感知图学习（flow-type-aware learning）和语义对齐算法显著提升了自动分析与修复的准确率。

总体而言，控制数据流图是连接程序语义、编译优化与机器学习分析的关键桥梁，为现代软件工程与电子设计自动化提供统一的语义基础。

[1]: https://www.emergentmind.com/topics/control-data-flow-graph-cdfg?utm_source=chatgpt.com "Control Data Flow Graphs (CDFG)"

# Q&A

Q1：demo.py生成的代码审计图片中显示的数字是什么意思？

A1: 为了支持对任意深度嵌套逻辑的自动化解析，系统在构建 CDFG 时引入了基于 AST 节点内存指纹的动态编号机制。这些数字确保了在复杂的递归处理过程中，每一个条件分支节点和路径节点都拥有全局唯一的标识符，从而避免了路径搜索时的命名冲突，并为后续的 SMT 约束回溯提供了精确的索引。



## 运行方式

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

默认仅在 `FLASK_DEBUG=1` 时开启 Debug 模式。


## 认证与安全配置

系统已启用基础用户名密码认证：

- 默认用户名：`admin`
- 默认密码：`Admin@123`

生产环境请通过环境变量覆盖：

```bash
export SECRET_KEY="your-random-secret"
export AUTH_USERNAME="your-admin"
export AUTH_PASSWORD="your-strong-password"
python app.py
```
# 切换分支
git switch -c codex/optimize-username/password-authentication-and-ui --track origin/codex/optimize-username/password-authentication-and-ui