"""Project-local geometry transfer for the pinned KiCad 10 / kipy 0.7.1 API.

Children have absolute board coordinates. Never replace the target instance
with the source instance: symbol linkage, field contents and pad nets belong
to the target. Pure planning; this module does not open or save a board.
"""
from dataclasses import dataclass
import hashlib
import uuid

from kipy.board_types import (FootprintInstance, Pad, BoardShape, BoardText,
                             Field, Zone, Footprint3DModel)
from kipy.proto.board.board_types_pb2 import BoardLayer
from core import LayoutError


@dataclass(frozen=True)
class EditOptions:
    pads: bool = True
    graphics: bool = True
    field_format: bool = False


@dataclass
class EditPlan:
    source: str
    targets: tuple
    options: EditOptions
    stamp: str
    updates: list
    rejected: dict
    rows: list
    source_side: str = ''


def geometry_stamp(objects, refs):
    digest = hashlib.sha256()
    for ref in sorted(set(refs)):
        if ref not in objects:
            raise LayoutError('Komponent artık bulunamıyor: ' + ref)
        digest.update(ref.encode('utf-8') + b'\0')
        digest.update(objects[ref].proto.SerializeToString(deterministic=True))
    return digest.hexdigest()


def pad_map(fp):
    result = {}
    for pad in fp.definition.pads:
        if pad.number in result:
            raise LayoutError('Yinelenen veya birden fazla numarasız pad güvenle eşleştirilemiyor.')
        if not pad.number and pad.net.name:
            raise LayoutError('Numarasız pad bir ağa bağlı; aktarım engellendi.')
        result[pad.number] = pad
    return result


def validate_items(fp):
    supported = (Pad, BoardShape, BoardText, Field, Zone, Footprint3DModel)
    if any(not isinstance(item, supported) for item in fp.definition.items):
        raise LayoutError('Desteklenmeyen footprint alt öğesi var; aktarım engellendi.')


GRAPHIC_LAYERS = {getattr(BoardLayer, 'BL_' + name) for name in (
    'F_SilkS', 'B_SilkS', 'F_Fab', 'B_Fab', 'F_CrtYd', 'B_CrtYd',
    'F_Mask', 'B_Mask', 'F_Paste', 'B_Paste', 'Dwgs_User', 'Cmts_User',
    'Eco1_User', 'Eco2_User')}


def graphics(fp):
    return [item for item in fp.definition.items if isinstance(item, (BoardShape, BoardText))]


def transfer(source, target, options, copper_count=2):
    # Lazy import avoids a transport dependency cycle.
    from adapter import moved_footprint
    from core import Pose
    validate_items(source)
    validate_items(target)
    if target.locked:
        raise LayoutError('Kilitli komponent: ' + target.reference_field.text.value)
    if not (options.pads or options.graphics or options.field_format):
        raise LayoutError('En az bir aktarım seçeneği seç.')
    src_pads, dst_pads = pad_map(source), pad_map(target)
    if set(src_pads) != set(dst_pads):
        raise LayoutError('Kaynak ve hedef pad numaraları farklı; pad ekleme/silme yapılmaz.')
    if options.graphics:
        if any(item.layer not in GRAPHIC_LAYERS for fp in (source, target) for item in graphics(fp)):
            raise LayoutError('Bakır veya desteklenmeyen katmanda çizim var; çizim aktarımı engellendi.')
    ref = target.reference_field.text.value
    side = 'B' if target.layer == BoardLayer.BL_B_Cu else 'F'
    template = source
    if source.layer != target.layer:
        from footprint_flip import flipped_template
        template = flipped_template(source, copper_count)
    transformed = moved_footprint(template, Pose(ref, target.id.value,
        target.position.x / 1e6, target.position.y / 1e6,
        target.orientation.degrees, side, source.reference_field.text.value))
    aligned = pad_map(transformed)
    updated = FootprintInstance(target.proto)
    # Change only the geometry subset. Target symbol-pin metadata, UUID,
    # number, lock and complete net message remain intact.
    if options.pads:
        for pad in updated.definition.pads:
            origin = aligned[pad.number].proto
            for name in ('type', 'pad_stack', 'position', 'copper_clearance_override'):
                field = origin.DESCRIPTOR.fields_by_name[name]
                if field.message_type:
                    if origin.HasField(name):
                        getattr(pad.proto, name).CopyFrom(getattr(origin, name))
                    else:
                        pad.proto.ClearField(name)
                else:
                    setattr(pad.proto, name, getattr(origin, name))
            prior_layers = {layer.layer: layer for layer in dst_pads[pad.number].proto.pad_stack.copper_layers}
            for layer in pad.proto.pad_stack.copper_layers:
                previous = prior_layers.get(layer.layer)
                for index, primitive in enumerate(layer.custom_shapes):
                    if previous is not None and index < len(previous.custom_shapes):
                        primitive.id.CopyFrom(previous.custom_shapes[index].id)
                    else:
                        primitive.id.value = str(uuid.uuid5(uuid.NAMESPACE_URL,
                            'layout-clone-pad:' + pad.id.value + ':' + str(layer.layer) + ':' + str(index) + ':' + primitive.id.value))
    if options.graphics:
        previous = graphics(updated)
        replacement = []
        for index, item in enumerate(graphics(transformed)):
            # Keep existing target graphic identity when the slot/type agrees.
            # Otherwise derive a fresh, target-specific UUID, never source IDs.
            if (index < len(previous)
                    and previous[index].proto.DESCRIPTOR.full_name == item.proto.DESCRIPTOR.full_name):
                item.proto.id.CopyFrom(previous[index].proto.id)
            else:
                item.proto.id.value = str(uuid.uuid5(uuid.NAMESPACE_URL,
                    'layout-clone:' + target.id.value + ':' + item.id.value + ':' + str(index)))
            if isinstance(item, BoardShape):
                item.proto.ClearField('net')  # Non-copper graphics have no copied electrical net.
            replacement.append(item)
        updated.definition.items = [item for item in updated.definition.items
            if not isinstance(item, (BoardShape, BoardText))] + replacement
    if options.field_format:
        for name in ('reference_field', 'value_field'):
            old = getattr(updated, name)
            text = old.text.value
            field = getattr(transformed, name)
            field.proto.id.CopyFrom(old.proto.id)
            field.proto.name = old.proto.name
            field.text.value = text
            setattr(updated, name, field)
    return updated


