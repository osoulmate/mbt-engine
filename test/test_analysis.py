import io
import tempfile
import unittest
from pathlib import Path

from analysis_service import AnalysisService
from app import app


class AnalysisServiceTest(unittest.TestCase):
    def test_generate_models_for_simple_function(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "sample.py"
            src.write_text(
                "def foo(x):\n"
                "    if x > 10:\n"
                "        return 1\n"
                "    return 0\n",
                encoding="utf-8",
            )
            service = AnalysisService(Path(td))
            result = service.analyze_file(src, output_name="test_out")
            self.assertTrue(result["test_cases"])
            self.assertIn("images/test_out.png", result["output_filename"])

    def test_analyze_multiple_functions_and_assignments(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "multi.py"
            src.write_text(
                "def f1(x):\n"
                "    y = x + 1\n"
                "    assert y > 0\n"
                "    return y\n\n"
                "def f2(z):\n"
                "    if z < 0:\n"
                "        return -1\n"
                "    return 1\n",
                encoding="utf-8",
            )
            service = AnalysisService(Path(td))
            result = service.analyze_file(src, output_name="multi_out")
            self.assertTrue(result["test_cases"])
            functions = {item.get("function") for item in result["test_cases"]}
            self.assertIn("f1", functions)
            self.assertIn("f2", functions)
            self.assertEqual(result["output_filename"], "images/multi_out.png")

    def test_warn_on_augmented_assignment(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "aug.py"
            src.write_text(
                "def f(x):\n"
                "    x += 1\n"
                "    return x\n",
                encoding="utf-8",
            )
            service = AnalysisService(Path(td))
            result = service.analyze_file(src, output_name="aug_out")
            warning_text = "\n".join(result["warnings"])
            self.assertIn("Unsupported augmented assignment", warning_text)


class FlaskAppTest(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["AUTH_USERNAME"] = "admin"
        self.client = app.test_client()

    def login(self):
        return self.client.post(
            "/login",
            data={"username": "admin", "password": "Admin@123"},
            follow_redirects=True,
        )

    def test_redirect_to_login_when_unauthenticated(self):
        resp = self.client.get("/", follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers["Location"])

    def test_reject_non_python_upload(self):
        self.login()
        resp = self.client.post(
            "/",
            data={"file": (io.BytesIO(b"hello"), "not_python.txt")},
            content_type="multipart/form-data",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("仅支持上传 .py 文件".encode("utf-8"), resp.data)


if __name__ == "__main__":
    unittest.main()
