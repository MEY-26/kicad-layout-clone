import sys
import unittest
from dataclasses import replace
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'plugins'))
from core import *
from i18n import set_language


def part(ref, value, pins, x=0, y=0, angle=0, footprint=None, side='F', **kw):
    prefix = re.sub(r'\d+.*', '', ref)
    return Component(ref, ref+'-uuid', value, footprint or prefix+'-footprint',
                     tuple(sorted(pins.items())), x, y, angle, side, **kw)


def circuit():
    # Values/footprints are deliberately identical; only anchored pin topology
    # tells R1 and R2 apart. References/net names/order do not carry roles.
    parts = [
        part('U1','DRV',{'1':'ga','2':'gb','3':'GND'},10,20,90),
        part('R1','10R',{'1':'ga','2':'a'},13,22,0),
        part('R2','10R',{'1':'gb','2':'b'},8,24,90),
        part('U2','DRV',{'1':'tx','2':'ty','3':'GND'},50,70,180),
        part('R8','10R',{'1':'ty','2':'z'},48,77,0),
        part('R9','10R',{'1':'tx','2':'q'},45,71,90),
    ]
    return {p.ref:p for p in parts}


class CoreTests(unittest.TestCase):
    def setUp(self):
        set_language('tr')

    def matched(self, cs=None):
        cs = cs or circuit()
        return cs, match_groups(cs,['U1','R1','R2'],['R8','U2','R9'],'U1','U2')

    def test_connection_roles_beat_reference_order(self):
        cs, m = self.matched()
        self.assertEqual(m.candidates, {'U1':('U2',),'R1':('R9',),'R2':('R8',)})

    def test_rotations_use_kicad_y_down_coordinates(self):
        for sa in (0,90,180,-90,37.5):
            for ta in (0,90,180,-90,12.5):
                with self.subTest(sa=sa,ta=ta):
                    cs = circuit()
                    cs['U1']=replace(cs['U1'],angle=sa)
                    cs['U2']=replace(cs['U2'],angle=ta)
                    cs,m=self.matched(cs)
                    ps={p.ref:p for p in plan_placement(cs,m,m.suggestion)}
                    rad=math.radians(ta-sa)
                    self.assertAlmostEqual(ps['R9'].x,50+3*math.cos(rad)+2*math.sin(rad))
                    self.assertAlmostEqual(ps['R9'].y,70-3*math.sin(rad)+2*math.cos(rad))
                    self.assertEqual((ps['U2'].x,ps['U2'].y,ps['U2'].angle),(50,70,normalized(ta)))

    def test_extra_rotation_rotates_anchor_angle_not_position(self):
        cs,m=self.matched()
        ps={p.ref:p for p in plan_placement(cs,m,m.suggestion,extra_angle=90)}
        self.assertEqual((ps['U2'].x,ps['U2'].y,ps['U2'].angle),(50,70,-90))

    def test_mirror_changes_centres_only_and_preserves_faces(self):
        cs=circuit();cs['U1']=replace(cs['U1'],angle=0);cs['U2']=replace(cs['U2'],angle=0)
        cs,m=self.matched(cs)
        x={p.ref:p for p in plan_placement(cs,m,m.suggestion,'x')}
        y={p.ref:p for p in plan_placement(cs,m,m.suggestion,'y')}
        self.assertEqual((x['R9'].x,x['R9'].y),(53,68))
        self.assertEqual((y['R9'].x,y['R9'].y),(47,72))
        self.assertEqual(x['R9'].side,'F')
        self.assertEqual(x['U2'].angle,0)

    def test_resistor_terminal_swap_compensates_angle(self):
        cs=circuit();cs['R9']=replace(cs['R9'],pins=(('1','q'),('2','tx')))
        cs,m=self.matched(cs)
        p=next(p for p in plan_placement(cs,m,m.suggestion) if p.ref=='R9')
        self.assertTrue(p.pin_swap)
        self.assertEqual(p.angle,-90)

    def test_parallel_passives_are_reported_as_ambiguous(self):
        cs=circuit()
        for r in ('R1','R2'):cs[r]=replace(cs[r],pins=(('1','ga'),('2','GND')))
        for r in ('R8','R9'):cs[r]=replace(cs[r],pins=(('1','tx'),('2','GND')))
        cs,m=self.matched(cs)
        self.assertEqual(set(m.candidates['R1']),{'R8','R9'})
        self.assertEqual(set(m.candidates['R2']),{'R8','R9'})
        self.assertEqual(len(plan_placement(cs,m,m.suggestion)),3)

    def test_invalid_bijection_and_wrong_connections_are_rejected(self):
        cs,m=self.matched()
        for mapping in ({'U1':'U2','R1':'R8','R2':'R9'}, {'U1':'U2','R1':'R9','R2':'R9'}):
            with self.assertRaises(LayoutError):plan_placement(cs,m,mapping)

    def test_values_and_polarized_capacitor_pins_are_not_interchangeable(self):
        cs=circuit();cs['R9']=replace(cs['R9'],value='100R')
        with self.assertRaises(LayoutError):self.matched(cs)
        self.assertFalse(part('C1','10u',{'1':'v','2':'GND'},footprint='Capacitor:CP_Elec').nonpolar)
        self.assertTrue(part('C1','10u',{'1':'v','2':'GND'},footprint='Capacitor:C_0402').nonpolar)

    def test_locked_targets_and_overlapping_batches_are_rejected(self):
        cs=circuit();cs['R8']=replace(cs['R8'],locked=True)
        cs,m=self.matched(cs)
        with self.assertRaises(LayoutError):plan_placement(cs,m,m.suggestion)
        with self.assertRaises(LayoutError):validate_batch(['U1'],[['U2'],['U2']])
        with self.assertRaises(LayoutError):validate_batch(['U1'],[['U1']])

    def test_unconnected_pins_are_not_a_shared_net_zero(self):
        cs,m=self.matched()
        cs['R1']=replace(cs['R1'],pins=(('1','ga'),('2','')))
        cs['R9']=replace(cs['R9'],pins=(('1','tx'),('2','')))
        cs['R2']=replace(cs['R2'],pins=(('1','gb'),('2','')))
        cs['R8']=replace(cs['R8'],pins=(('1','ty'),('2','')))
        cs,m=self.matched(cs)
        self.assertEqual(m.candidates['R1'],('R9',))

    def test_discovery_stops_at_power_bus_peer_anchor_mcu_connector(self):
        cs=circuit()
        cs['J1']=part('J1','MOTOR',{'1':'ga'})
        cs['U99']=part('U99','MCU',{str(i):('a' if i==1 else f'ctrl{i}') for i in range(1,101)})
        cs['C99']=part('C99','1u',{'1':'GND','2':'VCC'})
        self.assertEqual(set(discover_group(cs,'U1')),{'U1','R1','R2'})

    def test_reference_ranges_and_unknown_references(self):
        cs=circuit()
        self.assertEqual(parse_refs('U1, R1-R2',cs),['R1','R2','U1'])
        with self.assertRaises(LayoutError):parse_refs('R99',cs)

    def test_kelvin_end_pairs_must_rotate_together(self):
        parts=[part('U1','DRV',{'1':'s1','2':'n1','3':'p1'}),
               part('U2','DRV',{'1':'s2','2':'n2','3':'p2'},20,30),
               part('R1','WSK',{'1':'n1','2':'GND','3':'s1','4':'p1'},3,5,
                    kelvin_pairs=(('1','2'),('4','3'))),
               part('R2','WSK',{'1':'p2','2':'s2','3':'GND','4':'n2'},
                    kelvin_pairs=(('1','2'),('4','3')))]
        cs={c.ref:c for c in parts}
        m=match_groups(cs,['U1','R1'],['U2','R2'],'U1','U2')
        p=next(p for p in plan_placement(cs,m,m.suggestion) if p.ref=='R2')
        self.assertTrue(p.pin_swap);self.assertEqual(p.angle,-180)
        # Independent swapping of only force terminals is not equivalent.
        cs['R2']=replace(cs['R2'],pins=(('1','p2'),('2','GND'),('3','s2'),('4','n2')))
        with self.assertRaises(LayoutError):match_groups(cs,['U1','R1'],['U2','R2'],'U1','U2')



if __name__=='__main__':unittest.main()
