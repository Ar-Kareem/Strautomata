
import time
import numpy as np


FULL = (1 << 64) - 1
FILE_A = 0x0101010101010101
NOT_A = 0xFEFEFEFEFEFEFEFE
NOT_H = 0x7F7F7F7F7F7F7F7F
INNER_FILES = 0x7E7E7E7E7E7E7E7E
PACK_FILE = 0x0102040810204080

CORNERS = (1 << 0) | (1 << 7) | (1 << 56) | (1 << 63)
WIN = 100000
INF = 1000000

# Corner, diagonally adjacent square, orthogonally adjacent squares.
CORNER_INFO = (
    (1 << 0, 1 << 9, (1 << 1) | (1 << 8)),
    (1 << 7, 1 << 14, (1 << 6) | (1 << 15)),
    (1 << 56, 1 << 49, (1 << 48) | (1 << 57)),
    (1 << 63, 1 << 54, (1 << 55) | (1 << 62)),
)
ALL_X = sum(x for _, x, _ in CORNER_INFO)
ALL_C = sum(c for _, _, c in CORNER_INFO)
CORNER_ZONE = CORNERS | ALL_X | ALL_C

EDGE_SAFE = 0
SECOND_RING = 0
SWEET = 0
ORDER_WEIGHT = []

for _i in range(64):
    _r, _c = divmod(_i, 8)
    _b = 1 << _i
    if _b & CORNERS:
        _w = 100
    elif _b & (ALL_X | ALL_C):
        _w = 0
    elif _r in (0, 7) or _c in (0, 7):
        EDGE_SAFE |= _b
        _w = 12
    elif _r in (1, 6) or _c in (1, 6):
        SECOND_RING |= _b
        _w = -4
    elif _r in (2, 5) and _c in (2, 5):
        SWEET |= _b
        _w = 8
    else:
        _w = 2
    ORDER_WEIGHT.append(_w)

# Four increasing-index rays followed by four decreasing-index rays.
_DIRECTIONS = (
    (0, 1), (1, -1), (1, 0), (1, 1),
    (0, -1), (-1, 1), (-1, 0), (-1, -1),
)
_RAYS = []
for _sq in range(64):
    _r, _c = divmod(_sq, 8)
    _rr = []
    for _dr, _dc in _DIRECTIONS:
        _mask = 0
        _y, _x = _r + _dr, _c + _dc
        while 0 <= _y < 8 and 0 <= _x < 8:
            _mask |= 1 << (8 * _y + _x)
            _y += _dr
            _x += _dc
        _rr.append(_mask)
    _RAYS.append(tuple(_rr))
RAYS = tuple(_RAYS)

# Number of edge discs connected to either same-color corner.
_EDGE_STABLE = []
for _v in range(256):
    _mask = 0
    for _j in range(8):
        if not (_v & (1 << _j)):
            break
        _mask |= 1 << _j
    for _j in range(7, -1, -1):
        if not (_v & (1 << _j)):
            break
        _mask |= 1 << _j
    _EDGE_STABLE.append(_mask.bit_count())
EDGE_STABLE = tuple(_EDGE_STABLE)

# Entries: (depth, score, bound, best_move).
# Bounds: 0 = exact, 1 = lower, 2 = upper.
_TT = {}


