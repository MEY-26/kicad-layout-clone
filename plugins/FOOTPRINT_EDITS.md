# Footprint Edits — Layout Clone 0.3.1

[Türkçe](FOOTPRINT_EDITS.tr.md)

The **Placement** tab continues copying positions and orientations between
repeated circuits. The new **Footprint Edits** tab copies manual, project-local
footprint geometry. It does not edit the original library footprint.

## Use

1. Finish your manual source-footprint edits in PCB Editor. Open Layout Clone
   and switch to **Footprint Edits**.
2. Select **one source footprint** on the PCB and click **1 · Capture PCB
   source selection**. Capturing a new source clears this tab's target list.
3. Press Esc to clear the PCB selection. Select one or more target footprints
   and click **2 · Capture and add PCB target**. Repeat to add more targets.
   Selections are never expanded automatically.
4. Choose **Pad geometry and settings**, **Footprint graphics and free text**,
   or both. Reference/value text formatting and local positions are an
   additional, **off by default** option; their text contents remain target-specific.
5. Click **3 · Preview edits**. The report shows the exact targets, changed-pad
   count, graphic counts and proposed pad positions, dimensions and nets.
   Enable **Show all geometry and pad settings** to inspect the complete proposed
   pad, graphic and optional text records. This is a numerical preview, not DRC.
6. Remove incompatible targets and preview again. All listed targets must be
   compatible before Apply is enabled. Click **4 · Apply footprint edits**.
   Inspect the PCB and run DRC; save only when satisfied. **Ctrl+Z** in PCB Editor
   undoes the whole batch in one step.

The optional suggestions dialog lists reasons based on footprint library ID,
value/name and description. Only suggestions you explicitly check are added.
You can also remove selected targets or clear all targets without changing the source.
The two tabs maintain separate source/target selections.

## Exact scope

- **Pads:** position relative to the source footprint origin, orientation, pad
  type and complete padstack (shape/size, drill, layer set, mask/paste, custom
  pad geometry and zone/thermal settings), plus the pad clearance override.
  Pads match by their existing number, never by source net or UUID. An absent
  clearance override stays absent, preserving inheritance rather than forcing zero.
- **Graphics/free text:** replaces the target's supported local graphics/free
  text with the source's, transformed into the target's board coordinates.
  Supports front/back silkscreen, fabrication, courtyard, mask, paste and the
  Dwgs/Cmts/Eco1/Eco2 user layers. Existing target graphic IDs are retained by
  compatible slot/type where possible; added graphics receive target-specific IDs.
- **Optional reference/value formatting:** copies appearance and local position,
  keeping the target's field IDs, names and reference/value strings.
- **Always preserved:** target footprint UUID, library ID, position, orientation,
  board side, lock state, reference/value, symbol path/sheet information, complete
  per-pad nets and pad UUIDs/symbol-pin metadata. Target 3D models, custom fields,
  footprint-level rules/attributes, net ties and local zones remain unchanged.
- No library, schematic, track, via or board-zone edits; no automatic board save.

## Compatibility and safety

The source and each target need the **same pad-number set**. Front-to-back and
back-to-front transfer reflect the source geometry and convert side-specific
layers using KiCad flip conventions, while retaining the target side and angle.
Internal copper layers use the current board copper-layer count.
One unnumbered, net-free mechanical pad is supported. Multiple unnumbered pads
or repeated pad numbers are rejected because their correspondence is ambiguous.
Adding/removing/renumbering pads is deliberately unsupported. Locked targets,
unknown footprint child types, and copper/unsupported-layer graphics are rejected.
Disable graphics copying to copy pads only when copper graphics are present.
Rotated targets are supported, including angles that are not multiples of 90°.

Fresh geometry and metadata are checked immediately before writing. If the
source or any target changed after preview, preview again. Both tabs share the
existing KiCad 10 transaction guards: close the schematic editor and other PCB
editors before applying. Finish active placement/geometry tools and property
dialogs. A timed-out mutation is never automatically replayed; uncertain rollback
blocks further writes until the PCB Editor is reopened.

**Later “Update Footprints from Library” can overwrite these project-local edits.**
No special library override is created by this feature.

## Installation and validation

Download `Layout_Clone-0.3.1-pcm.zip` from the [release page](https://github.com/MEY-26/kicad-layout-clone/releases/tag/v0.3.1)
and use PCM **Install from File…**. Back up and remove the legacy manual
`com.sharkesc.layout-clone` installation before installing the community PCM
package, to avoid duplicate actions. Close and reopen the plugin after updating.
English remains the default for a fresh installation; the last chosen language is remembered.
Toolbar icons remain 24/48 pixels; the separate catalogue icon remains 64 pixels.

Tested against KiCad **10.0.5**, `kicad-python==0.7.1`, `wxPython==4.2.2` on Windows.
Regression tests use isolated IPC protobuf fixtures and the real wx interface.
An unsaved, separately launched PCB copy verified actual geometry updates,
a 37° target, optional text formatting, native transaction rollback, **one-step
Undo/Redo**, and the existing placement path. Live PCB/schematic/project files
were hash-checked and unchanged. Undo was invoked through the official IPC
tool action; keyboard input itself was not automated.

API references checked against the pinned implementation:
[KiCad 10.0.5 footprint serialization](https://gitlab.com/kicad/code/kicad/-/blob/10.0.5/pcbnew/footprint.cpp)
and [KiCad 10.0.5 Undo/Redo actions](https://gitlab.com/kicad/code/kicad/-/blob/10.0.5/common/tool/actions.cpp).

In 0.3.1, both transfer directions were compared with an independent KiCad C++
flip oracle, including asymmetric chamfer/trapezoid/custom pads, free text and
reference/value formatting. Native update and Undo passed. Checkbox widths are
remeasured after language changes to prevent truncated Turkish labels.
