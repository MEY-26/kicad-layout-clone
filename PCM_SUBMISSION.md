Update Layout Clone to 0.3.5 (no-connect shield pad reading fix)

Version 0.3.5 fixes a board-reading failure for repeated pad numbers on
no-connect pins. A USB-C socket's four `SH` shield pads can have distinct
KiCad-generated `unconnected-(...)` net names. The old reader treated them as
conflicting real nets and prevented the entire board from loading.

Only pads with `symbol_pin.no_connect` set AND a net name starting with
`unconnected-(` are treated as open in the in-memory matching model. Actual
PCB pad data, nets, symbol-pin metadata, the schematic and connections remain
unchanged. No pads are renumbered and no nets are renamed. Genuine duplicate-pin
net conflicts remain rejected; a generated-looking name without a no-connect
mark cannot bypass the check. Footprint Edits' unique numbered-pad requirement
for geometry transfer is unchanged.

The 0.3.4 automatic 3D model synchronization remains included: Footprint Edits
copies complete source model lists, paths, XYZ scale, rotation, offset,
visibility and opacity while preserving target placement, side, identity and
pad nets. Model-only copying/clearing and the existing embedded-model safeguards
remain. Placement continues retaining target models.

This updates the existing pending !694 submission to include versions 0.3.5,
0.3.4, 0.3.3 and 0.3.2. The accepted 0.3.3/0.3.2 entries and the pending 0.3.4
download fields are retained. Previously published archives, identifier and icon
are unchanged; this submission changes only the package metadata.

- Source/issues: https://github.com/MEY-26/kicad-layout-clone
- Contact: [yaman2198@gmail.com](mailto:yaman2198@gmail.com)
- Release: https://github.com/MEY-26/kicad-layout-clone/releases/tag/v0.3.5
- Source commit: `05dcef97f51bbeef79f4e596de384417129c94e0`
- Identifier: `com.github.mey-26.kicad-layout-clone`
- License: MIT
- Runtime/platform: IPC, KiCad 10.0, Windows, testing status
- Dependencies: `kicad-python==0.7.1` and `wxPython==4.2.2`
- ZIP SHA-256: `53918e901a16413650f06f85a3c8f92495dec617494093518843c19cce7de74f`
- Download size: 69,780 bytes; install size: 197,179 bytes.

60 public source/package tests passed, including 10 new adapter regressions
using real IPC protobuf objects. Windows development checks passed 124 existing
tests plus the 10 new focused regressions. The 10 regressions also passed using
code extracted from the release ZIP. New coverage verifies:

- Four repeated no-connect `SH` pads with separate generated names are accepted.
- Repeated pad numbers assigned to `GND` and `VBUS` are rejected.
- An `unconnected-(` name without a no-connect mark does not bypass validation.
- Connected/no-connect mixtures on the same pad number are rejected.
- Different unconnected pins remain separate in the connectivity graph.
- Reading preserves the complete original pad/footprint protobuf data.

Public fixtures contain no user PCB or schematic files. The unauthenticated
public ZIP download, SHA-256, sizes and official local PCM package/icon
validators passed. New live IPC or native Undo/Redo checks were not run for
this read-only fix; live board loading was not verified while the PCB Editor
was busy. Linux/macOS and installation through the generated catalogue remain
unverified. Previous native checks are documented in the source repository.

The committed metadata at `4af7a3cc8e9bbda8ee6dbe8150b6e2cd6da5ca2f` matches the
locally validated content. The [0.3.5 GitLab CI pipeline](https://gitlab.com/MEY-26/metadata/-/pipelines/2954321701)
and [GitHub source CI](https://github.com/MEY-26/kicad-layout-clone/actions/runs/38874320301)
passed. The existing !694 merge request is open, mergeable and has no conflicts.
The official PCM catalogue currently lists 0.3.3 and 0.3.2; maintainer review
and a catalogue refresh are still required for this update.
