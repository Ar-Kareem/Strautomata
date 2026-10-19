
import math
import random
import time
import numpy as np


# The 40 edges belonging to the 4x4 board.
_EDGES = (
    [(r, c, "H") for r in range(5) for c in range(4)]
    + [(r, c, "V") for r in range(4) for c in range(5)]
)
_INDEX = {edge: i for i, edge in enumerate(_EDGES)}
_BITS = tuple(1 << i for i in range(40))

_BOX_MASKS = []
_EDGE_BOXES = [[] for _ in range(40)]
for r in range(4):
    for c in range(4):
        b = 4 * r + c
        es = (
            _INDEX[(r, c, "H")],
            _INDEX[(r + 1, c, "H")],
            _INDEX[(r, c, "V")],
            _INDEX[(r, c + 1, "V")],
        )
        _BOX_MASKS.append(sum(_BITS[e] for e in es))
        for e in es:
            _EDGE_BOXES[e].append(b)

_BOX_MASKS = tuple(_BOX_MASKS)
_EDGE_BOXES = tuple(tuple(x) for x in _EDGE_BOXES)


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
                    p, q = transform(r, c), transform(r, c + 1)
                else:
                    p, q = transform(r, c), transform(r + 1, c)
                if p[0] == q[0]:
                    edge = (p[0], min(p[1], q[1]), "H")
                else:
                    edge = (min(p[0], q[0]), p[1], "V")
                permutation.append(_INDEX[edge])
            permutations.append(tuple(permutation))
    return tuple(permutations)


_SYMMETRIES = _make_symmetries()

# Component values do not depend on board coordinates or player identities.
_COMPONENT_CACHE = {(): 0}
_CLOSED_CACHE = {(): 0}


def _indices(mask):
    result = []
    while mask:
        bit = mask & -mask
        mask ^= bit
        result.append(bit.bit_length() - 1)
    return result


class _Timeout(Exception):
    pass


