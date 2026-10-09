"""Connectivity matching and anchor-relative placement, independent of KiCad/UI."""
from __future__ import annotations

from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
import hashlib
import json
import math
import re
import time
from i18n import tr

VERSION = '0.3.2'


class LayoutError(ValueError):
    def __str__(self):
        return tr(super().__str__())


def ref_key(ref):
    return tuple(int(s) if s.isdigit() else s.casefold() for s in re.split(r'(\d+)', ref))


@dataclass(frozen=True)
class Component:
    ref: str
    uid: str
    value: str
    footprint: str
    pins: tuple[tuple[str, str], ...]
    x: float = 0
    y: float = 0
    angle: float = 0
    side: str = 'F'
    locked: bool = False
    kelvin_pairs: tuple[tuple[str, str], ...] = ()  # (sense, force) for each physical end

    @property
    def prefix(self):
        return re.sub(r'[^A-Za-z].*', '', self.ref).upper()

    @property
    def nonpolar(self):
        numbers = {p for p, _ in self.pins}
        polarized = any(s in self.footprint.casefold() for s in ('cp_', 'polar', 'tantal', 'electroly'))
        return len(numbers) == 2 and (self.prefix == 'R' or (self.prefix == 'C' and not polarized))

    @property
    def kind(self):
        return (self.prefix, self.value.strip().casefold(), self.footprint,
                self.side, len({p for p, _ in self.pins}), self.nonpolar, self.kelvin_pairs)

    def net(self, number):
        return dict(self.pins)[number]


def fingerprint(components):
    """Includes identity, connectivity and poses, including locked state."""
    rows = [(r, c.uid, c.kind, c.pins, c.x, c.y, c.angle, c.locked)
            for r, c in sorted(components.items())]
    return hashlib.sha256(json.dumps(rows, ensure_ascii=False).encode()).hexdigest()


def parse_refs(text, components):
    result = set()
    for token in re.split(r'[,;\s]+', text.strip()):
        if not token:
            continue
        match = re.fullmatch(r'([A-Za-z]+)(\d+)-\1?(\d+)', token)
        if match:
            prefix, lo, hi = match.groups()
            lo, hi = int(lo), int(hi)
            if hi < lo or hi - lo > 5000:
                raise LayoutError('Geçersiz komponent aralığı: ' + token)
            result.update(f'{prefix.upper()}{n}' for n in range(lo, hi + 1))
        else:
            result.add(token.upper())
    unknown = result - set(components)
    if unknown:
        raise LayoutError('Kartta bulunmayan referanslar: ' + ', '.join(sorted(unknown, key=ref_key)))
    return sorted(result, key=ref_key)


POWER = re.compile(r'^(?:[ADP]?GND|VSS\w*|VDD\w*|VCC\w*|VBAT[+-]?|VBUS|BAT[+-]?|[+]?(?:3[.]3|5|12|15)V)$', re.I)


def discover_group(components, anchor, depth=6, ignored=(), max_fanout=12):
    """Conservative circuit traversal; shared rails/interfaces form boundaries.

    This is a suggestion, never an inferred authoritative group membership.
    Power-only decouplers must be added using selection or explicit references.
    """
    root = components[anchor]
    net_members = defaultdict(set)
    for ref, c in components.items():
        for _, net in c.pins:
            if net:
                net_members[net].add(ref)
    peers = {r for r, c in components.items() if c.kind == root.kind}
    pin_limit = max(32, len({p for p, _ in root.pins}))
    blocked = set(ignored)
    for net, members in net_members.items():
        if (POWER.fullmatch(net.rsplit('/', 1)[-1])
                or len(members) > max_fanout or len(members & peers) > 1):
            blocked.add(net)
    found = {anchor}
    queue = deque([(anchor, 0)])
    while queue:
        ref, hops = queue.popleft()
        if hops >= depth:
            continue
        for _, net in components[ref].pins:
            if not net or net in blocked:
                continue
            for other in net_members[net]:
                if other in found or (other in peers and other != anchor):
                    continue
                if components[other].prefix in ('J', 'P', 'H', 'TP'):
                    continue  # Interfaces are not implicitly part of the movable circuit.
                if len({p for p, _ in components[other].pins}) > pin_limit:
                    continue
                found.add(other)
                queue.append((other, hops + 1))
    return sorted(found, key=ref_key)


@dataclass
class Graph:
    labels: dict = field(default_factory=dict)
    edges: dict = field(default_factory=dict)
    pin_nets: dict = field(default_factory=dict)


