
import math
import random
import time
from functools import lru_cache

import numpy as np


# The 40 playable edges of the 4x4 box board.
_EDGES = (
    [(r, c, "H") for r in range(5) for c in range(4)]
    + [(r, c, "V") for r in range(4) for c in range(5)]
)
_EDGE_INDEX = {edge: i for i, edge in enumerate(_EDGES)}

_BOX_MASKS = []
_EDGE_BOXES = [[] for _ in range(40)]

for r in range(4):
    for c in range(4):
        box = 4 * r + c
        edges = (
            4 * r + c,
            4 * (r + 1) + c,
            20 + 5 * r + c,
            20 + 5 * r + c + 1,
        )
        mask = 0
        for e in edges:
            mask |= 1 << e
            _EDGE_BOXES[e].append(box)
        _BOX_MASKS.append(mask)

_BOX_MASKS = tuple(_BOX_MASKS)
_EDGE_BOXES = tuple(tuple(x) for x in _EDGE_BOXES)
_EDGE_BOX_BITS = tuple(
    sum(1 << b for b in boxes) for boxes in _EDGE_BOXES
)


def _make_symmetries():
    permutations = []

    for reflected in (False, True):
        for rotations in range(4):
            def transform(r, c):
                if reflected:
                    c = 4 - c
                for _ in range(rotations):
                    r, c = c, 4 - r
                return r, c

            permutation = []
            for r, c, direction in _EDGES:
                if direction == "H":
                    p = transform(r, c)
                    q = transform(r, c + 1)
                else:
                    p = transform(r, c)
                    q = transform(r + 1, c)

                if p[0] == q[0]:
                    edge = (p[0], min(p[1], q[1]), "H")
                else:
                    edge = (min(p[0], q[0]), p[1], "V")
                permutation.append(_EDGE_INDEX[edge])

            permutations.append(tuple(permutation))

    return tuple(permutations)


_SYMMETRIES = _make_symmetries()


def _indices(mask):
    result = []
    while mask:
        bit = mask & -mask
        result.append(bit.bit_length() - 1)
        mask ^= bit
    return result


def _reward(remaining, edge):
    bit = 1 << edge
    boxes = _EDGE_BOXES[edge]
    result = int((remaining & _BOX_MASKS[boxes[0]]) == bit)
    if len(boxes) == 2:
        result += int((remaining & _BOX_MASKS[boxes[1]]) == bit)
    return result


@lru_cache(maxsize=65536)
def _closed_value(components):
    """Future score difference for unopened chains and loops.

    Positive integers describe chains; negative integers describe loops.
    """
    if not components:
        return 0

    best = -17
    previous = None

    for i, component in enumerate(components):
        if component == previous:
            continue
        previous = component

        rest = components[:i] + components[i + 1:]
        following = _closed_value(rest)
        size = abs(component)

        if component > 0 and size <= 2:
            # A two-chain can be opened in its middle, denying a handout.
            value = -size - following
        else:
            handout = 2 if component > 0 else 4
            value = min(
                -size - following,
                2 * handout - size + following,
            )

        if value > best:
            best = value

    return best


def _analyse(remaining):
    """Return capture edges, safe edges, box degrees, and endgame value."""
    degrees = [0] * 16
    captures = 0
    dangerous = 0
    active = 0
    simple = True

    for b, box_mask in enumerate(_BOX_MASKS):
        missing = remaining & box_mask
        degree = missing.bit_count()
        degrees[b] = degree

        if degree:
            active |= 1 << b
        if degree == 1:
            captures |= missing
        elif degree == 2:
            dangerous |= missing
        elif degree > 2:
            simple = False

    safe = remaining & ~(captures | dangerous)

    if not simple:
        return captures, safe, degrees, None

    # Every remaining component is now a chain, loop, or opened run.
    unseen = active
    closed = []
    open_boxes = 0
    smallest_handout = 99

    while unseen:
        first = unseen & -unseen
        unseen ^= first
        stack = [first.bit_length() - 1]
        size = 0
        ends = 0
        boundary = 0

        while stack:
            b = stack.pop()
            size += 1
            if degrees[b] == 1:
                ends += 1

            edges = remaining & _BOX_MASKS[b]
            while edges:
                bit = edges & -edges
                edges ^= bit
                e = bit.bit_length() - 1
                other = _EDGE_BOX_BITS[e] ^ (1 << b)

                if not other:
                    boundary += 1
                elif unseen & other:
                    unseen ^= other
                    stack.append(other.bit_length() - 1)

        if ends == 0:
            closed.append(size if boundary else -size)
        else:
            open_boxes += size
            if ends == 1 and size >= 2:
                smallest_handout = min(smallest_handout, 2)
            elif ends == 2 and size >= 4:
                smallest_handout = min(smallest_handout, 4)

    value = _closed_value(tuple(sorted(closed)))

    if open_boxes:
        take_everything = open_boxes + value
        if smallest_handout != 99:
            retain_control = (
                open_boxes - 2 * smallest_handout - value
            )
            value = max(take_everything, retain_control)
        else:
            value = take_everything

    return captures, safe, degrees, value


