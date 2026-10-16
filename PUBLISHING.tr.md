# Resmi KiCad PCM yayını

Paket kimliği `com.github.mey-26.kicad-layout-clone`.
0.3.5, Windows / KiCad 10.0 IPC test sürümüdür.

## 16 Ekim 2026 tarihindeki katalog durumu

Resmi [PCM kataloğunda](https://repository.kicad.org/repository.json) şu anda
0.3.3 ve 0.3.2 bulunuyor. [0.3.3 güncellemesi !692](https://gitlab.com/kicad/addons/metadata/-/merge_requests/692)
13 Ekim'de birleştirildi; katalog 14 Ekim'de yenilendi.

[0.3.5 GitHub sürümü](https://github.com/MEY-26/kicad-layout-clone/releases/tag/v0.3.5)
yayımlandı. Aynı numaralı no-connect padlerin kartın okunmasını engellemesi,
yalnız bellekteki eşleştirme modeli düzeltilerek giderildi. Gerçek PCB ağları
ve padleri değiştirilmez. 0.3.4'teki otomatik 3B model aktarımı korunur;
yayımlanmış 0.3.4 ve önceki paketler değiştirilmedi.

İnceleme bekleyen mevcut [metadata güncellemesi !694](https://gitlab.com/kicad/addons/metadata/-/merge_requests/694),
0.3.4, 0.3.3 ve 0.3.2 kayıtları korunarak 0.3.5'i de içerecek şekilde
güncellendi. Commit edilen metadata, yerelde doğrulanan içerikle aynı.
[0.3.5 GitLab CI testleri](https://gitlab.com/MEY-26/metadata/-/pipelines/2954321701)
ve [GitHub kaynak kod testleri](https://github.com/MEY-26/kicad-layout-clone/actions/runs/38874320301)
geçti. Başvuru açık, birleştirilebilir ve çakışmasız; bakım ekibinin incelemesi
ve katalog yenilemesi gerekiyor. Beklerken ZIP, PCM'nin **Install from File** seçeneğiyle
kurulabilir. Varsayılan katalogdan arayüz üzerinden kurulum henüz doğrulanmadı.

## Paketleme ve doğrulama

Depo kökünde `python build_pcm.py` çalıştır. `dist/Layout_Clone-0.3.5-pcm.zip`,
`dist/SHA256SUMS.txt` ve `dist/submission/packages/com.github.mey-26.kicad-layout-clone/`
altında metadata/simge oluşur. ZIP metadata'sı yalnız bir sürüm içerir; indirme
alanları içermez ve `runtime: ipc` bildirir. Katalog başvurusunda önceki sürüm
kayıtları korunur.

Herkese açık 0.3.5 ZIP paketi oturum açılmadan indirilerek doğrulandı:

- SHA-256: `53918e901a16413650f06f85a3c8f92495dec617494093518843c19cce7de74f`
- İndirme boyutu: 69.780 bayt; kurulum boyutu: 197.179 bayt.
- Resmi yerel PCM paket ve simge doğrulayıcıları geçti.

Yayımlanmış ZIP değişmez; içerik değişikliği için yeni sürüm çıkarılır.

## Test kapsamı

10 yeni aktarım katmanı regresyonu dahil 60 açık kaynak/paket testi geçti.
Windows geliştirme kontrollerinde mevcut 124 test ve 10 yeni odaklı test geçti.
Aynı 10 regresyon, sürüm ZIP'inden çıkarılan kod üzerinde de geçti. Açık test
verileri sentetiktir; kullanıcı PCB veya şema verisi içermez.

Tekrarlanan bağlantısız gövde padleri, gerçek yinelenen pin/ağ çakışmaları,
no-connect işareti olmayan ağ adları, bağlı/bağlantısız pad karışımı, farklı
açık pinlerin ayrı tutulması ve gerçek IPC pad verilerinin korunması sınandı.
Mevcut yerleşim, geometri/model aktarımı, dil ve işlem testleri de korunur.

Bu salt okuma düzeltmesi için yeni canlı IPC veya yerel Undo/Redo testi
yapılmadı. PCB düzenleyicisi meşgulken canlı kart yükleme doğrulanamadı.
Linux/macOS çalışma zamanı doğrulanmadı.
