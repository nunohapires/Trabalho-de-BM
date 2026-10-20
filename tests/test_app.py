"""Exercita formulário, erros, relatórios e navegação no Streamlit real."""

from io import BytesIO
from pathlib import Path
import re
import unittest
from zipfile import ZipFile

from streamlit.testing.v1 import AppTest

from bm import ProjectInputs, calculate, decode_pump_tag
from reports import dynamometer_figure, export_excel, export_pdf


ROOT = Path(__file__).resolve().parents[1]


class AppTests(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()

    def assert_no_exception(self):
        self.assertEqual(len(self.app.exception), 0, [error.message for error in self.app.exception])

    def test_default_and_invalid_tag_recovery(self):
        self.assert_no_exception()
        self.assertGreater(len(self.app.metric), 0)
        self.app.text_input[0].set_value("invalid")
        self.app.button[0].click().run()
        self.assert_no_exception()
        self.assertIn("TAG inválida", self.app.error[0].value)
        self.assertEqual(len(self.app.metric), 0)
        self.app.text_input[0].set_value("C-640D-305-168")
        self.app.button[0].click().run()
        self.assert_no_exception()
        self.assertGreater(len(self.app.metric), 0)

    def test_invalid_geometry_and_capacity_warning(self):
        self.app.number_input(key="tubing_id").set_value(4.0)
        self.app.button[0].click().run()
        self.assert_no_exception()
        self.assertIn("diâmetro interno", self.app.error[0].value)
        self.app.number_input(key="tubing_id").set_value(2.992)
        self.app.text_input[0].set_value("C-1D-1-1")
        self.app.button[0].click().run()
        self.assert_no_exception()
        self.assertIn("ultrapassam", self.app.error[0].value)

    def test_downloads_persist_and_expire_after_input_change(self):
        self.app.button[1].click().run()
        self.assert_no_exception()
        pdf, excel = self.app.session_state["report_files"]
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertTrue(excel.startswith(b"PK"))
        self.app.run()
        self.assertEqual(self.app.session_state["report_files"][0], pdf)
        self.app.number_input(key="wellhead_pressure").set_value(200.0)
        self.app.button[0].click().run()
        self.assert_no_exception()
        self.assertNotIn("report_files", self.app.session_state)

    def test_method_navigation_and_legacy_entrypoint(self):
        self.app.number_input(key="wellhead_pressure").set_value(250.0)
        self.app.text_input[0].set_value("C-640D-305-168")
        self.app.button[0].click().run()
        self.app.sidebar.radio[0].set_value("Método e referências").run()
        self.assert_no_exception()
        self.assertEqual(self.app.title[0].value, "Método e referências")
        self.app.sidebar.radio[0].set_value("Dimensionamento").run()
        self.assert_no_exception()
        self.assertEqual(self.app.number_input(key="wellhead_pressure").value, 250)
        self.assertEqual(self.app.text_input[0].value, "C-640D-305-168")
        legacy = AppTest.from_file(str(ROOT / "1_⚙BM.py"), default_timeout=30).run()
        self.assertEqual(len(legacy.exception), 0)


class ExportTests(unittest.TestCase):
    def test_reports_contain_inputs_results_units_and_chart(self):
        inputs = ProjectInputs()
        results = calculate(inputs)
        tag = decode_pump_tag("C-456D-256-120")
        pdf = export_pdf(inputs, tag, results)
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertEqual(len(re.findall(rb"/Type /Page\b", pdf)), 4)
        with ZipFile(BytesIO(export_excel(inputs, tag, results))) as workbook:
            self.assertIn("xl/media/image1.png", workbook.namelist())
            text = workbook.read("xl/sharedStrings.xml").decode()
            for value in ("C-456D-256-120", "STB/d", "nível dinâmico", "motor"):
                self.assertIn(value, text)
        figure = dynamometer_figure(results)
        self.assertAlmostEqual(max(figure.axes[0].lines[0].get_xdata()), results["surface_stroke"])


if __name__ == "__main__":
    unittest.main()
