
import time
import numpy as np

_FULL = (1 << 64) - 1
_INNER_FILES = 0x7E7E7E7E7E7E7E7E
_FILE_A = 0x0101010101010101
_NOT_A = 0xFEFEFEFEFEFEFEFE
_NOT_H = 0x7F7F7F7F7F7F7F7F
_CORNERS = 0x8100000000000081
_GATHER = 0x0102040810204080
_WIN = 1_000_000
_INF = 10_000_000

# Rays in increasing and decreasing bit-index directions.
_POS_RAYS = []
_NEG_RAYS = []
for square in range(64):
    r, c = divmod(square, 8)
    groups = []
    for directions in (
        ((0, 1), (1, -1), (1, 0), (1, 1)),
        ((0, -1), (-1, 1), (-1, 0), (-1, -1)),
    ):
        rays = []
        for dr, dc in directions:
            rr, cc = r + dr, c + dc
            ray = 0
            while 0 <= rr < 8 and 0 <= cc < 8:
                ray |= 1 << (8 * rr + cc)
                rr += dr
                cc += dc
            rays.append(ray)
        groups.append(tuple(rays))
    _POS_RAYS.append(groups[0])
    _NEG_RAYS.append(groups[1])

_POS_RAYS = tuple(_POS_RAYS)
_NEG_RAYS = tuple(_NEG_RAYS)

# Number of discs on an edge connected to a same-color corner.
_EDGE_STABLE = []
for byte in range(256):
    stable = 0
    for i in range(8):
        if byte & (1 << i):
            stable |= 1 << i
        else:
            break
    for i in range(7, -1, -1):
        if byte & (1 << i):
            stable |= 1 << i
        else:
            break
    _EDGE_STABLE.append(stable.bit_count())
_EDGE_STABLE = tuple(_EDGE_STABLE)

_CORNER_NEIGHBORS = (
    (9, (1, 8)),
    (14, (6, 15)),
    (49, (48, 57)),
    (54, (55, 62)),
)
_DANGERS = []
for occupied in range(16):
    xs = cs = 0
    for j, (x, adjacent) in enumerate(_CORNER_NEIGHBORS):
        if not (occupied & (1 << j)):
            xs |= 1 << x
            for c in adjacent:
                cs |= 1 << c
    _DANGERS.append((xs, cs))
_DANGERS = tuple(_DANGERS)

_ORDER = (
    100, 0, 12, 8, 8, 12, 0, 100,
    0, -4, -2, -2, -2, -2, -4, 0,
    12, -2, 6, 3, 3, 6, -2, 12,
    8, -2, 3, 1, 1, 3, -2, 8,
    8, -2, 3, 1, 1, 3, -2, 8,
    12, -2, 6, 3, 3, 6, -2, 12,
    0, -4, -2, -2, -2, -2, -4, 0,
    100, 0, 12, 8, 8, 12, 0, 100,
)

