Add Layout Clone 0.3.2 (KiCad 10 IPC plugin)

Layout Clone has separate Placement and Footprint Edits tabs. The former copies
anchor-relative placement between repeated circuits; the latter transfers project-local
pad geometry/settings and footprint graphics to explicitly selected targets without changing libraries.
Target placement, board side, identity, schematic linkage and pad nets are preserved.
Front/back transfer applies geometry reflection and layer conversion. Selection is never expanded automatically.

- Source / issues: https://github.com/MEY-26/kicad-layout-clone
- Contact: [yaman2198@gmail.com](mailto:yaman2198@gmail.com)
- Release: https://github.com/MEY-26/kicad-layout-clone/releases/tag/v0.3.2
- License: MIT
- Identifier: com.github.mey-26.kicad-layout-clone
- Runtime: IPC; KiCad 10.0; Windows; testing status
- Dependencies: kicad-python 0.7.1, wxPython 4.2.2

I maintain the linked GitHub project. This MR adds only package metadata and a 64x64 catalogue icon.
The archive retains separate 24x24 / 48x48 toolbar icons. English is the default; Turkish is supported.
Both flows provide explicit selection, preview and native Undo. Pad edits require matching unique
numbered pads and unambiguous paste apertures; pad additions/deletions are unsupported.
Tracks and vias are not copied or rerouted.

0.3.2 fixes Footprint Edits rejecting small SMD footprints with separate unnumbered solder-paste
apertures, which previously blocked courtyard addition/removal in either direction. Net-free,
paste-only apertures match by their uniquely nearest numbered copper pad and relative board side,
with at most one aperture per pad and paste layer. Ambiguous associations remain blocked.
Graphics-only and field-only transfer preserve all target pads without requiring pad matching.

Validation: 91 Windows development tests and 28 public source/package tests passed. New regressions
cover courtyard addition/removal, aperture geometry and identity, rotated opposite-side targets,
graphics-only pad preservation and ambiguous mappings. Both directions were previewed against the
reported R1/R2 pair without writing to the user board; the user confirmed the installed 0.3.2 fix works.
Earlier native KiCad 10.0.5 tests verified geometry transfer, rollback, single-step Undo/Redo and
placement; face transfer was compared with an independent C++ flip oracle, including asymmetric/custom
pads and text. These native checks were not rerun for 0.3.2. Linux/macOS runtime operation and
installation from the generated PCM catalogue remain unverified.

The English/Turkish documentation explains exact copy scope, DRC, later library updates overwriting
project-local edits, and existing guards blocking writes with other PCB or schematic editors open.
The package remains a Windows-only testing release. Maintainer review is pending.

Public 0.3.2 archive downloaded without authentication; SHA-256 and size match this submission.
Official local PCM package/icon validation passed. GitHub Actions source/package validation passed.
