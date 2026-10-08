import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('build_pcm', ROOT/'build_pcm.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class PCMTests(unittest.TestCase):
    def test_archive_schema_namespace_and_submission_integrity(self):
        schema = json.loads((ROOT/'tests'/'pcm-schema.json').read_text(encoding='utf-8'))
        with tempfile.TemporaryDirectory() as folder:
            archive, submission_path = builder.build(ROOT, Path(folder))
            submission = json.loads(submission_path.read_text(encoding='utf-8'))
            jsonschema.validate(submission, schema)
            with zipfile.ZipFile(archive) as z:
                self.assertIsNone(z.testzip())
                self.assertEqual(set(z.namelist()), {'plugins/'+n for n in builder.FILES} |
                                 {'metadata.json','resources/icon.png'})
                metadata = json.loads(z.read('metadata.json'))
                jsonschema.validate(metadata, schema)
                version = metadata['versions'][0]
                self.assertEqual(version['runtime'], 'ipc')
                self.assertEqual(version['platforms'], ['windows'])
                self.assertFalse(any(k.startswith('download_') for k in version))
                manifest = json.loads(z.read('plugins/plugin.json'))
                self.assertEqual(manifest['identifier'], metadata['identifier'])
                self.assertEqual(len(metadata['description']) <= 150, True)
                self.assertEqual(struct.unpack('>II', z.read('resources/icon.png')[16:24]), (64,64))
                self.assertEqual(sum(i.file_size for i in z.infolist()), submission['versions'][0]['install_size'])
            published = submission['versions'][0]
            self.assertEqual(published['download_sha256'], hashlib.sha256(archive.read_bytes()).hexdigest())
            self.assertEqual(published['download_size'], archive.stat().st_size)
            self.assertTrue(published['download_url'].endswith('/v'+published['version']+'/'+archive.name))

    def test_build_is_reproducible(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            first, _ = builder.build(ROOT, Path(a))
            second, _ = builder.build(ROOT, Path(b))
            self.assertEqual(first.read_bytes(), second.read_bytes())


if __name__ == '__main__':
    unittest.main()
