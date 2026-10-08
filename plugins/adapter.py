"""KiCad 10 IPC transport. Mutations use one native undo transaction."""
from __future__ import annotations

from dataclasses import dataclass
import math
import time

from kipy import KiCad
from kipy.common_types import Commit
from kipy.errors import ApiError, ConnectionError as KiCadConnectionError
from kipy.proto.common import ApiStatusCode
from kipy.proto.common.types import KIID, DocumentType
from kipy.board_types import (FootprintInstance, Footprint3DModel, Group,
                             Field, Pad, BoardText, Zone, BoardShape)
from kipy.geometry import Angle, Vector2
from kipy.proto.board.board_types_pb2 import BoardLayer

from core import Component, LayoutError, fingerprint
from i18n import tr


def uid(item):
    return getattr(item.id, 'value', '')


def describe(fp):
    pins = {}
    for pad in fp.definition.pads:
        if not pad.number:  # Mechanical/NPTH pads are not electrical pins.
            continue
        net = pad.net.name
        if pad.number in pins and pins[pad.number] != net:
            raise LayoutError(f'{fp.reference_field.text.value}: aynı pin numarası farklı ağlara bağlı.')
        pins[pad.number] = net
    lib = fp.definition.id
    kelvin_pairs = ()
    if (fp.reference_field.text.value.startswith('R') and 'WSK1216' in str(lib).upper()
            and set(pins) == {'1', '2', '3', '4'}):
        kelvin_pairs = (('1', '2'), ('4', '3'))
    return Component(fp.reference_field.text.value, uid(fp), fp.value_field.text.value,
                     str(lib), tuple(sorted(pins.items())), fp.position.x/1e6,
                     fp.position.y/1e6, fp.orientation.degrees,
                     'B' if fp.layer == BoardLayer.BL_B_Cu else 'F', fp.locked, kelvin_pairs)


@dataclass
class Snapshot:
    components: dict
    objects: dict
    groups: dict
    selected: tuple
    board_key: str
    copper_count: int = 2

    @property
    def stamp(self):
        return fingerprint(self.components)


def moved_footprint(original, pose):
    """Use IPC wrapper transforms but retain local 3D models (kipy 0.7.1 drops
    unhandled children in its orientation setter). Unsupported item types are
    rejected before a board update, rather than silently being lost.
    """
    updated = FootprintInstance(original.proto)
    original_items = list(updated.definition.items)
    supported = (Field, Pad, BoardText, Zone, BoardShape, Footprint3DModel)
    unknown = [type(item).__name__ for item in original_items if not isinstance(item, supported)]
    if unknown:
        raise LayoutError(f'{pose.ref} desteklenmeyen bir kılıf öğesi içeriyor: '+', '.join(sorted(set(unknown))))
    updated.position = Vector2.from_xy_mm(pose.x, pose.y)
    updated.orientation = Angle.from_degrees(pose.angle)
    transformed = iter(updated.definition.items)
    updated.definition.items = [item if isinstance(item, Footprint3DModel) else next(transformed)
                                for item in original_items]
    return updated