def _legal(p, o):
    """Return all legal moves for p as a bitboard."""
    h = o & INNER_FILES

    t = h & (p << 1)
    t |= h & (t << 1)
    a = h & (h << 1)
    t |= a & (t << 2)
    t |= a & (t << 2)
    moves = t << 1

    t = h & (p >> 1)
    t |= h & (t >> 1)
    a = h & (h >> 1)
    t |= a & (t >> 2)
    t |= a & (t >> 2)
    moves |= t >> 1

    t = o & (p << 8)
    t |= o & (t << 8)
    a = o & (o << 8)
    t |= a & (t << 16)
    t |= a & (t << 16)
    moves |= t << 8

    t = o & (p >> 8)
    t |= o & (t >> 8)
    a = o & (o >> 8)
    t |= a & (t >> 16)
    t |= a & (t >> 16)
    moves |= t >> 8

    t = h & (p << 7)
    t |= h & (t << 7)
    a = h & (h << 7)
    t |= a & (t << 14)
    t |= a & (t << 14)
    moves |= t << 7

    t = h & (p >> 7)
    t |= h & (t >> 7)
    a = h & (h >> 7)
    t |= a & (t >> 14)
    t |= a & (t >> 14)
    moves |= t >> 7

    t = h & (p << 9)
    t |= h & (t << 9)
    a = h & (h << 9)
    t |= a & (t << 18)
    t |= a & (t << 18)
    moves |= t << 9

    t = h & (p >> 9)
    t |= h & (t >> 9)
    a = h & (h >> 9)
    t |= a & (t >> 18)
    t |= a & (t >> 18)
    moves |= t >> 9

    return moves & (FULL ^ (p | o))


def _flips(p, o, sq):
    """Find captured discs using the nearest non-opponent on each ray."""
    rays = RAYS[sq]
    inv = ~o
    flips = 0

    ray = rays[0]
    z = ray & inv
    b = z & -z
    if b & p:
        flips |= ray & (b - 1)

    ray = rays[1]
    z = ray & inv
    b = z & -z
    if b & p:
        flips |= ray & (b - 1)

    ray = rays[2]
    z = ray & inv
    b = z & -z
    if b & p:
        flips |= ray & (b - 1)

    ray = rays[3]
    z = ray & inv
    b = z & -z
    if b & p:
        flips |= ray & (b - 1)

    ray = rays[4]
    b = 1 << (ray & inv).bit_length()
    if (b >> 1) & p:
        flips |= ray & -b

    ray = rays[5]
    b = 1 << (ray & inv).bit_length()
    if (b >> 1) & p:
        flips |= ray & -b

    ray = rays[6]
    b = 1 << (ray & inv).bit_length()
    if (b >> 1) & p:
        flips |= ray & -b

    ray = rays[7]
    b = 1 << (ray & inv).bit_length()
    if (b >> 1) & p:
        flips |= ray & -b

    return flips


def _neighbors(b):
    horizontal = ((b & NOT_A) >> 1) | ((b & NOT_H) << 1)
    expanded = b | horizontal
    return (horizontal | (expanded << 8) | (expanded >> 8)) & FULL


def _danger_masks(occupied):
    xmask = 0
    cmask = 0
    for corner, x, c in CORNER_INFO:
        if not (occupied & corner):
            xmask |= x
            cmask |= c
    return xmask, cmask


def _terminal_diff(diff):
    if diff > 0:
        return WIN + 100 * diff
    if diff < 0:
        return -WIN + 100 * diff
    return 0


def _terminal(p, o):
    return _terminal_diff(p.bit_count() - o.bit_count())


def _stable_edge_difference(p, o, corner_diff):
    pa = (((p & FILE_A) * PACK_FILE) >> 56) & 255
    oa = (((o & FILE_A) * PACK_FILE) >> 56) & 255
    ph = ((((p >> 7) & FILE_A) * PACK_FILE) >> 56) & 255
    oh = ((((o >> 7) & FILE_A) * PACK_FILE) >> 56) & 255

    result = 0
    for pe, oe in (
        (p & 255, o & 255),
        (p >> 56, o >> 56),
        (pa, oa),
        (ph, oh),
    ):
        if (pe | oe) == 255:
            # Every disc on a completely occupied edge is stable.
            result += pe.bit_count() - oe.bit_count()
        else:
            result += EDGE_STABLE[pe] - EDGE_STABLE[oe]

    # Corners were counted on two edges; evaluate them separately.
    return result - 2 * corner_diff


