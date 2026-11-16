
import time
import numpy as np

_FULL = (1 << 64) - 1
_A = 0x0101010101010101
_H = 0x8080808080808080
_NOT_A = _FULL ^ _A
_NOT_H = _FULL ^ _H
_INNER = 0x7E7E7E7E7E7E7E7E
_CORNERS = 0x8100000000000081
_PACK = 0x0102040810204080

_INF = 10**9
_WIN = 1000000
_EXACT, _LOWER, _UPPER = 0, 1, 2

_QUADS = (
    0x000000000F0F0F0F,
    0x00000000F0F0F0F0,
    0x0F0F0F0F00000000,
    0xF0F0F0F000000000,
)


def _build_tables():
    positive = [[] for _ in range(64)]
    negative = [[] for _ in range(64)]
    directions = (
        (0, 1), (1, 0), (1, 1), (1, -1),
        (0, -1), (-1, 0), (-1, -1), (-1, 1),
    )

    for square in range(64):
        r, c = divmod(square, 8)
        for dr, dc in directions:
            rr, cc = r + dr, c + dc
            if not (0 <= rr < 8 and 0 <= cc < 8):
                continue
            adjacent = 1 << (8 * rr + cc)
            ray = 0
            while 0 <= rr < 8 and 0 <= cc < 8:
                ray |= 1 << (8 * rr + cc)
                rr += dr
                cc += dc
            target = positive if 8 * dr + dc > 0 else negative
            target[square].append((ray, adjacent))

    pst = (
        (0, 0, 16, 8, 8, 16, 0, 0),
        (0, 0, -10, -8, -8, -10, 0, 0),
        (16, -10, 12, 4, 4, 12, -10, 16),
        (8, -8, 4, 2, 2, 4, -8, 8),
        (8, -8, 4, 2, 2, 4, -8, 8),
        (16, -10, 12, 4, 4, 12, -10, 16),
        (0, 0, -10, -8, -8, -10, 0, 0),
        (0, 0, 16, 8, 8, 16, 0, 0),
    )
    groups = {}
    order = [0] * 64
    for square in range(64):
        weight = pst[square // 8][square % 8]
        order[square] = 2 * weight
        if weight:
            groups[weight] = groups.get(weight, 0) | (1 << square)

    adjacency = [0] * 64
    risk = [0] * 64
    corner_data = []
    for square in (0, 7, 56, 63):
        r, c = divmod(square, 8)
        dr = 1 if r == 0 else -1
        dc = 1 if c == 0 else -1
        corner = 1 << square
        c1 = 8 * (r + dr) + c
        c2 = 8 * r + c + dc
        x = 8 * (r + dr) + c + dc
        cs = (1 << c1) | (1 << c2)
        xs = 1 << x
        corner_data.append((corner, cs, xs))
        order[square] = 10000
        for i in (c1, c2):
            adjacency[i] = corner
            risk[i] = 65
        adjacency[x] = corner
        risk[x] = 170

    anchored = [0] * 256
    for value in range(256):
        stable = 0
        bit = 1
        while bit <= 128 and value & bit:
            stable |= bit
            bit <<= 1
        bit = 128
        while bit and value & bit:
            stable |= bit
            bit >>= 1
        anchored[value] = stable.bit_count()

    # Each table entry describes the stable-disc difference on one edge.
    edge = [0] * 65536
    for p in range(256):
        available = 255 ^ p
        o = available
        while True:
            if (p | o) == 255:
                value = p.bit_count() - o.bit_count()
            else:
                value = anchored[p] - anchored[o]
            edge[p | (o << 8)] = value
            if not o:
                break
            o = (o - 1) & available

    return (
        positive, negative, tuple(groups.items()), order,
        adjacency, risk, tuple(corner_data), edge,
    )


_POS, _NEG, _PST, _ORDER, _ADJ, _RISK, _CORNER_DATA, _EDGE = _build_tables()
_TT = {}


def _legal(p, o):
    """All legal placements, using parallel directional propagation."""
    mask = o & _INNER

    t = mask & (p << 1)
    t |= mask & (t << 1)
    pairs = mask & (mask << 1)
    t |= pairs & (t << 2)
    t |= pairs & (t << 2)
    result = t << 1

    t = mask & (p >> 1)
    t |= mask & (t >> 1)
    pairs = mask & (mask >> 1)
    t |= pairs & (t >> 2)
    t |= pairs & (t >> 2)
    result |= t >> 1

    t = mask & (p << 7)
    t |= mask & (t << 7)
    pairs = mask & (mask << 7)
    t |= pairs & (t << 14)
    t |= pairs & (t << 14)
    result |= t << 7

    t = mask & (p >> 7)
    t |= mask & (t >> 7)
    pairs = mask & (mask >> 7)
    t |= pairs & (t >> 14)
    t |= pairs & (t >> 14)
    result |= t >> 7

    t = mask & (p << 9)
    t |= mask & (t << 9)
    pairs = mask & (mask << 9)
    t |= pairs & (t << 18)
    t |= pairs & (t << 18)
    result |= t << 9

    t = mask & (p >> 9)
    t |= mask & (t >> 9)
    pairs = mask & (mask >> 9)
    t |= pairs & (t >> 18)
    t |= pairs & (t >> 18)
    result |= t >> 9

    t = o & (p << 8)
    t |= o & (t << 8)
    pairs = o & (o << 8)
    t |= pairs & (t << 16)
    t |= pairs & (t << 16)
    result |= t << 8

    t = o & (p >> 8)
    t |= o & (t >> 8)
    pairs = o & (o >> 8)
    t |= pairs & (t >> 16)
    t |= pairs & (t >> 16)
    result |= t >> 8

    return result & (_FULL ^ (p | o))


def _flips(square, p, o):
    flipped = 0
    not_o = ~o

    for ray, adjacent in _POS[square]:
        if o & adjacent:
            blockers = ray & not_o
            if blockers:
                anchor = blockers & -blockers
                if anchor & p:
                    flipped |= ray & (anchor - 1)

    for ray, adjacent in _NEG[square]:
        if o & adjacent:
            blockers = ray & not_o
            if blockers:
                anchor = 1 << (blockers.bit_length() - 1)
                if anchor & p:
                    flipped |= ray & -(anchor << 1)

    return flipped


def _neighbors(bits):
    horizontal = ((bits & _NOT_A) >> 1) | ((bits & _NOT_H) << 1)
    combined = bits | horizontal
    return horizontal | (combined << 8) | (combined >> 8)


def _outcome(difference):
    if difference > 0:
        return _WIN + 100 * difference
    if difference < 0:
        return -_WIN + 100 * difference
    return 0


def _evaluate(p, o, moves, empty_count):
    empty = _FULL ^ (p | o)
    opponent_moves = _legal(o, p)

    if empty_count > 40:
        mobility_w, potential_w, frontier_w = 40, 8, 12
        stable_w, disc_w = 65, -3
    elif empty_count > 20:
        mobility_w, potential_w, frontier_w = 44, 6, 10
        stable_w, disc_w = 80, 0
    elif empty_count > 10:
        mobility_w, potential_w, frontier_w = 38, 4, 7
        stable_w, disc_w = 95, 7
    else:
        mobility_w, potential_w, frontier_w = 26, 2, 3
        stable_w, disc_w = 100, 20

    corner_difference = (
        (p & _CORNERS).bit_count() - (o & _CORNERS).bit_count()
    )
    score = 360 * corner_difference
    danger = 0

    for corner, cs, xs in _CORNER_DATA:
        if empty & corner:
            danger |= cs | xs
            score -= 45 * ((p & cs).bit_count() - (o & cs).bit_count())
            score -= 135 * ((p & xs).bit_count() - (o & xs).bit_count())

    mobility_difference = moves.bit_count() - opponent_moves.bit_count()
    safe_difference = (
        (moves & ~danger).bit_count()
        - (opponent_moves & ~danger).bit_count()
    )
    score += (mobility_w - 10) * mobility_difference + 10 * safe_difference
    score += 120 * (
        (moves & _CORNERS).bit_count()
        - (opponent_moves & _CORNERS).bit_count()
    )

    frontier = _neighbors(empty)
    score -= frontier_w * (
        (p & frontier).bit_count() - (o & frontier).bit_count()
    )
    score += potential_w * (
        (_neighbors(o) & empty).bit_count()
        - (_neighbors(p) & empty).bit_count()
    )

    # Pack the two vertical edges into bytes.
    pa = (((p & _A) * _PACK) >> 56) & 255
    oa = (((o & _A) * _PACK) >> 56) & 255
    ph = ((((p >> 7) & _A) * _PACK) >> 56) & 255
    oh = ((((o >> 7) & _A) * _PACK) >> 56) & 255

    stable_difference = (
        _EDGE[(p & 255) | ((o & 255) << 8)]
        + _EDGE[(p >> 56) | ((o >> 56) << 8)]
        + _EDGE[pa | (oa << 8)]
        + _EDGE[ph | (oh << 8)]
        - corner_difference
    )
    score += stable_w * stable_difference

    positional = 0
    for weight, mask in _PST:
        positional += weight * (
            (p & mask).bit_count() - (o & mask).bit_count()
        )
    score += positional if empty_count > 16 else positional // 2
    score += disc_w * (p.bit_count() - o.bit_count())

    if empty_count <= 16:
        score += 12 if empty_count & 1 else -12

    return score


class _Timeout(Exception):
    pass


class _Search:
    __slots__ = (
        "deadline", "nodes", "tt", "history", "killers", "root_move"
    )

    def __init__(self, deadline):
        self.deadline = deadline
        self.nodes = 0
        self.tt = _TT
        self.history = [[0] * 64 for _ in range(2)]
        self.killers = [[0, 0] for _ in range(128)]
        self.root_move = 0

    def ordered(self, p, o, moves, hash_move, depth, ply, empty, count):
        # Yield the hash move before constructing the remaining children.
        if hash_move & moves:
            square = hash_move.bit_length() - 1
            flips = _flips(square, p, o)
            yield hash_move, o ^ flips, p | flips | hash_move, -1
            moves ^= hash_move

        if not moves:
            return

        odd = 0
        if count <= 16:
            for quadrant in _QUADS:
                if (empty & quadrant).bit_count() & 1:
                    odd |= quadrant

        history = self.history[ply & 1]
        killer1, killer2 = self.killers[ply]
        deep = depth >= 3
        candidates = []

        while moves:
            move = moves & -moves
            moves ^= move
            square = move.bit_length() - 1

            priority = _ORDER[square] + (history[square] >> 4)
            if empty & _ADJ[square]:
                priority -= _RISK[square]
            if move == killer1:
                priority += 300
            elif move == killer2:
                priority += 180
            if move & odd:
                priority += 90

            if deep:
                flips = _flips(square, p, o)
                cp, co = o ^ flips, p | flips | move
                cm = _legal(cp, co)
                priority -= 35 * cm.bit_count()
                if not cm:
                    priority += 1800
                candidates.append((priority, move, cp, co, cm))
            else:
                candidates.append((priority, move, 0, 0, -1))

        candidates.sort(reverse=True)
        for _, move, cp, co, cm in candidates:
            if not deep:
                flips = _flips(move.bit_length() - 1, p, o)
                cp, co = o ^ flips, p | flips | move
            yield move, cp, co, cm

    def search(self, p, o, depth, alpha, beta, ply=0, known_moves=-1):
        self.nodes += 1
        if (self.nodes & 63) == 0 and time.perf_counter() >= self.deadline:
            raise _Timeout

        key = (p, o)
        entry = self.tt.get(key)
        hash_move = 0

        if entry is not None:
            td, flag, value, hash_move = entry
            if td >= depth:
                if (
                    flag == _EXACT
                    or (flag == _LOWER and value >= beta)
                    or (flag == _UPPER and value <= alpha)
                ):
                    if ply == 0:
                        self.root_move = hash_move
                    return value

        occupied = p | o
        empty_count = 64 - occupied.bit_count()
        if not empty_count:
            value = _outcome(p.bit_count() - o.bit_count())
            self.tt[key] = (64, _EXACT, value, 0)
            return value

        moves = _legal(p, o) if known_moves < 0 else known_moves
        original_alpha = alpha

        if not moves:
            other_moves = _legal(o, p)
            if not other_moves:
                value = _outcome(p.bit_count() - o.bit_count())
                self.tt[key] = (64, _EXACT, value, 0)
                return value

            # A pass changes the player but consumes no search depth.
            value = -self.search(
                o, p, depth, -beta, -alpha, ply + 1, other_moves
            )
            flag = (
                _UPPER if value <= original_alpha
                else _LOWER if value >= beta
                else _EXACT
            )
            stored_depth = 64 if depth >= empty_count else depth
            if entry is None or stored_depth >= entry[0]:
                self.tt[key] = (stored_depth, flag, value, 0)
            return value

        if depth <= 0:
            value = _evaluate(p, o, moves, empty_count)
            if entry is None or entry[0] <= 0:
                self.tt[key] = (0, _EXACT, value, 0)
            return value

        if empty_count == 1:
            move = moves & -moves
            flips = _flips(move.bit_length() - 1, p, o)
            difference = (
                p.bit_count() - o.bit_count() + 1 + 2 * flips.bit_count()
            )
            value = _outcome(difference)
            self.tt[key] = (64, _EXACT, value, move)
            if ply == 0:
                self.root_move = move
            return value

        best_value = -_INF
        best_move = 0
        empty = _FULL ^ occupied
        pv_node = beta - alpha > 1

        children = self.ordered(
            p, o, moves, hash_move, depth, ply, empty, empty_count
        )
        for index, (move, cp, co, cm) in enumerate(children):
            next_depth = depth - 1

            if index == 0:
                value = -self.search(
                    cp, co, next_depth, -beta, -alpha, ply + 1, cm
                )
            else:
                reduction = 0
                if (
                    depth >= 5
                    and index >= 4
                    and empty_count > 18
                    and not (move & _CORNERS)
                    and cm != 0
                ):
                    reduction = 1
                    if depth >= 7 and index >= 10 and not pv_node:
                        reduction = 2

                if reduction:
                    value = -self.search(
                        cp, co, next_depth - reduction,
                        -alpha - 1, -alpha, ply + 1, cm
                    )

                if not reduction or value > alpha:
                    value = -self.search(
                        cp, co, next_depth,
                        -alpha - 1, -alpha, ply + 1, cm
                    )
                    if alpha < value < beta:
                        value = -self.search(
                            cp, co, next_depth,
                            -beta, -alpha, ply + 1, cm
                        )

            if value > best_value:
                best_value = value
                best_move = move
                if ply == 0:
                    self.root_move = move

            if value > alpha:
                alpha = value

            if alpha >= beta:
                square = move.bit_length() - 1
                history = self.history[ply & 1]
                history[square] = min(
                    4096, history[square] + depth * depth
                )
                killers = self.killers[ply]
                if killers[0] != move:
                    killers[1] = killers[0]
                    killers[0] = move
                break

        flag = (
            _UPPER if best_value <= original_alpha
            else _LOWER if best_value >= beta
            else _EXACT
        )
        stored_depth = 64 if depth >= empty_count else depth
        if entry is None or stored_depth >= entry[0]:
            self.tt[key] = (stored_depth, flag, best_value, best_move)

        return best_value


def _notation(move):
    square = move.bit_length() - 1
    return chr(ord("a") + (square & 7)) + str((square >> 3) + 1)


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    start = time.perf_counter()
    deadline = start + 0.90

    p = 0
    o = 0
    for square, occupied in enumerate(you.flat):
        if occupied:
            p |= 1 << square
    for square, occupied in enumerate(opponent.flat):
        if occupied:
            o |= 1 << square

    legal = _legal(p, o)
    if not legal:
        return "pass"

    if not (legal & (legal - 1)):
        return _notation(legal)

    corners = legal & _CORNERS
    fallback = corners if corners else legal
    best_move = fallback & -fallback

    if len(_TT) > 180000:
        _TT.clear()

    empty_count = 64 - (p | o).bit_count()
    cached = _TT.get((p, o))
    if cached is not None and cached[3] & legal:
        best_move = cached[3]
        if cached[1] == _EXACT and cached[0] >= empty_count:
            return _notation(best_move)

    engine = _Search(deadline)
    engine.root_move = best_move
    previous = None

    if empty_count <= 8:
        depths = sorted(set((1, empty_count)))
    elif empty_count <= 10:
        depths = (1, 4, empty_count)
    elif empty_count <= 12:
        depths = (1, 2, 4, 6, empty_count)
    else:
        depths = range(1, empty_count + 1)

    try:
        for depth in depths:
            if time.perf_counter() >= deadline:
                break

            engine.root_move = best_move
            if previous is None or depth == empty_count:
                alpha, beta = -_INF, _INF
            else:
                window = 170 + 12 * depth
                alpha, beta = previous - window, previous + window

            value = engine.search(p, o, depth, alpha, beta, 0, legal)

            # A fail-high winning score already establishes a winning move.
            if value >= _WIN and engine.root_move & legal:
                best_move = engine.root_move
                break

            if value <= alpha or value >= beta:
                value = engine.search(
                    p, o, depth, -_INF, _INF, 0, legal
                )

            if engine.root_move & legal:
                best_move = engine.root_move
            previous = value

            if depth >= empty_count or abs(value) >= _WIN:
                break

    except _Timeout:
        pass

    # Only moves from the original legal set can be returned.
    if not (best_move & legal) or best_move & (best_move - 1):
        best_move = legal & -legal
    return _notation(best_move)
