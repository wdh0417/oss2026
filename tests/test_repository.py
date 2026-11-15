import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RepositorySmokeTests(unittest.TestCase):
    def test_dashboard_metrics_are_valid_json(self):
        metrics_file = ROOT / "dashboard" / "metrics.json"
        with metrics_file.open(encoding="utf-8") as file:
            metrics = json.load(file)
        self.assertIsInstance(metrics, dict)

    def test_dashboard_entrypoint_exists(self):
        self.assertTrue((ROOT / "dashboard" / "index.html").is_file())

    def test_snapshot_generator_exists(self):
        self.assertTrue(
            (ROOT / "tools" / "generate_dashboard_snapshot.py").is_file()
        )


if __name__ == "__main__":
    unittest.main()