def build_graph(components, refs, anchor, shared):
    refs = set(refs)
    g = Graph()
    incidences = defaultdict(lambda: defaultdict(set))
    outside = set(net for r, c in components.items() if r not in refs for _, net in c.pins if net)
    for ref in sorted(refs, key=ref_key):
        c = components[ref]
        node = ('c', ref)
        g.labels[node] = ('component', c.kind, ref == anchor)
        g.edges[node] = {}
        if c.kelvin_pairs:
            for i, (sense, force) in enumerate(c.kelvin_pairs):
                end = ('e', ref, i)
                g.labels[end] = ('kelvin-end',)
                g.edges[end] = {node: ('end',)}
                g.edges[node][end] = ('end',)
                for pin, role in ((sense, 'sense'), (force, 'force')):
                    net = c.net(pin)
                    nn = ('n', net or ('open', ref, pin))
                    g.pin_nets[ref, pin] = nn
                    incidences[nn][end].add(role)
            continue
        for pin, net in c.pins:
            # Distinct, open pads are not one global net zero.
            key = net or ('open', ref, pin)
            nn = ('n', key)
            g.pin_nets[ref, pin] = nn
            incidences[nn][node].add(pin)
    for nn, members in incidences.items():
        net = nn[1]
        name = net if isinstance(net, str) and net in shared else None
        g.labels[nn] = ('net', name, net in outside, len(members))
        g.edges[nn] = {}
        for cn, pins in members.items():
            label = ('*',)*len(pins) if cn[0] == 'c' and components[cn[1]].nonpolar else tuple(sorted(pins))
            g.edges[nn][cn] = label
            g.edges[cn][nn] = label
    return g


def refine(a, b):
    graphs = (a, b)
    labels = [(i, n, label) for i, g in enumerate(graphs) for n, label in g.labels.items()]
    def assign(rows):
        keys = {repr(v) for _, _, v in rows}
        ids = {v: j for j, v in enumerate(sorted(keys))}
        return {(i, n): ids[repr(v)] for i, n, v in rows}
    colors = assign(labels)
    while True:
        rows = []
        for i, g in enumerate(graphs):
            for n in g.labels:
                neighbors = tuple(sorted((label, colors[i, other]) for other, label in g.edges[n].items()))
                rows.append((i, n, (colors[i, n], neighbors)))
        updated = assign(rows)
        if len(set(updated.values())) == len(set(colors.values())):
            return ({n: updated[0, n] for n in a.labels}, {n: updated[1, n] for n in b.labels})
        colors = updated


class SearchLimit(Exception):
    pass


class Solver:
    def __init__(self, a, b, max_states=100000, seconds=4.0):
        self.a, self.b = a, b
        ca, cb = refine(a, b)
        if Counter(ca.values()) != Counter(cb.values()):
            raise LayoutError('Grupların bağlantı yapıları eşleşmiyor. Grup listelerini ve ortak ağ sınırlarını kontrol et.')
        self.candidates = {n: tuple(m for m in b.labels if ca[n] == cb[m]) for n in a.labels}
        self.states = 0
        self.max_states = max_states
        self.deadline = time.monotonic() + seconds

    def solve(self, forced=None):
        mapping = {}
        used = set()
        def fits(n, m):
            return (m in self.candidates[n] and m not in used
                    and all(self.a.edges[n].get(p) == self.b.edges[m].get(q)
                            for p, q in mapping.items()))
        for n, m in (forced or {}).items():
            if n not in self.candidates or not fits(n, m):
                return None
            mapping[n] = m
            used.add(m)
        def walk():
            self.states += 1
            if self.states > self.max_states or time.monotonic() > self.deadline:
                raise SearchLimit()
            if len(mapping) == len(self.a.labels):
                return dict(mapping)
            best = None
            choices = None
            for n in self.a.labels:
                if n in mapping:
                    continue
                available = [m for m in self.candidates[n] if fits(n, m)]
                if not available:
                    return None
                rank = (len(available), -len(self.a.edges[n]), repr(n))
                if best is None or rank < best:
                    best, choices, node = rank, available, n
            for m in choices:
                mapping[node] = m
                used.add(m)
                result = walk()
                if result is not None:
                    return result
                used.remove(m)
                del mapping[node]
            return None
        return walk()


@dataclass
class Match:
    source: tuple
    target: tuple
    source_anchor: str
    target_anchor: str
    candidates: dict
    suggestion: dict
    graph_a: Graph
    graph_b: Graph
    limited: bool = False