def _evaluate(p, o, moves, opponent_moves=None):
    occupied = p | o
    empty = FULL ^ occupied
    e = empty.bit_count()

    if opponent_moves is None:
        opponent_moves = _legal(o, p)

    xmask, cmask = _danger_masks(occupied)
    mp = moves.bit_count()
    mo = opponent_moves.bit_count()
    sp = (moves & ~xmask).bit_count()
    so = (opponent_moves & ~xmask).bit_count()

    if e > 20:
        basic_mob, safe_mob = 8, 24
        frontier_weight, potential_weight = 12, 5
    elif e > 10:
        basic_mob, safe_mob = 8, 20
        frontier_weight, potential_weight = 8, 3
    else:
        basic_mob, safe_mob = 6, 14
        frontier_weight, potential_weight = 3, 2

    score = basic_mob * (mp - mo) + safe_mob * (sp - so)
    score += 120 * (sp - so) // (sp + so + 2)

    corner_diff = (p & CORNERS).bit_count() - (o & CORNERS).bit_count()
    score += 900 * corner_diff
    score += 350 * (
        (moves & CORNERS).bit_count()
        - (opponent_moves & CORNERS).bit_count()
    )

    if occupied & CORNERS:
        stable_weight = 65 if e > 32 else (80 if e > 12 else 100)
        score += stable_weight * _stable_edge_difference(p, o, corner_diff)

    frontier = _neighbors(empty)
    score += frontier_weight * (
        (o & frontier).bit_count() - (p & frontier).bit_count()
    )
    score += potential_weight * (
        (_neighbors(o) & empty).bit_count()
        - (_neighbors(p) & empty).bit_count()
    )

    score += 18 * ((p & EDGE_SAFE).bit_count() - (o & EDGE_SAFE).bit_count())
    score -= 6 * (
        (p & SECOND_RING).bit_count() - (o & SECOND_RING).bit_count()
    )
    score += 10 * ((p & SWEET).bit_count() - (o & SWEET).bit_count())
    score += 8 * ((p & ALL_C).bit_count() - (o & ALL_C).bit_count())
    score += 4 * ((p & ALL_X).bit_count() - (o & ALL_X).bit_count())

    if e > 10:
        x_weight, c_weight = 240, 100
    elif e > 4:
        x_weight, c_weight = 150, 65
    else:
        x_weight, c_weight = 60, 25

    score -= x_weight * ((p & xmask).bit_count() - (o & xmask).bit_count())
    score -= c_weight * ((p & cmask).bit_count() - (o & cmask).bit_count())

    if e > 44:
        disc_weight = -2
    elif e > 28:
        disc_weight = -1
    elif e > 18:
        disc_weight = 2
    elif e > 12:
        disc_weight = 6
    elif e > 7:
        disc_weight = 14
    else:
        disc_weight = 30
    score += disc_weight * (p.bit_count() - o.bit_count())

    if e < 20:
        score += 6 if e & 1 else -6

    return score


def _empty_regions(empty):
    """Map empty squares to their root four-connected empty regions."""
    regions = [0] * 64
    remaining = empty
    while remaining:
        region = remaining & -remaining
        while True:
            adjacent = (
                ((region & NOT_A) >> 1)
                | ((region & NOT_H) << 1)
                | (region << 8)
                | (region >> 8)
            )
            expanded = region | (adjacent & remaining)
            if expanded == region:
                break
            region = expanded

        bits = region
        while bits:
            bit = bits & -bits
            bits ^= bit
            regions[bit.bit_length() - 1] = region
        remaining &= ~region

    return regions


class _Timeout(Exception):
    pass


