"""Regressões de unidades, validação e dimensionamento. Execute unittest discover."""

from dataclasses import replace
from math import pi
import unittest

from bm import ProjectInputs, calculate, capacity_checks, decode_pump_tag, operating_warnings


class DimensioningTests(unittest.TestCase):
    def setUp(self):
        self.inputs = ProjectInputs()
        self.results = calculate(self.inputs)

    def test_tag_ratings_and_invalid_formats(self):
        tag = decode_pump_tag(" c-456d-256-120 ")
        self.assertEqual((tag.code, tag.torque_capacity, tag.load_capacity, tag.stroke_capacity),
                         ("C-456D-256-120", 456000, 25600, 120))
        for text in ("", "invalid", "C-456D-256", "C-0D-256-120", "C-456D-256-120-extra", "A-456D-256-120", "C-456X-256-120"):
            with self.subTest(tag=text), self.assertRaises(ValueError):
                decode_pump_tag(text)

    def test_default_numeric_reference(self):
        # Referência calculada por balanço de forças, Hooke e volume/ciclo.
        expected = {"rod_area": 0.4417864669, "fluid_load": 7501.2456987,
                    "peak_load": 14231.1684178, "min_load": 4628.3513767,
                    "plunger_stroke": 63.3917387, "flow_rate": 385.5468654,
                    "net_lift": 4261.7559119, "motor_power": 21.8331988}
        for key, value in expected.items():
            with self.subTest(result=key):
                self.assertAlmostEqual(self.results[key], value, places=5)

    def test_physical_volume_conversion_uses_piston_area_once(self):
        # in² × in/ciclo × ciclos/min × min/d ÷ in³/bbl.
        r = self.results
        volume_in_cubic_inches = pi * 2.5**2 / 4 * r["plunger_stroke"] * 12 * 1440
        self.assertAlmostEqual(r["displacement"] * 9702, volume_in_cubic_inches)
        doubled_efficiency = calculate(replace(self.inputs, efficiency=0.4))
        self.assertAlmostEqual(doubled_efficiency["flow_rate"], r["flow_rate"] / 2)

    def test_tubing_metal_area_and_anchoring(self):
        free = calculate(replace(self.inputs, anchored_tubing=False))
        self.assertAlmostEqual(free["tubing_area"], pi * (3.5**2 - 2.992**2) / 4)
        self.assertGreater(free["tubing_stretch"], 0)
        self.assertAlmostEqual(self.results["plunger_stroke"] - free["plunger_stroke"], free["tubing_stretch"])

    def test_stress_and_motor_factors_are_independent(self):
        changed = calculate(replace(self.inputs, motor_factor=2.0))
        self.assertEqual(changed["allowable_stress"], self.results["allowable_stress"])
        changed = calculate(replace(self.inputs, service_factor=0.45))
        self.assertAlmostEqual(changed["allowable_stress"], self.results["allowable_stress"] / 2)
        self.assertEqual(changed["motor_power"], self.results["motor_power"])

    def test_capacity_comparison_accepts_larger_units(self):
        self.assertTrue(all(row["Atende"] for row in capacity_checks(decode_pump_tag("C-640D-305-168"), self.results)))
        self.assertFalse(any(row["Atende"] for row in capacity_checks(decode_pump_tag("C-1D-1-1"), self.results)))
        # Mesmo com Sp menor, a capacidade de curso deve atender a S.
        stroke = capacity_checks(decode_pump_tag("C-456D-256-70"), self.results)[2]
        self.assertLess(self.results["plunger_stroke"], 70)
        self.assertFalse(stroke["Atende"])

    def test_speed_selection_and_compression_warnings(self):
        automatic = calculate(replace(self.inputs, use_limit_speed=True))
        self.assertEqual(automatic["operating_speed"], automatic["speed_limit"])
        fast = replace(self.inputs, speed=50)
        results = calculate(fast)
        messages = operating_warnings(fast, results)
        self.assertTrue(any("velocidade" in message for message in messages))
        self.assertTrue(any("compressão" in message for message in messages))

    def test_invalid_input_is_rejected_before_computation(self):
        for kwargs in (
            {"rod_diameter": 0}, {"depth": float("nan")}, {"speed": float("inf")},
            {"efficiency": 1.1}, {"service_factor": 1.5}, {"motor_factor": 0.5},
            {"tubing_id": 3.5}, {"crank_radius": 114}, {"fluid_level": 5000},
            {"oil_api": -131.5}, {"wellhead_pressure": -1}, {"steel_weight": True},
            {"acceleration_limit": 1.1}, {"depth": 30000, "speed": 0.1}, {"steel_weight": 10},
        ):
            with self.subTest(inputs=kwargs), self.assertRaises(ValueError):
                calculate(replace(self.inputs, **kwargs))


if __name__ == "__main__":
    unittest.main()
