Add Layout Clone 0.2.0 (KiCad 10 IPC plugin)

Layout Clone replicates footprint placement between repeated circuits using
anchor-relative geometry and pad-connectivity matching. Users select source
and target groups in the PCB Editor, preview mappings and apply one placement
to multiple targets. It supports English/Turkish, defaults to English and uses
native undo. Tracks, vias and zones are not copied.

- Source and issue tracker: https://github.com/MEY-26/kicad-layout-clone
- Release: https://github.com/MEY-26/kicad-layout-clone/releases/tag/v0.2.0
- License: MIT
- Identifier: com.github.mey-26.kicad-layout-clone
- Runtime: IPC; KiCad 10.0; Windows; testing status
- Dependencies: kicad-python 0.7.1, wxPython 4.2.2

The package and submission metadata are validated against KiCad's PCM v2
schema. Archive structure, hash, size, namespace and IPC manifest are checked.
Synthetic matching and language tests are in the public repository. The
development workspace also passed 58 tests, including Windows wx UI and
adapter tests. Earlier placement builds were tested on an isolated real KiCad
board copy. A new real-server placement test for 0.2.0 and other OS platforms
have not been verified.

The README documents centre-only reflection, placement-only scope, DRC and
the guard blocking writes while the schematic editor is open due to reported
KiCad IPC crashes (#25322 / #24966). The archive is hosted publicly on GitHub.
