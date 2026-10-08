"""English/Turkish UI catalogue and per-user language preference.

Turkish source messages remain stable keys, including existing diagnostics.
Only UI strings are passed here; references, values, nets and geometry are not.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
from string import Formatter

MESSAGES = {
    'Yerleşim Kopyala': 'Layout Clone',
    'Bir yerleşim. Birden fazla devre.': 'One layout. Multiple circuits.',
    'Kaynak yerleşim': 'Source layout', 'Hedef gruplar': 'Target groups',
    'Referans komponent': 'Anchor footprint', 'Hedef referans komponent': 'Target anchor footprint',
    'Grup üyeleri  ·  R1-R5 yazılabilir': 'Group members  ·  ranges such as R1-R5 supported',
    '1 · PCB kaynak seçimini al': '1 · Capture PCB source selection',
    '2 · PCB hedef seçimini al ve ekle': '2 · Capture and add PCB target',
    'Diğer kaynak seçenekleri': 'More source options',
    'İsteğe bağlı: kaynak grup öner': 'Optional: suggest source group',
    'Seçili KiCad grubunu kullan': 'Use selected KiCad group',
    'Elle ekleme ve grup önerisi': 'Manual entry and group suggestions',
    'İsteğe bağlı: aynı büyüklükte hedef öner': 'Optional: suggest matching target group',
    'Hedef grubunu listeye ekle': 'Add target group to list',
    'Seçili hedefi kaldır': 'Remove selected target',
    'Tüm hedefleri kaldır': 'Remove all targets',
    'Hedef listesini ve önizlemeleri temizler. Kaynak grubunu korur; PCB’deki parçaları değiştirmez.':
        'Clears the target list and previews. Keeps the source group; does not change footprints on the PCB.',
    'PCB’de kaynak seç → 1. düğme.\nEsc ile seçimi kaldır; hedef seç → 2. düğme.\nBirden fazla hedefi sırayla ekleyebilirsin.':
        'Select source on PCB → button 1.\nPress Esc; select target → button 2.\nAdd more target groups in the same way.',
    'Dönüş ayarları': 'Transform settings', 'Ek dönüş': 'Extra rotation',
    'Ayna yok': 'No mirror',
    'Merkezleri yerel X ekseninde aynala': 'Mirror centres across local X axis',
    'Merkezleri yerel Y ekseninde aynala': 'Mirror centres across local Y axis',
    '0°: hedef referans yerinde kalır. Ayna yalnız merkezleri yansıtır; pin düzeni ve kart yüzü korunur.':
        '0° keeps the target anchor in place. Mirroring reflects centres only; pin layout and board side are preserved.',
    '03  Eşleştirme ve önizleme': '03  Matching and preview',
    '3 · Eşleştir ve önizle': '3 · Match and preview',
    '4 · Tüm hedeflere uygula': '4 · Apply to all targets',
    'Kaynak: {n} komponent': 'Source: {n} footprints',
    'Hedef: {n} / kaynak: {s} komponent': 'Target: {n} / source: {s} footprints',
    '{n} hedef  ·  {c} komponent': '{n} targets  ·  {c} footprints',
    'Referans': 'Anchor', 'Parça': 'Parts', 'Durum': 'Status',
    'Kaynak': 'Source', 'Hedef': 'Target', 'Değer': 'Value', 'Eşleşme': 'Match',
    'Açı': 'Angle', 'Yüz': 'Side',
    'Kesin': 'Unique', 'Seçim gerekli': 'Choose match', 'Doğrulandı': 'Verified',
    'Uçlar +180°': 'Pins +180°', 'Önizleme gerekli': 'Preview required',
    'Eşleştirme hazır': 'Matching ready', 'Uygulandı': 'Applied',
    'Önizleme burada görünecek': 'Your layout preview will appear here',
    'PCB’den kaynak parçaları ve hedef grupları seç.': 'Select the source footprints and target groups on the PCB.',
    'Eşleştir ve önizle ile her grubun yeni yerleşimini kontrol et.': 'Use Match and preview to review each group’s new placement.',
    'Gri: mevcut   Turkuaz: yeni merkez/yön   Sarı: referans': 'Grey: current   Teal: new centre/orientation   Yellow: anchor',
    'Belirsiz satırlarda hedef seç. Her hedef yalnızca bir kez kullanılabilir.':
        'Choose a target in ambiguous rows. Each target may only be used once.',
    'Eşdeğer parçalar için geçerli öneriyi kullan': 'Use valid suggestion for equivalent parts',
    'Elektriksel olarak ayırt edilemeyen parçalar için bağlantılarla tutarlı bir eşleştirme seçer. Satırları uygulamadan önce kontrol edebilirsin.':
        'Chooses a connectivity-consistent mapping for electrically indistinguishable parts. Review the rows before applying.',
    'Sarı satırlarda eşleşen hedef komponentleri seç.': 'Choose the matching target footprints in the yellow rows.',
    '{n} komponent eşleşti. Çizim merkezleri ve açıları gösterir; pad/courtyard çakışma kontrolü değildir.':
        '{n} footprints matched. The drawing shows centres and angles; it does not check pad/courtyard collisions.',
    'KiCad bağlantısı hazırlanıyor…': 'Connecting to KiCad…', 'PCB okunuyor…': 'Reading PCB…',
    'PCB seçimi okunuyor…': 'Reading PCB selection…',
    'Bağlantı yapıları eşleştiriliyor…': 'Matching connectivity…',
    'Yerleşim tek işlem olarak uygulanıyor…': 'Applying layout as one transaction…',
    'PCB’de kaynak parçaları seçip 1. düğmeye, ardından hedef parçaları seçip 2. düğmeye bas.':
        'Select source footprints on the PCB and press button 1; then select target footprints and press button 2.',
    'Kaynak ve hedef gruplarını seç.': 'Select source and target groups.',
    'İşlem sürüyor…': 'Working…',
    'Hazır · Önizlemeyi kontrol edip uygula.': 'Ready · Review the preview and apply.',
    'Sarı satırlardaki eşleşmeleri tamamla.': 'Complete the matches in the yellow rows.',
    'Hedefler eklendi · Önizleme oluştur.': 'Targets added · Create a preview.',
    'Tüm hedefler ve önizlemeler temizlendi. Kaynak grup korundu; yeni hedefler seçebilirsin.':
        'All targets and previews cleared. The source group was kept; select new targets.',
    'Önizleme hazır. Sarı eşleşmeleri seç veya elektriksel olarak geçerli öneriyi kullan.':
        'Preview ready. Complete the yellow matches or use the electrically valid suggestion.',
    'İşlem sürüyor; tamamlandıktan sonra pencereyi kapatabilirsin.': 'An operation is running; close the window after it finishes.',
    '{n} seçili komponent alındı; referans {ref}. Referans ve grup listesini kontrol et.':
        'Captured {n} selected footprints; anchor {ref}. Check the anchor and group list.',
    '{n} seçili komponent alındı. Birden fazla uygun referans var; {field} alanından seç.':
        'Captured {n} selected footprints. Multiple anchors are suitable; choose one in the {field} field.',
    '{n} parçalık hedef önerildi; listeyi kontrol edip ekle.': 'Suggested a {n}-part target; check the list and add it.',
    '{ref}: {n} hedef komponent listeye eklendi. Başka hedef seçebilir veya 3 · Eşleştir ve önizle’ye basabilirsin.':
        '{ref}: added {n} target footprints. Select another target or press 3 · Match and preview.',
    '{n} komponent yerleşimi uygulandı. KiCad içinde Ctrl+Z ile tek adımda geri alabilirsin. Sonrasında DRC çalıştır.':
        'Applied placement to {n} footprints. Undo in one step with Ctrl+Z in KiCad. Run DRC afterwards.',
    'Kaynak {s}, hedef {n} komponent içeriyor. Sayıları eşit olmalı. PCB’de Esc ile eski seçimi kaldırıp yalnız {s2} hedef komponenti seç; otomatik parça eklenmez.':
        'Source has {s} footprints; target has {n}. Counts must match. Press Esc on the PCB and select only {s2} target footprints; no parts are added automatically.',
    'PCB içinde bir komponent veya komponent grubu seç.': 'Select a footprint or footprint group on the PCB.',
    'Önce kaynak referansı seç.': 'Choose a source anchor first.',
    'Seçimde kaynak referansa denk bir komponent yok.': 'The selection contains no footprint matching the source anchor.',
    'Kaynak grup listesini ve referansını kontrol et.': 'Check the source group list and anchor.',
    'Seçilen hedef kaynakla veya eklenmiş bir hedefle çakışıyor. PCB’de Esc ile eski seçimi kaldırıp yalnız yeni hedef parçalarını seç.':
        'The selected target overlaps the source or an existing target. Press Esc on the PCB and select only the new target footprints.',
    'Kaynakla aynı parça sayısı ve türlerinde güvenilir bir hedef önerilemedi. PCB’de hedef parçalarını seçip 2. düğmeye bas.':
        'No reliable target with the source’s part counts and types could be suggested. Select the target footprints on the PCB and press button 2.',
    'Önce PCB bağlantısını yükle.': 'Connect to the PCB first.',
    'Kaynak referans komponenti seç; kendi grubunun içinde olmalı.': 'Choose a source anchor; it must belong to the source group.',
    'Hedef referans grup listesinde olmalı.': 'The target anchor must be in its group list.',
    'Hedef referans kaynak referansla aynı tür, değer ve kılıfta olmalı.': 'The target anchor must have the source anchor’s type, value and footprint.',
    'Listeye en az bir hedef grup ekle.': 'Add at least one target group to the list.',
    'Hedef grubundaki bazı komponentler kartta yok.': 'Some target footprints are no longer on the board.',
    'Önce geçerli bir önizleme oluştur.': 'Create a valid preview first.',
    'KiCad meşgul. PCB içindeki aktif taşıma/çizim işlemini veya açık özellik penceresini bitirip yeniden dene.':
        'KiCad is busy. Finish the active move/drawing operation or close the properties dialog, then try again.',
    'KiCad bağlantısı veya eklenti işlemi başarısız:\n': 'KiCad connection or plugin operation failed:\n',
    'Geçersiz komponent aralığı: ': 'Invalid footprint range: ',
    'Kartta bulunmayan referanslar: ': 'References not found on the board: ',
    'Grupların bağlantı yapıları eşleşmiyor. Grup listelerini ve ortak ağ sınırlarını kontrol et.':
        'The groups’ connectivity does not match. Check their member lists and shared-net boundaries.',
    'Grup boyutları farklı: kaynak {s}, hedef {n} komponent.': 'Group sizes differ: source {s}, target {n} footprints.',
    'Kaynak ve hedef gruplar ortak komponent içeremez.': 'Source and target groups cannot share footprints.',
    'Referans komponent kendi grubunun içinde olmalı.': 'Each anchor footprint must belong to its group.',
    'Referans komponentlerin değeri, kılıfı, pin sayısı ve kart yüzü aynı olmalı.':
        'Anchor footprints must have the same value, footprint, pin count and board side.',
    'Grupların parça değerleri, kılıfları veya kart yüzleri eşleşmiyor.':
        'The groups’ part values, footprints or board sides do not match.',
    'Bağlantı eşleştirmesi çok karmaşık. Daha küçük bir grup veya daha belirgin bir referans seç.':
        'Connectivity matching is too complex. Choose a smaller group or a more distinctive anchor.',
    'Gruplar pin bağlantılarına göre eşdeğer değil.': 'The groups are not equivalent by pin connectivity.',
    'Her kaynak komponent tam bir kez, farklı bir hedef komponentle eşleşmeli.':
        'Each source footprint must map exactly once to a distinct target footprint.',
    'Referans komponent eşleşmesi değiştirilemez.': 'The anchor mapping cannot be changed.',
    'Seçilen eşleşme doğrulanamadı. Grubu küçült.': 'The chosen mapping could not be verified. Use a smaller group.',
    'Seçilen eşleşmeler bağlantılarla tutarlı değil.': 'The chosen mapping is inconsistent with the connectivity.',
    'Geçersiz yerleşim dönüşümü.': 'Invalid placement transform.',
    '{ref} kilitli. Taşımak için önce KiCad içinde kilidini kaldır.': '{ref} is locked. Unlock it in KiCad before moving it.',
    'Hedef gruplar kaynakla veya birbirleriyle çakışıyor: ': 'Target groups overlap the source or each other: ',
    ': aynı pin numarası farklı ağlara bağlı.': ': the same pin number is connected to different nets.',
    '{ref} desteklenmeyen bir kılıf öğesi içeriyor: {items}': '{ref} contains unsupported footprint items: {items}',
    'KiCad bağlantısı yenilenemedi.': 'Could not reconnect to KiCad.',
    'Açık PCB değişti. Eklentiyi yeni kart için yeniden aç.': 'The open PCB has changed. Reopen the plugin for the new board.',
    'Kartta yinelenen referanslar var; önce numaralandırmayı düzelt.': 'The board has duplicate references; fix the numbering first.',
    'İç içe KiCad gruplarında döngü tespit edildi.': 'A cycle was found in nested KiCad groups.',
    'Açık şema düzenleyicisi kontrol edilemedi; taşıma başlatılmadı. Ayrıntı: ': 'Could not check open schematic editors; no move was started. Details: ',
    'Şema düzenleyicisi açık. KiCad 10 IPC hatası bu durumda taşıma başlarken KiCad’i kapatabiliyor (hata kaydı #25322). Şemadaki işini kaydedip yalnız şema düzenleyicisini kapat; PCB açık kalsın. Sonra yeniden önizleyip uygula. Taşıma başlatılmadı.':
        'The schematic editor is open. A KiCad 10 IPC bug can crash KiCad when a move starts in this state (issue #25322). Save your schematic and close only the schematic editor; keep the PCB open. Then preview and apply again. No move was started.',
    'API sunucusunda yalnız bu PCB düzenleyicisi açık olmalı. Diğer PCB pencerelerindeki işini kaydedip kapat; taşıma başlatılmadı.':
        'Only this PCB editor should be open on the API server. Save and close other PCB editors; no move was started.',
    'Önceki işlemin iptali doğrulanamadı. PCB yerleşimini kontrol et; KiCad PCB düzenleyicisini yeniden açtıktan sonra tekrar dene.':
        'Cancellation of the previous operation could not be verified. Check the PCB placement and reopen the KiCad PCB editor before retrying.',
    'Yerleşim listesi boş veya aynı hedef birden fazla kez kullanılmış.': 'The placement list is empty or a target is used more than once.',
    'PCB önizlemeden sonra değişti. Önizlemeyi yeniden oluştur.': 'The PCB changed after the preview. Create a new preview.',
    'Hedef komponent artık bulunamıyor: ': 'Target footprint no longer found: ',
    'Kilitli komponent: ': 'Locked footprint: ', 'Kart yüzü önizlemeden sonra değişti: ': 'Board side changed after the preview: ',
    'KiCad tüm komponentleri güncelleyemedi.': 'KiCad could not update all footprints.',
    'KiCad istenen yerleşimi doğrulamadı: ': 'KiCad did not confirm the requested placement: ',
    'KiCad yanıtı alınamadı ({stage}, {seconds} sn). {rest}': 'No KiCad reply ({stage}, {seconds} s). {rest}',
    'Bağlantı/işlem iptali doğrulanamadı. PCB yerleşimini kontrol et; aktif taşıma veya özellik penceresini bitir. KiCad PCB düzenleyicisini yeniden açman gerekebilir. Ayrıntı: ':
        'Reconnection/cancellation could not be verified. Check the PCB placement and finish any active move or properties dialog. You may need to reopen the KiCad PCB editor. Details: ',
    'Komponent güncelleme çağrısı gönderilmedi.': 'No footprint update request was sent.',
    'Yarım kalan taşıma işlemi iptal edildi; değişiklikler geri alındı.': 'The incomplete move was cancelled; changes were rolled back.',
    'İşlemin sonucu kesinleştirilemedi; tamamlanmış olabilir. PCB yerleşimini kontrol et.': 'The operation’s result could not be confirmed; it may have completed. Check the PCB placement.',
    'Bağlantı yenilendi. PCB içindeki aktif işlemi/özellik penceresini bitirip yeniden önizle. Taşıma otomatik tekrarlanmadı.':
        'Reconnected. Finish any active operation/properties dialog in the PCB editor and preview again. The move was not replayed automatically.',
    'Bu istemciye ait açık işlem bulunamadı.': 'No open transaction was found for this client.',
    'Taşıma başarısız: {error}. İptal doğrulanamadı: {cleanup}. PCB yerleşimini kontrol et.':
        'Move failed: {error}. Cancellation could not be verified: {cleanup}. Check the PCB placement.',
    'KiCad PCB düzenleyicisiyle bağlantı kurulamadı.\nPCB açık olmalı ve Tercihler → Genel → API içindeki API sunucusu etkin olmalı.\n\n':
        'Could not connect to the KiCad PCB editor.\nOpen a PCB and enable the API server in Preferences → Common → API.\n\n',
    'PCB bağlantısı': 'PCB connection', 'bağlantıyı yenileme': 'reconnecting',
    'komponentleri okuma': 'reading footprints', 'KiCad gruplarını okuma': 'reading KiCad groups',
    'PCB seçimini okuma': 'reading PCB selection', 'yarım kalan işlemi iptal etme': 'cancelling incomplete operation',
    'açık şema düzenleyicisini kontrol etme': 'checking open schematic editors',
    'açık PCB düzenleyicisini kontrol etme': 'checking open PCB editors',
    'taşıma işlemini başlatma': 'starting move transaction',
    'komponent yerleşimini güncelleme': 'updating footprint placement',
    'taşıma işlemini tamamlama': 'finishing move transaction',
    'Yerleşim Kopyala: bağlantıya göre grup yerleşimi': 'Layout Clone: connectivity-matched group placement',
}


def preferences_path():
    base = Path(os.environ.get('LOCALAPPDATA') or os.environ.get('XDG_CONFIG_HOME') or Path.home()/'.config')
    return base/'shark-layout-clone'/'preferences.json'


def read_language(path=None):
    try:
        language = json.loads(Path(path or preferences_path()).read_text(encoding='utf-8')).get('language')
        return language if language in ('en', 'tr') else 'en'
    except (OSError, ValueError, TypeError, AttributeError):
        return 'en'


_language = read_language()


def get_language():
    return _language


def set_language(language, persist=False, path=None):
    global _language
    if language not in ('en', 'tr'):
        raise ValueError('Unsupported language')
    if persist:
        target = Path(path or preferences_path())
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix('.tmp')
        temporary.write_text(json.dumps({'language': language}), encoding='utf-8')
        temporary.replace(target)
    _language = language


def _template_pattern(message):
    parts, names = [], []
    for literal, name, spec, conversion in Formatter().parse(message):
        parts.append(re.escape(literal))
        if name is not None:
            names.append(name)
            parts.append('(.*?)')
    return re.compile(''.join(parts), re.DOTALL), names


_templates = [(*_template_pattern(source), english) for source, english in MESSAGES.items() if '{' in source]
_literals = {source: english for source, english in MESSAGES.items() if '{' not in source}
_literal_pattern = re.compile('|'.join(re.escape(s) for s in sorted(_literals, key=len, reverse=True)))


def tr(message, language=None):
    """Translate static and formatted diagnostics without touching PCB data."""
    message = str(message)
    language = language or _language
    if language == 'tr':
        return message
    if message in _literals:
        return _literals[message]
    for pattern, names, english in _templates:
        match = pattern.fullmatch(message)
        if match:
            result = english.format(**{name: tr(value, language) for name, value in zip(names, match.groups())})
            return re.sub(r'\b1 (footprints|targets)\b', lambda m: '1 '+m.group(1)[:-1], result)
    return _literal_pattern.sub(lambda match: _literals[match.group()], message)
