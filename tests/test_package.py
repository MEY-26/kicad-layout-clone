import json
from pathlib import Path
import unittest

import jsonschema


class PackageTests(unittest.TestCase):
    def test_manifest_matches_official_kicad_schema_and_files_exist(self):
        root=Path(__file__).resolve().parents[1]/'plugins'
        manifest=json.loads((root/'plugin.json').read_text(encoding='utf-8'))
        schema=json.loads(Path(__file__).with_name('plugin-schema.json').read_text())
        jsonschema.validate(manifest,schema)
        for action in manifest['actions']:
            for name in [action['entrypoint']]+action['icons-light']+action['icons-dark']:
                self.assertTrue((root/name).is_file(),name)
        self.assertEqual((root/'requirements.txt').read_text().splitlines(),
                         ['kicad-python==0.7.1','wxPython==4.2.2'])


if __name__=='__main__':unittest.main()
