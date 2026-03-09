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


class FlaskAppTest(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_reject_non_python_upload(self):
        resp = self.client.post(
            "/",
            data={"file": (io.BytesIO(b"hello"), "not_python.txt")},
            content_type="multipart/form-data",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("仅支持上传 .py 文件".encode("utf-8"), resp.data)


if __name__ == "__main__":
    unittest.main()
