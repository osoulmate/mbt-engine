import os
import uuid
from pathlib import Path

from flask import Flask, render_template, request, url_for
from werkzeug.utils import secure_filename

from analysis_service import AnalysisError, AnalysisService

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["STATIC_FOLDER"] = "static/images"
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024
app.config["ALLOWED_EXTENSIONS"] = {"py"}
app.config["DEBUG"] = os.getenv("FLASK_DEBUG", "0") == "1"

upload_dir = Path(app.config["UPLOAD_FOLDER"])
static_dir = Path(app.config["STATIC_FOLDER"])
upload_dir.mkdir(parents=True, exist_ok=True)
static_dir.mkdir(parents=True, exist_ok=True)

analysis_service = AnalysisService(static_dir)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]


@app.route("/", methods=["GET", "POST"])
def index():
    image_url = None
    test_cases = []
    warnings = []
    blocked_paths = []
    error_message = None

    if request.method == "POST":
        file = request.files.get("file")

        if not file or not file.filename:
            error_message = "请选择一个 .py 文件后再提交。"
        elif not allowed_file(file.filename):
            error_message = "仅支持上传 .py 文件。"
        else:
            safe_name = secure_filename(file.filename)
            suffix = Path(safe_name).suffix or ".py"
            random_name = f"{Path(safe_name).stem}_{uuid.uuid4().hex[:8]}{suffix}"
            file_path = upload_dir / random_name
            file.save(file_path)

            try:
                result = analysis_service.analyze_file(file_path)
                test_cases = result["test_cases"]
                warnings = result["warnings"]
                blocked_paths = result["blocked_paths"]
                image_url = url_for("static", filename=result["output_filename"])
            except (UnicodeDecodeError, SyntaxError):
                error_message = "上传文件不是合法的 UTF-8 Python 源码，请检查后重试。"
            except AnalysisError as exc:
                error_message = str(exc)
            except Exception:
                error_message = "分析过程中发生未知错误，请稍后重试。"

    return render_template(
        "index.html",
        image_url=image_url,
        test_cases=test_cases,
        warnings=warnings,
        blocked_paths=blocked_paths,
        error_message=error_message,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=app.config["DEBUG"])
