# Resmi KiCad PCM yayını

Paket kimliği `com.github.mey-26.kicad-layout-clone`.
0.3.3, Windows / KiCad 10.0 IPC test sürümüdür.

## 13 Ekim 2026 tarihindeki katalog durumu

[İlk başvuru !683](https://gitlab.com/kicad/addons/metadata/-/merge_requests/683),
Jon Evans tarafından 13 Ekim 2026 saat 01:47'de (İstanbul) birleştirildi.
Kabul edilen [metadata kaydı](https://gitlab.com/kicad/addons/metadata/-/blob/main/packages/com.github.mey-26.kicad-layout-clone/metadata.json)
0.3.2 sürümünü içeriyor. Varsayılan [PCM kataloğu](https://repository.kicad.org/repository.json)
13 Ekim saat 14:02'de (İstanbul) güncellendi ve artık Layout Clone 0.3.2'yi listeliyor.

0.3.3 [GitHub sürüm sayfasında](https://github.com/MEY-26/kicad-layout-clone/releases/tag/v0.3.3)
yayımlandı. [Metadata güncellemesi !692](https://gitlab.com/kicad/addons/metadata/-/merge_requests/692)
mevcut 0.3.2 kaydını koruyor. Yeni başvuru açık, çakışmasız ve bakım ekibinin incelemesini
bekliyor. [CI testleri](https://gitlab.com/MEY-26/metadata/-/pipelines/2942138149) geçti.
Herkese açık ZIP, resmi yerel paket/simge doğrulayıcılarından da geçti.
Bu güncelleme kabul edilene kadar 0.3.3 ZIP'i PCM'nin Install from File seçeneğiyle kurulabilir.
Üretilen varsayılan katalogdan arayüz üzerinden kurulum henüz doğrulanmadı.

## Paketleme ve doğrulama

Depo kökünde `python build_pcm.py` çalıştır. `dist/Layout_Clone-0.3.3-pcm.zip`,
`dist/SHA256SUMS.txt` ve `dist/submission/packages/com.github.mey-26.kicad-layout-clone/`
altında metadata/simge oluşur. ZIP metadata'sı indirme alanlarını içermez;
`runtime: ipc` bildirir. Resmi kaydı güncellemeden önce herkese açık indirmeyi
SHA-256 ve boyutla doğrula. Yayımlanmış ZIP değişmez; içerik değişikliği için yeni sürüm çıkar.

39 açık kaynak/paket ve 107 Windows geliştirme testi geçti. Yayın deposunda kullanıcı
PCB/şema dosyaları yoktur. KiCad 10.0.5 C++ pad çevirme karşılaştırması ve izole
arayüz/transport testleri yapıldı. Yeni canlı IPC Undo/Redo kontrolü yapılmadı;
Linux/macOS çalışma zamanı doğrulanmadı.
