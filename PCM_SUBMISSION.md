Update Layout Clone to 0.3.4 (automatic 3D model transfer)

Footprint Edits previously retained target 3D models after copying pad/graphic
edits. Version 0.3.4 automatically replaces the target model list with the
source list, including paths, XYZ scale, rotation, offset, visibility and opacity.
This keeps a manually adjusted model synchronized with the copied footprint.
No additional checkbox is required. Model settings stay footprint-local;
target position, angle, board side, identity, pad nets and schematic linkage
remain intact. The Placement tab continues retaining target models.

The preview shows old/new model counts and exact proposed settings. An empty
source clears target models, with an explicit preview message. Model-only
copying/clearing is supported with geometry options disabled. Source
`kicad-embed://` models are rejected before a transaction because their embedded
payloads are unavailable through the pinned IPC API; external paths are supported.

This metadata update retains the accepted 0.3.3 and 0.3.2 versions. The previous
update !692 was merged on 13 October 2026. The package identifier and icon stay
the same; only package metadata is changed in this submission.

- Source/issues: https://github.com/MEY-26/kicad-layout-clone
- Contact: [yaman2198@gmail.com](mailto:yaman2198@gmail.com)
- Release: https://github.com/MEY-26/kicad-layout-clone/releases/tag/v0.3.4
- Identifier: com.github.mey-26.kicad-layout-clone
- License: MIT
- Runtime/platform: IPC, KiCad 10.0, Windows, testing status
- Dependencies: kicad-python 0.7.1 and wxPython 4.2.2

44 public source/package tests and 119 Windows development tests passed.
Coverage includes multiple models and duplicates, every copied model property,
all F/B combinations and nonzero footprint angles, unchanged target identity,
EN/TR GUI preview/apply, source/target model changes invalidating previews,
and whole-batch rollback on corrupted returned models. The user confirmed the
installed 0.3.4 build works. Synthetic public tests contain no user PCB data.
New native IPC Undo/Redo checks were not run; GUI/transport tests use an isolated
test double. Linux/macOS and installation through the generated catalogue
remain unverified. Prior native checks are documented separately.

The public archive is checked by unauthenticated download, SHA-256 and sizes,
and the official local PCM package/icon validators before submission.
