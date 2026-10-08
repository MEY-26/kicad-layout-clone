import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'plugins'))
from i18n import tr, set_language, read_language, MESSAGES
from core import LayoutError


class LanguageTests(unittest.TestCase):
    def tearDown(self):
        set_language('tr')

    def test_default_english_and_invalid_preferences(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'preferences.json'
            self.assertEqual(read_language(path),'en')
            for value in ('not-json',json.dumps({'language':'de'}),'null','[]'):
                path.write_text(value)
                self.assertEqual(read_language(path),'en')

    def test_language_is_persisted_and_only_two_languages_allowed(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'nested'/'preferences.json'
            set_language('tr',persist=True,path=path)
            self.assertEqual(read_language(path),'tr')
            set_language('en',persist=True,path=path)
            self.assertEqual(read_language(path),'en')
            with self.assertRaises(ValueError):set_language('de')

    def test_formatted_errors_and_nested_details_translate(self):
        set_language('en')
        message=LayoutError('Grup boyutları farklı: kaynak 4, hedef 28 komponent.')
        self.assertEqual(str(message),'Group sizes differ: source 4, target 28 footprints.')
        self.assertEqual(tr('KiCad yanıtı alınamadı (taşıma işlemini başlatma, 20.0 sn). Komponent güncelleme çağrısı gönderilmedi.'),
            'No KiCad reply (starting move transaction, 20.0 s). No footprint update request was sent.')
        set_language('tr')
        self.assertEqual(str(message),'Grup boyutları farklı: kaynak 4, hedef 28 komponent.')

    def test_diagnostic_reference_suffixes_and_unknown_text_preserved(self):
        set_language('en')
        self.assertEqual(tr('Kilitli komponent: R64'),'Locked footprint: R64')
        self.assertEqual(tr('C58, D4, R64, R65'),'C58, D4, R64, R65')
        self.assertEqual(tr('BAT54SW'),'BAT54SW')

    def test_all_static_catalogue_entries_have_english_output(self):
        set_language('en')
        for source,english in MESSAGES.items():
            if '{' not in source:
                with self.subTest(source=source):self.assertEqual(tr(source),english)
