"""Modeless English/Turkish UI; the PCB remains selectable while open."""
from __future__ import annotations

from dataclasses import dataclass, field
from collections import Counter
from datetime import datetime, timezone
import math
import threading
import traceback
from pathlib import Path
import tempfile

import wx
import wx.grid
from wx.lib.scrolledpanel import ScrolledPanel
from wx.lib.buttons import GenButton

from core import (VERSION, LayoutError, discover_group, match_groups, parse_refs,
                  plan_placement, ref_key, validate_batch)
from i18n import tr, get_language, set_language


COLORS = dict(bg='#eef2f6', card='#ffffff', text='#24364b', muted='#62748a',
              line='#dce4ed', accent='#087f83', soft='#e6f3f2', header='#172b40',
              amber='#fff2cc', danger='#a44242')


def set_text(control, message):
    control._source_label = message
    control.SetLabel(tr(message))


def localize_tree(window):
    if isinstance(window, (wx.StaticText, wx.Button, GenButton, wx.CollapsiblePane)):
        source = getattr(window, '_source_label', window.GetLabel())
        set_text(window, source)
    tip = window.GetToolTip()
    if tip:
        source = getattr(window, '_source_tip', tip.GetTip())
        window._source_tip = source
        window.SetToolTip(tr(source))
    # CollapsiblePane owns its caption button; translating that child again
    # would cache the already translated caption and undo later switches.
    children = [window.GetPane()] if isinstance(window, wx.CollapsiblePane) else window.GetChildren()
    for child in children:
        localize_tree(child)


def text_style(control, size=None, bold=False, color=None):
    font = control.GetFont()
    if size:
        font.SetPointSize(size)
    font.SetWeight(wx.FONTWEIGHT_BOLD if bold else wx.FONTWEIGHT_NORMAL)
    control.SetFont(font)
    control.SetForegroundColour(color or COLORS['text'])
    return control


class ActionButton(GenButton):
    """Small themed button retaining wx keyboard, focus and disabled handling."""
    def __init__(self, parent, label, handler, tone='neutral'):
        super().__init__(parent, label=label, style=wx.BORDER_NONE)
        self.tone = tone
        self.SetBezelWidth(0)
        self.SetMinSize((-1, self.FromDIP(34)))
        text_style(self, bold=tone in ('primary', 'accent'))
        self.SetBackgroundColour(COLORS['accent'] if tone == 'primary' else
                                 COLORS['soft'] if tone == 'accent' else '#f1f4f8')
        self.SetForegroundColour('#ffffff' if tone == 'primary' else
                                 COLORS['accent'] if tone == 'accent' else
                                 COLORS['danger'] if tone == 'danger' else COLORS['text'])
        self.Bind(wx.EVT_BUTTON, handler)

    def Enable(self, enable=True):
        changed = super().Enable(enable)
        tone = getattr(self, 'tone', 'neutral')
        self.SetBackgroundColour('#e7edf2' if not enable else
                                 COLORS['accent'] if tone == 'primary' else
                                 COLORS['soft'] if tone == 'accent' else '#f1f4f8')
        self.SetForegroundColour('#8392a1' if not enable else
                                 '#ffffff' if tone == 'primary' else
                                 COLORS['accent'] if tone == 'accent' else
                                 COLORS['danger'] if tone == 'danger' else COLORS['text'])
        self.Refresh()
        return changed


