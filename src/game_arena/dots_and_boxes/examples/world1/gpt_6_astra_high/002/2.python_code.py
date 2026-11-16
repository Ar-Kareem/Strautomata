
import math
import random
import time
from functools import lru_cache

import numpy as np


# The 40 actual edges of a 4x4 box board.
_MOVE_NAMES = []
_EDGE_POINTS = []

for _r in range(5):
    for _c in range(4):
        _MOVE_NAMES.append(f"{_r},{_c},H")
        _EDGE_POINTS.append(((_r, _c), (_r, _c + 1)))

for _r in range(4):
    for _c in range(5):
        _MOVE_NAMES.append(f"{_r},{_c},V")
        _EDGE_POINTS.append(((_r, _c), (_r + 1, _c)))

_BOX_MASKS = []
_EDGE_BOXES = [[] for _ in range(40)]

for _r in range(4):
    for _c in range(4):
        _edges = (
            _r * 4 + _c,
            (_r + 1) * 4 + _c,
            20 + _r * 5 + _c,
            20 + _r * 5 + _c + 1,
        )
        _box = len(_BOX_MASKS)
        _BOX_MASKS.append(sum(1 << e for e in _edges))
        for _e in _edges:
            _EDGE_BOXES[_e].append(_box)

_BOX_MASKS = tuple(_BOX_MASKS)
_EDGE_BOXES = tuple(tuple(x) for x in _EDGE_BOXES)

_BOX_LINKS = []
for _box, _bm in enumerate(_BOX_MASKS):
    _links = []
    _bits = _bm
    while _bits:
        _bit = _bits & -_bits
        _bits ^= _bit
        _adj = _EDGE_BOXES[_bit.bit_length() - 1]
        _other = next((b for b in _adj if b != _box), -1)
        _links.append((_bit, _other))
    _BOX_LINKS.append(tuple(_links))
_BOX_LINKS = tuple(_BOX_LINKS)

# Board symmetries, used to avoid equivalent opening moves.
_POINT_EDGE = {
    tuple(sorted(points)): i for i, points in enumerate(_EDGE_POINTS)
}
_SYMMETRIES = []
for _reflection in range(2):
    for _rotation in range(4):
        _mapping = []
        for _points in _EDGE_POINTS:
            _transformed = []
            for _r, _c in _points:
                if _reflection:
                    _c = 4 - _c
                for _ in range(_rotation):
                    _r, _c = _c, 4 - _r
                _transformed.append((_r, _c))
            _mapping.append(
                _POINT_EDGE[tuple(sorted(_transformed))]
            )
        _SYMMETRIES.append(tuple(_mapping))
_SYMMETRIES = tuple(_SYMMETRIES)


@lru_cache(maxsize=100000)
def _component_game(parts):
    """
    Value from the current player's perspective.

    Codes 1..16: unopened chains.
    Codes 17..32: unopened loops of length code-16.
    Code 33: an open two-box chain.
    Code 34: an open four-box loop remainder.
    """
    if not parts:
        return 0

    best = -100
    previous = -1

    for i, component in enumerate(parts):
        if component == previous:
            continue
        previous = component
        rest = parts[:i] + parts[i + 1:]

        if component == 33 or component == 34:
            n = 2 if component == 33 else 4
            v = _component_game(rest)
            # Take everything, or make the hard-hearted handout.
            candidate = max(n + v, -n - v)

        elif component <= 2:
            # Opening the middle of a two-chain donates both boxes
            # without allowing the opponent a control-preserving reply.
            candidate = -component - _component_game(rest)

        elif component <= 16:
            opened = tuple(sorted(rest + (33,)))
            candidate = -(component - 2) - _component_game(opened)

        else:
            n = component - 16
            opened = tuple(sorted(rest + (34,)))
            candidate = -(n - 4) - _component_game(opened)

        best = max(best, candidate)

    return best


