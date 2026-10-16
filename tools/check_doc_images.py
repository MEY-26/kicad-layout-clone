"""Validate the local PNG screenshots referenced by both repository READMEs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

from preview_validation import validate_preview


def check_readmes(root):
    root = Path(root).resolve()
    reports = {}
    for name in ('README.md', 'README.tr.md'):
        text = (root/name).read_text(encoding='utf-8')
        references = re.findall(r'!\[[^\]]*\]\((docs/[^\s)]+\.png)\)', text)
        if not references:
            raise ValueError(f'{name} must reference a versioned local screenshot')
        for reference in references:
            image = (root/reference).resolve()
            if root not in image.parents:
                raise ValueError('Screenshot path escapes the repository')
            if reference not in reports:
                reports[reference] = validate_preview(image)
    return reports


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        print(json.dumps(check_readmes(args.root), indent=2))
    except (OSError, ValueError) as error:
        parser.exit(1, f'Documentation screenshot check failed: {error}\n')
