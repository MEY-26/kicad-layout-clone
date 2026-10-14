# Layout Clone 0.3.4

Footprint Edits now automatically copies the source's complete 3D model list,
including model paths, XYZ scale, rotation, offset, visibility and opacity.
No extra checkbox is needed. Target position, board angle and side remain
unchanged; model transforms stay in footprint-local coordinates.

The preview shows model counts, paths and all model settings. An empty source
model list clears the target models, with an explicit preview message. Turn
off the geometry options to copy or clear only models. Embedded
`kicad-embed://` source models are rejected before writing because the pinned
IPC API does not provide their embedded file contents; use an external path.

Validation: 44 public source/package tests and 119 Windows development tests
passed, including multiple models, exact local transforms across board sides
and angles, EN/TR GUI preview/apply, stale model previews and rollback of
corrupted model results. The user confirmed the installed 0.3.4 behavior works.
New native IPC Undo/Redo checks were not run; GUI/transport tests use an
isolated test double. Linux/macOS runtime is unverified.

Download `Layout_Clone-0.3.4-pcm.zip` and install through KiCad Plugin and Content
Manager → Install from File. Close and relaunch the plugin window after updating.
Windows / KiCad 10.0 / IPC / testing release. The official catalogue currently
offers 0.3.3; the 0.3.4 metadata update requires maintainer review.

## Türkçe

Footprint Düzenlemeleri artık kaynağın tüm 3B modellerini, dosya yollarını,
ölçek, dönüş, offset, görünürlük ve opaklık ayarlarını otomatik kopyalar.
Ek onay kutusu yoktur; hedefin karttaki konumu, açısı ve yüzü korunur.
Kaynakta model yoksa hedefin model listesi temizlenir; önizlemede açıkça gösterilir.
44 açık kaynak/paket ve 119 Windows geliştirme testi geçti. Kullanıcı kurulu
0.3.4 sürümünün çalıştığını doğruladı.
