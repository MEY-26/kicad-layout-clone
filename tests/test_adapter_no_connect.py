"""No-connect matching uses real IPC protobufs, never rewrites board pads."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'plugins'))
from adapter import KiCadAdapter, describe
from core import LayoutError, build_graph, discover_group
from kipy.board_types import FootprintInstance, Pad
from kipy.proto.common.types import KIID


AUTO_SH = 'unconnected-(J17-SHIELD-PadSH)'


def footprint(ref, pads):
    """Build a source object with realistic duplicate numbers and distinct IDs."""
    fp = FootprintInstance()
    fp.proto.id.value = ref + '-footprint'
    fp.reference_field.text.value = ref
    fp.value_field.text.value = 'USB-C' if ref.startswith('J') else 'IC'
    items = []
    for index, (number, net, no_connect) in enumerate(pads):
        pad = Pad()
        pad.proto.id.value = f'{ref}-pad-{index}'
        pad.number = number
        pad.proto.net.name = net
        pad.proto.net.code.value = index + 1
        pad.proto.symbol_pin.no_connect = no_connect
        items.append(pad)
    fp.definition.items = items
    return fp


def j17():
    return footprint('J17', [
        ('SH', AUTO_SH + suffix, True) for suffix in ('', '_1', '_2', '_3')
    ] + [('A1', 'GND', False), ('A4', 'VBUS', False)])


class ReadOnlyBoard:
    """Deliberately exposes no mutation API: snapshot must only read it."""
    def __init__(self, footprints):
        self.document = KIID(value='synthetic-board')
        self.footprints = footprints

    def get_footprints(self):
        return self.footprints

    def get_groups(self):
        return []

    def get_selection(self):
        return [self.footprints[0]]

    def get_copper_layer_count(self):
        return 8


class ReadOnlyKiCad:
    def __init__(self, footprints):
        self.board = ReadOnlyBoard(footprints)

    def get_board(self):
        return self.board


class AdapterNoConnectTests(unittest.TestCase):
    def test_j17_four_auto_named_shield_pads_are_accepted(self):
        fp = j17()
        # Ordering is irrelevant; duplicate pad numbers remain one logical pin.
        items = list(fp.definition.items)
        for ordered in (items, list(reversed(items))):
            with self.subTest(reversed=ordered != items):
                fp.definition.items = ordered
                self.assertEqual(dict(describe(fp).pins),
                                 {'SH': '', 'A1': 'GND', 'A4': 'VBUS'})

    def test_conflicting_real_nets_are_rejected_even_with_no_connect_flags(self):
        for flags in ((False, False), (True, True), (True, False), (False, True)):
            for nets in (('GND', 'VBUS'), ('VBUS', 'GND')):
                with self.subTest(flags=flags, nets=nets):
                    fp = footprint('J17', [('SH', net, flag)
                                          for net, flag in zip(nets, flags)])
                    with self.assertRaises(LayoutError):
                        describe(fp)

    def test_auto_name_without_no_connect_flag_cannot_bypass_conflict(self):
        for nets in ((AUTO_SH, AUTO_SH + '_1'), (AUTO_SH, ''),
                     (AUTO_SH, 'GND')):
            for ordered in (nets, nets[::-1]):
                with self.subTest(nets=ordered):
                    fp = footprint('J17', [('SH', net, False) for net in ordered])
                    with self.assertRaises(LayoutError):
                        describe(fp)

    def test_connected_and_auto_no_connect_duplicate_pad_is_rejected(self):
        for connected in ('GND', 'VBUS', AUTO_SH, AUTO_SH + '_1'):
            pads = [('SH', AUTO_SH, True), ('SH', connected, False)]
            for ordered in (pads, pads[::-1]):
                with self.subTest(connected=connected, reversed=ordered != pads):
                    with self.assertRaises(LayoutError):
                        describe(footprint('J17', ordered))

    def test_only_exact_generated_prefix_is_normalized(self):
        for name in ('Unconnected-(J17-SHIELD-PadSH)', 'unconnected-J17',
                     'prefix-unconnected-(J17-SHIELD-PadSH)', 'unconnected',
                     'GND', 'VBUS', ''):
            with self.subTest(name=name):
                self.assertEqual(describe(footprint('J17', [('SH', name, True)])).net('SH'),
                                 name)

    def test_real_same_net_duplicates_remain_connected(self):
        for no_connect in (False, True):
            with self.subTest(no_connect=no_connect):
                fp = footprint('J17', [('SH', 'GND', no_connect)] * 4)
                self.assertEqual(describe(fp).pins, (('SH', 'GND'),))

    def test_auto_no_connect_and_empty_open_duplicate_are_accepted(self):
        # Both are open in the matching model; neither is a real connected net.
        pads = [('SH', AUTO_SH, True), ('SH', '', True)]
        for ordered in (pads, pads[::-1]):
            with self.subTest(reversed=ordered != pads):
                self.assertEqual(describe(footprint('J17', ordered)).pins, (('SH', ''),))

    def test_different_open_pins_are_distinct_graph_nodes(self):
        # Deliberately reuse one generated label to detect accidental graph edges.
        first = footprint('U1', [('1', AUTO_SH, True), ('2', AUTO_SH, True)])
        second = footprint('U2', [('1', AUTO_SH, True), ('2', AUTO_SH, True)])
        components = {fp.reference_field.text.value: describe(fp)
                      for fp in (first, second)}
        graph = build_graph(components, components, 'U1', set())
        nodes = list(graph.pin_nets.values())
        self.assertEqual(len(set(nodes)), 4)
        self.assertTrue(all(len(graph.edges[node]) == 1 for node in nodes))
        self.assertEqual(discover_group(components, 'U1'), ['U1'])

    def test_describe_does_not_mutate_any_real_pad_data(self):
        fp = j17()
        before = fp.proto.SerializeToString()
        original_pads = [pad.proto.SerializeToString() for pad in fp.definition.pads]
        describe(fp)
        self.assertEqual(fp.proto.SerializeToString(), before)
        self.assertEqual([pad.proto.SerializeToString() for pad in fp.definition.pads],
                         original_pads)
        self.assertEqual([pad.net.name for pad in fp.definition.pads[:4]],
                         [AUTO_SH + suffix for suffix in ('', '_1', '_2', '_3')])

    def test_board_snapshot_reads_j17_without_rewriting_source_objects(self):
        connector = j17()
        other = footprint('U1', [('1', 'GND', False), ('2', 'VBUS', False)])
        footprints = [connector, other]
        before = [fp.proto.SerializeToString() for fp in footprints]
        snapshot = KiCadAdapter(ReadOnlyKiCad(footprints)).snapshot()
        self.assertEqual(set(snapshot.components), {'J17', 'U1'})
        self.assertEqual(snapshot.components['J17'].net('SH'), '')
        self.assertEqual(snapshot.components['U1'].pins, (('1', 'GND'), ('2', 'VBUS')))
        self.assertEqual(snapshot.selected, ('J17',))
        self.assertEqual(snapshot.copper_count, 8)
        self.assertIs(snapshot.objects['J17'], connector)
        self.assertEqual([fp.proto.SerializeToString() for fp in footprints], before)


if __name__ == '__main__':
    unittest.main()