def _root_representatives(remaining):
    edges = _indices(remaining)
    stabilizers = []

    for permutation in _SYMMETRIES:
        transformed = 0
        for e in edges:
            transformed |= 1 << permutation[e]
        if transformed == remaining:
            stabilizers.append(permutation)

    result = 0
    for e in edges:
        if e == min(p[e] for p in stabilizers):
            result |= 1 << e
    return result


def _forced_loss(remaining, edge, degrees):
    """Boxes conceded by opening an edge and allowing greedy captures."""
    state = remaining ^ (1 << edge)
    degree = degrees.copy()
    queue = []

    for b in _EDGE_BOXES[edge]:
        degree[b] -= 1
        if degree[b] == 1:
            queue.append(b)

    lost = 0

    while queue:
        b = queue.pop()
        if degree[b] != 1:
            continue

        bit = state & _BOX_MASKS[b]
        if not bit:
            continue

        state ^= bit
        e = bit.bit_length() - 1

        for neighbor in _EDGE_BOXES[e]:
            degree[neighbor] -= 1
            if degree[neighbor] == 0:
                lost += 1
            elif degree[neighbor] == 1:
                queue.append(neighbor)

    return lost


class _SearchTimeout(Exception):
    pass


class _Node:
    __slots__ = (
        "state", "visits", "total", "moves", "children", "value"
    )

    def __init__(self, state, moves, value):
        self.state = state
        self.visits = 0
        self.total = 0.0
        self.moves = moves
        self.children = []
        self.value = value