def _classify(mask):
    degrees = [(mask & bm).bit_count() for bm in _BOX_MASKS]
    captures, safe, risky = [], [], []
    forced = None

    bits = mask
    while bits:
        bit = bits & -bits
        bits ^= bit
        adjacent = _EDGE_BOXES[bit.bit_length() - 1]

        gain = sum(degrees[b] == 1 for b in adjacent)
        action = (bit, gain)

        if gain:
            captures.append(action)
            # These captures remove an independent, already available
            # box or pair of boxes, without consuming a turn.
            if gain == 2 or len(adjacent) == 1:
                forced = action
        elif all(degrees[b] >= 3 for b in adjacent):
            safe.append(action)
        else:
            risky.append(action)

    captures.sort(key=lambda action: -action[1])
    return captures, safe, risky, forced


def _gain(mask, bit):
    return sum(
        (mask & _BOX_MASKS[b]) == bit
        for b in _EDGE_BOXES[bit.bit_length() - 1]
    )


class _TimeUp(Exception):
    pass


class _Node:
    __slots__ = (
        "mask", "visits", "total", "untried", "children", "value"
    )

    def __init__(self, mask, actions, value):
        self.mask = mask
        self.visits = 0
        self.total = 0.0
        self.untried = actions
        self.children = []
        self.value = value


