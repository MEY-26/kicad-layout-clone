# Layout Clone 0.3.2

Fix Footprint Edits rejecting small SMD resistor footprints with separate,
unnumbered solder-paste apertures. A source with a courtyard can now add it to
a compatible target, and a courtyard-free source can remove it.

- Match each net-free, paste-only aperture to its uniquely nearest numbered
  copper pad and relative board side, independent of child order and rotation.
- Preserve target pad UUIDs, nets, symbol-pin metadata, placement and board side.
- Graphics-only and field-only transfers preserve all pads without requiring
  pad matching. Disable **Pad geometry and settings** for courtyard/graphics edits.
- Reject ambiguous aperture associations, multiple apertures on the same anchor,
  connected unnumbered pads, mismatched pad mappings and duplicate numbered pads
  when pad copying is selected. No pads are added, removed or renumbered.
- Retain the Placement tab, preview workflow, batch Undo and 24/48-pixel toolbar icons.

## Validation

91 Windows development tests and 28 public source/package tests passed.
New regressions cover courtyard addition/removal, aperture geometry and identity,
rotated opposite-side targets, graphics-only preservation and ambiguous mappings.
Both directions were previewed against the reported R1/R2 pair without writing
to the user board; the user confirmed the installed fix works.
Earlier native KiCad 10.0.5 checks covered geometry transfer, rollback, Undo/Redo
and the independent C++ flip oracle. These native checks were not rerun for 0.3.2.
Linux/macOS runtime operation remains unverified.

## Install

Download **Layout_Clone-0.3.2-pcm.zip**, then use KiCad
**Plugin and Content Manager → Install from File…**. Close and reopen the plugin
window after updating. Enable **Preferences → Common → API**. Close other PCB and
schematic editors before applying. Preview and inspect changes, then run DRC.

If moving from the legacy manual `com.sharkesc.layout-clone` installation, back up
and remove it before installing this PCM package to avoid duplicate toolbar entries.
Later **Update Footprints from Library** can overwrite project-local edits.

Windows / KiCad 10.0 testing prerelease. Default PCM catalogue availability remains
subject to KiCad maintainer review.

[English usage](https://github.com/MEY-26/kicad-layout-clone/blob/main/FOOTPRINT_EDITS.md) ·
[Türkçe kullanım](https://github.com/MEY-26/kicad-layout-clone/blob/main/FOOTPRINT_EDITS.tr.md) ·
[Issues](https://github.com/MEY-26/kicad-layout-clone/issues)

## Türkçe

Ayrı, numarasız pasta açıklıkları olan küçük SMD dirençlerdeki “Uyumsuz” hatası
giderildi. Courtyard olan kaynaktan ekleme, olmayan kaynaktan kaldırma çalışır.
Yalnız çizim aktarırken **Pad geometrisi ve ayarları** seçeneğini kapat; hedef
padler aynen korunur. 91 geliştirme testi ve 28 açık kaynak/paket testi geçti.
Kullanıcı yerel 0.3.2 düzeltmesinin çalıştığını doğruladı. Resmi PCM başvurusu
inceleme bekler.

MIT licensed. Archive SHA-256 is included in **SHA256SUMS.txt**.
