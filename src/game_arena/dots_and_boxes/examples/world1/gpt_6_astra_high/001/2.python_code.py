
import math
import random
import time
from functools import lru_cache

import numpy as np


# The 40 edges belonging to the 4x4 board.
_ACTIONS = []
_EDGE_AT = {}
_ENDPOINTS = []

for r in range(5):
    for c in range(4):
        i = len(_ACTIONS)
        _ACTIONS.append(f"{r},{c},H")
        _EDGE_AT[("H", r, c)] = 1 << i
        _ENDPOINTS.append(((r, c), (r, c + 1)))

for r in range(4):
    for c in range(5):
        i = len(_ACTIONS)
        _ACTIONS.append(f"{r},{c},V")
        _EDGE_AT[("V", r, c)] = 1 << i
        _ENDPOINTS.append(((r, c), (r + 1, c)))

_BM = []
_ADJ = {1 << i: [] for i in range(40)}

for r in range(4):
    for c in range(4):
        edges = (
            _EDGE_AT[("H", r, c)],
            _EDGE_AT[("H", r + 1, c)],
            _EDGE_AT[("V", r, c)],
            _EDGE_AT[("V", r, c + 1)],
        )
        b = len(_BM)
        _BM.append(sum(edges))
        for e in edges:
            _ADJ[e].append(b)

_ADJ = {e: tuple(bs) for e, bs in _ADJ.items()}
_OTHER = [{} for _ in range(16)]
_BOUNDARY = 0

for e, bs in _ADJ.items():
    if len(bs) == 1:
        _BOUNDARY |= e
        _OTHER[bs[0]][e] = -1
    else:
        a, b = bs
        _OTHER[a][e] = b
        _OTHER[b][e] = a


def _bits(mask):
    result = []
    while mask:
        e = mask & -mask
        mask ^= e
        result.append(e)
    return result


# Board automorphisms, used to eliminate equivalent root moves.
_SYMS = []
for reflection in range(2):
    for rotation in range(4):
        mapping = {}
        for i, endpoints in enumerate(_ENDPOINTS):
            transformed = []
            for r, c in endpoints:
                if reflection:
                    c = 4 - c
                for _ in range(rotation):
                    r, c = c, 4 - r
                transformed.append((r, c))
            (r1, c1), (r2, c2) = transformed
            if r1 == r2:
                image = _EDGE_AT[("H", r1, min(c1, c2))]
            else:
                image = _EDGE_AT[("V", min(r1, r2), c1)]
            mapping[1 << i] = image
        _SYMS.append(mapping)


def _symmetries(mask):
    result = []
    edges = _bits(mask)
    for mapping in _SYMS:
        transformed = 0
        for e in edges:
            transformed |= mapping[e]
        if transformed == mask:
            result.append(mapping)
    return result


def _representatives(moves, symmetries):
    result = []
    seen = set()
    for e in _bits(moves):
        if e not in seen:
            result.append(e)
            for mapping in symmetries:
                seen.add(mapping[e])
    return result


@lru_cache(maxsize=65536)
def _closed_value(items):
    """Exact current-player value of unopened chains and loops.

    Positive items are chains; negative items are loops.
    """
    if not items:
        return 0

    best = -100
    previous = None
    for i, item in enumerate(items):
        if item == previous:
            continue
        previous = item
        n = abs(item)
        rest = items[:i] + items[i + 1:]
        v = _closed_value(rest)

        take_all = -n - v
        if item > 0 and n <= 2:
            # A two-chain is opened internally, preventing a handout.
            candidate = take_all
        else:
            handout = 2 if item > 0 else 4
            candidate = min(take_all, 2 * handout - n + v)
        best = max(best, candidate)
    return best


def _components(rem):
    """Components of the graph formed by undrawn edges."""
    seen = 0
    result = []
    for start in range(16):
        if not rem[start] or (seen & (1 << start)):
            continue
        seen |= 1 << start
        stack = [start]
        n = stubs = ends = 0
        edges = 0
        branch = False

        while stack:
            b = stack.pop()
            bm = rem[b]
            degree = bm.bit_count()
            n += 1
            stubs += (bm & _BOUNDARY).bit_count()
            ends += degree == 1
            branch |= degree > 2
            edges |= bm

            while bm:
                e = bm & -bm
                bm ^= e
                other = _OTHER[b][e]
                if other >= 0 and not (seen & (1 << other)):
                    seen |= 1 << other
                    stack.append(other)

        result.append((n, stubs, edges, branch, ends))
    return result


