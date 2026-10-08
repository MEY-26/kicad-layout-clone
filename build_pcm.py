"""Build a deterministic IPC PCM ZIP and official-repository submission files.

Run at the root of the public repository: python build_pcm.py
No KiCad, wxPython or network access is required to build.
"""
import copy
import hashlib
import json
from pathlib import Path
import re
import zipfile

FILES = ('plugin.json', 'requirements.txt', 'main.py', 'core.py', 'adapter.py',
         'gui.py', 'edits_gui.py', 'footprint_edits.py', 'footprint_flip.py', 'i18n.py', 'icon.png', 'icon.svg', 'toolbar-24.png', 'toolbar-48.png',
         'README.md', 'README.tr.md', 'FOOTPRINT_EDITS.md', 'FOOTPRINT_EDITS.tr.md', 'LICENSE')


def build(root=None, output=None):
    root = Path(root or Path(__file__).resolve().parent)
    output = Path(output or root/'dist')
    source = root/'plugins'
    metadata = json.loads((root/'metadata.json').read_text(encoding='utf-8'))
    version = metadata['versions'][0]['version']
    code_version = re.search(r"^VERSION\s*=\s*['\"]([^'\"]+)",
                             (source/'core.py').read_text(encoding='utf-8'), re.M).group(1)
    if code_version != version:
        raise ValueError('Code and metadata versions differ')
    if any(key.startswith('download_') for v in metadata['versions'] for key in v):
        raise ValueError('Archive metadata must not contain download fields')
    manifest = json.loads((source/'plugin.json').read_text(encoding='utf-8'))
    if manifest['identifier'] != metadata['identifier']:
        raise ValueError('IPC and PCM identifiers differ')
    contents = {'plugins/'+name: (source/name).read_bytes() for name in FILES}
    contents['resources/icon.png'] = (source/'icon.png').read_bytes()
    contents['metadata.json'] = (json.dumps(metadata, indent=2, ensure_ascii=False)+'\n').encode('utf-8')
    output.mkdir(parents=True, exist_ok=True)
    archive = output/f'Layout_Clone-{version}-pcm.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, data in sorted(contents.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            z.writestr(info, data, compresslevel=9)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    submission = copy.deepcopy(metadata)
    submission['versions'][0].update(
        download_url=f"{metadata['resources']['homepage']}/releases/download/v{version}/{archive.name}",
        download_sha256=digest,
        download_size=archive.stat().st_size,
        install_size=sum(len(data) for data in contents.values()))
    package = output/'submission'/'packages'/metadata['identifier']
    package.mkdir(parents=True, exist_ok=True)
    (package/'metadata.json').write_text(json.dumps(submission, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    (package/'icon.png').write_bytes(contents['resources/icon.png'])
    (output/'SHA256SUMS.txt').write_text(f'{digest}  {archive.name}\n', encoding='utf-8')
    return archive, package/'metadata.json'


if __name__ == '__main__':
    for path in build():
        print(path)
