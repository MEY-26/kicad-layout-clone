# Layout Clone 0.3.1

Copy project-local footprint edits without changing the original library.

- New **Footprint Edits** tab alongside the existing **Placement** tab.
- Capture one source and any number of targets directly from PCB selection.
- Copy pad geometry/settings, footprint graphics/free text, and optionally reference/value formatting and local position.
- Preserve each target's position, angle, board side, reference/value, schematic linkage and pad nets.
- Support front-to-back and back-to-front transfer with geometry reflection and layer conversion.
- Preview all targets; optional similarity suggestions never expand a selection automatically.
- Native batch Undo, existing IPC transaction guards and no automatic board save.
- Fix clipped Turkish checkbox labels after switching language; retain 24/48-pixel toolbar icons.

Windows / KiCad 10.0 testing release, verified with KiCad 10.0.5.
85 development tests passed. Disposable native KiCad tests covered geometry transfer,
rollback, Undo/Redo and placement; opposite-side tests were compared with an independent
KiCad C++ flip oracle, including asymmetric and custom pads. Other OS platforms remain unverified.

## Install

Download **Layout_Clone-0.3.1-pcm.zip**, then use KiCad **Plugin and Content Manager → Install from File…**.
Enable **Preferences → Common → API**. Close other PCB and schematic editors before applying.
Targets must have matching unique pad-number sets; pad addition/deletion/renumbering is unsupported.
Read the usage notes for the complete scope. Run DRC after applying.

If moving from the legacy manual `com.sharkesc.layout-clone` installation, back up and remove it
before installing this PCM package to avoid duplicate toolbar entries.
Later **Update Footprints from Library** can overwrite project-local edits.

This is a **prerelease**. Default PCM catalogue availability remains subject to KiCad maintainer review.

[English usage](https://github.com/MEY-26/kicad-layout-clone/blob/main/FOOTPRINT_EDITS.md) ·
[Türkçe kullanım](https://github.com/MEY-26/kicad-layout-clone/blob/main/FOOTPRINT_EDITS.tr.md) ·
[Issues](https://github.com/MEY-26/kicad-layout-clone/issues)

## Türkçe

Yeni **Footprint Düzenlemeleri** sekmesi, PCB’de elle düzenlediğin bir footprintin padlerini
ve çizimlerini seçtiğin hedeflere aktarır. Orijinal kütüphane değişmez; hedefin konumu,
açısı, yüzü, referansı ve ağları korunur. Ön/arka yüzler arası aktarım desteklenir.
Türkçe etiket kesilmesi giderildi. Kaynak ve hedefleri PCB’den al, kapsamı seç,
önizlemeyi kontrol et ve uygula; tüm işlem tek Undo ile geri alınabilir.
Kurulum için PCM ZIP’ini **Dosyadan yükle…** ile seç. Resmi katalog başvurusu inceleme bekler.

MIT licensed. Archive SHA-256 is included in **SHA256SUMS.txt**.