class _Info:
    __slots__ = (
        "value", "force", "gain", "safe", "caps", "cross",
        "moves", "play", "roll", "high"
    )

    def __init__(self, value, force, gain, safe, caps, cross,
                 moves, play, roll, high):
        self.value = value
        self.force = force
        self.gain = gain
        self.safe = safe
        self.caps = caps
        self.cross = cross
        self.moves = moves
        self.play = play
        self.roll = roll
        self.high = high


class _Node:
    __slots__ = (
        "mask", "untried", "children", "n", "w", "solved", "complete"
    )

    def __init__(self, mask, info, rng):
        self.mask = mask
        self.untried = _bits(info.play)
        rng.shuffle(self.untried)
        self.children = []
        self.n = 0
        self.w = 0.0
        self.solved = info.value
        self.complete = info.play == info.moves


class _Timeout(Exception):
    pass


# Entries contain (value, bound type, best edge).
# Bound type: 0 exact, 1 lower bound, -1 upper bound.
_TT = {}


class _Engine:
    def __init__(self, mask, deadline):
        self.deadline = deadline
        self.rng = random.Random(mask ^ 0x9E3779B97F4A7C15)
        self.infos = {}
        self.normalized = {}
        self.nodes = {}
        self.ticks = 0

    def info(self, mask):
        cached = self.infos.get(mask)
        if cached is not None:
            return cached

        rem = [mask & bm for bm in _BM]
        degrees = [m.bit_count() for m in rem]
        bad = caps = 0
        high = 0

        for m, d in zip(rem, degrees):
            if d <= 2:
                bad |= m
            else:
                high += 1
            if d == 1:
                caps |= m

        safe = mask & ~bad

        if high == 0:
            closed = []
            opened = 0
            handout = 100

            for n, stubs, edges, branch, ends in _components(rem):
                if stubs == 2:
                    closed.append(n)
                elif stubs == 0 and ends == 0:
                    closed.append(-n)
                else:
                    opened += n
                    if stubs == 1 and n >= 2:
                        handout = min(handout, 2)
                    elif stubs == 0 and n >= 4:
                        handout = min(handout, 4)

            v = _closed_value(tuple(sorted(closed)))
            value = opened + v
            if handout < 100:
                value = max(value, opened - 2 * handout - v)

            result = _Info(
                value, 0, 0, safe, caps, 0, mask, 0, (), high
            )
            self.infos[mask] = result
            return result

        # Captures are forced unless they destroy the opportunity
        # for a two-box or four-box hard-hearted handout.
        cross = 0
        for e in _bits(caps):
            bs = _ADJ[e]
            gain = sum(rem[b] == e for b in bs)
            dangerous = False

            if gain == 1 and len(bs) == 2:
                b = bs[0] if rem[bs[0]] != e else bs[1]
                if degrees[b] == 2:
                    f = rem[b] ^ e
                    c = _OTHER[b][f]
                    if c < 0:
                        dangerous = True
                        cross |= f
                    elif degrees[c] == 2:
                        g = rem[c] ^ f
                        d = _OTHER[c][g]
                        if d >= 0 and rem[d] == g:
                            dangerous = True
                            cross |= f

            if not dangerous:
                result = _Info(
                    None, e, gain, safe, caps, cross,
                    e, e, (e,), high
                )
                self.infos[mask] = result
                return result

        moves = mask

        # Isolated unopened chains/loops have interchangeable openings.
        if not safe or mask.bit_count() <= 22:
            seen_types = set()
            for n, stubs, edges, branch, ends in _components(rem):
                if branch:
                    continue
                loop = stubs == 0 and ends == 0
                if stubs != 2 and not loop:
                    continue

                key = (-n if loop else n)
                moves &= ~edges
                if key not in seen_types:
                    seen_types.add(key)
                    options = edges
                    if not loop and n == 2:
                        options &= ~_BOUNDARY
                    moves |= options & -options

        if safe or caps:
            play = moves & (safe | caps | cross)
        else:
            play = moves

        if safe:
            roll = tuple(_bits(safe))
        elif caps:
            roll = tuple(_bits(caps))
        else:
            # Prefer opening a short strand during rollout.
            visited = 0
            least = 100
            preferred = 0
            for start in range(16):
                if degrees[start] != 2 or visited & (1 << start):
                    continue
                visited |= 1 << start
                stack = [start]
                count = 0
                edges = 0
                while stack:
                    b = stack.pop()
                    count += 1
                    edges |= rem[b]
                    for e in _bits(rem[b]):
                        other = _OTHER[b][e]
                        if (other >= 0 and degrees[other] == 2
                                and not (visited & (1 << other))):
                            visited |= 1 << other
                            stack.append(other)

                options = edges & moves
                if options:
                    if count < least:
                        least, preferred = count, options
                    elif count == least:
                        preferred |= options

            roll = tuple(_bits(preferred or play))

        result = _Info(
            None, 0, 0, safe, caps, cross,
            moves, play, roll, high
        )
        self.infos[mask] = result
        return result

    @staticmethod
    def gain(mask, e):
        return sum((mask & _BM[b]) == e for b in _ADJ[e])

    def normalize(self, mask):
        cached = self.normalized.get(mask)
        if cached is not None:
            return cached

        path = []
        total = 0
        while True:
            cached = self.normalized.get(mask)
            if cached is not None:
                mask, bonus = cached
                total += bonus
                break

            info = self.info(mask)
            if info.value is not None or not info.force:
                break
            path.append((mask, total))
            total += info.gain
            mask ^= info.force

        for old, before in path:
            self.normalized[old] = (mask, total - before)
        return mask, total

    def node(self, mask):
        result = self.nodes.get(mask)
        if result is None:
            result = _Node(mask, self.info(mask), self.rng)
            self.nodes[mask] = result
        return result

    def rollout(self, mask):
        total = 0
        sign = 1
        rng = self.rng

        while True:
            mask, bonus = self.normalize(mask)
            total += sign * bonus
            info = self.info(mask)

            if info.value is not None:
                return total + sign * info.value

            if info.caps:
                if (not info.safe and info.cross
                        and rng.random() < 0.28):
                    e = rng.choice(_bits(info.cross))
                else:
                    e = rng.choice(_bits(info.caps))
            elif info.safe:
                e = rng.choice(info.roll)
            elif rng.random() < 0.85:
                e = rng.choice(info.roll)
            else:
                e = rng.choice(_bits(info.play))

            gain = self.gain(mask, e)
            total += sign * gain
            if not gain:
                sign = -sign
            mask ^= e

    @staticmethod
    def edge_value(edge):
        _, reward, sign, child = edge
        v = child.solved
        if v is None:
            v = child.w / max(1, child.n)
        return reward + sign * v

    def monte_carlo(self, root, until):
        while time.perf_counter() < until and root.solved is None:
            node = root
            path = []

            while node.solved is None:
                if node.untried:
                    e = node.untried.pop()
                    gain = self.gain(node.mask, e)
                    sign = 1 if gain else -1
                    child_mask, bonus = self.normalize(node.mask ^ e)
                    child = self.node(child_mask)
                    reward = gain + sign * bonus
                    edge = (e, reward, sign, child)
                    node.children.append(edge)
                    path.append((node, reward, sign))
                    node = child
                    break

                logn = math.log(node.n + 1.0)
                best_edge = None
                best_score = -1e100
                for edge in node.children:
                    child = edge[3]
                    score = self.edge_value(edge)
                    if child.solved is None:
                        score += 4.2 * math.sqrt(
                            logn / max(1, child.n)
                        )
                    if score > best_score:
                        best_score = score
                        best_edge = edge

                if best_edge is None:
                    break
                _, reward, sign, child = best_edge
                path.append((node, reward, sign))
                node = child

            value = node.solved
            if value is None:
                value = self.rollout(node.mask)

            node.n += 1
            node.w += value

            for parent, reward, sign in reversed(path):
                value = reward + sign * value
                parent.n += 1
                parent.w += value
                if (parent.complete and not parent.untried
                        and parent.children
                        and all(e[3].solved is not None
                                for e in parent.children)):
                    parent.solved = max(
                        self.edge_value(e) for e in parent.children
                    )

    def recommendation(self, root, fallback):
        if not root.children:
            return fallback

        def quality(edge):
            child = edge[3]
            q = self.edge_value(edge)
            if child.solved is None:
                q -= 1.5 / math.sqrt(max(1, child.n))
            return q, child.n

        return max(root.children, key=quality)[0]

    def ordered_moves(self, mask, info, preferred=0):
        moves = _bits(info.moves)
        estimates = {}
        node = self.nodes.get(mask)
        if node is not None:
            estimates = {
                e[0]: self.edge_value(e) for e in node.children
            }
        cheap = set(info.roll)

        def key(e):
            if e == preferred:
                return (1, 0)
            default = (
                3.0 if e & info.caps else
                0.5 if e & info.safe else
                -1.0 if e in cheap else -3.0
            )
            return (0, estimates.get(e, default))

        moves.sort(key=key, reverse=True)
        return moves

    def solve(self, mask, alpha, beta):
        self.ticks += 1
        if (self.ticks & 127) == 0:
            if time.perf_counter() >= self.deadline:
                raise _Timeout

        entry = _TT.get(mask)
        preferred = 0
        if entry is not None:
            value, flag, preferred = entry
            if flag == 0:
                return value
            if flag == 1:
                alpha = max(alpha, value)
            else:
                beta = min(beta, value)
            if alpha >= beta:
                return value

        info = self.info(mask)
        if info.value is not None:
            _TT[mask] = (info.value, 0, 0)
            return info.value

        node = self.nodes.get(mask)
        if node is not None and node.solved is not None:
            best = max(node.children, key=self.edge_value)[0]
            _TT[mask] = (node.solved, 0, best)
            return node.solved

        alpha0, beta0 = alpha, beta
        best_value = -100
        best_move = 0

        if info.force:
            e = info.force
            value = info.gain + self.solve(
                mask ^ e, alpha - info.gain, beta - info.gain
            )
            best_value, best_move = value, e
        else:
            for e in self.ordered_moves(mask, info, preferred):
                gain = self.gain(mask, e)
                if gain:
                    value = gain + self.solve(
                        mask ^ e, alpha - gain, beta - gain
                    )
                else:
                    value = -self.solve(mask ^ e, -beta, -alpha)

                if value > best_value:
                    best_value, best_move = value, e
                alpha = max(alpha, value)
                if alpha >= beta:
                    break

        flag = (
            -1 if best_value <= alpha0 else
            1 if best_value >= beta0 else 0
        )
        _TT[mask] = (best_value, flag, best_move)
        return best_value


