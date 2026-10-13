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