_QUADRANTS = []
for square in range(64):
    r, c = divmod(square, 8)
    r0, c0 = (r // 4) * 4, (c // 4) * 4
    mask = 0
    for rr in range(r0, r0 + 4):
        for cc in range(c0, c0 + 4):
            mask |= 1 << (8 * rr + cc)
    _QUADRANTS.append(mask)
_QUADRANTS = tuple(_QUADRANTS)

_SAFE_EDGES = 0x3C0081818181003C
_CENTER = 0x00003C3C3C3C0000


def _moves(p, o):
    """Legal moves for p against o."""
    inner = o & _INNER_FILES
    result = 0
    for shift, twice in ((1, 2), (7, 14), (9, 18), (8, 16)):
        mask = o if shift == 8 else inner

        t = mask & (p << shift)
        t |= mask & (t << shift)
        pair = mask & (mask << shift)
        t |= pair & (t << twice)
        t |= pair & (t << twice)
        result |= t << shift

        t = mask & (p >> shift)
        t |= mask & (t >> shift)
        pair = mask & (mask >> shift)
        t |= pair & (t >> twice)
        t |= pair & (t >> twice)
        result |= t >> shift

    return result & (_FULL ^ (p | o))


def _flips(square, p, o):
    """Captured discs when p plays at square."""
    not_o = ~o
    result = 0

    for ray in _POS_RAYS[square]:
        stop = ray & not_o
        if stop:
            stop &= -stop
            if stop & p:
                result |= ray & (stop - 1)

    for ray in _NEG_RAYS[square]:
        stop = ray & not_o
        if stop:
            stop = 1 << (stop.bit_length() - 1)
            if stop & p:
                result |= ray & -(stop << 1)

    return result


def _neighbors(bits):
    sides = ((bits & _NOT_H) << 1) | ((bits & _NOT_A) >> 1)
    band = bits | sides
    return (sides | (band << 8) | (band >> 8)) & _FULL


def _danger_masks(occupied):
    index = (
        (occupied & 1)
        | ((occupied >> 6) & 2)
        | ((occupied >> 54) & 4)
        | ((occupied >> 60) & 8)
    )
    return _DANGERS[index]


def _terminal(diff):
    if diff > 0:
        return _WIN + 100 * diff
    if diff < 0:
        return -_WIN + 100 * diff
    return 0


def _stable_difference(p, o, corner_difference):
    pe = (
        p & 255,
        p >> 56,
        (((p & _FILE_A) * _GATHER) >> 56) & 255,
        ((((p >> 7) & _FILE_A) * _GATHER) >> 56) & 255,
    )
    oe = (
        o & 255,
        o >> 56,
        (((o & _FILE_A) * _GATHER) >> 56) & 255,
        ((((o >> 7) & _FILE_A) * _GATHER) >> 56) & 255,
    )

    result = -corner_difference
    table = _EDGE_STABLE
    for a, b in zip(pe, oe):
        if (a | b) == 255:
            result += a.bit_count() - b.bit_count()
        else:
            result += table[a] - table[b]
    return result


def _evaluate(p, o, legal, empties):
    occupied = p | o
    empty = _FULL ^ occupied
    other_legal = _moves(o, p)

    pm = legal.bit_count()
    om = other_legal.bit_count()
    mobility = pm - om
    mobility_weight = 9 if empties > 24 else (7 if empties > 10 else 4)
    score = mobility_weight * mobility
    score += (70 * mobility) // (pm + om + 2)

    frontier = _neighbors(empty)
    frontier_difference = (
        (p & frontier).bit_count() - (o & frontier).bit_count()
    )
    score -= (4 if empties > 18 else 2) * frontier_difference

    potential = (
        (_neighbors(o) & empty).bit_count()
        - (_neighbors(p) & empty).bit_count()
    )
    score += (2 if empties > 18 else 1) * potential

    corner_difference = (
        (p & _CORNERS).bit_count() - (o & _CORNERS).bit_count()
    )
    score += 170 * corner_difference

    xs, cs = _danger_masks(occupied)
    score -= 45 * ((p & xs).bit_count() - (o & xs).bit_count())
    score -= 18 * ((p & cs).bit_count() - (o & cs).bit_count())

    if occupied & _CORNERS:
        stable = _stable_difference(p, o, corner_difference)
        score += (22 if empties > 20 else 28) * stable

    score += 3 * (
        (p & _SAFE_EDGES).bit_count() - (o & _SAFE_EDGES).bit_count()
    )
    score += 2 * (
        (p & _CENTER).bit_count() - (o & _CENTER).bit_count()
    )

    disc_difference = 2 * p.bit_count() - (64 - empties)
    disc_weight = -1 if empties > 24 else (1 if empties > 10 else 4)
    score += disc_weight * disc_difference
    return score


class _Timeout(Exception):
    pass


class _Search:
    __slots__ = ("deadline", "nodes", "tt", "history")

    def __init__(self, deadline):
        self.deadline = deadline
        self.nodes = 0
        self.tt = {}
        self.history = [0] * 64

    def search(self, p, o, depth, alpha, beta, empties, legal=None):
        self.nodes += 1
        if (self.nodes & 63) == 0:
            if time.perf_counter() >= self.deadline:
                raise _Timeout

        if empties == 0:
            return _terminal(2 * p.bit_count() - 64)

        # Solve the last empty square directly, including passes.
        if empties == 1:
            square = (_FULL ^ (p | o)).bit_length() - 1
            flips = _flips(square, p, o)
            if flips:
                diff = 2 * p.bit_count() - 62 + 2 * flips.bit_count()
            else:
                flips = _flips(square, o, p)
                if flips:
                    diff = 2 * p.bit_count() - 64 - 2 * flips.bit_count()
                else:
                    diff = 2 * p.bit_count() - 63
            return _terminal(diff)

        original_alpha = alpha
        key = (p, o)
        tt_move = 0

        if depth > 0:
            entry = self.tt.get(key)
            if entry is not None:
                stored_depth, value, flag, tt_move = entry
                if stored_depth >= depth:
                    if flag == 0:
                        return value
                    if flag == 1 and value >= beta:
                        return value
                    if flag == 2 and value <= alpha:
                        return value

        if legal is None:
            legal = _moves(p, o)

        if not legal:
            other_legal = _moves(o, p)
            if not other_legal:
                return _terminal(2 * p.bit_count() - (64 - empties))

            value = -self.search(
                o, p, depth, -beta, -alpha, empties, other_legal
            )
            if depth > 0:
                flag = 2 if value <= original_alpha else (
                    1 if value >= beta else 0
                )
                self.tt[key] = (depth, value, flag, 0)
            return value

        if depth <= 0:
            return _evaluate(p, o, legal, empties)

        best = -_INF
        best_move = 0
        tried = 0

        # Search the previous principal-variation move before sorting others.
        if tt_move & legal:
            square = tt_move.bit_length() - 1
            flips = _flips(square, p, o)
            value = -self.search(
                o ^ flips,
                p | flips | tt_move,
                depth - 1,
                -beta,
                -alpha,
                empties - 1,
            )
            best = value
            best_move = tt_move
            tried = 1
            legal ^= tt_move
            if value > alpha:
                alpha = value
            if alpha >= beta:
                self.history[square] = min(
                    4096, self.history[square] + depth * depth
                )
                self.tt[key] = (depth, best, 1, best_move)
                return best

        children = []
        occupied = p | o
        empty = _FULL ^ occupied
        xs, cs = _danger_masks(occupied)
        remaining = legal

        while remaining:
            move = remaining & -remaining
            remaining ^= move
            square = move.bit_length() - 1
            flips = _flips(square, p, o)
            child_p = o ^ flips
            child_o = p | flips | move

            order = 16 * _ORDER[square] + self.history[square]
            if move & _CORNERS:
                order += 30000
            if move & xs:
                order -= 2000
            if move & cs:
                order -= 700

            child_legal = None
            if depth >= 3:
                child_legal = _moves(child_p, child_o)
                order -= 100 * child_legal.bit_count()
                order -= 5000 * (child_legal & _CORNERS).bit_count()
                if not child_legal:
                    order += 1000

            if empties <= 16:
                if (empty & _QUADRANTS[square]).bit_count() & 1:
                    order += 90

            children.append((order, move, child_p, child_o, child_legal))

        children.sort(reverse=True)

        for _, move, child_p, child_o, child_legal in children:
            next_depth = depth - 1

            if tried == 0:
                value = -self.search(
                    child_p, child_o, next_depth,
                    -beta, -alpha, empties - 1, child_legal
                )
            else:
                reduction = 0
                if (
                    empties > 16
                    and depth >= 4
                    and tried >= 4
                    and beta - alpha == 1
                    and not (move & _CORNERS)
                    and (child_legal is None or child_legal.bit_count() > 2)
                ):
                    reduction = 1
                    if depth >= 7 and tried >= 9:
                        reduction = 2

                value = -self.search(
                    child_p, child_o, next_depth - reduction,
                    -alpha - 1, -alpha, empties - 1, child_legal
                )

                if reduction and value > alpha:
                    value = -self.search(
                        child_p, child_o, next_depth,
                        -alpha - 1, -alpha, empties - 1, child_legal
                    )

                if alpha < value < beta:
                    value = -self.search(
                        child_p, child_o, next_depth,
                        -beta, -alpha, empties - 1, child_legal
                    )

            tried += 1
            if value > best:
                best = value
                best_move = move
            if value > alpha:
                alpha = value

            if alpha >= beta:
                square = move.bit_length() - 1
                self.history[square] = min(
                    4096, self.history[square] + depth * depth
                )
                break

        flag = 2 if best <= original_alpha else (
            1 if best >= beta else 0
        )
        self.tt[key] = (depth, best, flag, best_move)
        return best


def _notation(move):
    square = move.bit_length() - 1
    return chr(ord("a") + (square & 7)) + str((square >> 3) + 1)


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    start = time.perf_counter()

    p = 0
    o = 0
    for square, value in enumerate(you.ravel()):
        if value:
            p |= 1 << square
    for square, value in enumerate(opponent.ravel()):
        if value:
            o |= 1 << square

    legal = _moves(p, o)
    if not legal:
        return "pass"
    if not (legal & (legal - 1)):
        return _notation(legal)

    # Establish a legal fallback before starting any timed search.
    preferred = legal & _CORNERS
    best_move = (preferred & -preferred) if preferred else (legal & -legal)

    empties = 64 - (p | o).bit_count()
    engine = _Search(start + 0.90)

    if empties <= 12:
        depths = sorted({min(2, empties), min(4, empties),
                         min(6, empties), empties})
    elif empties <= 16:
        depths = [2, 4, 6, 8, empties]
    else:
        depths = range(1, empties + 1)

    previous_score = None
    root_key = (p, o)

    try:
        for depth in depths:
            if time.perf_counter() >= engine.deadline:
                break

            if (
                previous_score is not None
                and depth >= 4
                and depth < empties
                and abs(previous_score) < _WIN
            ):
                alpha = previous_score - 70
                beta = previous_score + 70
            else:
                alpha, beta = -_INF, _INF

            score = engine.search(
                p, o, depth, alpha, beta, empties, legal
            )

            if score <= alpha or score >= beta:
                score = engine.search(
                    p, o, depth, -_INF, _INF, empties, legal
                )

            entry = engine.tt.get(root_key)
            if entry is not None and (entry[3] & legal):
                best_move = entry[3]

            previous_score = score
            if depth >= empties or score >= _WIN:
                break

    except _Timeout:
        pass

    return _notation(best_move)