def policy(horizontal: np.ndarray,
           vertical: np.ndarray,
           capture: np.ndarray) -> str:
    start = time.perf_counter()
    deadline = start + 0.88

    mask = 0
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] == 0:
                mask |= _EDGE_AT[("H", r, c)]
    for r in range(4):
        for c in range(5):
            if vertical[r, c] == 0:
                mask |= _EDGE_AT[("V", r, c)]

    if not mask:
        # Defensive fallback for representations exposing unused array slots.
        for direction, array in (("H", horizontal), ("V", vertical)):
            for r in range(5):
                for c in range(5):
                    if array[r, c] == 0:
                        return f"{r},{c},{direction}"
        # A terminal position has no legal move and should not be queried.
        return "0,0,H"

    def action(e):
        return _ACTIONS[e.bit_length() - 1]

    fallback = mask & -mask
    if mask == fallback:
        return action(fallback)

    if len(_TT) > 150000:
        _TT.clear()

    cached = _TT.get(mask)
    if cached is not None and cached[1] == 0 and cached[2] & mask:
        return action(cached[2])

    engine = _Engine(mask, deadline)
    info = engine.info(mask)

    # Pure chains/loops, including partially consumed components,
    # can be evaluated exactly without tree search.
    if info.value is not None:
        best_move = fallback
        best_value = -100
        for e in _bits(mask):
            gain = engine.gain(mask, e)
            child_value = engine.info(mask ^ e).value
            value = gain + child_value if gain else -child_value
            if value > best_value:
                best_value, best_move = value, e
        return action(best_move)

    if info.force:
        return action(info.force)

    symmetries = _symmetries(mask)
    root = engine.node(mask)
    root.untried = _representatives(info.play, symmetries)
    engine.rng.shuffle(root.untried)

    if info.safe:
        fallback = info.safe & -info.safe
    elif info.caps:
        fallback = info.caps & -info.caps

    remaining = mask.bit_count()
    exact_phase = remaining <= 23 or info.high <= 4
    if exact_phase:
        mc_time = 0.14 if remaining <= 20 else 0.28
        mc_deadline = min(deadline, start + mc_time)
    else:
        mc_deadline = deadline

    engine.monte_carlo(root, mc_deadline)
    choice = engine.recommendation(root, fallback)

    if root.solved is not None:
        return action(choice)

    if exact_phase and time.perf_counter() < deadline:
        representatives = set(
            _representatives(info.moves, symmetries)
        )
        ordered = [
            e for e in engine.ordered_moves(mask, info, choice)
            if e in representatives
        ]

        # Search the Monte Carlo recommendation first. If time expires,
        # completed alternatives can only improve on that recommendation.
        best_value = -17
        completed_best = None
        finished = True

        try:
            for e in ordered:
                if time.perf_counter() >= deadline:
                    raise _Timeout

                gain = engine.gain(mask, e)
                if gain:
                    value = gain + engine.solve(
                        mask ^ e, best_value - gain, 17 - gain
                    )
                else:
                    value = -engine.solve(
                        mask ^ e, -17, -best_value
                    )

                if completed_best is None or value > best_value:
                    completed_best = e
                    best_value = value
        except _Timeout:
            finished = False

        if completed_best is not None:
            choice = completed_best
        if finished and completed_best is not None:
            _TT[mask] = (best_value, 0, completed_best)

    # Every selected edge originated in the current empty-edge mask.
    if not (choice & mask):
        choice = fallback
    return action(choice)
