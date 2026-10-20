"""Verifica a comparação com o projeto e os dados enviados à ilustração."""

from dataclasses import replace
import json
import re
import unittest

from bm import ProjectInputs, calculate
from visuals import DATA_SOURCES, system_html


class VisualModelTests(unittest.TestCase):
    def test_diagram_receives_current_data_and_explains_all_inputs(self):
        project = replace(ProjectInputs(), speed=15)
        html = system_html(project, calculate(project))
        payload = json.loads(re.search(r'<script type="application/json" id="bm-data">(.*?)</script>', html).group(1))
        self.assertEqual(payload["inputs"]["speed"], 15)
        self.assertEqual(payload["results"]["operating_speed"], 15)
        self.assertNotIn("__BM_DATA__", html)
        self.assertNotIn("__BM_MOTION__", html)
        source_keys = [key for _, _, keys in DATA_SOURCES for key in keys]
        self.assertCountEqual(source_keys, project.__dataclass_fields__)


if __name__ == "__main__":
    unittest.main()
