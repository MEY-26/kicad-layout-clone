import json
import struct
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

    def test_toolbar_icons_have_small_base_and_high_dpi_variant(self):
        root=Path(__file__).resolve().parents[1]/'plugins'
        manifest=json.loads((root/'plugin.json').read_text(encoding='utf-8'))
        for action in manifest['actions']:
            for theme in ('icons-light', 'icons-dark'):
                dimensions=[struct.unpack('>II',(root/name).read_bytes()[16:24])
                            for name in action[theme]]
                self.assertEqual(dimensions,[(24,24),(48,48)])
                self.assertNotIn('icon.png',action[theme])


if __name__=='__main__':unittest.main()