def _choose_move(remaining, started):
    finish = started + 0.89
    rng = random.Random(remaining ^ (remaining >> 17) ^ 0x9E3779B9)
    representatives = _root_representatives(remaining)

    captures, safe, degrees, end_value = _analyse(remaining)
    preferred = captures or safe or remaining
    preferred &= representatives

    fallback = max(
        _indices(preferred),
        key=lambda e: (
            _reward(remaining, e),
            sum(degrees[b] for b in _EDGE_BOXES[e]),
        ),
    )

    # Resolve pure chain/loop positions immediately, including double-crosses.
    if end_value is not None:
        best_edge = fallback
        best_key = (-100, -1)

        for e in _indices(representatives):
            gain = _reward(remaining, e)
            child = remaining ^ (1 << e)
            child_value = _analyse(child)[3]
            value = gain + child_value if gain else -child_value
            key = (value, gain)

            if key > best_key:
                best_key = key
                best_edge = e

        return best_edge

    # Entries are (value, bound type, best edge).
    # Bound type: 0 exact, 1 lower bound, -1 upper bound.
    table = {}
    calls = 0
    search_finish = min(
        finish,
        started + (0.73 if remaining.bit_count() <= 18 else 0.54),
    )

    def exact(state, alpha, beta):
        nonlocal calls
        calls += 1
        if (calls & 127) == 0 and time.perf_counter() >= search_finish:
            raise _SearchTimeout

        old_alpha, old_beta = alpha, beta
        entry = table.get(state)
        hint = -1

        if entry is not None:
            value, bound, hint = entry
            if bound == 0:
                return value
            if bound == 1:
                alpha = max(alpha, value)
            else:
                beta = min(beta, value)
            if alpha >= beta:
                return value

        cap, quiet, deg, value = _analyse(state)
        if value is not None:
            table[state] = (value, 0, -1)
            return value

        available = state
        if state == remaining:
            available &= representatives

        ordered = []
        for e in _indices(available):
            gain = _reward(state, e)
            bit = 1 << e
            risk = sum(deg[b] == 2 for b in _EDGE_BOXES[e])
            priority = (
                1000 * (e == hint)
                + 100 * gain
                + 15 * bool(quiet & bit)
                - 3 * risk
                + sum(deg[b] for b in _EDGE_BOXES[e])
            )
            ordered.append((priority, e, gain))
        ordered.sort(reverse=True)

        best = -17
        best_edge = ordered[0][1]

        for _, e, gain in ordered:
            child = state ^ (1 << e)

            if gain:
                score = gain + exact(
                    child, alpha - gain, beta - gain
                )
            else:
                score = -exact(child, -beta, -alpha)

            if score > best:
                best = score
                best_edge = e
            if score > alpha:
                alpha = score
            if alpha >= beta:
                break

        if best <= old_alpha:
            bound = -1
        elif best >= old_beta:
            bound = 1
        else:
            bound = 0

        table[state] = (best, bound, best_edge)
        return best

    if remaining.bit_count() <= 22:
        try:
            exact(remaining, -17, 17)
            entry = table.get(remaining)
            if entry is not None and entry[1] == 0 and entry[2] >= 0:
                return entry[2]
        except _SearchTimeout:
            pass

    def known_value(state):
        entry = table.get(state)
        if entry is not None and entry[1] == 0:
            return entry[0]
        return None

    def make_node(state):
        value = known_value(state)
        if value is not None:
            return _Node(state, [], value)

        cap, quiet, deg, value = _analyse(state)
        if value is not None:
            table[state] = (value, 0, -1)
            return _Node(state, [], value)

        if cap:
            # With no safe moves, include non-captures for handouts.
            candidates = cap if quiet else state
        else:
            candidates = quiet or state

        if state == remaining:
            candidates &= representatives

        moves = _indices(candidates)
        rng.shuffle(moves)
        moves.sort(
            key=lambda e: (
                _reward(state, e),
                bool(quiet & (1 << e)),
                -sum(deg[b] == 2 for b in _EDGE_BOXES[e]),
            )
        )
        return _Node(state, moves, None)

    def rollout(state):
        accumulated = 0
        sign = 1

        while state:
            value = known_value(state)
            if value is not None:
                return accumulated + sign * value

            cap, quiet, deg, value = _analyse(state)
            if value is not None:
                table[state] = (value, 0, -1)
                return accumulated + sign * value

            if cap:
                choices = _indices(cap)
                e = rng.choice(choices)

                # Prefer double captures when available.
                if len(choices) > 1 and _reward(state, e) < 2:
                    for candidate in choices:
                        if _reward(state, candidate) == 2:
                            e = candidate
                            break

            elif quiet:
                choices = _indices(quiet)
                e = rng.choice(choices)

                # A mild bias toward leaving flexible boxes.
                if len(choices) > 1 and rng.random() < 0.20:
                    other = rng.choice(choices)
                    if (
                        sum(deg[b] for b in _EDGE_BOXES[other])
                        > sum(deg[b] for b in _EDGE_BOXES[e])
                    ):
                        e = other
            else:
                choices = _indices(state)

                if len(choices) > 1 and rng.random() < 0.85:
                    sample = (
                        choices if len(choices) <= 5
                        else rng.sample(choices, 5)
                    )
                    rng.shuffle(sample)
                    e = min(
                        sample,
                        key=lambda candidate: _forced_loss(
                            state, candidate, deg
                        ),
                    )
                else:
                    e = rng.choice(choices)

            gain = _reward(state, e)
            state ^= 1 << e

            if gain:
                accumulated += sign * gain
            else:
                sign = -sign

        return accumulated

    root = make_node(remaining)

    while time.perf_counter() < finish:
        node = root
        path = []

        while True:
            if node.value is not None:
                value = node.value
                break

            if node.moves:
                e = node.moves.pop()
                gain = _reward(node.state, e)
                direction = 1 if gain else -1
                child = make_node(node.state ^ (1 << e))
                node.children.append((e, gain, direction, child))
                path.append((node, gain, direction))
                node = child

                value = (
                    node.value if node.value is not None
                    else rollout(node.state)
                )
                break

            logarithm = math.log(max(2, node.visits))
            best_child = None
            best_ucb = -float("inf")

            for item in node.children:
                e, gain, direction, child = item
                mean = gain + direction * child.total / child.visits
                bonus = 3.8 * math.sqrt(logarithm / child.visits)
                ucb = mean + bonus

                if ucb > best_ucb:
                    best_ucb = ucb
                    best_child = item

            if best_child is None:
                value = rollout(node.state)
                break

            _, gain, direction, child = best_child
            path.append((node, gain, direction))
            node = child

        node.visits += 1
        node.total += value

        for parent, gain, direction in reversed(path):
            value = gain + direction * value
            parent.visits += 1
            parent.total += value

    if not root.children:
        return fallback

    # Prefer the most thoroughly supported root move.
    best = max(
        root.children,
        key=lambda item: (
            item[3].visits,
            item[1] + item[2] * item[3].total / item[3].visits,
        ),
    )
    return best[0]


def policy(
    horizontal: np.ndarray,
    vertical: np.ndarray,
    capture: np.ndarray,
) -> str:
    started = time.perf_counter()
    remaining = 0
    fallback = None

    for e, (r, c, direction) in enumerate(_EDGES):
        array = horizontal if direction == "H" else vertical
        if array[r, c] == 0:
            remaining |= 1 << e
            if fallback is None:
                fallback = f"{r},{c},{direction}"

    if not remaining:
        # Defensive handling if the caller treats padding entries as moves.
        for direction, array in (("H", horizontal), ("V", vertical)):
            for r in range(5):
                for c in range(5):
                    if array[r, c] == 0:
                        return f"{r},{c},{direction}"

        # A completed board has no legal move; policy normally is not called.
        return "0,0,H"

    try:
        edge = _choose_move(remaining, started)
        if remaining & (1 << edge):
            r, c, direction = _EDGES[edge]
            return f"{r},{c},{direction}"
    except Exception:
        # Search failure must never turn an available move into an illegal one.
        pass

    return fallback
