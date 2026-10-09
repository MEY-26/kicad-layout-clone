# Footprint Düzenlemeleri — Layout Clone 0.3.2

[English](FOOTPRINT_EDITS.md)

**Yerleşim** sekmesi aynı devrelerin konum ve yönlerini kopyalamaya devam eder.
Yeni **Footprint Düzenlemeleri** sekmesi PCB üzerinde elle yaptığım, projeye özgü
footprint düzenlemelerini başka parçalara aktarır. Orijinal kütüphane footprinti
değişmez.

## Kullanım

1. PCB üzerinde kaynak footprintin düzenlemesini bitiririm. Layout Clone’u
   açıp **Footprint Düzenlemeleri** sekmesine geçerim.
2. PCB’de **tek kaynak footprint** seçip **1 · PCB kaynak seçimini al** düğmesine
   basarım. Yeni kaynak alınması bu sekmedeki hedef listesini temizler.
3. Esc ile PCB seçimini kaldırırım. Bir veya birden fazla hedef footprint seçip
   **2 · PCB hedef seçimini al ve ekle** düğmesine basarım. Başka hedefleri de bu
   şekilde ekleyebilirim. Seçimler otomatik genişletilmez.
4. Pad geometrisi/ayarları ve footprint çizimleri/serbest metinler seçeneklerinden
   istediklerimi seçerim. Referans/değer yazılarının biçimi ve yerel konumu ayrıca
   seçilebilir; **varsayılan olarak kapalıdır** ve yazı içerikleri hedefe ait kalır.
5. **3 · Düzenlemeleri önizle** ile hedef listesini, değişecek pad sayısını, çizim
   sayılarını, pad konumlarını, boyutlarını ve ağlarını kontrol ederim.
   **Tüm geometri ve pad ayarlarını göster** seçeneği önerilen pad/çizim/yazı
   kayıtlarını ayrıntılı gösterir. Bu sayısal bir önizlemedir; DRC kontrolü değildir.
6. Uyumsuz hedefleri kaldırıp yeniden önizlerim. Listedeki tüm hedefler uyumlu
   olduğunda **4 · Footprint düzenlemelerini uygula** açılır. PCB’yi kontrol edip
   DRC çalıştırırım; uygun bulduğumda kaydederim. PCB düzenleyicisinde **Ctrl+Z**
   bütün hedeflere yapılan değişikliği tek adımda geri alır.

İsteğe bağlı öneriler footprint kimliği, değer/isim ve açıklamaya göre gerekçeli
listelenir. Yalnız benim işaretlediğim öneriler eklenir. Seçili hedefleri veya
tüm hedefleri kaldırabilirim; kaynak korunur. İki sekmenin kaynak/hedef listeleri ayrıdır.

## Aktarım kapsamı

- **Padler:** footprint merkezine göre konum, açı, pad türü ve tam padstack:
  boyut/şekil, delik, katmanlar, maske/pasta, özel pad geometrisi ve termal/zone
  ayarları. Padin clearance override değeri de aktarılır. Mevcut pad numarasıyla
  eşleştirme yapılır; kaynak ağları veya UUID’leri kullanılmaz. Override yoksa
  yok olarak kalır; miras alınan kural açıkça sıfıra dönüştürülmez.
- **Çizimler/serbest metinler:** hedefteki desteklenen yerel çizimler kaynak
  geometrisiyle değiştirilir ve hedefin kart koordinatlarına dönüştürülür.
  Ön/arka silkscreen, fabrication, courtyard, maske, pasta ve Dwgs/Cmts/Eco1/Eco2
  kullanıcı katmanları desteklenir. Uygun sıra/türdeki hedef çizim kimlikleri
  mümkün olduğunca korunur; eklenen çizimler hedefe özgü yeni kimlik alır.
- **İsteğe bağlı referans/değer biçimi:** görünüm ve yerel konum kopyalanır;
  hedefin alan kimliği, adı, referans ve değer metni korunur.
- **Her zaman korunanlar:** hedef footprintin UUID’si, kütüphane kimliği, konumu,
  açısı, kart yüzü, kilidi, referansı/değeri, şema ve sayfa bağlantıları; her padin
  tam ağ kaydı, UUID’si ve sembol pin bilgileri. Hedefteki 3B modeller, özel
  alanlar, footprint kuralları/özellikleri, net-tie tanımları ve yerel zone öğeleri korunur.
- Kütüphane, şema, yol, via ve kart zone öğelerine müdahale edilmez. Kart otomatik kaydedilmez.

## Uyumluluk ve kontroller