def plan_edits(snapshot, source, targets, options=EditOptions()):
    targets = tuple(targets)
    if source not in snapshot.objects or not targets:
        raise LayoutError('Bir kaynak ve en az bir hedef footprint seç.')
    if source in targets or len(set(targets)) != len(targets):
        raise LayoutError('Kaynak hedef olarak kullanılamaz; hedefler benzersiz olmalı.')
    stamp = geometry_stamp(snapshot.objects, (source,) + targets)
    if any(snapshot.objects[source].layer != snapshot.objects[ref].layer for ref in targets):
        stamp += ':' + str(snapshot.copper_count)
    updates, rejected, rows = [], {}, []
    for ref in targets:
        try:
            original = snapshot.objects[ref]
            update = transfer(snapshot.objects[source], original, options, snapshot.copper_count)
            updates.append(update)
            changes = sum(p.proto.SerializeToString() != pad_map(original)[p.number].proto.SerializeToString()
                          for p in update.definition.pads)
            rows.append((ref, changes, len(graphics(original)), len(graphics(update))))
        except LayoutError as error:
            rejected[ref] = ValueError.__str__(error)
    side = 'B' if snapshot.objects[source].layer == BoardLayer.BL_B_Cu else 'F'
    return EditPlan(source, targets, options, stamp, updates, rejected, rows, side)


def suggestions(snapshot, source, excluded=()):
    """Return reasons, never mutate a selection or automatically add targets."""
    fp = snapshot.objects[source]
    result = []
    for ref, candidate in snapshot.objects.items():
        if ref == source or ref in excluded:
            continue
        reasons = []
        if str(fp.definition.id) == str(candidate.definition.id):
            reasons.append('Footprint kimliği')
        if fp.value_field.text.value and fp.value_field.text.value == candidate.value_field.text.value:
            reasons.append('Değer')
        desc = fp.description_field.text.value or fp.proto.definition.attributes.description
        other = candidate.description_field.text.value or candidate.proto.definition.attributes.description
        if desc and desc == other:
            reasons.append('Açıklama')
        if reasons:
            result.append((ref, reasons))
    return result


def verify_result(expected, actual):
    """Compare complete intended instances, allowing integer rounding only.

    KiCad may reorder repeated child messages during serialization. Match
    footprint children by UUID (3D models by content), not list position.
    """
    def compare(a, b):
        for field in a.DESCRIPTOR.fields:
            va, vb = getattr(a, field.name), getattr(b, field.name)
            if field.label == field.LABEL_REPEATED:
                if len(va) != len(vb):
                    return False
                if field.name == 'items':
                    # Any payloads have to be unpacked before tolerant comparison.
                    from kipy.board_types import unwrap
                    aa = [unwrap(v) for v in va]; bb = [unwrap(v) for v in vb]
                    def key(v):
                        return (v.proto.DESCRIPTOR.full_name, getattr(getattr(v, 'id', None), 'value',
                            v.proto.SerializeToString().hex()))
                    if sorted(map(key, aa)) != sorted(map(key, bb)):
                        return False
                    aa.sort(key=key); bb.sort(key=key)
                    if not all(compare(x.proto, y.proto) for x, y in zip(aa, bb)):
                        return False
                elif field.message_type:
                    if field.name == 'copper_layers':
                        va, vb = sorted(va, key=lambda item: item.layer), sorted(vb, key=lambda item: item.layer)
                    if not all(compare(x, y) for x, y in zip(va, vb)):
                        return False
                elif field.name == 'layers':
                    if set(va) != set(vb):
                        return False
                elif list(va) != list(vb):
                    return False
            elif field.message_type:
                # Presence distinguishes an explicit zero override from inheriting
                # the parent's value. KiCad also emits harmless empty containers
                # (e.g. net) so only enforce presence on optional value wrappers.
                if any(f.name in ('value_nm', 'value') for f in field.message_type.fields):
                    if a.HasField(field.name) != b.HasField(field.name):
                        return False
                if not compare(va, vb):
                    return False
            elif field.name in ('x_nm', 'y_nm'):
                if abs(va - vb) > 3:
                    return False
            elif field.name == 'value_degrees':
                if abs((va - vb + 180) % 360 - 180) > 0.00001:
                    return False
            elif va != vb:
                return False
        return True
    if not compare(expected.proto, actual.proto):
        raise LayoutError('KiCad footprint düzenlemesini doğrulamadı: ' + expected.reference_field.text.value)
