
import time
import numpy as np

FULL = (1 << 64) - 1
FILE_A = 0x0101010101010101
NOT_A = 0xFEFEFEFEFEFEFEFE
NOT_H = 0x7F7F7F7F7F7F7F7F
INNER_FILES = 0x7E7E7E7E7E7E7E7E
CORNERS = 0x8100000000000081
PACK = 0x0102040810204080
INF = 1000000

# Position values exclude corner and corner-adjacency bonuses,
# which are evaluated dynamically.
BASE = (
     0,  0, 12,  5,  5, 12,  0,  0,
     0,  0, -8, -6, -6, -8,  0,  0,
    12, -8, 10,  3,  3, 10, -8, 12,
     5, -6,  3,  3,  3,  3, -6,  5,
     5, -6,  3,  3,  3,  3, -6,  5,
    12, -8, 10,  3,  3, 10, -8, 12,
     0,  0, -8, -6, -6, -8,  0,  0,
     0,  0, 12,  5,  5, 12,  0,  0,
)

POSITION_MASKS = tuple(
    (weight, sum(1 << i for i, value in enumerate(BASE)
                 if value == weight))
    for weight in sorted(set(BASE)) if weight
)

CORNER_NEIGHBORS = (
    (1 << 0,  1 << 9,  (1 << 1) | (1 << 8)),
    (1 << 7,  1 << 14, (1 << 6) | (1 << 15)),
    (1 << 56, 1 << 49, (1 << 48) | (1 << 57)),
    (1 << 63, 1 << 54, (1 << 55) | (1 << 62)),
)

QUADRANTS = tuple(
    sum(1 << (r * 8 + c)
        for r in range(r0, r0 + 4)
        for c in range(c0, c0 + 4))
    for r0, c0 in ((0, 0), (0, 4), (4, 0), (4, 4))
)

# Rays ordered by increasing/decreasing bit index.
POS_RAYS = []
NEG_RAYS = []
for square in range(64):
    row, col = divmod(square, 8)
    positive, negative = [], []
    for dr, dc in (
        (0, 1), (1, 0), (1, 1), (1, -1),
        (0, -1), (-1, 0), (-1, -1), (-1, 1),
    ):
        r, c = row + dr, col + dc
        ray = 0
        while 0 <= r < 8 and 0 <= c < 8:
            ray |= 1 << (r * 8 + c)
            r += dr
            c += dc
        if ray:
            if dr * 8 + dc > 0:
                positive.append(ray)
            else:
                negative.append(ray)
    POS_RAYS.append(tuple(positive))
    NEG_RAYS.append(tuple(negative))

EDGE_STABLE = []
for value in range(256):
    left = 0
    while left < 8 and value & (1 << left):
        left += 1
    if left == 8:
        EDGE_STABLE.append(8)
    else:
        right = 0
        while right < 8 and value & (1 << (7 - right)):
            right += 1
        EDGE_STABLE.append(left + right)

# Entries: (search depth, bound type, score, best move).
# Bound types: 0 exact, 1 lower bound, 2 upper bound.
_TABLE = {}


def _moves(p, o):
    """Generate all legal moves using parallel directional propagation."""
    m = o & INNER_FILES

    t = m & (p << 1)
    t |= m & (t << 1)
    d = m & (m << 1)
    t |= d & (t << 2)
    t |= d & (t << 2)
    result = t << 1

    t = m & (p >> 1)
    t |= m & (t >> 1)
    d >>= 1
    t |= d & (t >> 2)
    t |= d & (t >> 2)
    result |= t >> 1

    t = m & (p << 7)
    t |= m & (t << 7)
    d = m & (m << 7)
    t |= d & (t << 14)
    t |= d & (t << 14)
    result |= t << 7

    t = m & (p >> 7)
    t |= m & (t >> 7)
    d >>= 7
    t |= d & (t >> 14)
    t |= d & (t >> 14)
    result |= t >> 7

    t = m & (p << 9)
    t |= m & (t << 9)
    d = m & (m << 9)
    t |= d & (t << 18)
    t |= d & (t << 18)
    result |= t << 9

    t = m & (p >> 9)
    t |= m & (t >> 9)
    d >>= 9
    t |= d & (t >> 18)
    t |= d & (t >> 18)
    result |= t >> 9

    t = o & (p << 8)
    t |= o & (t << 8)
    d = o & (o << 8)
    t |= d & (t << 16)
    t |= d & (t << 16)
    result |= t << 8

    t = o & (p >> 8)
    t |= o & (t >> 8)
    d >>= 8
    t |= d & (t >> 16)
    t |= d & (t >> 16)
    result |= t >> 8

    return result & (FULL ^ (p | o))


