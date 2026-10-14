# Resmi KiCad PCM yayını

Paket kimliği `com.github.mey-26.kicad-layout-clone`.
0.3.4, Windows / KiCad 10.0 IPC test sürümüdür.

## 14 Ekim 2026 tarihindeki katalog durumu

[0.3.3 güncellemesi !692](https://gitlab.com/kicad/addons/metadata/-/merge_requests/692),
Jon Evans tarafından 13 Ekim saat 15:18'de (İstanbul) birleştirildi.
Varsayılan [PCM kataloğu](https://repository.kicad.org/repository.json) artık
0.3.3'ü listeliyor ve 0.3.2 kaydını koruyor. Katalog 14 Ekim saat 14:02'de güncellendi.

0.3.4, Footprint Düzenlemeleri sekmesine otomatik 3B model aktarımı ekler.
[GitHub sürümü](https://github.com/MEY-26/kicad-layout-clone/releases/tag/v0.3.4)
ve kabul edilmiş iki sürümü koruyan yeni metadata güncellemesi yayın için hazırlanır.
Bakım ekibinin incelemesi ve katalog güncellemesi beklenirken ZIP, PCM'nin
Install from File seçeneğiyle kurulabilir. Varsayılan katalogdan arayüz
üzerinden kurulum henüz doğrulanmadı.

## Paketleme ve doğrulama

Depo kökünde `python build_pcm.py` çalıştır. `dist/Layout_Clone-0.3.4-pcm.zip`,
`dist/SHA256SUMS.txt` ve `dist/submission/packages/com.github.mey-26.kicad-layout-clone/`
altında metadata/simge oluşur. ZIP metadata'sı indirme alanlarını içermez;
`runtime: ipc` bildirir. Resmi kaydı güncellemeden önce herkese açık indirmeyi
SHA-256 ve boyutla doğrula. Yayımlanmış ZIP değişmez; içerik değişikliği için yeni sürüm çıkar.

44 açık kaynak/paket ve 119 Windows geliştirme testi geçti. Açık testler sentetiktir;
kullanıcı PCB/şema verileri içermez. Kullanıcı kurulu 0.3.4 sürümünün çalıştığını
doğruladı. Çoklu modeller, tüm dönüşüm ayarları, yalnız model aktarımı/temizliği,
arayüz çevirileri, eskiyen önizleme ve toplu geri alma test edildi.
Yeni canlı IPC Undo/Redo kontrolü yapılmadı; Linux/macOS çalışma zamanı doğrulanmadı.
