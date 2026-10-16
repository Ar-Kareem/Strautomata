
import math
import random
import time
import numpy as np


# The 40 geometric edges of the 4x4 board.
_MOVES = (
    [(r, c, "H") for r in range(5) for c in range(4)]
    + [(r, c, "V") for r in range(4) for c in range(5)]
)
_LABELS = [f"{r},{c},{d}" for r, c, d in _MOVES]
_BITS = [1 << i for i in range(40)]
_BOX_MASKS = []
_EDGE_BOXES = [[] for _ in range(40)]

for r in range(4):
    for c in range(4):
        edges = (r * 4 + c, (r + 1) * 4 + c,
                 20 + r * 5 + c, 20 + r * 5 + c + 1)
        b = len(_BOX_MASKS)
        _BOX_MASKS.append(sum(_BITS[e] for e in edges))
        for e in edges:
            _EDGE_BOXES[e].append(b)

_BOX_ADJ = [[] for _ in range(16)]
for e, boxes in enumerate(_EDGE_BOXES):
    for b in boxes:
        other = -1 if len(boxes) == 1 else boxes[0] + boxes[1] - b
        _BOX_ADJ[b].append((_BITS[e], other))


def _make_symmetries():
    lookup = {m: i for i, m in enumerate(_MOVES)}
    result = []
    for reflected in range(2):
        for rotations in range(4):
            permutation = []
            for r, c, direction in _MOVES:
                if direction == "H":
                    endpoints = [(r, c), (r, c + 1)]
                else:
                    endpoints = [(r, c), (r + 1, c)]
                transformed = []
                for y, x in endpoints:
                    if reflected:
                        x = 4 - x
                    for _ in range(rotations):
                        y, x = x, 4 - y
                    transformed.append((y, x))
                (y1, x1), (y2, x2) = transformed
                if y1 == y2:
                    move = (y1, min(x1, x2), "H")
                else:
                    move = (min(y1, y2), x1, "V")
                permutation.append(lookup[move])
            result.append(permutation)
    return result


_SYMMETRIES = _make_symmetries()
_CHAIN_CACHE = {(): 0}


class _Timeout(Exception):
    pass


def _indices(mask):
    result = []
    while mask:
        bit = mask & -mask
        result.append(bit.bit_length() - 1)
        mask ^= bit
    return result