def _flips(square, p, o):
    """Find the nearest non-opponent square on every ray."""
    non_opponent = ~o
    result = 0

    for ray in POS_RAYS[square]:
        blockers = ray & non_opponent
        anchor = (blockers & -blockers) & p
        if anchor:
            result |= (anchor - 1) & ray

    for ray in NEG_RAYS[square]:
        above_anchor = 1 << (ray & non_opponent).bit_length()
        if (above_anchor >> 1) & p:
            result |= (-above_anchor) & ray

    return result


def _adjacent(bits):
    horizontal = ((bits << 1) & NOT_A) | ((bits >> 1) & NOT_H)
    band = bits | horizontal
    return (horizontal | (band << 8) | (band >> 8)) & FULL


def _poison_masks(occupied):
    xs = cs = 0
    for corner, x_square, c_squares in CORNER_NEIGHBORS:
        if not occupied & corner:
            xs |= x_square
            cs |= c_squares
    return xs, cs


def _stable_edge_count(p):
    return (
        EDGE_STABLE[p & 255]
        + EDGE_STABLE[(p >> 56) & 255]
        + EDGE_STABLE[(((p & FILE_A) * PACK) >> 56) & 255]
        + EDGE_STABLE[(((((p >> 7) & FILE_A) * PACK) >> 56) & 255)]
    )


def _terminal(difference):
    if difference > 0:
        return 30000 + 100 * difference
    if difference < 0:
        return -30000 + 100 * difference
    return 0


def _evaluate(p, o, legal, empties):
    opponent_legal = _moves(o, p)
    my_mobility = legal.bit_count()
    their_mobility = opponent_legal.bit_count()
    mobility_difference = my_mobility - their_mobility

    mobility_weight = 34 if empties > 20 else 20 + empties // 2
    score = mobility_weight * mobility_difference
    score += int(
        120 * mobility_difference /
        (my_mobility + their_mobility + 4)
    )
    score += 140 * (
        (legal & CORNERS).bit_count()
        - (opponent_legal & CORNERS).bit_count()
    )

    occupied = p | o
    empty = FULL ^ occupied
    frontier = _adjacent(empty)
    frontier_difference = (
        (p & frontier).bit_count() - (o & frontier).bit_count()
    )
    score -= (12 if empties > 20 else 7) * frontier_difference

    potential_difference = (
        (_adjacent(o) & empty).bit_count()
        - (_adjacent(p) & empty).bit_count()
    )
    score += (6 if empties > 20 else 3) * potential_difference

    my_corners = (p & CORNERS).bit_count()
    their_corners = (o & CORNERS).bit_count()
    corner_difference = my_corners - their_corners
    score += 750 * corner_difference

    stable_difference = 0
    if my_corners:
        stable_difference += _stable_edge_count(p)
    if their_corners:
        stable_difference -= _stable_edge_count(o)
    # Each corner occurs in two edge counts; it is scored separately.
    score += 90 * (stable_difference - 2 * corner_difference)

    xs, cs = _poison_masks(occupied)
    score -= (210 if empties > 14 else 140) * (
        (p & xs).bit_count() - (o & xs).bit_count()
    )
    score -= 75 * ((p & cs).bit_count() - (o & cs).bit_count())

    for weight, mask in POSITION_MASKS:
        score += weight * (
            (p & mask).bit_count() - (o & mask).bit_count()
        )

    if empties > 40:
        disc_weight = -2
    elif empties > 24:
        disc_weight = -1
    elif empties > 12:
        disc_weight = 4
    else:
        disc_weight = 12
    score += disc_weight * (p.bit_count() - o.bit_count())

    return score


class _Timeout(Exception):
    pass


