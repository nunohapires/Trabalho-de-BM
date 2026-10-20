"""Verifica fechamento, escala e dependências físicas do ciclo aproximado."""

from dataclasses import replace
from math import isfinite
import unittest

from bm import ProjectInputs, approximate_dynamometer, calculate


class DynamometerTests(unittest.TestCase):
    def test_closed_cycle_and_reversal_loads(self):
        p = ProjectInputs()
        r = calculate(p)
        points = approximate_dynamometer(p, r)
        self.assertEqual(len(points), 721)
        self.assertEqual(points[0], points[-1])
        self.assertEqual(min(x for x, _ in points), 0)
        self.assertAlmostEqual(max(x for x, _ in points), r['surface_stroke'])
        self.assertTrue(all(isfinite(x) and isfinite(y) for x, y in points))
        self.assertAlmostEqual(points[0][1], r['buoyant_weight'] + r['dynamic_max'])
        self.assertAlmostEqual(points[360][1], r['buoyant_weight'] + r['fluid_load'] - r['dynamic_min'])
        self.assertLess(max(y for _, y in points), r['peak_load'])
        self.assertGreater(min(y for _, y in points), r['min_load'])

    def test_elasticity_and_speed_change_cycle_without_noise(self):
        p = ProjectInputs()
        baseline = approximate_dynamometer(p, calculate(p))
        for changed in [replace(p, speed=15), replace(p, elastic_modulus=60000000),
                        replace(p, anchored_tubing=False), replace(p, depth=4500)]:
            with self.subTest(changed=changed):
                points = approximate_dynamometer(changed, calculate(changed))
                self.assertNotEqual(points, baseline)
                self.assertEqual(points, approximate_dynamometer(changed, calculate(changed)))
        auto = replace(p, use_limit_speed=True)
        manual = replace(p, speed=calculate(auto)['operating_speed'])
        self.assertEqual(approximate_dynamometer(auto, calculate(auto)),
                         approximate_dynamometer(manual, calculate(manual)))

    def test_rejects_uncompleted_load_transfer_but_exports_remain_available(self):
        from reports import export_excel, export_pdf
        from bm import decode_pump_tag

        p = ProjectInputs(elastic_modulus=5000000, speed=20)
        r = calculate(p)
        with self.assertRaisesRegex(ValueError, 'fora do domínio'):
            approximate_dynamometer(p, r)
        tag = decode_pump_tag('C-456D-256-120')
        self.assertTrue(export_pdf(p, tag, r).startswith(b'%PDF'))
        self.assertTrue(export_excel(p, tag, r).startswith(b'PK'))


if __name__ == '__main__':
    unittest.main()
