import argparse
import importlib.util
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "wandeling-en-fietsen-guide" / "scripts" / "nl_route.py"
spec = importlib.util.spec_from_file_location("nl_route", SCRIPT)
nl_route = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(nl_route)


class DutchRouteHelperTests(unittest.TestCase):
    def test_parse_point_accepts_dutch_coordinate(self):
        self.assertEqual(nl_route.parse_point("52.370216,4.895168"), (52.370216, 4.895168))

    def test_parse_point_rejects_outside_netherlands(self):
        with self.assertRaises(argparse.ArgumentTypeError):
            nl_route.parse_point("48.8566,2.3522")

    def test_write_gpx_is_well_formed_and_tracks_geometry(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "route.gpx"
            nl_route.write_gpx(
                output,
                "A & B",
                "walk",
                [(52.370216, 4.895168), (52.372, 4.9)],
                [[4.895168, 52.370216], [4.9, 52.372]],
            )
            root = ET.parse(output).getroot()
            self.assertTrue(root.tag.endswith("gpx"))
            self.assertEqual(len(list(root.iter("{http://www.topografix.com/GPX/1/1}trkpt"))), 2)
            self.assertIn("A &amp; B", output.read_text())

    def test_haversine_is_zero_for_same_coordinate(self):
        self.assertEqual(nl_route.haversine_km(52.0, 5.0, 52.0, 5.0), 0.0)


if __name__ == "__main__":
    unittest.main()