class EmptyPreview(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.SetBackgroundColour(COLORS['card'])
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.Bind(wx.EVT_PAINT, self.draw)

    def draw(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        dc.SetBackground(wx.Brush(COLORS['card']))
        dc.Clear()
        w, h = self.GetClientSize()
        cx, cy = w//2, max(92, h//2-55)
        # A native vector motif: one source and two repeated component groups.
        for index, x in enumerate((cx-142, cx-20, cx+102)):
            accent = COLORS['accent'] if index == 0 else '#8aa5b9'
            dc.SetPen(wx.Pen('#d7e2eb', 1))
            dc.SetBrush(wx.Brush(COLORS['soft'] if index == 0 else '#f5f8fb'))
            dc.DrawRoundedRectangle(x, cy-47, 92, 92, 12)
            dc.SetPen(wx.Pen(accent, 2))
            dc.DrawLines([(x+25,cy-20),(x+46,cy-20),(x+46,cy+20),(x+67,cy+20)])
            dc.DrawLine(x+25,cy+20,x+46,cy+20)
            for px, py in ((x+25,cy-20),(x+67,cy+20),(x+25,cy+20)):
                dc.SetBrush(wx.Brush(accent))
                dc.DrawRoundedRectangle(px-6,py-5,12,10,2)
            dc.SetBrush(wx.Brush('#edb94c'))
            dc.DrawCircle(x+46,cy,6)
            if index < 2:
                dc.SetPen(wx.Pen('#aebfce', 2))
                dc.DrawLine(x+98,cy,x+112,cy)
                dc.DrawLine(x+107,cy-4,x+112,cy)
                dc.DrawLine(x+107,cy+4,x+112,cy)
        font = self.GetFont()
        font.SetPointSize(15); font.SetWeight(wx.FONTWEIGHT_BOLD)
        dc.SetFont(font); dc.SetTextForeground(COLORS['text'])
        title = tr('Önizleme burada görünecek')
        tw, th = dc.GetTextExtent(title)
        dc.DrawText(title,cx-tw//2,cy+75)
        font.SetPointSize(10); font.SetWeight(wx.FONTWEIGHT_NORMAL)
        dc.SetFont(font); dc.SetTextForeground(COLORS['muted'])
        for i, line in enumerate(('PCB’den kaynak parçaları ve hedef grupları seç.',
                                  'Eşleştir ve önizle ile her grubun yeni yerleşimini kontrol et.')):
            line = tr(line)
            tw, th = dc.GetTextExtent(line)
            dc.DrawText(line,cx-tw//2,cy+112+i*23)


@dataclass
class Target:
    anchor: str
    refs: tuple
    match: object = None
    mapping: dict = field(default_factory=dict)


class Plot(wx.Panel):
    def __init__(self, parent, components, poses, anchor):
        super().__init__(parent, size=(-1, 180))
        self.SetMinSize((-1, 88))
        self.components, self.poses, self.anchor = components, poses, anchor
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.Bind(wx.EVT_PAINT, self.draw)
        self.Bind(wx.EVT_SIZE, lambda event: (self.Refresh(), event.Skip()))

    def draw(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        dc.SetBackground(wx.Brush('#172331'))
        dc.Clear()
        w, h = self.GetClientSize()
        dc.SetPen(wx.Pen('#21374a', 1))
        for x in range(24, w, 32):
            dc.DrawLine(x, 40, x, h)
        for y in range(40, h, 32):
            dc.DrawLine(0, y, w, y)
        points = [(self.components[p.ref].x, self.components[p.ref].y) for p in self.poses]
        points += [(p.x, p.y) for p in self.poses]
        if not points or w < 50 or h < 50:
            return
        lo_x, hi_x = min(x for x, y in points)-1, max(x for x, y in points)+1
        lo_y, hi_y = min(y for x, y in points)-1, max(y for x, y in points)+1
        scale = min((w-48)/max(hi_x-lo_x, 2), (h-54)/max(hi_y-lo_y, 2))
        def pixel(x, y):
            return (round(w/2+(x-(lo_x+hi_x)/2)*scale),
                    round((h+12)/2+(y-(lo_y+hi_y)/2)*scale))
        dc.SetTextForeground('#b9c9da')
        dc.DrawText(tr('Gri: mevcut   Turkuaz: yeni merkez/yön   Sarı: referans'), 9, 8)
        dc.SetPen(wx.Pen('#51677a', 1))
        dc.SetBrush(wx.Brush('#51677a'))
        for p in self.poses:
            old = self.components[p.ref]
            ox, oy = pixel(old.x, old.y)
            nx, ny = pixel(p.x, p.y)
            dc.DrawLine(ox, oy, nx, ny)
            dc.DrawCircle(ox, oy, 3)
        for p in self.poses:
            x, y = pixel(p.x, p.y)
            color = '#ffd166' if p.ref == self.anchor else '#53d9ce'
            dc.SetPen(wx.Pen(color, 2))
            dc.SetBrush(wx.Brush(color))
            dc.DrawCircle(x, y, 4 if p.ref == self.anchor else 3)
            rad = math.radians(p.angle)
            dc.DrawLine(x, y, x+round(10*math.cos(rad)), y-round(10*math.sin(rad)))
            if len(self.poses) <= 26 or p.ref == self.anchor:
                dc.SetTextForeground(color)
                dc.DrawText(p.ref, x+5, y+3)


class TargetPage(wx.Panel):
    def __init__(self, parent, target, components, mirror, rotation, changed):
        super().__init__(parent)
        self.SetBackgroundColour(COLORS['card'])
        self.target = target
        self.components = components
        self.mirror, self.rotation = mirror, rotation
        self.changed = changed
        match = target.match
        self.grid = wx.grid.Grid(self)
        self.grid.CreateGrid(len(match.source), 8)
        self.grid.SetDefaultCellBackgroundColour(COLORS['card'])
        self.grid.SetDefaultCellTextColour(COLORS['text'])
        self.grid.SetGridLineColour(COLORS['line'])
        self.grid.SetLabelBackgroundColour('#edf3f8')
        self.grid.SetLabelTextColour(COLORS['muted'])
        self.grid.SetDefaultRowSize(30)
        self.grid.SetColLabelSize(34)
        self.grid.SetSelectionBackground('#d6eceb')
        self.grid.SetSelectionForeground(COLORS['text'])
        self.grid.SetMinSize((360, 120))
        for i, name in enumerate(('Kaynak', 'Hedef', 'Değer', 'Eşleşme', 'X (mm)', 'Y (mm)', 'Açı', 'Yüz')):
            self.grid.SetColLabelValue(i, name)
        self.grid.SetRowLabelSize(36)
        for row, source in enumerate(match.source):
            for col in range(8):
                self.grid.SetCellBackgroundColour(row, col, '#f6f9fc' if row % 2 else COLORS['card'])
            options = match.candidates[source]
            self.grid.SetCellValue(row, 0, source)
            self.grid.SetCellValue(row, 2, components[source].value)
            selected = options[0] if len(options) == 1 else target.mapping.get(source, '')
            self.grid.SetCellValue(row, 1, selected)
            self.grid.SetCellEditor(row, 1, wx.grid.GridCellChoiceEditor(['']+list(options), allowOthers=False))
            self.grid.SetCellValue(row, 3, tr('Kesin' if len(options) == 1 else 'Seçim gerekli'))
            if len(options) > 1:
                self.grid.SetCellBackgroundColour(row, 1, COLORS['amber'])
            if len(options) == 1 or source == match.source_anchor:
                self.grid.SetReadOnly(row, 1)
            for col in (0, 2, 3, 4, 5, 6, 7):
                self.grid.SetReadOnly(row, col)
        for col, width in enumerate((65, 72, 130, 110, 84, 84, 68, 48)):
            self.grid.SetColSize(col, width)
        self.grid.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.on_changed)
        self.plot_container = wx.Panel(self)
        self.plot_sizer = wx.BoxSizer(wx.VERTICAL)
        self.plot_container.SetSizer(self.plot_sizer)
        self.note = wx.StaticText(self, label='Belirsiz satırlarda hedef seç. Her hedef yalnızca bir kez kullanılabilir.')
        text_style(self.note, color=COLORS['muted'])
        self.note.Wrap(max(320, self.GetClientSize().width-20))
        self.fill_button = ActionButton(self, 'Eşdeğer parçalar için geçerli öneriyi kullan', self.use_suggestion, 'accent')
        self.fill_button.SetToolTip('Elektriksel olarak ayırt edilemeyen parçalar için bağlantılarla tutarlı bir eşleştirme seçer. Satırları uygulamadan önce kontrol edebilirsin.')
        self.fill_button.Show(any(len(options) > 1 for options in match.candidates.values()))
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.note, 0, wx.ALL, 7)
        sizer.Add(self.fill_button, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 7)
        sizer.Add(self.grid, 3, wx.EXPAND | wx.ALL, 7)
        sizer.Add(self.plot_container, 2, wx.EXPAND | wx.ALL, 7)
        self.SetSizer(sizer)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.refresh_pose()
        self.localize()

    def localize(self):
        localize_tree(self)
        for col, name in enumerate(('Kaynak', 'Hedef', 'Değer', 'Eşleşme', 'X (mm)', 'Y (mm)', 'Açı', 'Yüz')):
            self.grid.SetColLabelValue(col, tr(name))
        self.refresh_pose()

    def mapping(self):
        return {self.grid.GetCellValue(row, 0): self.grid.GetCellValue(row, 1)
                for row in range(self.grid.GetNumberRows())}

    def refresh_pose(self):
        mapping = self.mapping()
        self.target.mapping = mapping
        self.plot_sizer.Clear(delete_windows=True)
        try:
            if any(not r for r in mapping.values()):
                raise LayoutError('Sarı satırlarda eşleşen hedef komponentleri seç.')
            poses = plan_placement(self.components, self.target.match, mapping, self.mirror, self.rotation)
            self.poses = poses
            self.note_text = f'{len(poses)} komponent eşleşti. Çizim merkezleri ve açıları gösterir; pad/courtyard çakışma kontrolü değildir.'
            set_text(self.note, self.note_text)
            by_source = {p.source_ref: p for p in poses}
            for row in range(self.grid.GetNumberRows()):
                p = by_source[self.grid.GetCellValue(row, 0)]
                for col, value in ((4, f'{p.x:.4f}'), (5, f'{p.y:.4f}'), (6, f'{p.angle:.1f}°'), (7, p.side)):
                    self.grid.SetCellValue(row, col, value)
                self.grid.SetCellValue(row, 3, tr('Uçlar +180°' if p.pin_swap else 'Doğrulandı'))
            self.plot_sizer.Add(Plot(self.plot_container, self.components, poses, self.target.anchor), 1, wx.EXPAND)
        except LayoutError as error:
            self.poses = None
            self.note_text = ValueError.__str__(error)
            set_text(self.note, self.note_text)
            for row in range(self.grid.GetNumberRows()):
                source = self.grid.GetCellValue(row, 0)
                self.grid.SetCellValue(row, 3, tr('Kesin' if len(self.target.match.candidates[source]) == 1 else 'Seçim gerekli'))
                for col in (4, 5, 6, 7):
                    self.grid.SetCellValue(row, col, '')
        self.note.Wrap(max(320, self.GetClientSize().width-20))
        self.Layout()

    def on_size(self, event):
        set_text(self.note, getattr(self, 'note_text', self.note.GetLabel()))
        self.note.Wrap(max(250, self.GetClientSize().width-20))
        self.Layout()
        event.Skip()

    def on_changed(self, event):
        self.refresh_pose()
        self.changed()
        event.Skip()

    def use_suggestion(self, event):
        for row in range(self.grid.GetNumberRows()):
            source = self.grid.GetCellValue(row, 0)
            self.grid.SetCellValue(row, 1, self.target.match.suggestion[source])
        self.refresh_pose()
        self.changed()


class MainFrame(wx.Frame):
    def __init__(self, adapter):
        super().__init__(None, title=f'Yerleşim Kopyala {VERSION} — KiCad', size=(1240, 960))
        self.SetMinSize((1000, 700))
        self.adapter = adapter
        self.snapshot = None
        self.targets = []
        self._source_state = None
        self.pages = []
        self.preview_stamp = None
        self.working = False
        self.closed = False
        self.queue_status = {}
        self._status_source = ''
        self.log_path = Path(tempfile.gettempdir(), 'shark-layout-clone-error.log')
        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour(COLORS['bg'])
        self.panel.SetFont(wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT))
        self.status = self.CreateStatusBar()
        self.set_status('KiCad bağlantısı hazırlanıyor…')
        self.Bind(wx.EVT_CLOSE, self.on_close)
        root = wx.BoxSizer(wx.VERTICAL)
        header = wx.Panel(self.panel)
        header.SetBackgroundColour(COLORS['header'])
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        brand = wx.BoxSizer(wx.VERTICAL)
        title = wx.StaticText(header, label='Yerleşim Kopyala')
        text_style(title, 19, True, '#ffffff')
        subtitle = wx.StaticText(header, label='Bir yerleşim. Birden fazla devre.')
        text_style(subtitle, 10, color='#b7cbdc')
        brand.Add(title, 0, wx.BOTTOM, 4)
        brand.Add(subtitle)
        header_sizer.Add(brand, 1, wx.ALL, 12)
        version = wx.StaticText(header, label=f'KiCad 10  ·  v{VERSION}')
        text_style(version, 10, color='#b7cbdc')
        header_sizer.Add(version, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 22)
        language_box = wx.BoxSizer(wx.VERTICAL)
        language_label = wx.StaticText(header, label='Language / Dil')
        text_style(language_label, color='#b7cbdc')
        self.language = wx.Choice(header, choices=['English', 'Türkçe'], size=(115, -1))
        self.language.SetSelection(0 if get_language() == 'en' else 1)
        self.language.Bind(wx.EVT_CHOICE, self.language_changed)
        language_box.Add(language_label, 0, wx.BOTTOM, 4)
        language_box.Add(self.language)
        header_sizer.Add(language_box, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 16)
        header.SetSizer(header_sizer)
        root.Add(header, 0, wx.EXPAND)
        outer = wx.BoxSizer(wx.HORIZONTAL)
        self.left_panel = ScrolledPanel(self.panel, size=(350, -1), style=wx.VSCROLL)
        self.left_panel.SetBackgroundColour(COLORS['bg'])
        self.left_panel.SetMinSize((335, -1))
        left = wx.BoxSizer(wx.VERTICAL)
        source_card, source_box = self.card(self.left_panel, '01', 'Kaynak yerleşim', 'Kaynak: 0 komponent')
        self.source_count = source_card.subtitle
        text_style(self.source_count, bold=True, color=COLORS['accent'])
        self.source_anchor = wx.ComboBox(source_card, style=wx.CB_READONLY)
        source_box.Add(self.label(source_card, 'Referans komponent'), 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        source_box.Add(self.source_anchor, 0, wx.EXPAND | wx.ALL, 5)
        self.source_group = wx.TextCtrl(source_card, style=wx.TE_MULTILINE, size=(-1, 40))
        source_box.Add(self.label(source_card, 'Grup üyeleri  ·  R1-R5 yazılabilir'), 0, wx.LEFT | wx.RIGHT, 5)
        source_box.Add(self.source_group, 0, wx.EXPAND | wx.ALL, 5)
        self.button(source_box, '1 · PCB kaynak seçimini al', self.capture_source, source_card, 'accent')
        self.source_extra = wx.CollapsiblePane(source_card, label='Diğer kaynak seçenekleri', style=wx.CP_NO_TLW_RESIZE)
        extra = self.source_extra.GetPane()
        extra.SetBackgroundColour(COLORS['card'])
        extras = wx.BoxSizer(wx.VERTICAL)
        self.button(extras, 'İsteğe bağlı: kaynak grup öner', self.find_source, extra)
        self.groups = wx.ComboBox(extra, style=wx.CB_READONLY)
        extras.Add(self.groups, 0, wx.EXPAND | wx.ALL, 5)
        self.button(extras, 'Seçili KiCad grubunu kullan', self.use_group, extra)
        extra.SetSizer(extras)
        source_box.Add(self.source_extra, 0, wx.EXPAND | wx.ALL, 5)
        self.source_extra.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.relayout_sidebar)
        left.Add(source_card, 0, wx.EXPAND | wx.ALL, 8)
        target_card, target_box = self.card(self.left_panel, '02', 'Hedef gruplar', 'Hedef: 0 / kaynak: 0 komponent')
        self.target_count = target_card.subtitle
        text_style(self.target_count, bold=True, color=COLORS['accent'])
        self.target_anchor = wx.ComboBox(target_card, style=wx.CB_READONLY)
        target_box.Add(self.label(target_card, 'Hedef referans komponent'), 0, wx.LEFT | wx.RIGHT | wx.TOP, 5)
        target_box.Add(self.target_anchor, 0, wx.EXPAND | wx.ALL, 5)
        self.target_group = wx.TextCtrl(target_card, style=wx.TE_MULTILINE, size=(-1, 40))
        target_box.Add(self.target_group, 0, wx.EXPAND | wx.ALL, 5)
        self.button(target_box, '2 · PCB hedef seçimini al ve ekle', self.capture_target, target_card, 'accent')
        self.target_extra = wx.CollapsiblePane(target_card, label='Elle ekleme ve grup önerisi', style=wx.CP_NO_TLW_RESIZE)
        extra = self.target_extra.GetPane()
        extra.SetBackgroundColour(COLORS['card'])
        extras = wx.BoxSizer(wx.VERTICAL)
        self.button(extras, 'İsteğe bağlı: aynı büyüklükte hedef öner', self.find_target, extra)
        self.button(extras, 'Hedef grubunu listeye ekle', self.add_target, extra)
        extra.SetSizer(extras)
        target_box.Add(self.target_extra, 0, wx.EXPAND | wx.ALL, 5)
        self.target_extra.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.relayout_sidebar)
        self.queue = wx.ListCtrl(target_card, style=wx.LC_REPORT | wx.LC_SINGLE_SEL, size=(-1, 90))
        self.queue.InsertColumn(0, 'Referans', width=74)
        self.queue.InsertColumn(1, 'Parça', width=51)
        self.queue.InsertColumn(2, 'Durum', width=162)
        target_box.Add(self.queue, 0, wx.EXPAND | wx.ALL, 5)
        self.remove_button = self.button(target_box, 'Seçili hedefi kaldır', self.remove_target, target_card)
        self.clear_button = self.button(target_box, 'Tüm hedefleri kaldır', self.clear_targets, target_card, 'danger')
        self.clear_button.SetToolTip('Hedef listesini ve önizlemeleri temizler. Kaynak grubunu korur; PCB’deki parçaları değiştirmez.')
        self.remove_button.Enable(False)
        self.clear_button.Enable(False)
        self.queue.Bind(wx.EVT_LIST_ITEM_SELECTED, self.queue_selection_changed)
        self.queue.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.queue_selection_changed)
        left.Add(target_card, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        left_note = self.label(self.left_panel, 'PCB’de kaynak seç → 1. düğme.\nEsc ile seçimi kaldır; hedef seç → 2. düğme.\nBirden fazla hedefi sırayla ekleyebilirsin.')
        left_note.Wrap(300)
        left.Add(left_note, 0, wx.ALL, 10)
        self.left_panel.SetSizer(left)
        self.left_panel.SetupScrolling(scroll_x=False)
        outer.Add(self.left_panel, 0, wx.EXPAND | wx.TOP | wx.BOTTOM | wx.LEFT, 8)
        right = wx.BoxSizer(wx.VERTICAL)
        toolbar, toolbar_body = self.card(self.panel, '↻', 'Dönüş ayarları', None)
        options = wx.BoxSizer(wx.HORIZONTAL)
        options.Add(self.label(toolbar, 'Ek dönüş'), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        self.rotation = wx.SpinCtrlDouble(toolbar, min=-360, max=360, inc=90, initial=0, size=(90, -1))
        options.Add(self.rotation, 0, wx.RIGHT, 18)
        self.mirror = wx.Choice(toolbar, choices=['Ayna yok', 'Merkezleri yerel X ekseninde aynala', 'Merkezleri yerel Y ekseninde aynala'])
        self.mirror.SetSelection(0)
        options.Add(self.mirror, 1, wx.EXPAND)
        toolbar_body.Add(options, 0, wx.EXPAND | wx.ALL, 5)
        self.info_text = '0°: hedef referans yerinde kalır. Ayna yalnız merkezleri yansıtır; pin düzeni ve kart yüzü korunur.'
        self.info = self.label(toolbar, self.info_text)
        self.info.Wrap(700)
        toolbar_body.Add(self.info, 0, wx.EXPAND | wx.ALL, 5)
        right.Add(toolbar, 0, wx.EXPAND | wx.BOTTOM, 12)
        preview_heading = wx.BoxSizer(wx.HORIZONTAL)
        preview_heading.Add(text_style(wx.StaticText(self.panel, label='03  Eşleştirme ve önizleme'), 12, True), 1)
        self.summary = self.label(self.panel, '0 hedef  ·  0 komponent')
        preview_heading.Add(self.summary, 0, wx.ALIGN_CENTER_VERTICAL)
        right.Add(preview_heading, 0, wx.EXPAND | wx.BOTTOM, 10)
        self.preview_area = wx.Panel(self.panel)
        self.preview_area.SetBackgroundColour(COLORS['card'])
        self.preview_sizer = wx.BoxSizer(wx.VERTICAL)
        self.empty_preview = EmptyPreview(self.preview_area)
        self.notebook = wx.Notebook(self.preview_area)
        self.preview_sizer.Add(self.empty_preview, 1, wx.EXPAND)
        self.preview_sizer.Add(self.notebook, 1, wx.EXPAND)
        self.notebook.Hide()
        self.preview_area.SetSizer(self.preview_sizer)
        right.Add(self.preview_area, 1, wx.EXPAND)
        outer.Add(right, 1, wx.EXPAND | wx.ALL, 16)
        root.Add(outer, 1, wx.EXPAND)
        footer = wx.Panel(self.panel)
        footer.SetBackgroundColour(COLORS['card'])
        controls = wx.BoxSizer(wx.HORIZONTAL)
        self.stage_note = self.label(footer, 'Kaynak ve hedef gruplarını seç.')
        controls.Add(self.stage_note, 1, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 20)
        self.preview_button = ActionButton(footer, '3 · Eşleştir ve önizle', self.preview, 'accent')
        self.preview_button.SetMinSize((180, 38))
        controls.Add(self.preview_button, 0, wx.ALL, 10)
        self.apply_button = ActionButton(footer, '4 · Tüm hedeflere uygula', self.apply, 'primary')
        self.apply_button.SetMinSize((210, 38))
        self.apply_button.Enable(False)
        controls.Add(self.apply_button, 0, wx.TOP | wx.BOTTOM | wx.RIGHT, 10)
        footer.SetSizer(controls)
        root.Add(footer, 0, wx.EXPAND)
        self.panel.SetSizer(root)
        for control in (self.source_anchor, self.source_group, self.target_anchor, self.target_group, self.groups, self.rotation, self.mirror):
            control.SetBackgroundColour(COLORS['card'])
            control.SetForegroundColour(COLORS['text'])
        self.source_anchor.Bind(wx.EVT_COMBOBOX, self.source_changed)
        self.source_group.Bind(wx.EVT_TEXT, self.source_group_changed)
        self.target_anchor.Bind(wx.EVT_COMBOBOX, self.target_changed)
        self.target_group.Bind(wx.EVT_TEXT, lambda event: (self.update_counts(), event.Skip()))
        self.rotation.Bind(wx.EVT_SPINCTRLDOUBLE, self.invalidate)
        self.rotation.Bind(wx.EVT_TEXT, self.invalidate)
        self.mirror.Bind(wx.EVT_CHOICE, self.invalidate)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Layout()
        self.Centre()
        self.apply_language()
        wx.CallAfter(self.load)

    def set_status(self, message):
        self._status_source = message
        self.status.SetStatusText(tr(message).replace('\n', ' ')[:220])

    def set_queue_status(self, row, message):
        self.queue_status[self.targets[row].anchor] = message
        self.queue.SetItem(row, 2, tr(message))

    def language_changed(self, event):
        language = ('en', 'tr')[self.language.GetSelection()]
        try:
            set_language(language, persist=True)
        except OSError:
            # The current session still switches if the preference cannot be saved.
            set_language(language)
        self.apply_language()

    def apply_language(self):
        self.language.SetSelection(0 if get_language() == 'en' else 1)
        localize_tree(self.panel)
        self.SetTitle(f'{tr("Yerleşim Kopyala")} {VERSION} — KiCad')
        mirror = self.mirror.GetSelection()
        self.mirror.SetItems([tr(s) for s in ('Ayna yok', 'Merkezleri yerel X ekseninde aynala', 'Merkezleri yerel Y ekseninde aynala')])
        self.mirror.SetSelection(mirror)
        for col, label in enumerate(('Referans', 'Parça', 'Durum')):
            column = self.queue.GetColumn(col)
            column.SetText(tr(label))
            self.queue.SetColumn(col, column)
        for row, target in enumerate(self.targets):
            self.queue.SetItem(row, 2, tr(self.queue_status.get(target.anchor, 'Önizleme gerekli')))
        for page in self.pages:
            page.localize()
        self.set_status(self._status_source)
        self.update_apply()
        self.info.SetLabel(tr(self.info_text))
        self.info.Wrap(max(360, self.panel.GetClientSize().width-395))
        self.left_panel.Layout()
        self.left_panel.FitInside()
        self.panel.Layout()
        self.Refresh()

    def label(self, parent, label, accent=False):
        return text_style(wx.StaticText(parent, label=label), bold=accent,
                          color=COLORS['accent'] if accent else COLORS['muted'])

    def card(self, parent, number, title, subtitle):
        card = wx.Panel(parent)
        card.SetBackgroundColour(COLORS['card'])
        border = wx.BoxSizer(wx.VERTICAL)
        body = wx.BoxSizer(wx.VERTICAL)
        heading = wx.BoxSizer(wx.HORIZONTAL)
        badge = wx.StaticText(card, label=number)
        text_style(badge, 12, True, COLORS['accent'])
        heading.Add(badge, 0, wx.RIGHT, 10)
        titles = wx.BoxSizer(wx.VERTICAL)
        titles.Add(text_style(wx.StaticText(card, label=title), 12, True))
        if subtitle:
            card.subtitle = self.label(card, subtitle)
            titles.Add(card.subtitle, 0, wx.TOP, 3)
        heading.Add(titles, 1)
        body.Add(heading, 0, wx.EXPAND | wx.ALL, 5)
        body.Add(wx.StaticLine(card), 0, wx.EXPAND | wx.ALL, 5)
        border.Add(body, 1, wx.EXPAND | wx.ALL, 6)
        card.SetSizer(border)
        return card, body

    def button(self, sizer, label, handler, parent=None, tone='neutral'):
        button = ActionButton(parent or self.left_panel, label, handler, tone)
        sizer.Add(button, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        return button

    def relayout_sidebar(self, event):
        self.left_panel.Layout()
        self.left_panel.FitInside()
        event.Skip()

    def show_preview(self):
        visible = bool(self.notebook.GetPageCount())
        self.notebook.Show(visible)
        self.empty_preview.Show(not visible)
        self.preview_area.Layout()

    def queue_selection_changed(self, event):
        self.remove_button.Enable(self.queue.GetFirstSelected() >= 0)
        event.Skip()

    def on_size(self, event):
        if hasattr(self, 'info'):
            set_text(self.info, self.info_text)
            self.info.Wrap(max(360, self.panel.GetClientSize().width-375))
            self.panel.Layout()
        event.Skip()

    def error(self, error):
        if isinstance(error, LayoutError):
            message = str(error)
        elif 'busy' in str(error).casefold():
            message = 'KiCad meşgul. PCB içindeki aktif taşıma/çizim işlemini veya açık özellik penceresini bitirip yeniden dene.'
        else:
            message = 'KiCad bağlantısı veya eklenti işlemi başarısız:\n' + str(error)
        self.set_status(message)
        wx.MessageBox(tr(message), tr('Yerleşim Kopyala'), wx.OK | wx.ICON_INFORMATION, self)

    def task(self, label, work, done, invalidate_on_error=False):
        if self.working:
            return
        self.working = True
        self.panel.Enable(False)
        self.set_status(label)
        def finish(result, error):
            if self.closed:
                return
            self.working = False
            self.panel.Enable(True)
            if error is not None:
                if invalidate_on_error:
                    self.invalidate()
                self.error(error)
            else:
                done(result)
            self.update_apply()
        def worker():
            try:
                result = work()
                wx.CallAfter(finish, result, None)
            except Exception as error:
                context = (f'Yerleşim Kopyala {VERSION} · {datetime.now(timezone.utc).isoformat()}\n'
                           f'KiCad adımı: {getattr(self.adapter, "last_stage", "bilinmiyor")}\n'
                           f'Süre: {getattr(self.adapter, "last_duration", 0):.3f} sn\n')
                self.log_path.write_text(context+traceback.format_exc(), encoding='utf-8')
                wx.CallAfter(finish, None, error)
        threading.Thread(target=worker, daemon=True).start()

    def load(self):
        self.task('PCB okunuyor…', self.adapter.snapshot, self.loaded)

    def loaded(self, snapshot):
        self.snapshot = snapshot
        refs = sorted(snapshot.components, key=ref_key)
        self.source_anchor.SetItems(refs)
        self.groups.SetItems(sorted(snapshot.groups))
        if snapshot.groups:
            self.groups.SetSelection(0)
        if snapshot.selected:
            anchor = self.choose_source_anchor(snapshot.selected)
            self.source_anchor.SetSelection(refs.index(anchor) if anchor else wx.NOT_FOUND)
            self.source_group.ChangeValue(', '.join(sorted(snapshot.selected, key=ref_key)))
        else:
            self.source_anchor.SetSelection(wx.NOT_FOUND)
        self.source_changed()
        self.set_status('PCB’de kaynak parçaları seçip 1. düğmeye, ardından hedef parçaları seçip 2. düğmeye bas.')

    def group_for(self, anchor):
        groups = [refs for refs in self.snapshot.groups.values() if anchor in refs]
        if groups:
            return sorted(min(groups, key=len), key=ref_key)
        return discover_group(self.snapshot.components, anchor)

    def source_changed(self, event=None):
        self.sync_source(ensure_group=True)
        if event is not None:
            event.Skip()

    def source_group_changed(self, event):
        self.sync_source(ensure_group=False)
        event.Skip()

    def members(self, field):
        try:
            return set(parse_refs(field.GetValue(), self.snapshot.components))
        except LayoutError:
            return None  # A partially typed list is not authoritative group membership.

    def choose_source_anchor(self, refs):
        current = self.source_anchor.GetValue()
        if current in refs:
            return current  # Keep the user's explicitly selected reference.
        largest = max(len(self.snapshot.components[r].pins) for r in refs)
        candidates = [r for r in refs if len(self.snapshot.components[r].pins) == largest]
        return candidates[0] if len(candidates) == 1 else None

    def sync_source(self, ensure_group=False):
        self.invalidate()
        if self.snapshot is None:
            return
        source = self.source_anchor.GetValue()
        members = self.members(self.source_group)
        if ensure_group and source in self.snapshot.components and (members is None or source not in members):
            members = {source}
            self.source_group.ChangeValue(', '.join(sorted(members, key=ref_key)))
        state = (source, frozenset(members) if members is not None else None)
        changed = state != self._source_state
        if changed:
            self.targets.clear()
            self.pages.clear()
            self.notebook.DeleteAllPages()
            self.show_preview()
            self.refresh_queue()
            self.target_group.ChangeValue('')
            self._source_state = state
        self.refresh_target_choices(preserve_members=not changed)

    def update_counts(self):
        if self.snapshot is None:
            return
        source = self.members(self.source_group)
        target = self.members(self.target_group)
        ns = str(len(source)) if source is not None else '?'
        nt = str(len(target)) if target is not None else '?'
        set_text(self.source_count, f'Kaynak: {ns} komponent')
        set_text(self.target_count, f'Hedef: {nt} / kaynak: {ns} komponent')
        set_text(self.summary, f'{len(self.targets)} hedef  ·  {sum(len(t.refs) for t in self.targets)} komponent')

    def check_count(self, source, target):
        if len(source) != len(target):
            raise LayoutError(f'Kaynak {len(source)}, hedef {len(target)} komponent içeriyor. '
                              'Sayıları eşit olmalı. PCB’de Esc ile eski seçimi kaldırıp '
                              f'yalnız {len(source)} hedef komponenti seç; otomatik parça eklenmez.')

    def refresh_target_choices(self, preserve_members=True):
        source = self.source_anchor.GetValue()
        members = self.members(self.source_group)
        current = self.target_anchor.GetValue()
        candidates = []
        if source in self.snapshot.components and members is not None and source in members:
            excluded = members | {r for target in self.targets for r in target.refs}
            kind = self.snapshot.components[source].kind
            candidates = sorted((r for r,c in self.snapshot.components.items()
                                 if c.kind == kind and r not in excluded), key=ref_key)
        self.target_anchor.SetItems(candidates)
        self.target_anchor.SetSelection(candidates.index(current) if current in candidates else wx.NOT_FOUND)
        self.target_changed(preserve_members=preserve_members)

    def target_changed(self, event=None, preserve_members=True):
        if self.snapshot is None:
            return
        anchor = self.target_anchor.GetValue()
        members = self.members(self.target_group)
        excluded = (self.members(self.source_group) or set()) | {r for target in self.targets for r in target.refs}
        if anchor not in self.snapshot.components or anchor in excluded:
            self.target_group.ChangeValue('')
        elif not (preserve_members and members is not None and anchor in members and not members & excluded):
            self.target_group.ChangeValue('')
        self.update_counts()
        if event is not None:
            event.Skip()

    def invalidate(self, event=None):
        self.preview_stamp = None
        self.apply_button.Enable(False)
        self.update_apply()
        if event is not None:
            event.Skip()

    def capture(self, target=False, add_selected=False):
        def done(snapshot):
            self.snapshot = snapshot
            if not snapshot.selected:
                self.error(LayoutError('PCB içinde bir komponent veya komponent grubu seç.'))
                return
            refs = sorted(snapshot.selected, key=ref_key)
            if target:
                source = self.source_anchor.GetValue()
                if source not in snapshot.components:
                    self.error(LayoutError('Önce kaynak referansı seç.'))
                    return
                candidates = [r for r in refs if snapshot.components[r].kind == snapshot.components[source].kind]
                if not candidates:
                    self.error(LayoutError('Seçimde kaynak referansa denk bir komponent yok.'))
                    return
                source_refs = self.members(self.source_group)
                if source_refs is None or source not in source_refs:
                    self.error(LayoutError('Kaynak grup listesini ve referansını kontrol et.'))
                    return
                try:
                    self.check_count(source_refs, refs)
                except LayoutError as error:
                    self.error(error)
                    return
                excluded = source_refs | {r for t in self.targets for r in t.refs}
                if set(refs) & excluded:
                    self.error(LayoutError('Seçilen hedef kaynakla veya eklenmiş bir hedefle çakışıyor. '
                                           'PCB’de Esc ile eski seçimi kaldırıp yalnız yeni hedef parçalarını seç.'))
                    return
                current = self.target_anchor.GetValue()
                anchor = current if current in candidates else (candidates[0] if len(candidates) == 1 else None)
                # Multiple equally suitable selected anchors need an explicit
                # choice; never silently take the first reference in the list.
                self.target_anchor.SetItems(candidates)
                self.target_anchor.SetSelection(candidates.index(anchor) if anchor else wx.NOT_FOUND)
                self.target_group.ChangeValue(', '.join(refs))
            else:
                anchor = self.choose_source_anchor(refs)
                all_refs = sorted(snapshot.components, key=ref_key)
                self.source_anchor.SetItems(all_refs)
                self.source_anchor.SetSelection(all_refs.index(anchor) if anchor else wx.NOT_FOUND)
                self.source_group.ChangeValue(', '.join(refs))
                self.source_changed()
            self.invalidate()
            self.update_counts()
            if target and add_selected and anchor:
                self.add_target(None)
                return
            if anchor:
                self.set_status(f'{len(refs)} seçili komponent alındı; referans {anchor}. Referans ve grup listesini kontrol et.')
            else:
                label = 'Hedef referans komponent' if target else 'Referans komponent'
                self.set_status(f'{len(refs)} seçili komponent alındı. Birden fazla uygun referans var; {label} alanından seç.')
                if target:
                    self.target_extra.Expand()
                    self.left_panel.Layout()
                    self.left_panel.FitInside()
        self.task('PCB seçimi okunuyor…', self.adapter.snapshot, done)

    def capture_source(self, event):
        self.capture(False)

    def capture_target(self, event):
        self.capture(True, add_selected=True)

    def find_source(self, event):
        anchor = self.source_anchor.GetValue()
        if anchor and self.snapshot:
            self.source_group.SetValue(', '.join(self.group_for(anchor)))

    def find_target(self, event):
        anchor = self.target_anchor.GetValue()
        if anchor and self.snapshot:
            try:
                source = parse_refs(self.source_group.GetValue(), self.snapshot.components)
                cs = self.snapshot.components
                kinds = Counter(cs[r].kind for r in source)
                excluded = set(source) | {r for t in self.targets for r in t.refs}
                refs = [r for r in self.group_for(anchor) if r not in excluded and cs[r].kind in kinds]
                # Keep only an exact multiset. Never arbitrarily trim duplicate
                # kinds by reference order or current placement distance.
                if Counter(cs[r].kind for r in refs) != kinds:
                    raise LayoutError('Kaynakla aynı parça sayısı ve türlerinde güvenilir bir hedef '
                                      'önerilemedi. PCB’de hedef parçalarını seçip 2. düğmeye bas.')
                match_groups(cs, source, refs, self.source_anchor.GetValue(), anchor)
                self.target_group.SetValue(', '.join(refs))
                self.set_status(f'{len(refs)} parçalık hedef önerildi; listeyi kontrol edip ekle.')
            except Exception as error:
                self.target_group.ChangeValue('')
                self.update_counts()
                self.error(error)

    def use_group(self, event):
        group = self.groups.GetValue()
        if self.snapshot and group in self.snapshot.groups:
            self.source_group.SetValue(', '.join(sorted(self.snapshot.groups[group], key=ref_key)))

    def add_target(self, event):
        try:
            if not self.snapshot:
                raise LayoutError('Önce PCB bağlantısını yükle.')
            refs = parse_refs(self.target_group.GetValue(), self.snapshot.components)
            source = parse_refs(self.source_group.GetValue(), self.snapshot.components)
            self.check_count(source, refs)
            source_anchor = self.source_anchor.GetValue()
            if source_anchor not in source:
                raise LayoutError('Kaynak referans komponenti seç; kendi grubunun içinde olmalı.')
            anchor = self.target_anchor.GetValue()
            if anchor not in refs:
                raise LayoutError('Hedef referans grup listesinde olmalı.')
            if self.snapshot.components[anchor].kind != self.snapshot.components[source_anchor].kind:
                raise LayoutError('Hedef referans kaynak referansla aynı tür, değer ve kılıfta olmalı.')
            validate_batch(source, [t.refs for t in self.targets]+[refs])
            self.targets.append(Target(anchor, tuple(refs)))
            self.refresh_queue()
            self.refresh_target_choices(preserve_members=False)
            self.invalidate()
            self.set_status(f'{anchor}: {len(refs)} hedef komponent listeye eklendi. '
                                      'Başka hedef seçebilir veya 3 · Eşleştir ve önizle’ye basabilirsin.')
        except Exception as error:
            self.error(error)

    def refresh_queue(self):
        self.queue_status = {}
        self.queue.DeleteAllItems()
        for i, t in enumerate(self.targets):
            row = self.queue.InsertItem(i, t.anchor)
            self.queue.SetItem(row, 1, str(len(t.refs)))
            self.set_queue_status(row, 'Önizleme gerekli')
        self.clear_button.Enable(bool(self.targets))
        self.remove_button.Enable(False)
        self.update_counts()
        self.update_apply()

    def remove_target(self, event):
        index = self.queue.GetFirstSelected()
        if index >= 0:
            self.targets.pop(index)
            self.pages.clear()
            self.notebook.DeleteAllPages()
            self.show_preview()
            self.refresh_queue()
            self.refresh_target_choices()
            self.invalidate()

    def clear_targets(self, event=None):
        self.targets.clear()
        self.pages.clear()
        self.notebook.DeleteAllPages()
        self.show_preview()
        self.target_anchor.SetSelection(wx.NOT_FOUND)
        self.target_group.ChangeValue('')
        self.refresh_queue()
        self.refresh_target_choices(preserve_members=False)
        self.invalidate()
        self.set_status('Tüm hedefler ve önizlemeler temizlendi. Kaynak grup korundu; yeni hedefler seçebilirsin.')

    def preview(self, event):
        try:
            if not self.targets:
                raise LayoutError('Listeye en az bir hedef grup ekle.')
            source_anchor = self.source_anchor.GetValue()
            source_text = self.source_group.GetValue()
            targets = [Target(t.anchor, t.refs, mapping=dict(t.mapping)) for t in self.targets]
            mirror = ('none', 'x', 'y')[self.mirror.GetSelection()]
            rotation = self.rotation.GetValue()
            self.invalidate()
            def work():
                snapshot = self.adapter.snapshot()
                refs = parse_refs(source_text, snapshot.components)
                validate_batch(refs, [t.refs for t in targets])
                for t in targets:
                    if set(t.refs)-set(snapshot.components):
                        raise LayoutError('Hedef grubundaki bazı komponentler kartta yok.')
                    t.match = match_groups(snapshot.components, refs, t.refs, source_anchor, t.anchor)
                    t.mapping = {r: v for r, v in t.mapping.items() if r in t.match.candidates and v in t.match.candidates[r]}
                return snapshot, targets
            def done(result):
                snapshot, targets = result
                self.snapshot, self.targets = snapshot, targets
                self.notebook.DeleteAllPages()
                self.pages = []
                for i, target in enumerate(targets):
                    page = TargetPage(self.notebook, target, snapshot.components, mirror, rotation, self.update_apply)
                    self.notebook.AddPage(page, target.anchor)
                    self.pages.append(page)
                    self.set_queue_status(i, 'Eşleştirme hazır')
                self.show_preview()
                self.preview_stamp = snapshot.stamp
                self.set_status('Önizleme hazır. Sarı eşleşmeleri seç veya elektriksel olarak geçerli öneriyi kullan.')
                self.update_apply()
            self.task('Bağlantı yapıları eşleştiriliyor…', work, done)
        except Exception as error:
            self.error(error)

    def update_apply(self):
        ready = (not self.working and self.preview_stamp is not None and bool(self.pages)
                 and not getattr(self.adapter, 'needs_restart', False)
                 and len(self.pages) == len(self.targets) and all(p.poses is not None for p in self.pages))
        self.apply_button.Enable(ready)
        self.preview_button.Enable(bool(self.targets) and not self.working)
        if self.working:
            set_text(self.stage_note, 'İşlem sürüyor…')
        elif ready:
            set_text(self.stage_note, 'Hazır · Önizlemeyi kontrol edip uygula.')
        elif self.preview_stamp is not None and self.pages:
            set_text(self.stage_note, 'Sarı satırlardaki eşleşmeleri tamamla.')
        elif self.targets:
            set_text(self.stage_note, 'Hedefler eklendi · Önizleme oluştur.')
        else:
            set_text(self.stage_note, 'Kaynak ve hedef gruplarını seç.')

    def apply(self, event):
        if self.preview_stamp is None or not all(p.poses is not None for p in self.pages):
            self.error(LayoutError('Önce geçerli bir önizleme oluştur.'))
            return
        poses = [pose for page in self.pages for pose in page.poses]
        stamp = self.preview_stamp
        def done(count):
            self.preview_stamp = None
            self.set_status(f'{count} komponent yerleşimi uygulandı. KiCad içinde Ctrl+Z ile tek adımda geri alabilirsin. Sonrasında DRC çalıştır.')
            for i in range(len(self.targets)):
                self.set_queue_status(i, 'Uygulandı')
        self.task('Yerleşim tek işlem olarak uygulanıyor…', lambda: self.adapter.apply(poses, stamp), done,
                  invalidate_on_error=True)

    def on_close(self, event):
        if self.working:
            self.set_status('İşlem sürüyor; tamamlandıktan sonra pencereyi kapatabilirsin.')
            event.Veto()
            return
        self.closed = True
        self.Destroy()