class _Engine:
    def __init__(self, mask, stop):
        self.stop = stop
        self.rng = random.Random(mask ^ (mask >> 20) ^ 0x58319D)
        self.end_cache = {0: 0}
        self.nodes = {}
        self.tt = {}
        self.ticks = 0

    def check_time(self):
        if time.perf_counter() >= self.stop:
            raise _TimeUp

    def end_value(self, mask):
        if mask in self.end_cache:
            return self.end_cache[mask]

        degrees = [(mask & bm).bit_count() for bm in _BOX_MASKS]
        if any(d > 2 for d in degrees):
            self.end_cache[mask] = None
            return None

        seen = 0
        parts = []
        free_gain = 0

        for first in range(16):
            if degrees[first] == 0 or (seen >> first) & 1:
                continue

            stack = [first]
            seen |= 1 << first
            size = 0
            boundaries = 0
            all_degree_two = True

            while stack:
                box = stack.pop()
                size += 1
                if degrees[box] != 2:
                    all_degree_two = False

                for bit, neighbor in _BOX_LINKS[box]:
                    if not mask & bit:
                        continue
                    if neighbor < 0:
                        boundaries += 1
                    elif not (seen >> neighbor) & 1:
                        seen |= 1 << neighbor
                        stack.append(neighbor)

            if boundaries == 2:
                parts.append(size)
            elif boundaries == 1:
                if size == 1:
                    free_gain += 1
                else:
                    free_gain += size - 2
                    parts.append(33)
            elif all_degree_two:
                parts.append(16 + size)
            elif size <= 3:
                free_gain += size
            else:
                free_gain += size - 4
                parts.append(34)

        value = free_gain + _component_game(tuple(sorted(parts)))
        self.end_cache[mask] = value
        return value

    def node(self, mask):
        existing = self.nodes.get(mask)
        if existing is not None:
            return existing

        value = self.end_value(mask)
        actions = []

        if value is None:
            captures, safe, risky, forced = _classify(mask)
            if forced is not None:
                actions = [forced]
            elif not captures and safe:
                actions = safe
            else:
                actions = captures + safe + risky

            self.rng.shuffle(actions)
            actions.sort(key=lambda action: -action[1])
            actions.reverse()

        result = _Node(mask, actions, value)
        self.nodes[mask] = result
        return result

    def reduce_root_symmetry(self, root):
        stabilizers = []
        for mapping in _SYMMETRIES:
            transformed = 0
            bits = root.mask
            while bits:
                bit = bits & -bits
                bits ^= bit
                transformed |= 1 << mapping[bit.bit_length() - 1]
            if transformed == root.mask:
                stabilizers.append(mapping)

        if len(stabilizers) <= 1:
            return

        representatives = set()
        reduced = []
        for action in root.untried:
            edge = action[0].bit_length() - 1
            representative = min(mapping[edge] for mapping in stabilizers)
            if representative not in representatives:
                representatives.add(representative)
                reduced.append(action)
        root.untried = reduced

    def cascade_size(self, mask, bit):
        """Boxes obtained by greedily answering a non-scoring opening."""
        remaining = mask ^ bit
        queue = list(_EDGE_BOXES[bit.bit_length() - 1])
        score = 0

        while queue:
            box = queue.pop()
            available = remaining & _BOX_MASKS[box]
            if not available or available & (available - 1):
                continue

            remaining ^= available
            for neighbor in _EDGE_BOXES[available.bit_length() - 1]:
                degree = (remaining & _BOX_MASKS[neighbor]).bit_count()
                if degree == 0:
                    score += 1
                elif degree == 1:
                    queue.append(neighbor)

        return score

    def rollout(self, mask):
        sign = 1
        score = 0
        steps = 0

        while mask:
            if steps & 7 == 0:
                self.check_time()
            steps += 1

            value = self.end_value(mask)
            if value is not None:
                return score + sign * value

            captures, safe, risky, forced = _classify(mask)

            if forced is not None:
                bit, gain = forced
            elif captures:
                bit, gain = self.rng.choice(captures)
            elif safe:
                bit, gain = self.rng.choice(safe)
            else:
                best_cost = 100
                choices = []
                for action in risky:
                    cost = self.cascade_size(mask, action[0])
                    if cost < best_cost:
                        best_cost = cost
                        choices = [action]
                    elif cost == best_cost:
                        choices.append(action)
                bit, gain = self.rng.choice(choices)

            mask ^= bit
            if gain:
                score += sign * gain
            else:
                sign = -sign

        return score

    @staticmethod
    def child_score(gain, child):
        if child.value is not None:
            value = child.value
        elif child.visits:
            value = child.total / child.visits
        else:
            value = 0.0
        return gain + value if gain else -value

    def mcts(self, root):
        while root.value is None:
            self.check_time()
            node = root
            path = []

            while node.value is None:
                if node.untried:
                    bit, gain = node.untried.pop()
                    child = self.node(node.mask ^ bit)
                    node.children.append((bit, gain, child))
                    path.append((node, gain))
                    node = child
                    break

                log_visits = math.log(node.visits + 1.0)
                best = None
                best_score = -float("inf")

                for bit, gain, child in node.children:
                    if child.visits == 0:
                        selection = float("inf")
                    else:
                        selection = self.child_score(gain, child)
                        selection += 3.8 * math.sqrt(
                            log_visits / child.visits
                        )
                    if selection > best_score:
                        best_score = selection
                        best = (bit, gain, child)

                if best is None:
                    node.value = 0
                    break

                _, gain, child = best
                path.append((node, gain))
                node = child

            value = (
                node.value if node.value is not None
                else self.rollout(node.mask)
            )
            node.visits += 1
            node.total += value

            for parent, gain in reversed(path):
                value = gain + value if gain else -value
                parent.visits += 1
                parent.total += value

                if (
                    not parent.untried
                    and parent.children
                    and all(c.value is not None for _, _, c in parent.children)
                ):
                    parent.value = max(
                        self.child_score(g, c)
                        for _, g, c in parent.children
                    )

    def best_mcts_move(self, root, fallback):
        if not root.children:
            return fallback

        if root.value is not None:
            return max(
                root.children,
                key=lambda item: self.child_score(item[1], item[2]),
            )[0]

        return max(
            root.children,
            key=lambda item: (
                item[2].visits,
                self.child_score(item[1], item[2]),
            ),
        )[0]

    def solve(self, mask, alpha, beta):
        self.ticks += 1
        if self.ticks & 127 == 0:
            self.check_time()

        end = self.end_value(mask)
        if end is not None:
            return end

        entry = self.tt.get(mask)
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

        alpha_original, beta_original = alpha, beta

        captures, safe, risky, forced = _classify(mask)
        if forced is not None:
            actions = [forced]
        else:
            actions = captures + safe + risky

            tree_node = self.nodes.get(mask)
            estimates = {}
            if tree_node is not None:
                estimates = {
                    bit: self.child_score(gain, child)
                    for bit, gain, child in tree_node.children
                    if child.visits or child.value is not None
                }

            safe_bits = {bit for bit, _ in safe}

            def ordering(action):
                bit, gain = action
                if bit == preferred:
                    return 1000.0
                if bit in estimates:
                    return estimates[bit]
                if gain:
                    return 2.0 * gain
                return 0.0 if bit in safe_bits else -5.0

            actions.sort(key=ordering, reverse=True)

        best = -100
        best_bit = actions[0][0]

        for bit, gain in actions:
            if gain:
                value = gain + self.solve(
                    mask ^ bit, alpha - gain, beta - gain
                )
            else:
                value = -self.solve(mask ^ bit, -beta, -alpha)

            if value > best:
                best = value
                best_bit = bit
            alpha = max(alpha, value)
            if alpha >= beta:
                break

        if best <= alpha_original:
            flag = -1  # Upper bound.
        elif best >= beta_original:
            flag = 1   # Lower bound.
        else:
            flag = 0   # Exact.

        self.tt[mask] = (best, flag, best_bit)
        return best