class _Search:
    def __init__(self, deadline, p, o, table):
        self.deadline = deadline
        self.nodes = 0
        self.tt = table
        self.history = [0] * 64
        self.killers = [[0, 0] for _ in range(130)]
        self.root_empty = 64 - (p | o).bit_count()
        self.exact = False
        self.regions = (
            _empty_regions(FULL ^ (p | o))
            if self.root_empty <= 16
            else None
        )

    def _ordered(self, p, o, moves, depth, ply, ttmove):
        # Yield the cached move before doing expensive ordering work.
        if ttmove and (moves & ttmove):
            moves ^= ttmove
            yield ttmove, ttmove.bit_length() - 1, None, None

        if not moves:
            return

        if not (moves & (moves - 1)):
            yield moves, moves.bit_length() - 1, None, None
            return

        occupied = p | o
        empty = FULL ^ occupied
        xmask, cmask = _danger_masks(occupied)
        killer1, killer2 = self.killers[ply]
        analyze_children = depth >= (5 if self.exact else 3)
        ranked = []

        while moves:
            move = moves & -moves
            moves ^= move
            sq = move.bit_length() - 1
            score = 8 * ORDER_WEIGHT[sq]
            score += self.history[sq] // (4 if self.exact else 1)

            if move & CORNERS:
                score += 100000
            if move == killer1:
                score += 20000
            elif move == killer2:
                score += 10000

            if move & xmask:
                score -= 3000
            elif move & cmask:
                score -= 1000

            if self.regions is not None:
                if (self.regions[sq] & empty).bit_count() & 1:
                    score += 180

            flips = None
            child_moves = None
            if analyze_children:
                flips = _flips(p, o, sq)
                child_moves = _legal(o ^ flips, p | move | flips)
                score -= (30 if self.exact else 60) * child_moves.bit_count()
                score -= 10000 * (child_moves & CORNERS).bit_count()
                if not child_moves:
                    score += 2500
                if self.root_empty > 20:
                    score -= 3 * flips.bit_count()
                else:
                    score += 2 * flips.bit_count()

            ranked.append((score, move, sq, flips, child_moves))

        ranked.sort(reverse=True)
        for _, move, sq, flips, child_moves in ranked:
            yield move, sq, flips, child_moves

    def search(self, p, o, depth, alpha, beta, ply=0, moves=None):
        self.nodes += 1
        if (self.nodes & 63) == 0:
            if time.perf_counter() >= self.deadline:
                raise _Timeout

        if depth <= 0:
            if self.exact or (p | o) == FULL:
                return _terminal(p, o)
            if moves is None:
                moves = _legal(p, o)
            if moves:
                return _evaluate(p, o, moves)
            other_moves = _legal(o, p)
            if not other_moves:
                return _terminal(p, o)
            return -_evaluate(o, p, other_moves, 0)

        # Exact one-empty-square solver, including either kind of pass.
        if self.exact and depth == 1:
            empty = FULL ^ (p | o)
            sq = empty.bit_length() - 1
            diff = p.bit_count() - o.bit_count()
            flips = _flips(p, o, sq)
            if flips:
                diff += 1 + 2 * flips.bit_count()
            else:
                flips = _flips(o, p, sq)
                if flips:
                    diff -= 1 + 2 * flips.bit_count()
            return _terminal_diff(diff)

        key = (p, o)
        entry = self.tt.get(key)
        ttmove = 0
        if entry is not None:
            old_depth, old_score, bound, ttmove = entry
            if old_depth >= depth:
                if bound == 0:
                    return old_score
                if bound == 1 and old_score >= beta:
                    return old_score
                if bound == 2 and old_score <= alpha:
                    return old_score

        if moves is None:
            moves = _legal(p, o)

        original_alpha = alpha

        if not moves:
            other_moves = _legal(o, p)
            if not other_moves:
                return _terminal(p, o)
            value = -self.search(
                o, p, depth, -beta, -alpha, ply + 1, other_moves
            )
            bound = 2 if value <= original_alpha else (1 if value >= beta else 0)
            self.tt[key] = (depth, value, bound, 0)
            return value

        best_value = -INF
        best_move = 0

        for number, (move, sq, flips, child_moves) in enumerate(
            self._ordered(p, o, moves, depth, ply, ttmove)
        ):
            if flips is None:
                flips = _flips(p, o, sq)
            child_p = o ^ flips
            child_o = p | move | flips

            if number == 0 or depth == 1:
                value = -self.search(
                    child_p, child_o, depth - 1,
                    -beta, -alpha, ply + 1, child_moves
                )
            else:
                # Conservative late-move reduction, never in the endgame
                # or on corner-related / low-mobility tactical moves.
                reduce = (
                    not self.exact
                    and self.root_empty > 18
                    and depth >= 4
                    and number >= 4
                    and not (move & CORNER_ZONE)
                    and move not in self.killers[ply]
                    and child_moves is not None
                    and not (child_moves & CORNERS)
                    and child_moves.bit_count() > 3
                )

                if reduce:
                    value = -self.search(
                        child_p, child_o, depth - 2,
                        -alpha - 1, -alpha, ply + 1, child_moves
                    )
                else:
                    value = alpha + 1

                if value > alpha:
                    value = -self.search(
                        child_p, child_o, depth - 1,
                        -alpha - 1, -alpha, ply + 1, child_moves
                    )
                    if alpha < value < beta:
                        value = -self.search(
                            child_p, child_o, depth - 1,
                            -beta, -alpha, ply + 1, child_moves
                        )

            if value > best_value:
                best_value = value
                best_move = move

            if value > alpha:
                alpha = value

            if alpha >= beta:
                self.history[sq] = min(
                    32768, self.history[sq] + depth * depth
                )
                if self.killers[ply][0] != move:
                    self.killers[ply][1] = self.killers[ply][0]
                    self.killers[ply][0] = move
                break

        bound = (
            2 if best_value <= original_alpha
            else (1 if best_value >= beta else 0)
        )
        self.tt[key] = (depth, best_value, bound, best_move)
        return best_value