class KiCadAdapter:
    TIMEOUT_MS = 20000

    def __init__(self, kicad=None, reconnect=None):
        self.kicad = kicad or KiCad(timeout_ms=self.TIMEOUT_MS)
        self._reconnect_override = reconnect
        self.last_stage = 'PCB bağlantısı'
        self.last_duration = 0
        self.needs_restart = False
        self.board = self.kicad.get_board()
        self.board_key = self.board.document.SerializeToString().hex()

    def request(self, label, function, *args):
        self.last_stage = label
        started = time.monotonic()
        try:
            return function(*args)
        finally:
            self.last_duration = time.monotonic()-started

    def reconnect(self):
        if self._reconnect_override is not None:
            replacement = self._reconnect_override()
        elif isinstance(self.kicad, KiCad):
            # kicad-python 0.7.1 exposes no public reconnect method. Read its
            # pinned transport configuration, close the timed-out Req0 socket,
            # and use the public constructor. Keep the *same* client identity
            # and learned server token so cleanup can only affect our commit.
            client = self.kicad._client
            options = dict(socket_path=client._socket_path,
                           client_name=client._client_name,
                           kicad_token=client._kicad_token,
                           timeout_ms=self.TIMEOUT_MS)
            if client.connected:
                client._conn.close()
                client._connected = False
            replacement = KiCad(**options)
        else:
            raise LayoutError('KiCad bağlantısı yenilenemedi.')
        board = self.request('bağlantıyı yenileme', replacement.get_board)
        if board.document.SerializeToString().hex() != self.board_key:
            raise LayoutError('Açık PCB değişti. Eklentiyi yeni kart için yeniden aç.')
        self.kicad, self.board = replacement, board

    def snapshot(self):
        try:
            return self._snapshot()
        except KiCadConnectionError:
            # A complete read can be repeated once; mutations are never replayed.
            self.reconnect()
            return self._snapshot()

    def _snapshot(self):
        current = self.kicad.get_board()
        if current.document.SerializeToString().hex() != self.board_key:
            raise LayoutError('Açık PCB değişti. Eklentiyi yeni kart için yeniden aç.')
        footprints = self.request('komponentleri okuma', self.board.get_footprints)
        objects = {fp.reference_field.text.value: fp for fp in footprints}
        if len(objects) != len(footprints):
            raise LayoutError('Kartta yinelenen referanslar var; önce numaralandırmayı düzelt.')
        by_id = {uid(fp): r for r, fp in objects.items()}
        groups = self.request('KiCad gruplarını okuma', self.board.get_groups)
        raw_groups = {uid(g): g for g in groups}
        def members(g, visiting=None):
            visiting = set(visiting or ())
            if uid(g) in visiting:
                raise LayoutError('İç içe KiCad gruplarında döngü tespit edildi.')
            visiting.add(uid(g))
            refs = set()
            for item_id in g.proto.items:
                key = item_id.value
                if key in by_id:
                    refs.add(by_id[key])
                elif key in raw_groups:
                    refs.update(members(raw_groups[key], visiting))
            return refs
        named = {g.name or uid(g): members(g) for g in groups}
        selected = set()
        for item in self.request('PCB seçimini okuma', self.board.get_selection):
            if uid(item) in by_id:
                selected.add(by_id[uid(item)])
            elif isinstance(item, Group):
                selected.update(members(item))
        return Snapshot({r: describe(fp) for r, fp in objects.items()}, objects,
                        named, tuple(sorted(selected)), self.board_key)

    def drop_own_commit(self, commit):
        # KiCad 10.0.5 explicitly ignores commit.id for CMA_DROP, allowing a
        # client to cancel *its own* BeginCommit whose response/id was lost.
        # Do not use a new anonymous client for this request.
        try:
            self.request('yarım kalan işlemi iptal etme', self.board.drop_commit,
                         commit if commit is not None else Commit(KIID()))
            return True
        except ApiError as error:
            missing = ('does not has a commit in progress' in str(error)
                       or 'does not have a commit in progress' in str(error))
            if error.code == ApiStatusCode.AS_BAD_REQUEST and missing:
                return False
            raise

    def edits_snapshot(self):
        snapshot = self.snapshot()
        snapshot.copper_count = self.request('bakır katman sayısını okuma', self.board.get_copper_layer_count)
        if not 2 <= snapshot.copper_count <= 32 or snapshot.copper_count % 2:
            raise LayoutError('Kartın bakır katman sayısı doğrulanamadı.')
        return snapshot

    def check_write_context(self):
        # kipy 0.7.1 BeginCommit has no document selector. In KiCad 10.0.5
        # an open schematic can receive this board transaction and crash the
        # process (KiCad issues 25322/24966). Never probe with a trial write.
        try:
            schematics = self.request('açık şema düzenleyicisini kontrol etme',
                                      self.kicad.get_open_documents, DocumentType.DOCTYPE_SCHEMATIC)
        except ApiError as error:
            # A PCB-only server has no handler for schematic document queries.
            # Any other error leaves the editor context unknown: refuse writes.
            if (error.code == ApiStatusCode.AS_UNHANDLED and str(error) ==
                    'KiCad returned error: no handler available for request of type '
                    'kiapi.common.commands.GetOpenDocuments'):
                schematics = []
            else:
                raise LayoutError('Açık şema düzenleyicisi kontrol edilemedi; taşıma başlatılmadı. '
                                  f'Ayrıntı: {error}') from error
        if schematics:
            raise LayoutError('Şema düzenleyicisi açık. KiCad 10 IPC hatası bu durumda taşıma '
                              'başlarken KiCad’i kapatabiliyor (hata kaydı #25322). '
                              'Şemadaki işini kaydedip yalnız şema düzenleyicisini kapat; '
                              'PCB açık kalsın. Sonra yeniden önizleyip uygula. Taşıma başlatılmadı.')
        documents = self.request('açık PCB düzenleyicisini kontrol etme',
                                 self.kicad.get_open_documents, DocumentType.DOCTYPE_PCB)
        if len(documents) != 1 or documents[0].SerializeToString().hex() != self.board_key:
            raise LayoutError('API sunucusunda yalnız bu PCB düzenleyicisi açık olmalı. '
                              'Diğer PCB pencerelerindeki işini kaydedip kapat; taşıma başlatılmadı.')

    def apply(self, poses, expected_stamp):
        if self.needs_restart:
            raise LayoutError('Önceki işlemin iptali doğrulanamadı. PCB yerleşimini kontrol et; '
                              'KiCad PCB düzenleyicisini yeniden açtıktan sonra tekrar dene.')
        poses = list(poses)
        if not poses or len({p.uid for p in poses}) != len(poses):
            raise LayoutError('Yerleşim listesi boş veya aynı hedef birden fazla kez kullanılmış.')
        before = self.snapshot()
        if before.stamp != expected_stamp:
            raise LayoutError('PCB önizlemeden sonra değişti. Önizlemeyi yeniden oluştur.')
        # Validate and construct every target before opening any transaction.
        updates = []
        for pose in poses:
            original = before.objects.get(pose.ref)
            if original is None or uid(original) != pose.uid:
                raise LayoutError('Hedef komponent artık bulunamıyor: ' + pose.ref)
            if original.locked:
                raise LayoutError('Kilitli komponent: ' + pose.ref)
            current_side = 'B' if original.layer == BoardLayer.BL_B_Cu else 'F'
            if current_side != pose.side:
                raise LayoutError('Kart yüzü önizlemeden sonra değişti: ' + pose.ref)
            updates.append(moved_footprint(original, pose))
        def verify(results):
            by_id = {uid(fp): fp for fp in results if isinstance(fp, FootprintInstance)}
            if set(by_id) != {p.uid for p in poses}:
                raise LayoutError('KiCad tüm komponentleri güncelleyemedi.')
            for pose in poses:
                actual = describe(by_id[pose.uid])
                prior = before.components[pose.ref]
                old_fp = before.objects[pose.ref]
                new_fp = by_id[pose.uid]
                models_ok = ([m.proto.SerializeToString() for m in old_fp.definition.models]
                             == [m.proto.SerializeToString() for m in new_fp.definition.models])
                pads_ok = ([p.id.value for p in old_fp.definition.pads]
                           == [p.id.value for p in new_fp.definition.pads])
                angle_error = (actual.angle-pose.angle+180) % 360-180
                if (math.hypot(actual.x-pose.x, actual.y-pose.y) > .000003
                        or abs(angle_error) > .00001 or actual.side != pose.side
                        or actual.pins != prior.pins or actual.kind != prior.kind
                        or not models_ok or not pads_ok):
                    raise LayoutError('KiCad istenen yerleşimi doğrulamadı: ' + pose.ref)
        self.write_transaction(updates, verify, 'Yerleşim Kopyala: bağlantıya göre grup yerleşimi')
        return len(poses)

    def apply_edits(self, plan):
        from footprint_edits import plan_edits, verify_result
        if self.needs_restart:
            raise LayoutError('Önceki işlemin iptali doğrulanamadı. PCB yerleşimini kontrol et; '
                              'KiCad PCB düzenleyicisini yeniden açtıktan sonra tekrar dene.')
        before = self.edits_snapshot()
        fresh = plan_edits(before, plan.source, plan.targets, plan.options)
        if fresh.stamp != plan.stamp:
            raise LayoutError('PCB önizlemeden sonra değişti. Önizlemeyi yeniden oluştur.')
        if fresh.rejected or not fresh.updates:
            raise LayoutError('Uyumsuz hedefleri kaldırıp yeniden önizle.')
        def verify(results):
            actual = {uid(fp): fp for fp in results if isinstance(fp, FootprintInstance)}
            if len(results) != len(fresh.updates) or set(actual) != {uid(fp) for fp in fresh.updates}:
                raise LayoutError('KiCad tüm komponentleri güncelleyemedi.')
            for expected in fresh.updates:
                verify_result(expected, actual[uid(expected)])
        self.write_transaction(fresh.updates, verify, 'Yerleşim Kopyala: footprint düzenlemeleri')
        return len(fresh.updates)

    def write_transaction(self, updates, verify, description):
        """Both tabs use the same guarded transaction and uncertain-reply recovery."""
        self.check_write_context()
        commit = None
        phase = 'başlatma'
        try:
            commit = self.request('taşıma işlemini başlatma', self.board.begin_commit)
            phase = 'güncelleme'
            results = self.request('komponent yerleşimini güncelleme', self.board.update_items, updates)
            verify(results)
            phase = 'tamamlama'
            self.request('taşıma işlemini tamamlama', self.board.push_commit, commit, tr(description))
        except KiCadConnectionError as error:
            failed_stage, duration = self.last_stage, self.last_duration
            try:
                self.reconnect()
                cancelled = self.drop_own_commit(commit)
            except Exception as cleanup_error:
                self.needs_restart = True
                raise LayoutError(f'KiCad yanıtı alınamadı ({failed_stage}, {duration:.1f} sn). '
                                  'Bağlantı/işlem iptali doğrulanamadı. PCB yerleşimini kontrol et; '
                                  'aktif taşıma veya özellik penceresini bitir. KiCad PCB düzenleyicisini '
                                  f'yeniden açman gerekebilir. Ayrıntı: {cleanup_error}') from error
            if phase == 'başlatma':
                result = 'Komponent güncelleme çağrısı gönderilmedi.'
            elif cancelled:
                result = 'Yarım kalan taşıma işlemi iptal edildi; değişiklikler geri alındı.'
            else:
                result = ('İşlemin sonucu kesinleştirilemedi; tamamlanmış olabilir. '
                          'PCB yerleşimini kontrol et.')
            raise LayoutError(f'KiCad yanıtı alınamadı ({failed_stage}, {duration:.1f} sn). '
                              f'{result} Bağlantı yenilendi. PCB içindeki aktif işlemi/özellik '
                              'penceresini bitirip yeniden önizle. Taşıma otomatik tekrarlanmadı.') from error
        except Exception as error:
            if commit is not None:
                try:
                    if not self.drop_own_commit(commit):
                        raise LayoutError('Bu istemciye ait açık işlem bulunamadı.')
                except Exception as cleanup_error:
                    self.needs_restart = True
                    raise LayoutError(f'Taşıma başarısız: {error}. İptal doğrulanamadı: '
                                      f'{cleanup_error}. PCB yerleşimini kontrol et.') from error
            raise
