"""Synthetic regressions for automatic footprint-local 3D model transfer."""
from pathlib import Path
import sys
import unittest

sys.path[:0] = [str(Path(__file__).resolve().parents[1] / 'plugins'),
               str(Path(__file__).resolve().parent)]
from kipy.board_types import Footprint3DModel, FootprintInstance
from kipy.proto.board.board_types_pb2 import BoardLayer as L
from core import LayoutError, Pose
from adapter import Snapshot, moved_footprint
from footprint_edits import EditOptions, plan_edits, transfer, verify_result
from footprint_flip import flipped_template
from test_footprint_edits import footprint


def model(filename, hidden=False):
    result = Footprint3DModel()
    result.proto.filename = filename
    result.proto.scale.x_nm, result.proto.scale.y_nm, result.proto.scale.z_nm = 1.2, .8, 2.0
    result.proto.rotation.x_nm, result.proto.rotation.y_nm, result.proto.rotation.z_nm = 90., 12.5, -90.
    # KiCad serializes local offsets in mm despite these generic proto names.
    result.proto.offset.x_nm, result.proto.offset.y_nm, result.proto.offset.z_nm = 3.07, -1.66, 1.3
    result.proto.visible = not hidden
    result.proto.opacity = .35 if hidden else 1.
    return result


def set_models(fp, models):
    fp.definition.items = [i for i in fp.definition.items
                           if not isinstance(i, Footprint3DModel)] + list(models)


def model_bytes(fp):
    return [m.proto.SerializeToString(deterministic=True) for m in fp.definition.models]


class AutomaticModelTests(unittest.TestCase):
    def test_complete_source_list_replaces_existing_models_with_every_edit_scope(self):
        for options in (EditOptions(), EditOptions(True, False),
                        EditOptions(False, True), EditOptions(False, False, True),
                        EditOptions(False, False, False)):
            with self.subTest(options=options):
                source, target = footprint('R1', True), footprint('R2', False)
                set_models(source, [model('${KIPRJMOD}/models/SOT-523.step'),
                                    model('C:/models/second.wrl', hidden=True)])
                set_models(target, [model('old.step')])
                source_before, target_before = source.proto.SerializeToString(), target.proto.SerializeToString()
                after = transfer(source, target, options)
                self.assertEqual(model_bytes(after), model_bytes(source))
                self.assertEqual([m.proto.filename for m in after.definition.models],
                                 ['${KIPRJMOD}/models/SOT-523.step', 'C:/models/second.wrl'])
                second = after.definition.models[1].proto
                self.assertEqual((second.scale.x_nm, second.scale.y_nm, second.scale.z_nm), (1.2, .8, 2.))
                self.assertEqual((second.rotation.x_nm, second.rotation.y_nm, second.rotation.z_nm), (90., 12.5, -90.))
                self.assertEqual((second.offset.x_nm, second.offset.y_nm, second.offset.z_nm), (3.07, -1.66, 1.3))
                self.assertFalse(second.visible)
                self.assertEqual(second.opacity, .35)
                self.assertEqual(source.proto.SerializeToString(), source_before)
                self.assertEqual(target.proto.SerializeToString(), target_before)
                self.assertEqual(after.id, target.id)
                verify_result(after, FootprintInstance(after.proto))

    def test_model_transforms_are_local_across_board_faces_and_angles(self):
        for source_side in ('F', 'B'):
            for target_side in ('F', 'B'):
                for source_angle, target_angle in ((0., 37.), (90., -120.)):
                    with self.subTest(source_side=source_side, target_side=target_side,
                                      source_angle=source_angle, target_angle=target_angle):
                        source, target = footprint('R1', True), footprint('R2', False)
                        if source_side == 'B':
                            source = flipped_template(source, 6)
                        if target_side == 'B':
                            target = flipped_template(target, 6)
                        source = moved_footprint(source, Pose('R1', source.id.value, 10., 15., source_angle, source_side, 'R1'))
                        target = moved_footprint(target, Pose('R2', target.id.value, 30., 45., target_angle, target_side, 'R2'))
                        set_models(source, [model('local-model.step')])
                        set_models(target, [model('obsolete.wrl')])
                        after = transfer(source, target, EditOptions(), 6)
                        self.assertEqual(model_bytes(after), model_bytes(source))
                        self.assertEqual(after.position, target.position)
                        self.assertEqual(after.orientation, target.orientation)
                        self.assertEqual(after.layer, L.BL_F_Cu if target_side == 'F' else L.BL_B_Cu)
                        for old, new in zip(target.definition.pads, after.definition.pads):
                            self.assertEqual(old.id, new.id)
                            self.assertEqual(old.net, new.net)

    def test_empty_source_clears_target_models_and_preview_reports_counts(self):
        source, target = footprint('R1', True), footprint('R2', False)
        set_models(target, [model('old.step'), model('second.step')])
        snapshot = Snapshot({}, {'R1': source, 'R2': target}, {}, (), 'synthetic')
        plan = plan_edits(snapshot, 'R1', ['R2'])
        self.assertFalse(plan.rejected)
        self.assertEqual(plan.rows[0][-2:], (2, 0))
        self.assertEqual(model_bytes(plan.updates[0]), [])

    def test_embedded_model_payload_cannot_be_copied_as_a_reference_only(self):
        for filename in ('kicad-embed://model.step', 'KiCad-Embed://model.step'):
            with self.subTest(filename=filename):
                source, target = footprint('R1', True), footprint('R2', False)
                set_models(source, [model(filename)])
                before = target.proto.SerializeToString()
                with self.assertRaises(LayoutError):
                    transfer(source, target, EditOptions())
                self.assertEqual(target.proto.SerializeToString(), before)

    def test_copied_models_are_detached_and_verification_rejects_lost_model_properties(self):
        source, target = footprint('R1', True), footprint('R2', False)
        set_models(source, [model('source.step')])
        expected = transfer(source, target, EditOptions())
        expected_models = model_bytes(expected)
        source.definition.models[0].proto.offset.x_nm = 99.
        self.assertEqual(model_bytes(expected), expected_models)
        for field in ('filename', 'offset', 'rotation', 'scale', 'visible', 'opacity'):
            with self.subTest(field=field):
                actual = FootprintInstance(expected.proto)
                copied = actual.definition.models[0].proto
                if field in ('offset', 'rotation', 'scale'):
                    getattr(copied, field).x_nm += .01
                elif field == 'filename':
                    copied.filename = 'wrong.step'
                elif field == 'visible':
                    copied.visible = not copied.visible
                else:
                    copied.opacity = .2
                with self.assertRaises(LayoutError):
                    verify_result(expected, actual)


if __name__ == '__main__':
    unittest.main()
