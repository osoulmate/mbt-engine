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

@app.route('/', methods=['GET', 'POST'])
def index():
    image_url = None
    analysis_log = []

    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.py'):
            # 1. 保存上传文件
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)

            # 2. 动态加载并解析函数
            try:
                with open(file_path, 'r') as f:
                    code = f.read()
                
                # 初始化解析器
                app_logic = RecursiveAutoCDFG()
                tree = ast.parse(code)
                
                # 假设解析第一个函数
                entry = CDFGNode("Start")
                app_logic.analyzer.all_nodes.append(entry)
                app_logic.build_recursive(tree.body[0].body, entry)
                
                # 3. SMT 分析
                app_logic.analyzer.find_paths(entry, None, [], [])
                
                # 4. 生成图片到 static 目录
                output_name = 'current_analysis'
                full_output_path = os.path.join(app.config['STATIC_FOLDER'], output_name)
                app_logic.analyzer.visualize(full_output_path)
                
                image_url = url_for('static', filename=f'images/{output_name}.png')
            except Exception as e:
                analysis_log.append(f"Error: {str(e)}")

    return render_template('index.html', image_url=image_url)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)