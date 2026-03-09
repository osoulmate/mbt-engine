import os
import ast
import inspect
import importlib.util
from flask import Flask, render_template, request, redirect, url_for
from auto_cdfg_recursive import RecursiveAutoCDFG  # 导入你之前的递归解析类
from cdfg_analyzer import CDFGNode

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['STATIC_FOLDER'] = 'static/images'

# 确保目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['STATIC_FOLDER'], exist_ok=True)

# 在 app.py 中更新 index 路由
@app.route('/', methods=['GET', 'POST'])
def index():
    image_url = None
    test_cases = []  # 新增：用于存储生成的测试用例

    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.py'):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)

            try:
                # 初始化解析器并构建图
                app_logic = RecursiveAutoCDFG()
                tree = ast.parse(open(file_path).read())
                entry = CDFGNode("Start")
                app_logic.analyzer.all_nodes.append(entry)
                app_logic.build_recursive(tree.body[0].body, entry)
                
                # 执行分析并获取测试数据
                app_logic.analyzer.find_paths(entry, None, [], [])
                
                # 从 analyzer 中提取记录的测试用例（需要微调 analyzer 类存储数据）
                test_cases = app_logic.analyzer.generated_models 
                
                # 生成图片
                output_name = 'analysis_result'
                app_logic.analyzer.visualize(os.path.join(app.config['STATIC_FOLDER'], output_name))
                image_url = url_for('static', filename=f'images/{output_name}.png')
            except Exception as e:
                print(f"Error: {e}")
    print(f"Generated test cases: {test_cases}")  # 调试输出生成的测试用例
    return render_template('index.html', image_url=image_url, test_cases=test_cases)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)