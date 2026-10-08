"""Explicit PCB-selection workflow for project-local footprint edits."""
import wx
from core import LayoutError, ref_key
from footprint_edits import EditOptions, plan_edits, suggestions
from i18n import tr


class FootprintEditsPanel(wx.Panel):
    def __init__(self, parent, frame):
        super().__init__(parent)
        # Import lazily: gui constructs this panel after defining its widgets.
        from gui import ActionButton, COLORS, text_style, set_text
        self.frame = frame
        self.source = None
        self.targets = []
        self.plan = None
        self.SetBackgroundColour(COLORS['bg'])
        root = wx.BoxSizer(wx.VERTICAL)
        note = wx.StaticText(self, label='Yalnız bu PCB’deki footprint geometrisini kopyalar. Yerleşim ve kütüphane değişmez.')
        self.note = note
        text_style(note, 12, True)
        root.Add(note, 0, wx.ALL, 16)
        body = wx.BoxSizer(wx.HORIZONTAL)
        sidebar = wx.Panel(self)
        sidebar.SetBackgroundColour(COLORS['card'])
        left = wx.BoxSizer(wx.VERTICAL)
        self.source_label = wx.StaticText(sidebar, label='Kaynak footprint seçilmedi.')
        text_style(self.source_label, bold=True, color=COLORS['accent'])
        left.Add(self.source_label, 0, wx.ALL, 10)
        left.Add(ActionButton(sidebar, '1 · PCB kaynak seçimini al', self.capture_source, 'accent'), 0, wx.EXPAND | wx.ALL, 8)
        help_text = wx.StaticText(sidebar, label='PCB’de tek kaynak seç. Sonra Esc ile seçimi kaldır ve hedefleri seç.')
        self.help_text = help_text
        set_text(help_text, help_text.GetLabel())
        text_style(help_text, color=COLORS['muted']); help_text.Wrap(300)
        left.Add(help_text, 0, wx.ALL, 10)
        left.Add(ActionButton(sidebar, '2 · PCB hedef seçimini al ve ekle', self.capture_targets, 'accent'), 0, wx.EXPAND | wx.ALL, 8)
        self.queue = wx.ListBox(sidebar, style=wx.LB_EXTENDED, size=(315, 170))
        left.Add(self.queue, 1, wx.EXPAND | wx.ALL, 8)
        left.Add(ActionButton(sidebar, 'Seçili hedefi kaldır', self.remove, 'neutral'), 0, wx.EXPAND | wx.ALL, 8)
        left.Add(ActionButton(sidebar, 'Tüm hedefleri kaldır', self.clear, 'danger'), 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)
        left.Add(ActionButton(sidebar, 'İsteğe bağlı: benzer footprint öner', self.suggest), 0, wx.EXPAND | wx.ALL, 8)
        sidebar.SetSizer(left)
        body.Add(sidebar, 0, wx.EXPAND | wx.LEFT | wx.BOTTOM, 16)
        content = wx.Panel(self)
        content.SetBackgroundColour(COLORS['card'])
        right = wx.BoxSizer(wx.VERTICAL)
        self.pads = wx.CheckBox(content, label='Pad geometrisi ve ayarları'); self.pads.SetValue(True)
        self.graphics = wx.CheckBox(content, label='Footprint çizimleri ve serbest metinler'); self.graphics.SetValue(True)
        self.fields = wx.CheckBox(content, label='Referans/değer yazılarının biçimi ve yerel konumu')
        for check in (self.pads, self.graphics, self.fields):
            right.Add(check, 0, wx.ALL, 10)
            check.Bind(wx.EVT_CHECKBOX, lambda event: self.invalidate())
        scope = wx.StaticText(content, label='Korunur: konum, yön, yüz, referans, değer, şema bağlantısı ve pad ağları.\n3B modeller, özel alanlar, footprint kuralları ve zone öğeleri hedefte korunur.')
        self.scope = scope
        set_text(scope, scope.GetLabel())
        text_style(scope, color=COLORS['muted']); scope.Wrap(650)
        right.Add(scope, 0, wx.ALL, 10)
        self.details = wx.CheckBox(content, label='Tüm geometri ve pad ayarlarını göster')
        right.Add(self.details, 0, wx.ALL, 10)
        self.details.Bind(wx.EVT_CHECKBOX, lambda event: self.render_report())
        self.report = wx.TextCtrl(content, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP)
        self.report.SetBackgroundColour('#f6f9fc')
        right.Add(self.report, 1, wx.EXPAND | wx.ALL, 10)
        content.SetSizer(right)
        body.Add(content, 1, wx.EXPAND | wx.ALL, 16)
        root.Add(body, 1, wx.EXPAND)
        footer = wx.BoxSizer(wx.HORIZONTAL)
        self.preview_button = ActionButton(self, '3 · Düzenlemeleri önizle', self.preview, 'accent')
        self.apply_button = ActionButton(self, '4 · Footprint düzenlemelerini uygula', self.apply, 'primary')
        footer.AddStretchSpacer()
        footer.Add(self.preview_button, 0, wx.ALL, 10)
        footer.Add(self.apply_button, 0, wx.ALL, 10)
        root.Add(footer, 0, wx.EXPAND)
        self.SetSizer(root)
        self.localize()
        self.Bind(wx.EVT_SIZE, self.on_size)

    def localize(self):
        from gui import localize_tree
        localize_tree(self)
        self.source_label.SetLabel(tr('Kaynak') + ': ' + self.source if self.source else tr('Kaynak footprint seçilmedi.'))
        self.render_report()
        self.refresh_buttons()
        self.wrap_text()
        self.Layout()
        self.pads.GetParent().Layout()

    def wrap_text(self):
        from gui import set_text
        for control, width in ((self.help_text, 300),
                               (self.scope, max(300, self.GetClientSize().width - 410)),
                               (self.note, max(500, self.GetClientSize().width - 32))):
            set_text(control, getattr(control, '_source_label', control.GetLabel()))
            control.Wrap(width)

    def on_size(self, event):
        self.wrap_text()
        self.Layout()
        event.Skip()

    def refresh_buttons(self):
        self.preview_button.Enable(bool(self.source and self.targets) and not self.frame.working)
        self.apply_button.Enable(bool(self.plan and self.plan.updates and not self.plan.rejected)
            and not self.frame.working and not getattr(self.frame.adapter, 'needs_restart', False))

    def invalidate(self):
        self.plan = None
        self.render_report()
        self.refresh_buttons()

    def capture_source(self, event=None):
        self.invalidate()
        def done(snapshot):
            if len(snapshot.selected) != 1:
                self.frame.error(LayoutError('PCB’de yalnız bir kaynak footprint seç.'))
                return
            self.source = snapshot.selected[0]
            self.targets = []
            self.queue.SetItems([])
            self.invalidate(); self.localize()
        self.frame.task('PCB seçimi okunuyor…', self.frame.adapter.edits_snapshot, done)

    def capture_targets(self, event=None):
        if not self.source:
            self.frame.error(LayoutError('Önce kaynak footprinti al.')); return
        self.invalidate()
        def done(snapshot):
            if not snapshot.selected or self.source in snapshot.selected:
                self.frame.error(LayoutError('Kaynak seçimini kaldırıp yalnız hedef footprintleri seç.')); return
            self.targets = sorted(set(self.targets) | set(snapshot.selected), key=ref_key)
            self.queue.SetItems(self.targets)
            self.invalidate()
        self.frame.task('PCB seçimi okunuyor…', self.frame.adapter.edits_snapshot, done)

    def remove(self, event=None):
        selected = set(self.queue.GetSelections())
        self.targets = [r for index, r in enumerate(self.targets) if index not in selected]
        self.queue.SetItems(self.targets); self.invalidate()

    def clear(self, event=None):
        self.targets = []; self.queue.SetItems([]); self.invalidate()

    def suggest(self, event=None):
        if not self.source:
            self.frame.error(LayoutError('Önce kaynak footprinti al.')); return
        def work():
            snapshot = self.frame.adapter.edits_snapshot()
            if self.source not in snapshot.objects:
                raise LayoutError('Komponent artık bulunamıyor: ' + self.source)
            return suggestions(snapshot, self.source, self.targets)
        def done(candidates):
            if not candidates:
                self.frame.set_status('Benzer footprint önerisi bulunamadı.'); return
            dialog = wx.MultiChoiceDialog(self, tr('Yalnız işaretlediğin öneriler hedef listesine eklenir.'),
                tr('Benzer footprintler'), [ref + ' · ' + ', '.join(tr(r) for r in reasons) for ref, reasons in candidates])
            try:
                if dialog.ShowModal() == wx.ID_OK:
                    self.targets = sorted(set(self.targets) | {candidates[i][0] for i in dialog.GetSelections()}, key=ref_key)
                    self.queue.SetItems(self.targets); self.invalidate()
            finally:
                dialog.Destroy()
        self.frame.task('PCB okunuyor…', work, done)

    def preview(self, event=None):
        source, targets = self.source, tuple(self.targets)
        options = EditOptions(self.pads.GetValue(), self.graphics.GetValue(), self.fields.GetValue())
        self.invalidate()
        def done(plan):
            self.plan = plan; self.render_report(); self.refresh_buttons()
        self.frame.task('Footprint düzenlemeleri hazırlanıyor…',
            lambda: plan_edits(self.frame.adapter.edits_snapshot(), source, targets, options), done)

    def render_report(self):
        if not self.plan:
            self.report.ChangeValue(tr('Kaynak ve hedefleri al; aktarım kapsamını seçip önizle.'))
            return
        from footprint_edits import graphics
        lines = [tr('Kaynak') + ': ' + self.plan.source + ' (' + self.plan.source_side + ')',
                 tr('Hedef') + ': ' + ', '.join(self.plan.targets), '']
        lines.append(tr('Her hedef mevcut konumunda ve açısında kalır. Pad numaraları birebir eşleştirilir.'))
        lines.append(tr('Aktarılacak kapsam') + ': ' + ', '.join(tr(label) for enabled, label in (
            (self.plan.options.pads, 'Pad geometrisi ve ayarları'),
            (self.plan.options.graphics, 'Footprint çizimleri ve serbest metinler'),
            (self.plan.options.field_format, 'Referans/değer yazılarının biçimi ve yerel konumu')) if enabled))
        for ref, changed, before, after in self.plan.rows:
            lines.extend(['', tr('{ref}: {n} pad değişecek; çizimler {old} → {new}.').format(ref=ref, n=changed, old=before, new=after)])
            update = next(fp for fp in self.plan.updates if fp.reference_field.text.value == ref)
            from kipy.proto.board.board_types_pb2 import BoardLayer
            side = 'B' if update.layer == BoardLayer.BL_B_Cu else 'F'
            lines.append('  ' + tr('Yüz') + ': ' + side)
            if side != self.plan.source_side:
                lines.append('  ' + tr('Yerel geometri karşı yüz için yansıtıldı; hedefin yüzü ve açısı korundu.'))
            # Exact proposed dimensions and positions, independent of the view scale.
            for pad in update.definition.pads:
                lines.append('  ' + tr('Pad') + ' ' + (pad.number or tr('Mekanik')) +
                    f' · X {pad.position.x / 1e6:.4f} mm · Y {pad.position.y / 1e6:.4f} mm' +
                    f' · {pad.padstack.angle.degrees:.2f}° · ' + tr('Ağ') + ': ' + pad.net.name)
                for layer in pad.proto.pad_stack.copper_layers:
                    from kipy.proto.board.board_types_pb2 import BoardLayer, PadStackShape
                    lines.append(f'    {BoardLayer.Name(layer.layer)} · {PadStackShape.Name(layer.shape)}' +
                                 f' · {layer.size.x_nm / 1e6:.4f} × {layer.size.y_nm / 1e6:.4f} mm')
            if self.details.GetValue():
                from google.protobuf.text_format import MessageToString
                lines.extend(['', tr('Önerilen geometri ve ayarlar (KiCad API alanları):')])
                if self.plan.options.pads:
                    for pad in update.definition.pads:
                        lines.append(MessageToString(pad.proto))
                if self.plan.options.graphics:
                    for item in graphics(update):
                        lines.append(MessageToString(item.proto))
                if self.plan.options.field_format:
                    lines.append(MessageToString(update.reference_field.proto))
                    lines.append(MessageToString(update.value_field.proto))
        for ref, reason in self.plan.rejected.items():
            lines.extend(['', ref + ': ' + tr('Uyumsuz') + ' — ' + tr(reason)])
        if self.plan.rejected:
            lines.extend(['', tr('Uyumsuz hedefleri kaldırıp yeniden önizle.')])
        self.report.ChangeValue('\n'.join(lines))

    def apply(self, event=None):
        if not self.plan or self.plan.rejected:
            self.frame.error(LayoutError('Önce geçerli bir önizleme oluştur.')); return
        plan = self.plan
        def done(count):
            self.invalidate()
            self.frame.invalidate()  # Placement preview may include changed pad geometry.
            self.frame.set_status(tr('{n} footprint düzenlendi. KiCad’de Ctrl+Z ile tek adımda geri alınabilir.').format(n=count))
        self.frame.task('Footprint düzenlemeleri uygulanıyor…',
            lambda: self.frame.adapter.apply_edits(plan), done, invalidate_on_error=True)
