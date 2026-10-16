# Official KiCad PCM publication

The package identifier is `com.github.mey-26.kicad-layout-clone`.
Version 0.3.5 is a Windows / KiCad 10.0 IPC testing release.

## Catalogue status checked on 16 October 2026

The official [PCM catalogue](https://repository.kicad.org/repository.json)
currently lists 0.3.3 and 0.3.2. The [0.3.3 update !692](https://gitlab.com/kicad/addons/metadata/-/merge_requests/692)
was merged on 13 October; the catalogue was refreshed on 14 October.

The [0.3.5 GitHub release](https://github.com/MEY-26/kicad-layout-clone/releases/tag/v0.3.5)
is public. It fixes board reading for repeated no-connect pad numbers by
normalizing only the local matching model, without changing PCB nets or pads.
It retains 0.3.4's automatic 3D model synchronization in Footprint Edits.
Published 0.3.4 and older archives remain unchanged.

The existing pending [metadata update !694](https://gitlab.com/kicad/addons/metadata/-/merge_requests/694)
now includes 0.3.5 while retaining 0.3.4, 0.3.3 and 0.3.2. Its committed metadata
matches the locally validated content. The [0.3.5 GitLab CI pipeline](https://gitlab.com/MEY-26/metadata/-/pipelines/2954321701)
and [GitHub source CI](https://github.com/MEY-26/kicad-layout-clone/actions/runs/38874320301)
passed. The merge request is open, mergeable and has no conflicts; maintainer
review and a catalogue refresh are still required. Install the release ZIP through PCM's **Install from File** while
waiting. Installation through the generated default catalogue has not been
verified.

## Build and verify

Run `python build_pcm.py` at the repository root. It produces
`dist/Layout_Clone-0.3.5-pcm.zip`, `dist/SHA256SUMS.txt`, and submission metadata/icon
under `dist/submission/packages/com.github.mey-26.kicad-layout-clone/`.
The archive metadata has exactly one version, omits download fields and declares
`runtime: ipc`. The catalogue submission retains all previously listed versions.

The public 0.3.5 ZIP was downloaded without authentication and verified:

- SHA-256: `53918e901a16413650f06f85a3c8f92495dec617494093518843c19cce7de74f`
- Download size: 69,780 bytes; install size: 197,179 bytes.
- Official local PCM package and icon validators passed.

Published archives are immutable; publish a new version to change their contents.

## Validation scope

60 public source/package tests passed, including 10 new adapter regressions.
The Windows development checks passed 124 existing tests plus the 10 new
focused tests. The same 10 regressions also passed against the extracted release
ZIP. Public fixtures are synthetic and contain no user PCB or schematic data.

Coverage includes repeated no-connect shield pads, genuine duplicate-pin net
conflicts, names without no-connect marks, mixed connected/open pads, separate
open-pin graph nodes and unchanged original IPC pad data. Existing placement,
geometry/model transfer, language and transaction checks remain in the suite.

New live IPC or native Undo/Redo checks were not run for this read-only fix.
Live board loading was not verified while the PCB Editor was busy.
Linux/macOS runtime remains unverified.
