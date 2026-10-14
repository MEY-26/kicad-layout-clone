# Official KiCad PCM publication

The package identifier is `com.github.mey-26.kicad-layout-clone`.
Version 0.3.4 is a Windows / KiCad 10.0 IPC testing release.

## Catalogue status checked on 14 October 2026

The [0.3.3 update !692](https://gitlab.com/kicad/addons/metadata/-/merge_requests/692)
was merged by Jon Evans on 13 October at 15:18 Istanbul time. The default
[PCM catalogue](https://repository.kicad.org/repository.json) now lists 0.3.3
and retains 0.3.2. The catalogue was refreshed on 14 October at 14:02 Istanbul time.

Version 0.3.4 adds automatic 3D model synchronization in Footprint Edits.
Its [GitHub release](https://github.com/MEY-26/kicad-layout-clone/releases/tag/v0.3.4)
is prepared for publication with a separate metadata update retaining both
accepted versions. Install its ZIP through PCM's Install from File while
waiting for maintainer review and the catalogue refresh.
Installation through the generated default catalogue has not been verified.

## Build and verify

Run `python build_pcm.py` at the repository root. It produces
`dist/Layout_Clone-0.3.4-pcm.zip`, `dist/SHA256SUMS.txt`, and submission metadata/icon
under `dist/submission/packages/com.github.mey-26.kicad-layout-clone/`.
The archive metadata omits download fields and declares `runtime: ipc`.
Verify the public download's SHA-256 and size before updating the official entry.
Published archives are immutable; publish a new version to change their contents.

44 public/package tests and 119 Windows development tests passed. Public tests
are synthetic and contain no user PCB or schematic files. The user confirmed
the installed 0.3.4 behavior works. Model regressions cover multiple models,
all transforms, model-only copying/clearing, GUI translations, stale previews
and batch rollback. New live IPC Undo/Redo checks were not run;
Linux/macOS runtime remains unverified.