class _Engine:
    def __init__(self, mask, deadline):
        self.root_mask = mask
        self.deadline = deadline
        self.ticks = 0
        self.infos = {}
        self.tt = {}
        self.rng = random.Random(mask ^ (mask >> 17) ^ 0x9E3779B97F4A7C15)
        self.root_representatives = None
        self.partial_move = None
        self.partial_value = -100

    def tick(self):
        self.ticks += 1
        if (self.ticks & 63) == 0:
            if time.perf_counter() >= self.deadline:
                raise _Timeout

    def gain(self, mask, edge):
        bit = _BITS[edge]
        return sum(
            (_BOX_MASKS[b] & mask) == bit
            for b in _EDGE_BOXES[edge]
        )

    def info(self, mask):
        old = self.infos.get(mask)
        if old is not None:
            return old

        captures = 0
        dangerous = 0
        nonlinear = False
        live = 0
        remaining = []
        for box_mask in _BOX_MASKS:
            rem = box_mask & mask
            remaining.append(rem)
            degree = rem.bit_count()
            if degree:
                live += 1
            if degree == 1:
                captures |= rem
            elif degree == 2:
                dangerous |= rem
            elif degree > 2:
                nonlinear = True

        safe = mask & ~(captures | dangerous)
        components = None

        if not nonlinear:
            seen = 0
            components_list = []
            for start in range(16):
                if not remaining[start] or (seen & (1 << start)):
                    continue

                seen |= 1 << start
                stack = [start]
                size = stubs = open_ends = 0

                while stack:
                    b = stack.pop()
                    size += 1
                    rem = remaining[b]
                    if rem.bit_count() == 1:
                        open_ends += 1

                    while rem:
                        bit = rem & -rem
                        rem ^= bit
                        edge = bit.bit_length() - 1
                        adjacent = _EDGE_BOXES[edge]
                        if len(adjacent) == 1:
                            stubs += 1
                        else:
                            other = adjacent[0] ^ adjacent[1] ^ b
                            if not (seen & (1 << other)):
                                seen |= 1 << other
                                stack.append(other)

                # Types:
                # 0: path with two capturable ends
                # 1: path with one capturable end and one boundary stub
                # 2: unopened chain with two boundary stubs
                # 3: unopened loop
                kind = 3 if stubs == 0 and open_ends == 0 else stubs
                components_list.append((size << 2) | kind)

            components = tuple(sorted(components_list))

        answer = (captures, safe, components, live)
        self.infos[mask] = answer
        return answer

    def closed_value(self, components):
        cached = _CLOSED_CACHE.get(components)
        if cached is not None:
            return cached
        self.tick()

        best = -100
        previous = -1
        for i, code in enumerate(components):
            if code == previous:
                continue
            previous = code
            size, kind = code >> 2, code & 3
            rest = components[:i] + components[i + 1:]
            continuation = self.closed_value(rest)
            handout = 4 if kind == 3 else 2

            # The opponent either takes everything, or keeps control.
            value = min(
                -size - continuation,
                2 * handout - size + continuation,
            )
            if value > best:
                best = value

        _CLOSED_CACHE[components] = best
        return best

    def component_value(self, components):
        cached = _COMPONENT_CACHE.get(components)
        if cached is not None:
            return cached
        self.tick()

        # Standard long-chain/loop endgames have a very small exact
        # recurrence. Open components can be collected first, retaining
        # control with the cheapest available handout if desirable.
        short_closed = False
        closed = []
        open_total = 0
        donation = 100

        for code in components:
            size, kind = code >> 2, code & 3
            if kind in (2, 3):
                closed.append(code)
                if kind == 2 and size < 3:
                    short_closed = True
            else:
                open_total += size
                if kind == 1 and size >= 2:
                    donation = min(donation, 2)
                elif kind == 0 and size >= 4:
                    donation = min(donation, 4)

        if not short_closed:
            continuation = self.closed_value(tuple(closed))
            best = open_total + continuation
            if donation < 100:
                best = max(
                    best,
                    open_total - 2 * donation - continuation,
                )
            _COMPONENT_CACHE[components] = best
            return best

        # Short chains require the full component game. Drawing an edge
        # either shortens a path, opens it, or splits it into two paths.
        total = sum(code >> 2 for code in components)
        best = -100
        previous = -1

        for i, code in enumerate(components):
            if code == previous:
                continue
            previous = code
            size, kind = code >> 2, code & 3
            rest = components[:i] + components[i + 1:]
            successors = []

            if kind == 0:
                if size == 2:
                    successors.append((2, ()))
                else:
                    successors.append((1, (((size - 1) << 2),)))
                for left in range(2, size // 2 + 1):
                    successors.append((
                        0,
                        (left << 2, (size - left) << 2),
                    ))

            elif kind == 1:
                if size == 1:
                    successors.append((1, ()))
                else:
                    successors.append((
                        1, ((((size - 1) << 2) | 1),)
                    ))
                    successors.append((0, (size << 2,)))
                    for left in range(2, size):
                        successors.append((
                            0,
                            (left << 2, ((size - left) << 2) | 1),
                        ))

            elif kind == 2:
                successors.append((0, ((size << 2) | 1,)))
                for left in range(1, size // 2 + 1):
                    successors.append((
                        0,
                        ((left << 2) | 1,
                         ((size - left) << 2) | 1),
                    ))

            else:
                successors.append((0, (size << 2,)))

            for gain, added in successors:
                child = tuple(sorted(rest + added))
                future = self.component_value(child)
                value = gain + future if gain else -future
                if value > best:
                    best = value
                if best == total:
                    _COMPONENT_CACHE[components] = best
                    return best

        _COMPONENT_CACHE[components] = best
        return best

    def gift(self, mask, edge):
        """Number of boxes exposed by the local forced-capture cascade."""
        remaining = mask ^ _BITS[edge]
        pending = 0
        for b in _EDGE_BOXES[edge]:
            rem = _BOX_MASKS[b] & remaining
            if rem and not (rem & (rem - 1)):
                pending |= rem

        lost = 0
        while pending:
            bit = pending & -pending
            pending ^= bit
            if not (remaining & bit):
                continue
            e = bit.bit_length() - 1
            lost += self.gain(remaining, e)
            remaining ^= bit
            for b in _EDGE_BOXES[e]:
                rem = _BOX_MASKS[b] & remaining
                if rem and not (rem & (rem - 1)):
                    pending |= rem
        return lost

    def ordered(self, mask, info, restricted=False, randomized=False):
        captures, safe, _, _ = info

        if restricted and safe:
            allowed = captures if captures else safe
        else:
            allowed = mask

        moves = _indices(allowed)
        if randomized:
            self.rng.shuffle(moves)

        def key(edge):
            bit = _BITS[edge]
            if captures & bit:
                return (0, -self.gain(mask, edge))
            if safe & bit:
                degree_threes = sum(
                    (_BOX_MASKS[b] & mask).bit_count() == 3
                    for b in _EDGE_BOXES[edge]
                )
                return (1, 0 if randomized else -degree_threes)
            return (2, self.gift(mask, edge))

        moves.sort(key=key)
        return moves

    def solve(self, mask, alpha=-17, beta=17):
        self.tick()
        if not mask:
            return 0

        entry = self.tt.get(mask)
        if entry is not None:
            value, flag, _ = entry
            if flag == 0:
                return value
            if flag == 1:
                alpha = max(alpha, value)
            else:
                beta = min(beta, value)
            if alpha >= beta:
                return value

        original_alpha, original_beta = alpha, beta
        info = self.info(mask)
        if info[2] is not None:
            value = self.component_value(info[2])
            self.tt[mask] = (value, 0, None)
            return value

        moves = self.ordered(mask, info)
        if mask == self.root_mask and self.root_representatives is not None:
            moves = [e for e in moves if e in self.root_representatives]

        if entry is not None and entry[2] in moves:
            moves.remove(entry[2])
            moves.insert(0, entry[2])

        best = -100
        best_move = moves[0]
        for edge in moves:
            gain = self.gain(mask, edge)
            child = mask ^ _BITS[edge]
            if gain:
                value = gain + self.solve(
                    child, alpha - gain, beta - gain
                )
            else:
                value = -self.solve(child, -beta, -alpha)

            if value > best:
                best, best_move = value, edge
                if mask == self.root_mask:
                    self.partial_move = edge
                    self.partial_value = value

            alpha = max(alpha, best)
            if alpha >= beta or best == info[3]:
                break

        if best == info[3]:
            flag = 0
        elif best <= original_alpha:
            flag = 2                 # Upper bound
        elif best >= original_beta:
            flag = 1                 # Lower bound
        else:
            flag = 0                 # Exact

        self.tt[mask] = (best, flag, best_move)
        return best

    def random_edge(self, mask):
        index = self.rng.randrange(mask.bit_count())
        while index:
            mask &= mask - 1
            index -= 1
        return (mask & -mask).bit_length() - 1

    def rollout(self, mask):
        score = 0
        sign = 1

        while mask:
            self.tick()
            entry = self.tt.get(mask)
            if entry is not None and entry[1] == 0:
                return score + sign * entry[0]

            captures, safe, components, _ = self.info(mask)
            if components is not None:
                return score + sign * self.component_value(components)

            if mask.bit_count() <= 12:
                return score + sign * self.solve(mask)

            if captures:
                edge = self.random_edge(captures)
                # Prefer an available double capture.
                if self.gain(mask, edge) == 1:
                    other = self.random_edge(captures)
                    if self.gain(mask, other) == 2:
                        edge = other
            elif safe:
                edge = self.random_edge(safe)
            else:
                # Sample several possible sacrifices and prefer a short one.
                candidates = {
                    self.random_edge(mask) for _ in range(4)
                }
                edge = min(candidates, key=lambda e: self.gift(mask, e))

            gain = self.gain(mask, edge)
            score += sign * gain
            mask ^= _BITS[edge]
            if not gain:
                sign = -sign

        return score


class _Node:
    __slots__ = ("mask", "visits", "total", "exact", "todo", "children")

    def __init__(self, engine, mask, moves=None):
        self.mask = mask
        self.visits = 0
        self.total = 0.0
        self.children = []
        self.exact = None

        entry = engine.tt.get(mask)
        info = engine.info(mask)
        if entry is not None and entry[1] == 0:
            self.exact = entry[0]
        elif info[2] is not None:
            self.exact = engine.component_value(info[2])

        if self.exact is not None:
            self.todo = []
        else:
            if moves is None:
                moves = engine.ordered(
                    mask, info, restricted=True, randomized=True
                )
            self.todo = list(reversed(moves))


def _edge_value(gain, child):
    value = (
        child.exact if child.exact is not None
        else child.total / max(1, child.visits)
    )
    return gain + value if gain else -value


def _mcts(engine, mask, root_moves, fallback, hard_deadline):
    root = _Node(engine, mask, root_moves)

    if root.exact is not None:
        # A preceding exact search may already have solved this position.
        entry = engine.tt.get(mask)
        if entry is not None and entry[2] is not None:
            return entry[2]
        return fallback

    try:
        while time.perf_counter() < hard_deadline:
            node = root
            path = []

            while True:
                if node.exact is not None:
                    value = node.exact
                    break

                if node.todo:
                    edge = node.todo.pop()
                    gain = engine.gain(node.mask, edge)
                    child = _Node(engine, node.mask ^ _BITS[edge])
                    node.children.append((edge, gain, child))
                    path.append((node, gain))
                    node = child
                    value = (
                        node.exact if node.exact is not None
                        else engine.rollout(node.mask)
                    )
                    break

                if all(c.exact is not None for _, _, c in node.children):
                    node.exact = max(
                        _edge_value(g, c) for _, g, c in node.children
                    )
                    value = node.exact
                    break

                log_visits = math.log(node.visits + 1.0)
                best_score = -1e100
                selected = None

                for edge, gain, child in node.children:
                    estimate = _edge_value(gain, child)
                    if child.exact is None:
                        estimate += 4.0 * math.sqrt(
                            log_visits / max(1, child.visits)
                        )
                    if estimate > best_score:
                        best_score = estimate
                        selected = (gain, child)

                gain, child = selected
                path.append((node, gain))
                node = child

            node.visits += 1
            node.total += value

            for parent, gain in reversed(path):
                value = gain + value if gain else -value
                parent.visits += 1
                parent.total += value

                if (
                    not parent.todo
                    and parent.children
                    and all(c.exact is not None
                            for _, _, c in parent.children)
                ):
                    parent.exact = max(
                        _edge_value(g, c) for _, g, c in parent.children
                    )

            if root.exact is not None:
                break

    except _Timeout:
        pass

    usable = [
        item for item in root.children
        if item[2].visits or item[2].exact is not None
    ]
    if not usable:
        return fallback

    if root.exact is not None:
        return max(usable, key=lambda x: _edge_value(x[1], x[2]))[0]

    if any(child.exact is not None for _, _, child in usable):
        log_visits = math.log(root.visits + 2.0)

        def final_score(item):
            _, gain, child = item
            value = _edge_value(gain, child)
            if child.exact is None:
                value -= math.sqrt(log_visits / max(1, child.visits))
            return value

        return max(usable, key=final_score)[0]

    return max(
        usable,
        key=lambda x: (x[2].visits, _edge_value(x[1], x[2])),
    )[0]


def _representatives(mask):
    moves = _indices(mask)
    automorphisms = []
    for permutation in _SYMMETRIES:
        transformed = 0
        for edge in moves:
            transformed |= _BITS[permutation[edge]]
        if transformed == mask:
            automorphisms.append(permutation)

    return {
        edge for edge in moves
        if edge == min(p[edge] for p in automorphisms)
    }


def _choose(mask, start):
    hard_deadline = start + 0.88
    engine = _Engine(mask, hard_deadline)
    info = engine.info(mask)

    representatives = _representatives(mask)
    engine.root_representatives = representatives

    ordered = engine.ordered(mask, info, randomized=True)
    ordered = [e for e in ordered if e in representatives]
    fallback = ordered[0]

    # Solve pure path/loop positions, including short-chain exceptions.
    if info[2] is not None:
        try:
            target = engine.component_value(info[2])
            best = -100
            for edge in ordered:
                gain = engine.gain(mask, edge)
                child_info = engine.info(mask ^ _BITS[edge])
                future = engine.component_value(child_info[2])
                value = gain + future if gain else -future
                if value > best:
                    best, fallback = value, edge
                if value == target:
                    return edge
        except _Timeout:
            pass
        return fallback

    root_moves = engine.ordered(
        mask, info, restricted=True, randomized=True
    )
    root_moves = [e for e in root_moves if e in representatives]

    if len(root_moves) == 1 and info[1]:
        return root_moves[0]

    # Exact alpha-beta is particularly effective once only a few
    # branching boxes remain.
    edges_left = mask.bit_count()
    if edges_left <= 17 or (
        edges_left <= 22 and info[1].bit_count() <= 6
    ):
        engine.deadline = min(hard_deadline, start + 0.48)
        try:
            engine.solve(mask)
            entry = engine.tt.get(mask)
            if entry is not None and entry[1] == 0:
                if entry[2] is not None:
                    return entry[2]
        except _Timeout:
            pass

        if engine.partial_move is not None:
            fallback = engine.partial_move
            if fallback not in root_moves:
                root_moves.insert(0, fallback)
            else:
                root_moves.remove(fallback)
                root_moves.insert(0, fallback)

    engine.deadline = hard_deadline

    if time.perf_counter() >= hard_deadline:
        return fallback

    try:
        return _mcts(
            engine, mask, root_moves, fallback, hard_deadline
        )
    except _Timeout:
        return fallback


def policy(horizontal: np.ndarray,
           vertical: np.ndarray,
           capture: np.ndarray) -> str:
    start = time.perf_counter()
    mask = 0

    for edge, (row, col, direction) in enumerate(_EDGES):
        array = horizontal if direction == "H" else vertical
        if array[row, col] == 0:
            mask |= _BITS[edge]

    if not mask:
        # Normally the arena never requests a move after the game ends.
        # Also support representations that expose unused array entries.
        for direction, array in (("H", horizontal), ("V", vertical)):
            for row in range(5):
                for col in range(5):
                    if array[row, col] == 0:
                        return f"{row},{col},{direction}"
        return "0,0,H"

    fallback = (mask & -mask).bit_length() - 1

    # Bound persistent memory across many games.
    if len(_COMPONENT_CACHE) > 150000:
        _COMPONENT_CACHE.clear()
        _COMPONENT_CACHE[()] = 0
    if len(_CLOSED_CACHE) > 50000:
        _CLOSED_CACHE.clear()
        _CLOSED_CACHE[()] = 0

    try:
        edge = _choose(mask, start)
        if not isinstance(edge, int) or not (mask & _BITS[edge]):
            edge = fallback
    except Exception:
        edge = fallback

    row, col, direction = _EDGES[edge]
    return f"{row},{col},{direction}"
