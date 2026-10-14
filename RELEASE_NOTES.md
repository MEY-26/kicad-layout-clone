# Layout Clone 0.3.4

Footprint Edits automatically replaces each target's complete 3D model list
with the source list, including model paths, XYZ scale, rotation, offset,
visibility and opacity. No extra checkbox is required. Model settings remain
in footprint-local coordinates, preserving the target's board position, angle
and side. The preview shows model counts and all proposed model settings.

An empty source model list clears the target models. Disable the geometry
options to synchronize models alone when either footprint has models.
Embedded `kicad-embed://` source models are rejected before writing because
the pinned IPC API does not provide their embedded file contents.

Published 0.3.3 archives remain unchanged.

Validation: 44 public source/package tests and 119 Windows development tests
passed. The user confirmed the installed 0.3.4 behavior works. New native IPC
Undo/Redo checks were not run; GUI/transport tests use an isolated test double.

## Türkçe

Footprint Düzenlemeleri artık kaynak footprint'in tüm 3B modellerini, dosya
yollarını, ölçek, dönüş, offset, görünürlük ve opaklık ayarlarını otomatik kopyalar.
Ek bir onay kutusu yoktur. Hedefin karttaki konumu, açısı ve yüzü korunur.
Kaynakta model yoksa hedefin model listesi temizlenir; önizlemede açıkça gösterilir.

# Layout Clone 0.3.3

Placement groups can now mix front/back footprints. Each target takes the board
side of its electrically matched source, including an opposite-side anchor.
The target geometry is flipped before position/angle are applied; pads, paste,
mask, graphics and text change sides, while target identity, nets, fields and
3D models are retained. The preview shows F → B / B → F changes.

Values, footprints, pin topology, locked targets, explicit selection and native
transaction checks remain. Board-side and copper-stack changes invalidate a
preview. Unsupported embedded zones block a flip before any board write.
Footprint Edits continues preserving target placement and board side.

Validation: 39 public/package tests, 107 Windows development tests, all 64
synthetic side combinations, the reported R1/R2/C1 example, mixed-side GUI
preview/apply, rollback of bad flip geometry, and independent KiCad 10.0.5 C++
pad-flip comparison. User PCB files were not changed. New live IPC Undo/Redo
checks were not run; transport and GUI checks use an isolated test double.

The user confirmed the installed 0.3.3 behavior works. Download
`Layout_Clone-0.3.3-pcm.zip` and install through KiCad Plugin and Content Manager
→ Install from File. Close and relaunch the plugin window after updating.
The initial 0.3.2 metadata submission was accepted; 0.3.3 catalogue availability
depends on the separate metadata update and catalogue refresh.

## Türkçe

Ön/arka yüzleri karışık yerleşim grupları artık eşleştirilebilir. Her hedef,
eşleşen kaynak komponentin yüzüne alınır; padler, pasta/maske açıklıkları,
çizimler ve yazılar uygun şekilde çevrilir. Hedef kimliği ve ağları korunur.
Önizlemede F → B / B → F görünür. Kullanıcı yerel 0.3.3 sürümünün çalıştığını
doğruladı. 39 açık kaynak/paket ve 107 Windows geliştirme testi geçti.

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
