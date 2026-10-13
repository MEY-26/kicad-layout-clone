# Official KiCad PCM publication

The package identifier is `com.github.mey-26.kicad-layout-clone`.
Version 0.3.3 is a Windows / KiCad 10.0 IPC testing release.

## Catalogue status checked on 13 October 2026

The [initial submission !683](https://gitlab.com/kicad/addons/metadata/-/merge_requests/683)
was merged by Jon Evans on 13 October 2026 at 01:47 Istanbul time.
The accepted [metadata entry](https://gitlab.com/kicad/addons/metadata/-/blob/main/packages/com.github.mey-26.kicad-layout-clone/metadata.json)
contains version 0.3.2. At the time of this check, the default
[PCM catalogue](https://repository.kicad.org/repository.json) had not yet included
Layout Clone. Acceptance and catalogue refresh are separate steps.

Version 0.3.3 is published on [GitHub](https://github.com/MEY-26/kicad-layout-clone/releases/tag/v0.3.3).
Its metadata update is being submitted in a new merge request, based on upstream
main; the already merged !683 is not reused. The existing 0.3.2 version is retained.
Install the 0.3.3 ZIP through PCM's Install from File while waiting for the catalogue.
Installation through the generated default catalogue has not been verified.

## Build and verify

Run `python build_pcm.py` at the repository root. It produces
`dist/Layout_Clone-0.3.3-pcm.zip`, `dist/SHA256SUMS.txt`, and submission metadata/icon
under `dist/submission/packages/com.github.mey-26.kicad-layout-clone/`.
The archive metadata omits download fields and declares `runtime: ipc`.
Verify the public download's SHA-256 and size before updating the official entry.
Published archives are immutable; publish a new version to change their contents.

39 public/package tests and 107 Windows development tests passed. The source is
synthetic and contains no user PCB or schematic files. The current version includes
an independent KiCad 10.0.5 C++ pad-flip comparison and isolated GUI/transport tests.
New live IPC Undo/Redo checks were not run; Linux/macOS runtime remains unverified.

References: [PCM submission](https://dev-docs.kicad.org/en/addons/index.html),
[IPC plugin development](https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/for-addon-developers/).
