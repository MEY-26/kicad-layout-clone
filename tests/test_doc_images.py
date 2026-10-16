"""Check the actual documentation assets, not only generated validator samples."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from check_doc_images import check_readmes


class DocumentationImageTests(unittest.TestCase):
    def test_both_readmes_reference_valid_opaque_local_screenshots(self):
        reports = check_readmes(ROOT)
        self.assertTrue(reports)
        for report in reports.values():
            self.assertEqual(report['nonopaque_pixels'], 0)


if __name__ == '__main__':
    unittest.main()