def match_groups(components, source, target, source_anchor, target_anchor, seconds=4.0):
    source, target = tuple(source), tuple(target)
    if not source or len(source) != len(target):
        raise LayoutError(f'Grup boyutları farklı: kaynak {len(source)}, hedef {len(target)} komponent.')
    if set(source) & set(target):
        raise LayoutError('Kaynak ve hedef gruplar ortak komponent içeremez.')
    if source_anchor not in source or target_anchor not in target:
        raise LayoutError('Referans komponent kendi grubunun içinde olmalı.')
    if components[source_anchor].kind != components[target_anchor].kind:
        raise LayoutError('Referans komponentlerin değeri, kılıfı, pin sayısı ve kart yüzü aynı olmalı.')
    if Counter(components[r].kind for r in source) != Counter(components[r].kind for r in target):
        raise LayoutError('Grupların parça değerleri, kılıfları veya kart yüzleri eşleşmiyor.')
    shared = {n for r in source for _, n in components[r].pins if n} & {n for r in target for _, n in components[r].pins if n}
    a = build_graph(components, source, source_anchor, shared)
    b = build_graph(components, target, target_anchor, shared)
    solver = Solver(a, b, seconds=seconds)
    try:
        solution = solver.solve()
    except SearchLimit:
        raise LayoutError('Bağlantı eşleştirmesi çok karmaşık. Daha küçük bir grup veya daha belirgin bir referans seç.')
    if solution is None:
        raise LayoutError('Gruplar pin bağlantılarına göre eşdeğer değil.')
    candidates = {}
    limited = False
    for ref in source:
        n = ('c', ref)
        possible = []
        for m in solver.candidates[n]:
            if m == solution[n]:
                possible.append(m[1])
                continue
            try:
                if solver.solve({n: m}) is not None:
                    possible.append(m[1])
            except SearchLimit:
                limited = True
                possible.append(m[1])  # Never claim an untested candidate is impossible/unique.
        candidates[ref] = tuple(sorted(possible, key=ref_key))
    return Match(source, target, source_anchor, target_anchor, candidates,
                 {r: solution['c', r][1] for r in source}, a, b, limited)


def validate_mapping(match, mapping):
    if set(mapping) != set(match.source) or set(mapping.values()) != set(match.target):
        raise LayoutError('Her kaynak komponent tam bir kez, farklı bir hedef komponentle eşleşmeli.')
    if mapping[match.source_anchor] != match.target_anchor:
        raise LayoutError('Referans komponent eşleşmesi değiştirilemez.')
    solver = Solver(match.graph_a, match.graph_b, seconds=3.0)
    try:
        result = solver.solve({('c', s): ('c', t) for s, t in mapping.items()})
    except SearchLimit:
        raise LayoutError('Seçilen eşleşme doğrulanamadı. Grubu küçült.')
    if result is None:
        raise LayoutError('Seçilen eşleşmeler bağlantılarla tutarlı değil.')
    return result


def rotate(x, y, angle):
    rad = math.radians(angle)
    c, s = math.cos(rad), math.sin(rad)
    return c*x + s*y, -s*x + c*y


def normalized(angle):
    return (angle + 180) % 360 - 180


@dataclass(frozen=True)
class Pose:
    ref: str
    uid: str
    x: float
    y: float
    angle: float
    side: str
    source_ref: str
    pin_swap: bool = False


def plan_placement(components, match, mapping, mirror='none', extra_angle=0.0):
    """Mirror reflects placement centres only, never fabricates mirrored footprints.

    Two-terminal R/nonpolar C pin swaps are compensated by 180 degrees so
    electrically equivalent terminals land in the corresponding positions.
    The destination anchor's position is invariant; optional extra rotation
    rotates its orientation together with the rest of the group.
    """
    if mirror not in ('none', 'x', 'y') or not math.isfinite(extra_angle):
        raise LayoutError('Geçersiz yerleşim dönüşümü.')
    solution = validate_mapping(match, mapping)
    sa = components[match.source_anchor]
    ta = components[match.target_anchor]
    anchor_swap = False
    if sa.nonpolar or sa.kelvin_pairs:
        first = sorted({p for p, _ in sa.pins})[0]
        anchor_swap = solution[match.graph_a.pin_nets[sa.ref, first]] != match.graph_b.pin_nets[ta.ref, first]
    frame = ta.angle + extra_angle + (180 if anchor_swap else 0)
    poses = []
    for sr in match.source:
        source, target = components[sr], components[mapping[sr]]
        if target.locked:
            raise LayoutError(f'{target.ref} kilitli. Taşımak için önce KiCad içinde kilidini kaldır.')
        x, y = rotate(source.x-sa.x, source.y-sa.y, -sa.angle)
        if mirror == 'x':
            y = -y
        elif mirror == 'y':
            x = -x
        x, y = rotate(x, y, frame)
        swap = False
        if (source.nonpolar or source.kelvin_pairs) and sr != match.source_anchor:
            pins = sorted({p for p, _ in source.pins})
            expected = solution[match.graph_a.pin_nets[sr, pins[0]]]
            swap = expected != match.graph_b.pin_nets[target.ref, pins[0]]
        # Anchor rotation is explicit; selecting a reference fixes its frame,
        # not an inferred arbitrary electrical terminal ordering.
        if sr == match.source_anchor:
            angle = ta.angle + extra_angle
            swap = anchor_swap
        else:
            angle = source.angle-sa.angle+frame+(180 if swap else 0)
        poses.append(Pose(target.ref, target.uid, ta.x+x, ta.y+y,
                          normalized(angle), target.side, sr, swap))
    return poses


def validate_batch(source, target_groups):
    used = set(source)
    for refs in target_groups:
        overlap = used & set(refs)
        if overlap:
            raise LayoutError('Hedef gruplar kaynakla veya birbirleriyle çakışıyor: ' + ', '.join(sorted(overlap, key=ref_key)))
        used.update(refs)