def _move_string(move):
    sq = move.bit_length() - 1
    return chr(ord("a") + (sq & 7)) + str((sq >> 3) + 1)


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    deadline = time.perf_counter() + 0.90

    p = 0
    o = 0
    for i, value in enumerate(you.flat):
        if value:
            p |= 1 << i
    for i, value in enumerate(opponent.flat):
        if value:
            o |= 1 << i

    moves = _legal(p, o)
    if not moves:
        return "pass"

    if not (moves & (moves - 1)):
        return _move_string(moves)

    # Establish a legal answer before doing any search.
    corner_moves = moves & CORNERS
    best_move = (
        corner_moves & -corner_moves
        if corner_moves
        else moves & -moves
    )

    if len(_TT) > 80000:
        _TT.clear()

    engine = _Search(deadline, p, o, _TT)
    empties = engine.root_empty
    previous_score = None
    start_depth = 1

    cached = _TT.get((p, o))
    if cached is not None and cached[3] and (cached[3] & moves):
        best_move = cached[3]
        if cached[2] == 0:
            previous_score = cached[1]
            if cached[0] >= empties:
                return _move_string(best_move)
            start_depth = cached[0] + 1

    if empties <= 10:
        depths = sorted(set(d for d in (1, 2, 4, empties) if d <= empties))
    elif empties <= 12:
        depths = [1, 2, 3, 4, 6, empties]
    elif empties <= 14:
        depths = [1, 2, 3, 4, 5, 6, 7, 8, empties]
    else:
        depths = range(1, empties + 1)

    try:
        for depth in depths:
            if depth < start_depth:
                continue
            if time.perf_counter() >= deadline:
                break

            engine.exact = depth == empties

            if (
                previous_score is not None
                and depth >= 4
                and not engine.exact
                and abs(previous_score) < WIN
            ):
                low = previous_score - 220
                high = previous_score + 220
                value = engine.search(p, o, depth, low, high, 0, moves)
                if value <= low or value >= high:
                    value = engine.search(p, o, depth, -INF, INF, 0, moves)
            else:
                value = engine.search(p, o, depth, -INF, INF, 0, moves)

            result = _TT.get((p, o))
            if result is not None and result[3] and (result[3] & moves):
                best_move = result[3]
            previous_score = value

            if engine.exact:
                break

    except _Timeout:
        pass

    # best_move always comes from the original legal move set.
    return _move_string(best_move)
