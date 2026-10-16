# Layout Clone 0.3.5

Fix board reading for repeated no-connect pad numbers, such as a USB-C socket's
four `SH` shield pads with separate KiCad-generated unconnected net names.
Only a pad marked `symbol_pin.no_connect` whose net name starts with
`unconnected-(` is treated as open in the local matching model.

Real PCB pad data, nets, pin metadata, the schematic and connections stay
unchanged. No pads are renumbered and no nets are renamed. Genuine conflicting
nets still reject repeated pad numbers. Footprint Edits geometry copying still
requires unique numbered pads; this release does not broaden that operation.

60 public source/package tests passed, including 10 new adapter regressions
using real IPC protobuf objects. The new coverage verifies:

- Four repeated no-connect `SH` pads are accepted.
- Repeated pad numbers assigned to `GND` and `VBUS` are rejected.
- A name starting with `unconnected-(` does not bypass the check without a
  no-connect mark.
- A connected/no-connect mixture on the same pad number is rejected.
- Different unconnected pins are not treated as electrically connected.
- Reading does not change the original pad/footprint data.

No new live IPC or native Undo/Redo checks were run for this read-only fix.
Published 0.3.4 and older archives remain unchanged.

Download `Layout_Clone-0.3.5-pcm.zip` and use **KiCad Plugin and Content Manager
→ Install from File…**. Close and relaunch the plugin window after updating.
Windows / KiCad 10.0 / IPC / testing release. The official catalogue currently
lists 0.3.3 and 0.3.2; the newer metadata update awaits review and a refresh.

## Türkçe

USB-C soketinin dört `SH` gövde padi gibi aynı numaralı bağlantısız padlerin,
KiCad'in verdiği ayrı otomatik ağ adları nedeniyle kartın okunmasını engellemesi
düzeltildi. Yalnız no-connect işaretli ve ağ adı `unconnected-(` ile başlayan
padler, bellekteki eşleştirme modelinde bağlantısız sayılır.

Gerçek PCB pad verileri, ağlar, pin bilgileri, şema ve bağlantılar değiştirilmez;
pad numarası veya ağ adı değiştirilmez. Gerçek ağ çakışmaları reddedilmeye devam
eder. Footprint Düzenlemeleri'nde geometri aktarımı için benzersiz pad numarası
gerekliliği aynı kalır.

10 yeni regresyon dahil 60 açık kaynak/paket testi geçti. Testlerde dört
bağlantısız `SH` padinin kabulü, `GND`/`VBUS` çakışmasının reddi, no-connect
işareti olmadan otomatik görünümlü ağ adının kontrolü aşamaması, bağlı ve
bağlantısız pad karışımının reddi, farklı açık pinlerin birbirine bağlı
sayılmaması ve okuma sırasında gerçek verinin değişmemesi doğrulandı.
Yeni canlı IPC veya yerel Undo/Redo testi yapılmadı. Önceki yayımlanmış paketler
değiştirilmedi.

`Layout_Clone-0.3.5-pcm.zip` paketini **Plugin and Content Manager → Install from
File…** ile kur; ardından eklenti penceresini kapatıp yeniden aç. Windows /
KiCad 10.0 IPC test sürümüdür. Resmi katalogda şu anda 0.3.3 ve 0.3.2 bulunur;
yeni sürümler metadata incelemesini ve katalog yenilemesini bekler.