Pad aktarımı seçiliyse kaynak ve hedefin **pad eşleşmeleri aynı** olmalıdır. Ön yüzden arkaya
ve arkadan öne aktarım desteklenir: yerel geometri KiCad kurallarına göre
yansıtılır, ön/arka katmanlar dönüştürülür. Hedefin yüzü ve açısı korunur. İç bakır
katmanları güncel kartın bakır katman sayısına göre eşleştirilir.
Numaralı padler benzersiz numaralarıyla eşleştirilir. Yalnız pasta katmanında
bulunan, ağa bağlı olmayan açıklıklar en yakın numaralı bakır pad ve göreli kart
yüzüyle eşleştirilir; her pad ve pasta katmanı için bir açıklık desteklenir.
Böylece küçük SMD dirençlerdeki ayrı pasta padleri de aktarılabilir. Belirsiz
eşleşmeler ve yinelenen numaralı padler engellenir. Ayrıca tek bir numarasız,
ağa bağlı olmayan mekanik pad desteklenir. Yalnız çizim veya alan biçimi
aktarılırken pad eşleştirmesi yapılmaz; hedef padler aynen korunur.
Courtyard/çizimleri padlere dokunmadan aktarmak için **Pad geometrisi ve ayarları**
seçeneğini kapatırım.
Pad ekleme/silme/yeniden numaralandırma bu sürümün kapsamı dışındadır.
Kilitli hedefler, bilinmeyen footprint alt öğeleri ve bakır/desteklenmeyen
katmandaki çizimler engellenir. Bakır çizim varsa çizim aktarımını kapatıp yalnız
pad aktarımı yapılabilir. 90°’nin katı olmayan açılardaki hedefler de desteklenir.

Uygulamadan hemen önce kaynak/hedeflerin güncel geometri ve bilgileri kontrol
edilir. Önizlemeden sonra değişiklik yaptıysam yeniden önizlerim. İki sekmede de
KiCad 10 işlem kontrolleri geçerlidir: uygulamadan önce şema düzenleyicisini ve
diğer PCB pencerelerini kapatırım; aktif taşıma/çizim işlemlerini ve özellik
pencerelerini bitiririm. Zaman aşımına uğrayan yazma otomatik tekrarlanmaz;
iptal doğrulanamazsa PCB düzenleyicisi yeniden açılana kadar yazma engellenir.

**Daha sonra “Kütüphaneden footprintleri güncelle” işlemi bu yerel değişiklikleri
üzerine yazabilir.** Özellik kütüphanede özel bir override oluşturmaz.

## Kurulum ve doğrulama

[Sürüm sayfasından](https://github.com/MEY-26/kicad-layout-clone/releases/tag/v0.3.2)
`Layout_Clone-0.3.2-pcm.zip` paketini indirip PCM’nin **Dosyadan yükle…**
seçeneğiyle kurarım. Topluluk PCM paketine geçmeden önce eski manuel
`com.sharkesc.layout-clone` kurulumunu yedekleyip kaldırırım; böylece iki
araç çubuğu düğmesi oluşmaz. Güncellemeden sonra eklenti penceresini yeniden açarım.
Yeni kurulumda dil İngilizce gelir; son seçtiğim dil hatırlanır. Araç çubuğu
simgeleri 24/48, ayrı katalog simgesi 64 piksel olarak korunmuştur.

Windows’ta KiCad **10.0.5**, `kicad-python==0.7.1` ve `wxPython==4.2.2` ile
test edildi. İzole API kayıtları ve gerçek wx arayüzüyle regresyon testleri yapıldı.
Ayrı açılan, kaydedilmeyen deneme PCB’sinde gerçek geometri aktarımı, 37° hedef,
yazı biçimi aktarımı, işlem iptali, **tek adımda Undo/Redo** ve mevcut yerleşim
akışı doğrulandı. Canlı PCB/şema/proje dosyalarının hash değerleri değişmedi.
Undo resmi IPC komutuyla çalıştırıldı; klavyeden tuş gönderilmedi.

Kontrol edilen API kaynakları:
[KiCad 10.0.5 footprint serileştirmesi](https://gitlab.com/kicad/code/kicad/-/blob/10.0.5/pcbnew/footprint.cpp)
ve [Undo/Redo komutları](https://gitlab.com/kicad/code/kicad/-/blob/10.0.5/common/tool/actions.cpp).

0.3.1 sürümünde iki aktarım yönü de KiCad’in bağımsız C++ çevirme işlemiyle
karşılaştırıldı. Asimetrik chamfer/trapezoid/özel padler, serbest metin ve
referans/değer biçimi eşleşti; gerçek aktarım ve Undo doğrulandı. Dil değişince
onay kutularının genişliği yeniden hesaplanarak Türkçe etiket kesilmesi giderildi.

0.3.2 düzeltmesi ayrı, numarasız pasta açıklıklarını numaralı bakır padleriyle
eşleştirir. Courtyard ekleme/kaldırma, iki aktarım yönü ve karşı yüzler dahil
91 test geçti. Açık karttaki R1/R2 için iki yönde yalnız önizleme doğrulandı;
kart üzerinde değişiklik uygulanmadı.
