# Resmi KiCad PCM başvurusu

[English](PUBLISHING.md)

Yayın projesi `MEY-26/kicad-layout-clone`, paket kimliği
`com.github.mey-26.kicad-layout-clone`. 0.2.0, Windows için test sürümüdür.

## Güncel başvuru

[Resmi metadata başvurusu !683](https://gitlab.com/kicad/addons/metadata/-/merge_requests/683),
8 Ekim 2026 tarihinde açıldı ve KiCad ekibinin incelemesine hazır duruma getirildi.
Hesap doğrulamasından sonra [merge doğrulaması](https://gitlab.com/MEY-26/metadata/-/pipelines/2925946387)
ve [fork doğrulama/katalog oluşturma işleri](https://gitlab.com/MEY-26/metadata/-/pipelines/2925943705)
geçti. Üretilen test kataloğunun paket/simge hash'leri ve sürüm arşivinin
hash/boyutu da doğrulandı. Bu durum, eklenti kataloğuna kabul edildiği anlamına
gelmiyor. Üretilen katalogdan PCM arayüzü üzerinden kurulum henüz doğrulanmadı.

[Geçici v2 PCM test deposu](https://gitlab.com/MEY-26/metadata/-/jobs/17026339881/artifacts/raw/artifacts/repository.json),
ayrı KiCad yapılandırmasında kurulum denemek için PCM'deki Manage Repositories
alanına eklenebilir. GitLab CI dosyalarının süresi dolabilir.
KiCad ekibinin incelemesi bekleniyor.

## Sürüm dosyaları

Depo kökünde `python build_pcm.py` çalıştırıldığında:

- `dist/Layout_Clone-0.2.0-pcm.zip`: PCM'de Install from File ile kurulacak paket.
- `dist/SHA256SUMS.txt`: paketin bütünlük özeti.
- `dist/submission/packages/com.github.mey-26.kicad-layout-clone/metadata.json`:
  indirme bağlantısı, hash ve boyutları içeren resmi depo başvuru dosyası.
- Aynı klasörde `icon.png`: 64×64 katalog simgesi.

ZIP içindeki metadata indirme alanlarını içermez. `runtime: ipc` alanı paketin
eski SWIG eklentisi sayılmasını önler. ZIP ve checksum dosyalarını GitHub'da
`v0.2.0` etiketli herkese açık sürüme ekle. Giriş yapmadan indirilebildiğini ve
SHA256SUMS ile eşleştiğini kontrol et. Başvuru sonrasında paketi değiştirmek
yerine yeni bir sürüm çıkar.

## Varsayılan katalogda aranabilir hale gelmesi

1. GitLab'a giriş yapıp [kicad/addons/metadata](https://gitlab.com/kicad/addons/metadata)
   deposunu fork et.
2. Fork içinde örneğin `add-layout-clone` dalını oluştur.
3. Üretilen `packages/com.github.mey-26.kicad-layout-clone/` klasörünü metadata
   deposunun `packages/` klasörüne ekle.
4. Commit oluştur ve ana deponun varsayılan dalına merge request aç.
   Açıklama için [PCM_SUBMISSION.md](PCM_SUBMISSION.md) hazırlandı.
5. KiCad ekibinin incelemesini takip et. Başvuru kabul edilip katalog
   güncellendiğinde kullanıcılar varsayılan PCM listesinde **Layout Clone** arayabilir.

GitHub sürümü veya yerel ZIP, PCM liste başvurusunun kabul edildiği anlamına
gelmez. Başvuru ve takibi için GitLab hesabı gerekir. Kabul ve zamanlama
KiCad ekibinin kontrolündedir; belirlenmiş bir inceleme süresi vaat edilmiyor.

## Geliştirme kontrolleri

Paket doğrulama testleri için `jsonschema` kurup şu komutları çalıştır:

```sh
python -m unittest discover -s tests -p "test_*.py"
python build_pcm.py
```

Testler sentetik devreleri kullanır; yayın deposunda proje PCB/şema dosyaları
bulunmaz. GitHub Actions testleri çalıştırıp ZIP'i oluşturur. Gerçek kurulum
kontrolü için ayrı KiCad yapılandırmasında ZIP'i kurup deneme kartında kaynak
seçimi, hedef seçimi, önizleme, uygulama ve geri alma akışını dene.

Resmi kaynaklar: [PCM paketleme ve başvuru](https://dev-docs.kicad.org/en/addons/index.html),
[IPC eklenti geliştirme](https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/for-addon-developers/).
