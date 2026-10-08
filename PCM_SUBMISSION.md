Add Layout Clone 0.3.1 (KiCad 10 IPC plugin)

Layout Clone has separate Placement and Footprint Edits tabs. The former copies
anchor-relative placement between repeated circuits; the latter transfers project-local
pad geometry/settings and footprint graphics to explicitly selected targets without changing libraries.
Target placement, board side, identity, schematic linkage and pad nets are preserved.
Front/back transfer applies geometry reflection and layer conversion. Selection is never expanded automatically.

- Source / issues: https://github.com/MEY-26/kicad-layout-clone
- Release: https://github.com/MEY-26/kicad-layout-clone/releases/tag/v0.3.1
- License: MIT
- Identifier: com.github.mey-26.kicad-layout-clone
- Runtime: IPC; KiCad 10.0; Windows; testing status
- Dependencies: kicad-python 0.7.1, wxPython 4.2.2

I maintain the linked GitHub project. This MR adds only package metadata and a 64x64 catalogue icon.
The archive retains separate 24x24 / 48x48 toolbar icons. English is the default; Turkish is supported.
Both flows provide explicit selection, preview and native Undo. Footprint edits require matching unique
pad-number sets; pad additions/deletions are unsupported. Tracks and vias are not copied or rerouted.

Validation: PCM v2 schema, IPC manifest, reproducible archive, namespace, download hash and sizes
are checked by repository tests. 85 Windows development tests passed. Disposable native KiCad 10.0.5
tests verified footprint edits, rotated targets, rollback, single-step Undo/Redo and placement.
Both face-transfer directions were compared with an independent KiCad C++ flip oracle, including
asymmetric/custom pads and text. User project files remained unchanged; the user also confirmed
the local 0.3.1 build works. Linux/macOS and installation from the generated PCM catalogue remain unverified.

The English/Turkish documentation explains exact copy scope, DRC, later library updates overwriting
project-local edits, and existing guards blocking writes with other PCB or schematic editors open.
The package remains a Windows-only testing release. Maintainer review is pending.