def policy(
    horizontal: np.ndarray,
    vertical: np.ndarray,
    capture: np.ndarray,
) -> str:
    started = time.perf_counter()
    mask = 0

    for r in range(5):
        for c in range(4):
            if horizontal[r, c] == 0:
                mask |= 1 << (r * 4 + c)

    for r in range(4):
        for c in range(5):
            if vertical[r, c] == 0:
                mask |= 1 << (20 + r * 5 + c)

    if not mask:
        # Defensive fallback for representations that expose padding slots
        # as playable. A fully occupied terminal board has no legal move.
        for direction, array in (("H", horizontal), ("V", vertical)):
            for r in range(5):
                for c in range(5):
                    if array[r, c] == 0:
                        return f"{r},{c},{direction}"
        return "0,0,H"

    captures, safe, risky, forced = _classify(mask)

    if forced is not None:
        return _MOVE_NAMES[forced[0].bit_length() - 1]

    initial_actions = captures or safe or risky
    fallback_bit = initial_actions[0][0]

    engine = _Engine(mask, started + 0.90)
    end = engine.end_value(mask)

    if end is not None:
        best_value = -100
        best_bit = fallback_bit
        bits = mask

        while bits:
            bit = bits & -bits
            bits ^= bit
            gain = _gain(mask, bit)
            following = engine.end_value(mask ^ bit)
            value = gain + following if gain else -following

            if value > best_value:
                best_value = value
                best_bit = bit

        return _MOVE_NAMES[best_bit.bit_length() - 1]

    root = engine.node(mask)
    engine.reduce_root_symmetry(root)

    tactical = mask.bit_count() <= 20
    engine.stop = started + (0.25 if tactical else 0.89)

    try:
        engine.mcts(root)
    except _TimeUp:
        pass

    chosen_bit = engine.best_mcts_move(root, fallback_bit)

    if tactical and time.perf_counter() < started + 0.87:
        engine.stop = started + 0.90
        try:
            engine.solve(mask, -17, 17)
            entry = engine.tt.get(mask)
            if entry is not None and entry[2]:
                chosen_bit = entry[2]
        except _TimeUp:
            pass

    # Final legality guard: every selected bit must still be empty.
    if not chosen_bit or not (mask & chosen_bit):
        chosen_bit = mask & -mask

    return _MOVE_NAMES[chosen_bit.bit_length() - 1]
