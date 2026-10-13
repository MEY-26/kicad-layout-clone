Update Layout Clone to 0.3.3 (KiCad 10 IPC plugin)

This updates the accepted Layout Clone package to 0.3.3 and retains the existing
0.3.2 version. The initial submission !683 was merged on 13 October 2026.
Only the package metadata changes; the catalogue icon and identifier stay the same.

The Placement tab now accepts mixed front/back groups and opposite-side anchors.
Each target takes the board side of its electrically matched source. Target pads,
paste/mask, graphics and text are reflected/converted before position and angle
are applied. The preview shows F → B / B → F. Target UUIDs, pad numbers/nets,
schematic linkage, custom fields and 3D models are preserved. Values, footprints,
pad topology, explicit selection and native transaction guards remain enforced.
Footprint Edits continues preserving target placement and board side.

- Source/issues: https://github.com/MEY-26/kicad-layout-clone
- Contact: [yaman2198@gmail.com](mailto:yaman2198@gmail.com)
- Release: https://github.com/MEY-26/kicad-layout-clone/releases/tag/v0.3.3
- Identifier: com.github.mey-26.kicad-layout-clone
- License: MIT
- Runtime/platform: IPC, KiCad 10.0, Windows, testing status
- Dependencies: kicad-python 0.7.1 and wxPython 4.2.2

39 public source/package tests and 107 Windows development tests passed. Tests
cover all 64 synthetic face combinations, the reported resistor/capacitor example,
mixed-side GUI preview/apply, rollback of invalid flip geometry, stale side/stackup
previews, and an independent KiCad 10.0.5 C++ pad-flip comparison. The user confirmed
the installed 0.3.3 behavior works. User PCB files were not changed. New live IPC
Undo/Redo checks were not run; the transport and GUI checks use an isolated test
double. Earlier native IPC checks are documented separately. Linux/macOS and
installation through the generated catalogue remain unverified.

No tracks or vias are copied/rerouted. Footprints with embedded zones or unsupported
children are rejected before a flip transaction. English is the default and Turkish
is supported. Documentation covers DRC, library updates overwriting project-local
edits, and existing guards against concurrent PCB/schematic editors.

The public archive's unauthenticated download, SHA-256, sizes and official local
PCM package/icon validation will be verified before submission.