class _Search:
    __slots__ = (
        "deadline", "table", "nodes", "killers", "history", "root_best"
    )

    def __init__(self, deadline, table, fallback):
        self.deadline = deadline
        self.table = table
        self.nodes = 0
        self.killers = [0] * 130
        self.history = [0] * 64
        self.root_best = fallback

    def ordered(self, p, o, legal, tt_move, depth, empties, ply):
        # Try the hash move without preparing the remaining children.
        if tt_move & legal:
            square = tt_move.bit_length() - 1
            yield tt_move, _flips(square, p, o), -1
            legal ^= tt_move

        if not legal:
            return

        xs, cs = _poison_masks(p | o)
        odd_regions = 0
        if empties <= 16:
            empty = FULL ^ (p | o)
            for quadrant in QUADRANTS:
                if (empty & quadrant).bit_count() & 1:
                    odd_regions |= quadrant

        killer = self.killers[ply]
        history = self.history
        ranked = []
        deep_ordering = depth >= 3

        while legal:
            move = legal & -legal
            legal ^= move
            square = move.bit_length() - 1

            priority = 3 * BASE[square]
            priority += min(128, history[square] >> 2)
            if move == killer:
                priority += 90
            if move & CORNERS:
                priority += 10000
            if move & xs:
                priority -= 230
            if move & cs:
                priority -= 85
            if move & odd_regions:
                priority += 95

            if deep_ordering:
                flipped = _flips(square, p, o)
                next_p = o ^ flipped
                next_o = p | flipped | move
                next_legal = _moves(next_p, next_o)

                priority -= 32 * next_legal.bit_count()
                priority -= 450 * (next_legal & CORNERS).bit_count()
                if not next_legal:
                    priority += 180
                priority += (
                    2 if empties <= 16 else -2
                ) * flipped.bit_count()
                ranked.append((priority, move, flipped, next_legal))
            else:
                ranked.append((priority, move, 0, -1))

        ranked.sort(reverse=True)
        for _, move, flipped, next_legal in ranked:
            if not deep_ordering:
                flipped = _flips(move.bit_length() - 1, p, o)
            yield move, flipped, next_legal

    def search(self, p, o, depth, alpha, beta, empties,
               legal=-1, ply=0):
        self.nodes += 1
        if not (self.nodes & 127):
            if time.perf_counter() >= self.deadline:
                raise _Timeout

        if empties == 0:
            return _terminal(2 * p.bit_count() - 64)

        # Exact one-empty resolution, including either player's pass.
        if empties == 1:
            empty = FULL ^ (p | o)
            square = empty.bit_length() - 1
            difference = p.bit_count() - o.bit_count()
            flipped = _flips(square, p, o)
            if flipped:
                difference += 1 + 2 * flipped.bit_count()
            else:
                flipped = _flips(square, o, p)
                if flipped:
                    difference -= 1 + 2 * flipped.bit_count()
            return _terminal(difference)

        key = (p, o)
        entry = self.table.get(key)
        tt_move = 0
        if entry is not None:
            old_depth, flag, value, tt_move = entry
            if old_depth >= depth:
                if (flag == 0
                        or (flag == 1 and value >= beta)
                        or (flag == 2 and value <= alpha)):
                    if ply == 0 and tt_move:
                        self.root_best = tt_move
                    return value

        original_alpha = alpha
        if legal == -1:
            legal = _moves(p, o)

        if not legal:
            other_legal = _moves(o, p)
            if not other_legal:
                value = _terminal(p.bit_count() - o.bit_count())
                self.table[key] = (64, 0, value, 0)
                return value

            value = -self.search(
                o, p, depth, -beta, -alpha, empties,
                other_legal, ply + 1
            )
            flag = 1 if value >= beta else (
                2 if value <= original_alpha else 0
            )
            self.table[key] = (depth, flag, value, 0)
            return value

        if depth <= 0:
            value = _evaluate(p, o, legal, empties)
            if entry is None or entry[0] <= 0:
                self.table[key] = (0, 0, value, 0)
            return value

        best_value = -INF
        best_move = 0
        move_count = legal.bit_count()
        principal_node = beta - alpha > 1
        search = self.search

        for index, (move, flipped, next_legal) in enumerate(
            self.ordered(p, o, legal, tt_move, depth, empties, ply)
        ):
            next_p = o ^ flipped
            next_o = p | flipped | move
            next_depth = depth - 1

            if index == 0:
                value = -search(
                    next_p, next_o, next_depth, -beta, -alpha,
                    empties - 1, next_legal, ply + 1
                )
            else:
                reduction = 0
                if (
                    depth >= 4
                    and depth < empties
                    and empties > 18
                    and ply > 0
                    and index >= 3
                    and move_count >= 5
                    and not (move & CORNERS)
                    and next_legal != -1
                    and next_legal.bit_count() >= 3
                    and abs(alpha) < 29000
                ):
                    reduction = 1
                    if depth >= 7 and index >= 7 and not principal_node:
                        reduction = 2

                value = -search(
                    next_p, next_o, next_depth - reduction,
                    -alpha - 1, -alpha,
                    empties - 1, next_legal, ply + 1
                )

                if reduction and value > alpha:
                    value = -search(
                        next_p, next_o, next_depth,
                        -alpha - 1, -alpha,
                        empties - 1, next_legal, ply + 1
                    )

                if alpha < value < beta:
                    value = -search(
                        next_p, next_o, next_depth, -beta, -alpha,
                        empties - 1, next_legal, ply + 1
                    )

            if value > best_value:
                best_value = value
                best_move = move
            if value > alpha:
                alpha = value

            if alpha >= beta:
                self.killers[ply] = move
                square = move.bit_length() - 1
                self.history[square] = min(
                    1024, self.history[square] + depth * depth
                )
                break

        flag = 1 if best_value >= beta else (
            2 if best_value <= original_alpha else 0
        )
        self.table[key] = (depth, flag, best_value, best_move)

        if ply == 0:
            self.root_best = best_move
        return best_value


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    global _TABLE

    started = time.perf_counter()
    deadline = started + 0.90

    p = 0
    o = 0
    for square, (mine, theirs) in enumerate(
        zip(you.flat, opponent.flat)
    ):
        if mine:
            p |= 1 << square
        elif theirs:
            o |= 1 << square

    legal = _moves(p, o)
    if not legal:
        return "pass"

    best_move = legal & -legal
    if legal == best_move:
        square = best_move.bit_length() - 1
        return chr(97 + square % 8) + str(square // 8 + 1)

    if len(_TABLE) > 120000:
        _TABLE = {}

    empties = 64 - (p | o).bit_count()
    context = _Search(deadline, _TABLE, best_move)

    # Establish a sensible fallback independently of search completion.
    best_move = next(
        context.ordered(p, o, legal, 0, 1, empties, 0)
    )[0]
    context.root_best = best_move

    if empties <= 12:
        depths = sorted({d for d in (1, 2, 4, empties)
                         if d <= empties})
    elif empties <= 16:
        depths = sorted({d for d in (1, 2, 4, 6, 8, empties)
                         if d <= empties})
    else:
        depths = range(1, empties + 1)

    previous_score = 0

    try:
        for depth in depths:
            if time.perf_counter() >= deadline:
                break

            if depth >= 4 and depth < empties:
                width = 200
                alpha = max(-INF, previous_score - width)
                beta = min(INF, previous_score + width)
            else:
                width = INF
                alpha, beta = -INF, INF

            while True:
                score = context.search(
                    p, o, depth, alpha, beta, empties, legal, 0
                )

                if score <= alpha and alpha > -INF:
                    width *= 2
                    alpha = max(-INF, score - width)
                elif score >= beta and beta < INF:
                    width *= 2
                    beta = min(INF, score + width)
                else:
                    candidate = context.root_best
                    if candidate and candidate & legal:
                        best_move = candidate
                    previous_score = score
                    break

                if time.perf_counter() >= deadline:
                    raise _Timeout

            if depth >= empties or abs(previous_score) >= 30000:
                break

    except _Timeout:
        pass

    # Final defensive legality check.
    if not best_move or not (best_move & legal):
        best_move = legal & -legal
    else:
        best_move &= -best_move

    square = best_move.bit_length() - 1
    return chr(97 + square % 8) + str(square // 8 + 1)