class _Engine:
    def __init__(self, deadline, seed, base_score):
        self.deadline = deadline
        self.rng = random.Random(seed)
        self.base_score = base_score
        self.ticks = 0
        self.tt = {}
        self.best_move = None
        self.best_value = -17
        self.root_values = {}

    def tick(self):
        self.ticks += 1
        if (self.ticks & 63) == 0 and time.perf_counter() >= self.deadline:
            raise _Timeout

    @staticmethod
    def degrees(mask):
        return [(mask & b).bit_count() for b in _BOX_MASKS]

    @staticmethod
    def score(edge, degrees):
        return sum(degrees[b] == 1 for b in _EDGE_BOXES[edge])

    @staticmethod
    def components(mask, degrees):
        """Encode disjoint paths and cycles when every box degree is <= 2.

        Code = 4 * number_of_boxes + kind:
          0: path open at both ends
          1: path open at one end
          2: unopened chain
          3: unopened loop
        """
        seen = 0
        codes = []
        for start in range(16):
            if not degrees[start] or (seen & (1 << start)):
                continue
            seen |= 1 << start
            stack = [start]
            size = 0
            outside = 0
            cycle = True
            while stack:
                b = stack.pop()
                size += 1
                if degrees[b] != 2:
                    cycle = False
                for bit, other in _BOX_ADJ[b]:
                    if not (mask & bit):
                        continue
                    if other < 0:
                        outside += 1
                    elif not (seen & (1 << other)):
                        seen |= 1 << other
                        stack.append(other)
            kind = 3 if cycle and outside == 0 else outside
            codes.append(4 * size + kind)
        return tuple(sorted(codes))

    def chain_value(self, state):
        cached = _CHAIN_CACHE.get(state)
        if cached is not None:
            return cached
        self.tick()

        # Harvest captures that cannot remove a useful double-cross.
        gain = 0
        normalized = []
        for code in state:
            size, kind = divmod(code, 4)
            if kind == 1:
                if size == 1:
                    gain += 1
                else:
                    gain += size - 2
                    normalized.append(9)       # Open two-box chain.
            elif kind == 0:
                if size <= 3:
                    gain += size
                else:
                    gain += size - 4
                    normalized.append(16)      # Open four-box loop.
            else:
                normalized.append(code)

        normalized = tuple(sorted(normalized))
        if normalized != state:
            value = gain + self.chain_value(normalized)
            _CHAIN_CACHE[state] = value
            return value

        best = -17
        previous = -1
        for i, code in enumerate(state):
            if code == previous:
                continue
            previous = code
            rest = state[:i] + state[i + 1:]
            size, kind = divmod(code, 4)

            if kind == 0 or kind == 1:
                # Take everything, or hand out two/four boxes.
                value = abs(size + self.chain_value(rest))
                best = max(best, value)
            elif kind == 3:
                successor = tuple(sorted(rest + (4 * size,)))
                best = max(best, -self.chain_value(successor))
            else:
                # Open at a boundary, or split the chain internally.
                successor = tuple(sorted(rest + (4 * size + 1,)))
                best = max(best, -self.chain_value(successor))
                for left in range(1, size // 2 + 1):
                    successor = tuple(sorted(
                        rest + (4 * left + 1, 4 * (size - left) + 1)
                    ))
                    best = max(best, -self.chain_value(successor))

        _CHAIN_CACHE[state] = best
        return best

    def ordered_moves(self, mask, degrees):
        def priority(e):
            boxes = _EDGE_BOXES[e]
            captures = sum(degrees[b] == 1 for b in boxes)
            danger = sum(degrees[b] == 2 for b in boxes)
            safe = captures == 0 and danger == 0
            return 1000 * captures + 100 * safe - 10 * danger
        return sorted(_indices(mask), key=priority, reverse=True)

    def search(self, mask, alpha, beta):
        self.tick()
        if not mask:
            return 0

        entry = self.tt.get(mask)
        if entry is not None:
            value, flag = entry
            if flag == 0:
                return value
            if flag == 1:
                alpha = max(alpha, value)
            else:
                beta = min(beta, value)
            if alpha >= beta:
                return value

        degrees = self.degrees(mask)
        if max(degrees) <= 2:
            value = self.chain_value(self.components(mask, degrees))
            self.tt[mask] = (value, 0)
            return value

        original_alpha, original_beta = alpha, beta
        best = -17
        for edge in self.ordered_moves(mask, degrees):
            captured = self.score(edge, degrees)
            successor = mask ^ _BITS[edge]
            if captured:
                value = captured + self.search(
                    successor, alpha - captured, beta - captured
                )
            else:
                value = -self.search(successor, -beta, -alpha)

            best = max(best, value)
            alpha = max(alpha, best)
            if alpha >= beta:
                break

        flag = (-1 if best <= original_alpha
                else 1 if best >= original_beta else 0)
        self.tt[mask] = (best, flag)
        return best

    def search_root(self, mask, representatives):
        degrees = self.degrees(mask)
        allowed = set(representatives)
        moves = [e for e in self.ordered_moves(mask, degrees) if e in allowed]
        alpha = -17

        for edge in moves:
            if time.perf_counter() >= self.deadline:
                raise _Timeout
            captured = self.score(edge, degrees)
            successor = mask ^ _BITS[edge]
            if captured:
                value = captured + self.search(
                    successor, alpha - captured, 17 - captured
                )
            else:
                value = -self.search(successor, -17, -alpha)

            self.root_values[edge] = value
            if self.best_move is None or value > self.best_value:
                self.best_move = edge
                self.best_value = value
            alpha = max(alpha, value)

            # A proven win is sufficient.
            if self.base_score + self.best_value > 0:
                return self.best_move

        return self.best_move

    def sensible_moves(self, mask, degrees):
        captures, safe, other = [], [], []
        for e in _indices(mask):
            boxes = _EDGE_BOXES[e]
            if any(degrees[b] == 1 for b in boxes):
                captures.append(e)
            elif all(degrees[b] >= 3 for b in boxes):
                safe.append(e)
            else:
                other.append(e)

        if captures:
            # With safe moves left, collecting boxes is normally free.
            return captures if safe else captures + other
        return safe if safe else other

    @staticmethod
    def gift(mask, degrees, edge):
        """Boxes conceded by an opening followed by greedy captures."""
        degrees = degrees[:]
        mask ^= _BITS[edge]
        queue = []
        for b in _EDGE_BOXES[edge]:
            degrees[b] -= 1
            if degrees[b] == 1:
                queue.append(b)

        total = 0
        while queue:
            b = queue.pop()
            if degrees[b] != 1:
                continue
            bit = mask & _BOX_MASKS[b]
            if not bit:
                continue
            mask ^= bit
            e = bit.bit_length() - 1
            for neighbor in _EDGE_BOXES[e]:
                degrees[neighbor] -= 1
                if degrees[neighbor] == 0:
                    total += 1
                elif degrees[neighbor] == 1:
                    queue.append(neighbor)
        return total

    def rollout(self, mask, turn, score):
        while mask:
            self.tick()
            degrees = self.degrees(mask)
            if max(degrees) <= 2:
                return score + turn * self.chain_value(
                    self.components(mask, degrees)
                )

            entry = self.tt.get(mask)
            if entry is not None and entry[1] == 0:
                return score + turn * entry[0]

            if mask.bit_count() <= 10:
                return score + turn * self.search(mask, -17, 17)

            captures, safe, risky = [], [], []
            for edge in _indices(mask):
                boxes = _EDGE_BOXES[edge]
                n = sum(degrees[b] == 1 for b in boxes)
                if n:
                    captures.append((n, edge))
                elif all(degrees[b] >= 3 for b in boxes):
                    safe.append(edge)
                else:
                    risky.append(edge)

            if captures:
                maximum = max(n for n, _ in captures)
                edge = self.rng.choice(
                    [e for n, e in captures if n == maximum]
                )
            elif safe:
                edge = self.rng.choice(safe)
            else:
                self.rng.shuffle(risky)
                edge = min(risky, key=lambda e: self.gift(mask, degrees, e))

            captured = self.score(edge, degrees)
            mask ^= _BITS[edge]
            if captured:
                score += turn * captured
            else:
                turn = -turn
        return score


class _Node:
    __slots__ = (
        "mask", "turn", "score", "degrees", "untried", "children",
        "visits", "total", "end", "edge"
    )

    def __init__(self, engine, mask, turn, score, edge=-1, actions=None):
        self.mask = mask
        self.turn = turn
        self.score = score
        self.edge = edge
        self.degrees = engine.degrees(mask)
        self.children = []
        self.visits = 0
        self.total = 0.0
        self.end = None

        if not mask:
            self.end = score
        elif max(self.degrees) <= 2:
            self.end = score + turn * engine.chain_value(
                engine.components(mask, self.degrees)
            )
        else:
            entry = engine.tt.get(mask)
            if entry is not None and entry[1] == 0:
                self.end = score + turn * entry[0]

        if self.end is not None:
            self.untried = []
        else:
            self.untried = list(
                actions if actions is not None
                else engine.sensible_moves(mask, self.degrees)
            )
            engine.rng.shuffle(self.untried)


def _mcts(engine, mask, actions, fallback):
    root = _Node(engine, mask, 1, 0, actions=actions)
    if root.end is not None:
        return fallback

    try:
        while time.perf_counter() < engine.deadline:
            node = root
            path = [node]

            while node.end is None:
                if node.untried:
                    edge = node.untried.pop()
                    captured = engine.score(edge, node.degrees)
                    child = _Node(
                        engine,
                        node.mask ^ _BITS[edge],
                        node.turn if captured else -node.turn,
                        node.score + node.turn * captured,
                        edge
                    )
                    node.children.append(child)
                    node = child
                    path.append(node)
                    break

                logarithm = math.log(max(2, node.visits))
                turn = node.turn
                node = max(
                    node.children,
                    key=lambda child: (
                        turn * child.total / child.visits
                        + 0.65 * math.sqrt(logarithm / child.visits)
                    )
                )
                path.append(node)

            result = (
                node.end if node.end is not None
                else engine.rollout(node.mask, node.turn, node.score)
            )
            final_margin = engine.base_score + result
            reward = final_margin / (3.0 + abs(final_margin))
            for visited in path:
                visited.visits += 1
                visited.total += reward

    except _Timeout:
        pass

    completed = [child for child in root.children if child.visits]
    if not completed:
        return fallback
    return max(
        completed, key=lambda child: (child.visits, child.total / child.visits)
    ).edge


def _representatives(mask):
    stabilizers = []
    for permutation in _SYMMETRIES:
        transformed = 0
        remaining = mask
        while remaining:
            bit = remaining & -remaining
            transformed |= _BITS[permutation[bit.bit_length() - 1]]
            remaining ^= bit
        if transformed == mask:
            stabilizers.append(permutation)

    return [
        e for e in _indices(mask)
        if e == min(permutation[e] for permutation in stabilizers)
    ]


def policy(horizontal: np.ndarray, vertical: np.ndarray,
           capture: np.ndarray) -> str:
    started = time.perf_counter()
    deadline = started + 0.90

    legal = []
    for e, (r, c, direction) in enumerate(_MOVES):
        array = horizontal if direction == "H" else vertical
        if array[r, c] == 0:
            legal.append(e)

    # Terminal positions should not request a move. This also accommodates
    # interfaces that expose unused array entries as legal edges.
    if not legal:
        for direction, array in (("H", horizontal), ("V", vertical)):
            for r in range(5):
                for c in range(5):
                    if array[r, c] == 0:
                        return f"{r},{c},{direction}"
        return "0,0,H"

    fallback = legal[0]
    try:
        mask = sum(_BITS[e] for e in legal)
        degrees = _Engine.degrees(mask)

        def fallback_rank(e):
            boxes = _EDGE_BOXES[e]
            captures = sum(degrees[b] == 1 for b in boxes)
            dangerous = sum(degrees[b] == 2 for b in boxes)
            return captures, -dangerous

        fallback = max(legal, key=fallback_rank)
        if len(legal) == 1:
            return _LABELS[fallback]

        base_score = sum(
            int(capture[r, c]) for r in range(4) for c in range(4)
        )
        if len(_CHAIN_CACHE) > 150000:
            _CHAIN_CACHE.clear()
            _CHAIN_CACHE[()] = 0

        engine = _Engine(
            deadline, mask ^ (base_score + 32) * 1000003, base_score
        )
        representatives = _representatives(mask)
        pure_endgame = max(degrees) <= 2

        if pure_endgame or len(legal) <= 22:
            allowance = 0.90 if pure_endgame else (
                0.64 if len(legal) <= 18 else 0.34
            )
            engine.deadline = min(deadline, started + allowance)
            try:
                answer = engine.search_root(mask, representatives)
                if answer is not None:
                    return _LABELS[answer]
            except _Timeout:
                pass

            if engine.best_move is not None:
                fallback = engine.best_move
                if base_score + engine.best_value >= 0:
                    return _LABELS[fallback]

        engine.deadline = deadline
        if time.perf_counter() >= deadline - 0.01:
            return _LABELS[fallback]

        sensible = set(engine.sensible_moves(mask, degrees))
        actions = [e for e in representatives if e in sensible]
        if not actions:
            actions = representatives
        if len(actions) == 1:
            return _LABELS[actions[0]]

        answer = _mcts(engine, mask, actions, fallback)

        # Do not discard a better proven result for an inferior searched move.
        known = engine.root_values.get(answer)
        if (known is not None and engine.best_move is not None
                and known < engine.best_value):
            answer = engine.best_move

        return _LABELS[answer] if answer in legal else _LABELS[fallback]

    except Exception:
        return _LABELS[fallback]
