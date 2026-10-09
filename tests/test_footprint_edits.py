"""Standalone regressions for separate paste apertures; no user PCB data or IPC."""
from pathlib import Path
import sys
import unittest
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'plugins'))
from kipy.board_types import FootprintInstance, Pad, BoardShape
from kipy.geometry import Vector2, Angle
from kipy.proto.board.board_types_pb2 import BoardLayer as L
from core import LayoutError, Pose
from adapter import moved_footprint
from footprint_edits import EditOptions, transfer, pad_map, graphics
from footprint_flip import flipped_template


def footprint(ref, courtyard):
    fp = FootprintInstance()
    fp.proto.id.value = str(uuid.uuid5(uuid.NAMESPACE_URL, ref))
    fp.reference_field.text.value = ref
    fp.layer = L.BL_F_Cu
    fp.position = Vector2.from_xy_mm(10 if ref == 'R1' else 20, 10)
    fp.orientation = Angle.from_degrees(0)
    items = []
    for number, x in [('1', -320000), ('2', 320000)]:
        pad = Pad()
        pad.proto.id.value = str(uuid.uuid5(uuid.NAMESPACE_URL, ref + number))
        pad.number = number
        pad.proto.type = 2  # SMD
        pad.position = Vector2.from_xy(fp.position.x + x, fp.position.y)
        pad.proto.net.name = ref + '-net-' + number
        pad.proto.pad_stack.layers.extend([L.BL_F_Cu, L.BL_F_Mask])
        pad.proto.pad_stack.copper_layers[0].size.x_nm = 300000
        pad.proto.pad_stack.copper_layers[0].size.y_nm = 350000
        paste = Pad(pad.proto)
        paste.proto.id.value = str(uuid.uuid5(uuid.NAMESPACE_URL, ref + '-paste-' + number))
        paste.number = ''
        paste.proto.net.Clear()
        paste.proto.position.x_nm += -25000 if number == '1' else 25000
        del paste.proto.pad_stack.layers[:]
        paste.proto.pad_stack.layers.append(L.BL_F_Paste)
        items.extend([paste, pad])
    if courtyard:
        shape = BoardShape()
        shape.proto.id.value = str(uuid.uuid5(uuid.NAMESPACE_URL, ref + '-courtyard'))
        shape.layer = L.BL_F_CrtYd
        shape.proto.shape.segment.start.CopyFrom(Vector2.from_xy_mm(9, 9).proto)
        shape.proto.shape.segment.end.CopyFrom(Vector2.from_xy_mm(11, 9).proto)
        items.append(shape)
    fp.definition.items = items
    return fp


class PasteApertureTests(unittest.TestCase):
    def test_courtyard_addition_and_removal_keep_pad_identity_and_nets(self):
        for present in (True, False):
            source, target = footprint('R1', present), footprint('R2', not present)
            target.definition.items = list(reversed(target.definition.items))
            after = transfer(source, target, EditOptions())
            self.assertEqual(any(g.layer == L.BL_F_CrtYd for g in graphics(after)), present)
            self.assertEqual(len(after.definition.pads), 4)
            for key, pad in pad_map(after).items():
                self.assertEqual(pad.id, pad_map(target)[key].id)
                self.assertEqual(pad.net, pad_map(target)[key].net)
                self.assertEqual(pad.proto.symbol_pin, pad_map(target)[key].proto.symbol_pin)

    def test_paste_geometry_is_copied_by_anchor_not_item_order(self):
        source, target = footprint('R1', True), footprint('R2', False)
        pad_map(source)[('paste', '1', True)].proto.pad_stack.copper_layers[0].size.x_nm = 190000
        target.definition.items = list(reversed(target.definition.items))
        after = transfer(source, target, EditOptions())
        self.assertEqual(pad_map(after)[('paste', '1', True)].proto.pad_stack.copper_layers[0].size.x_nm, 190000)
        self.assertEqual(pad_map(after)[('paste', '2', True)].proto.pad_stack.copper_layers[0].size.x_nm, 300000)

    def test_rotated_opposite_side_keeps_target_pose_and_paste_layer(self):
        source, target = footprint('R1', True), footprint('R2', False)
        target = flipped_template(target, 6)
        target = moved_footprint(target, Pose('R2', target.id.value, 30, 40, 37, 'B', 'R2'))
        after = transfer(source, target, EditOptions(), 6)
        self.assertEqual(after.position, target.position)
        self.assertEqual(after.orientation, target.orientation)
        self.assertEqual(after.layer, L.BL_B_Cu)
        for key, pad in pad_map(after).items():
            self.assertEqual(pad.id, pad_map(target)[key].id)
            if isinstance(key, tuple):
                self.assertEqual(list(pad.proto.pad_stack.layers), [L.BL_B_Paste])

    def test_graphics_only_preserves_pads_without_matching(self):
        source, target = footprint('R1', True), footprint('R2', False)
        target.definition.pads[-1].number = '1'
        before = [p.proto.SerializeToString() for p in target.definition.pads]
        after = transfer(source, target, EditOptions(False, True))
        self.assertEqual([p.proto.SerializeToString() for p in after.definition.pads], before)
        with self.assertRaises(LayoutError):
            transfer(source, target, EditOptions())

    def test_ambiguous_or_duplicate_paste_anchor_is_rejected(self):
        source, target = footprint('R1', True), footprint('R2', False)
        aperture = next(p for p in target.definition.pads if not p.number)
        aperture.position = target.position
        with self.assertRaises(LayoutError):
            transfer(source, target, EditOptions())
        target = footprint('R2', False)
        duplicate = Pad(next(p for p in target.definition.pads if not p.number).proto)
        duplicate.proto.id.value = 'duplicate'
        target.definition.items = list(target.definition.items) + [duplicate]
        with self.assertRaises(LayoutError):
            transfer(source, target, EditOptions())

    def test_missing_or_net_connected_aperture_is_rejected(self):
        source, target = footprint('R1', True), footprint('R2', False)
        aperture = next(p for p in target.definition.pads if not p.number)
        aperture.proto.net.name = 'invalid-paste-net'
        with self.assertRaises(LayoutError):
            transfer(source, target, EditOptions())
        target.definition.items = [i for i in target.definition.items if not isinstance(i, Pad) or i.number]
        with self.assertRaises(LayoutError):
            transfer(source, target, EditOptions())


if __name__ == '__main__':
    unittest.main()
