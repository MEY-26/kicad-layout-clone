"""Automatic placement-side transfer using real IPC objects, without live IPC."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'plugins'))
from placement_fixture import footprint
from adapter import moved_footprint, describe
from core import Pose, LayoutError
from footprint_flip import flipped_footprint
from kipy.board_types import Field, Footprint3DModel, Zone
from kipy.geometry import Vector2, Angle
from kipy.proto.board.board_types_pb2 import BoardLayer as L


def detailed_target():
    fp = footprint('R2',True)
    items = list(fp.definition.items)
    # Asymmetric coordinates expose a fake layer-only flip.
    items[0].proto.position.y_nm += 110000
    items[0].proto.pad_stack.copper_layers[0].offset.y_nm = 45000
    field = Field()
    field.proto.name = 'MPN'
    field.text.value = 'Example target MPN'
    field.text.position = Vector2.from_xy_mm(20.2,9.6)
    field.layer = L.BL_F_Fab
    model = Footprint3DModel()
    model.proto.filename = 'example-target.step'
    items.extend([field,model])
    fp.reference_field.layer = L.BL_F_SilkS
    fp.reference_field.text.position = Vector2.from_xy_mm(20,8.8)
    fp.value_field.layer = L.BL_F_Fab
    fp.definition.items = items
    return fp


class PlacementSideTests(unittest.TestCase):
    def test_full_target_flip_preserves_ids_nets_fields_and_models(self):
        original = detailed_target()
        original_bytes = original.proto.SerializeToString()
        flipped = flipped_footprint(original,6)
        self.assertEqual(original.proto.SerializeToString(),original_bytes)
        self.assertEqual(flipped.layer,L.BL_B_Cu)
        self.assertEqual(flipped.id,original.id)
        self.assertEqual(describe(flipped).pins,describe(original).pins)
        self.assertEqual([m.proto for m in flipped.definition.models],
                         [m.proto for m in original.definition.models])
        for old,new in zip(original.definition.pads,flipped.definition.pads):
            self.assertEqual(new.id,old.id)
            self.assertEqual(new.net,old.net)
            self.assertEqual(new.position.x,old.position.x)
            self.assertEqual(new.position.y,2*original.position.y-old.position.y)
            expected={L.BL_F_Cu:L.BL_B_Cu,L.BL_F_Paste:L.BL_B_Paste,L.BL_F_Mask:L.BL_B_Mask}
            self.assertEqual(list(new.proto.pad_stack.layers),
                             [expected.get(l,l) for l in old.proto.pad_stack.layers])
        self.assertEqual(flipped.reference_field.layer,L.BL_B_SilkS)
        field = next(i for i in flipped.definition.items if isinstance(i,Field))
        self.assertEqual(field.layer,L.BL_B_Fab)
        self.assertEqual(field.proto.name,'MPN')
        self.assertEqual(field.text.value,'Example target MPN')
        self.assertEqual(field.text.position.y,2*original.position.y-9600000)
        self.assertEqual(len(flipped.definition.items),len(original.definition.items))

    def test_full_flip_round_trip_keeps_complete_target(self):
        original = detailed_target()
        twice = flipped_footprint(flipped_footprint(original,6),6)
        from footprint_edits import verify_result
        verify_result(original,twice)

    def test_flip_then_move_both_directions_keeps_target_identity(self):
        for source_side in ['F','B']:
            for destination_side in ['F','B']:
                with self.subTest(source=source_side,destination=destination_side):
                    original = detailed_target()
                    if source_side=='B':original = flipped_footprint(original,6)
                    raw = original.proto.SerializeToString()
                    pose = Pose('R2',original.id.value,31.2,44.7,37,destination_side,'R1')
                    after = moved_footprint(original,pose,6)
                    self.assertEqual(original.proto.SerializeToString(),raw)
                    self.assertEqual(after.layer,L.BL_F_Cu if destination_side=='F' else L.BL_B_Cu)
                    self.assertAlmostEqual(after.orientation.degrees,37)
                    self.assertEqual(after.id,original.id)
                    self.assertEqual(describe(after).pins,describe(original).pins)
                    self.assertEqual(after.reference_field.text.value,'R2')
                    self.assertEqual([m.proto for m in after.definition.models],
                                     [m.proto for m in original.definition.models])

    def test_embedded_zone_is_not_silently_lost_by_flip(self):
        original = detailed_target()
        original.definition.items = list(original.definition.items)+[Zone()]
        with self.assertRaises(LayoutError):flipped_footprint(original,6)

    def test_flip_matches_kicad_cpp_pad_positions_and_layers(self):
        try:
            import pcbnew
        except ImportError:
            self.skipTest('Optional independent KiCad C++ flip oracle is unavailable')
        for start_side in ['F','B']:
            for angle in [0,37,-61,90]:
                with self.subTest(side=start_side,angle=angle):
                    fp = footprint('R2',False)
                    if start_side=='B':fp=flipped_footprint(fp,2)
                    fp=moved_footprint(fp,Pose('R2',fp.id.value,20,10,angle,start_side,'R2'))
                    cpp_board=pcbnew.BOARD()
                    cpp_fp=pcbnew.FOOTPRINT(cpp_board)
                    cpp_board.Add(cpp_fp)
                    cpp_fp.SetPosition(pcbnew.VECTOR2I(fp.position.x,fp.position.y))
                    cpp_fp.SetLayer(pcbnew.F_Cu if start_side=='F' else pcbnew.B_Cu)
                    cpp_fp.SetOrientationDegrees(angle)
                    for index,pad in enumerate(fp.definition.pads):
                        cpp_pad=pcbnew.PAD(cpp_fp)
                        cpp_pad.SetNumber(str(index))
                        cpp_pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
                        cpp_pad.SetShape(pcbnew.PAD_SHAPE_RECT)
                        cpp_pad.SetSize(pcbnew.VECTOR2I(300000,350000))
                        layers=pcbnew.LSET()
                        layers.AddLayer(pcbnew.F_Cu if start_side=='F' else pcbnew.B_Cu)
                        cpp_pad.SetLayerSet(layers)
                        cpp_pad.SetPosition(pcbnew.VECTOR2I(pad.position.x,pad.position.y))
                        cpp_pad.SetOrientationDegrees(pad.padstack.angle.degrees)
                        cpp_fp.Add(cpp_pad)
                    cpp_fp.Flip(cpp_fp.GetPosition(),pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
                    actual=flipped_footprint(fp,2)
                    self.assertAlmostEqual(cpp_fp.GetOrientationDegrees(),actual.orientation.degrees)
                    for expected in cpp_fp.Pads():
                        pad=actual.definition.pads[int(expected.GetNumber())]
                        self.assertLessEqual(abs(expected.GetPosition().x-pad.position.x),3)
                        self.assertLessEqual(abs(expected.GetPosition().y-pad.position.y),3)
                        self.assertAlmostEqual((expected.GetOrientationDegrees()-pad.padstack.angle.degrees+180)%360-180,0)
                        self.assertTrue(expected.IsOnLayer(pcbnew.B_Cu if start_side=='F' else pcbnew.F_Cu))


if __name__=='__main__':unittest.main()
