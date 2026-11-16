
import time
import numpy as np

# ---------- Bitboard constants / precomputation ----------

FULL = (1 << 64) - 1
INF = 10**9
WIN = 10**7

DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)]

# Strong classical Othello square table.
POS_WEIGHTS = (
    120, -25,  20,   5,   5,  20, -25, 120,
    -25, -55,  -5,  -5,  -5,  -5, -55, -25,
     20,  -5,  15,   3,   3,  15,  -5,  20,
      5,  -5,   3,   3,   3,   3,  -5,   5,
      5,  -5,   3,   3,   3,   3,  -5,   5,
     20,  -5,  15,   3,   3,  15,  -5,  20,
    -25, -55,  -5,  -5,  -5,  -5, -55, -25,
    120, -25,  20,   5,   5,  20, -25, 120,
)

# Move-ordering table: even more corner-focused.
ORDER_WEIGHTS = (
    10000, -2000,  600,  120,  120,  600, -2000, 10000,
    -2000, -3000, -500, -300, -300, -500, -3000, -2000,
      600,  -500,  250,   80,   80,  250,  -500,   600,
      120,  -300,   80,   40,   40,   80,  -300,   120,
      120,  -300,   80,   40,   40,   80,  -300,   120,
      600,  -500,  250,   80,   80,  250,  -500,   600,
    -2000, -3000, -500, -300, -300, -500, -3000, -2000,
    10000, -2000,  600,  120,  120,  600, -2000, 10000,
)

CORNERS = (1 << 0) | (1 << 7) | (1 << 56) | (1 << 63)

CORNER_ADJ = (
    (0,  (1, 8, 9)),
    (7,  (6, 14, 15)),
    (56, (48, 49, 57)),
    (63, (54, 55, 62)),
)

# Masks for wrap-safe shifts.
NOT_A = 0
NOT_H = 0
for r in range(8):
    for c in range(8):
        b = 1 << (r * 8 + c)
        if c != 0:
            NOT_A |= b
        if c != 7:
            NOT_H |= b

# Rays from every square in each of the 8 directions.
RAYS = []
for sq in range(64):
    r, c = divmod(sq, 8)
    sq_rays = []
    for dr, dc in DIRS:
        ray = []
        rr, cc = r + dr, c + dc
        while 0 <= rr < 8 and 0 <= cc < 8:
            ray.append(1 << (rr * 8 + cc))
            rr += dr
            cc += dc
        sq_rays.append(tuple(ray))
    RAYS.append(tuple(sq_rays))

DEADLINE = 0.0
NODES = 0
TT = {}


class SearchTimeout(Exception):
    pass


# ---------- Basic bitboard helpers ----------

def _neighbors(bb: int) -> int:
    """All squares adjacent to any bit in bb."""
    return (
        ((bb & NOT_A) >> 1) |
        ((bb & NOT_H) << 1) |
        (bb >> 8) |
        ((bb << 8) & FULL) |
        ((bb & NOT_A) >> 9) |
        ((bb & NOT_H) >> 7) |
        (((bb & NOT_A) << 7) & FULL) |
        (((bb & NOT_H) << 9) & FULL)
    ) & FULL


def _flips_for_move(sq: int, me: int, opp: int) -> int:
    flips = 0
    for ray in RAYS[sq]:
        line = 0
        for bit in ray:
            if opp & bit:
                line |= bit
            elif me & bit:
                flips |= line
                break
            else:
                break
    return flips


def _gen_moves(me: int, opp: int):
    """Return list of (square, flips_bitboard)."""
    empty = (~(me | opp)) & FULL
    candidates = empty & _neighbors(opp)
    moves = []
    while candidates:
        bit = candidates & -candidates
        sq = bit.bit_length() - 1
        flips = _flips_for_move(sq, me, opp)
        if flips:
            moves.append((sq, flips))
        candidates ^= bit
    return moves


def _weighted_sum(bb: int) -> int:
    s = 0
    while bb:
        bit = bb & -bb
        s += POS_WEIGHTS[bit.bit_length() - 1]
        bb ^= bit
    return s


def _stable_corner_edge_bonus(me: int, opp: int) -> int:
    """Small bonus for owning continuous edge discs extending from corners."""
    bonus = 0

    def count_line(start, step, owner):
        cnt = 0
        sq = start
        while 0 <= sq < 64 and (owner & (1 << sq)):
            cnt += 1
            sq += step
        return cnt

    # Top-left
    if me & 1:
        bonus += 25 * (count_line(0, 1, me) + count_line(0, 8, me))
    elif opp & 1:
        bonus -= 25 * (count_line(0, 1, opp) + count_line(0, 8, opp))

    # Top-right
    if me & (1 << 7):
        bonus += 25 * (count_line(7, -1, me) + count_line(7, 8, me))
    elif opp & (1 << 7):
        bonus -= 25 * (count_line(7, -1, opp) + count_line(7, 8, opp))

    # Bottom-left
    if me & (1 << 56):
        bonus += 25 * (count_line(56, 1, me) + count_line(56, -8, me))
    elif opp & (1 << 56):
        bonus -= 25 * (count_line(56, 1, opp) + count_line(56, -8, opp))

    # Bottom-right
    if me & (1 << 63):
        bonus += 25 * (count_line(63, -1, me) + count_line(63, -8, me))
    elif opp & (1 << 63):
        bonus -= 25 * (count_line(63, -1, opp) + count_line(63, -8, opp))

    return bonus


def _evaluate(me: int, opp: int) -> int:
    my_discs = me.bit_count()
    op_discs = opp.bit_count()
    occupied = my_discs + op_discs
    empties = 64 - occupied
    empty = (~(me | opp)) & FULL

    my_moves = len(_gen_moves(me, opp))
    op_moves = len(_gen_moves(opp, me))

    mobility = my_moves - op_moves
    if my_moves + op_moves:
        mobility_scaled = 100 * mobility // (my_moves + op_moves)
    else:
        mobility_scaled = 0

    corner_diff = (me & CORNERS).bit_count() - (opp & CORNERS).bit_count()

    positional = _weighted_sum(me) - _weighted_sum(opp)

    adj_empty = _neighbors(empty)
    frontier_diff = (me & adj_empty).bit_count() - (opp & adj_empty).bit_count()

    # Potential mobility: empty squares near opponent discs.
    pot_my = (empty & _neighbors(opp)).bit_count()
    pot_op = (empty & _neighbors(me)).bit_count()
    potential = pot_my - pot_op

    disc_diff = my_discs - op_discs

    # Penalize occupying X/C squares while the corresponding corner is empty.
    corner_adj_penalty = 0
    for corner, adj in CORNER_ADJ:
        cb = 1 << corner
        if not ((me | opp) & cb):
            for a in adj:
                ab = 1 << a
                if me & ab:
                    corner_adj_penalty -= 70
                elif opp & ab:
                    corner_adj_penalty += 70

    if empties > 44:
        # Opening: mobility and not giving corners matter more than disc count.
        score = (
            85 * mobility_scaled +
            900 * corner_diff +
            8 * positional -
            28 * frontier_diff +
            12 * potential -
            6 * disc_diff +
            corner_adj_penalty
        )
    elif empties > 16:
        # Midgame.
        score = (
            70 * mobility_scaled +
            1050 * corner_diff +
            10 * positional -
            22 * frontier_diff +
            10 * potential +
            2 * disc_diff +
            corner_adj_penalty
        )
    else:
        # Endgame: disc count and exact-ish stability become increasingly important.
        score = (
            45 * mobility_scaled +
            1200 * corner_diff +
            6 * positional -
            10 * frontier_diff +
            4 * potential +
            (18 + (16 - empties) * 4) * disc_diff +
            corner_adj_penalty
        )

    score += _stable_corner_edge_bonus(me, opp)
    return score


def _terminal_score(me: int, opp: int) -> int:
    diff = me.bit_count() - opp.bit_count()
    if diff > 0:
        return WIN + diff * 10000
    if diff < 0:
        return -WIN + diff * 10000
    return 0


def _move_order_score(sq: int, flips: int, me: int, opp: int, tt_move):
    score = ORDER_WEIGHTS[sq] + 5 * flips.bit_count()
    if tt_move is not None and sq == tt_move:
        score += 1000000

    occupied = me | opp
    for corner, adj in CORNER_ADJ:
        if sq in adj:
            cb = 1 << corner
            if not (occupied & cb):
                score -= 5500
            elif me & cb:
                score += 700
            elif opp & cb:
                score -= 300
    return score


def _ordered_moves(moves, me: int, opp: int, tt_move=None):
    return sorted(
        moves,
        key=lambda mf: _move_order_score(mf[0], mf[1], me, opp, tt_move),
        reverse=True
    )


# ---------- Alpha-beta search ----------

def _check_time():
    global NODES
    NODES += 1
    if (NODES & 1023) == 0 and time.perf_counter() > DEADLINE:
        raise SearchTimeout()


def _negamax(me: int, opp: int, depth: int, alpha: int, beta: int) -> int:
    _check_time()

    key = (me, opp, depth)
    entry = TT.get(key)
    if entry is not None:
        flag, val, _best = entry
        if flag == 0:
            return val
        if flag == 1:
            alpha = max(alpha, val)
        elif flag == 2:
            beta = min(beta, val)
        if alpha >= beta:
            return val

    alpha_orig = alpha
    beta_orig = beta

    moves = _gen_moves(me, opp)

    if not moves:
        opp_moves = _gen_moves(opp, me)
        if not opp_moves:
            return _terminal_score(me, opp)
        # Pass move. Do not reduce depth because no disc was placed.
        return -_negamax(opp, me, depth, -beta, -alpha)

    if depth <= 0:
        return _evaluate(me, opp)

    tt_move = entry[2] if entry is not None else None
    moves = _ordered_moves(moves, me, opp, tt_move)

    best_val = -INF
    best_sq = moves[0][0]

    for sq, flips in moves:
        bit = 1 << sq
        new_me = me | bit | flips
        new_opp = opp & ~flips

        val = -_negamax(new_opp, new_me, depth - 1, -beta, -alpha)

        if val > best_val:
            best_val = val
            best_sq = sq

        if val > alpha:
            alpha = val

        if alpha >= beta:
            break

    # TT flags: 0 exact, 1 lower bound, 2 upper bound.
    if best_val <= alpha_orig:
        flag = 2
    elif best_val >= beta_orig:
        flag = 1
    else:
        flag = 0

    if len(TT) < 250000:
        TT[key] = (flag, best_val, best_sq)

    return best_val


def _root_search(me: int, opp: int, depth: int, current_best):
    moves = _gen_moves(me, opp)
    tt_entry = TT.get((me, opp, depth))
    tt_move = tt_entry[2] if tt_entry is not None else current_best
    moves = _ordered_moves(moves, me, opp, tt_move)

    alpha = -INF
    beta = INF
    best_val = -INF
    best_sq = moves[0][0]

    for sq, flips in moves:
        if time.perf_counter() > DEADLINE:
            raise SearchTimeout()

        bit = 1 << sq
        new_me = me | bit | flips
        new_opp = opp & ~flips

        val = -_negamax(new_opp, new_me, depth - 1, -beta, -alpha)

        if val > best_val:
            best_val = val
            best_sq = sq

        if val > alpha:
            alpha = val

    if len(TT) < 250000:
        TT[(me, opp, depth)] = (0, best_val, best_sq)

    return best_val, best_sq


# ---------- API helpers ----------

def _to_bitboards(you: np.ndarray, opponent: np.ndarray):
    me = 0
    opp = 0
    for r in range(8):
        base = r * 8
        for c in range(8):
            bit = 1 << (base + c)
            if you[r][c]:
                me |= bit
            elif opponent[r][c]:
                opp |= bit
    return me, opp


def _sq_to_str(sq: int) -> str:
    r, c = divmod(sq, 8)
    return chr(ord('a') + c) + str(r + 1)


def _fallback_policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """Very safe legal-move fallback using direct board scanning."""
    for r in range(8):
        for c in range(8):
            if you[r][c] or opponent[r][c]:
                continue
            legal = False
            for dr, dc in DIRS:
                rr, cc = r + dr, c + dc
                seen_opp = False
                while 0 <= rr < 8 and 0 <= cc < 8 and opponent[rr][cc]:
                    seen_opp = True
                    rr += dr
                    cc += dc
                if seen_opp and 0 <= rr < 8 and 0 <= cc < 8 and you[rr][cc]:
                    legal = True
                    break
            if legal:
                return chr(ord('a') + c) + str(r + 1)
    return "pass"


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Return a legal Othello move such as 'd3', or 'pass' only when no legal move exists.
    """
    global DEADLINE, NODES, TT

    try:
        me, opp = _to_bitboards(you, opponent)
        root_moves = _gen_moves(me, opp)

        if not root_moves:
            return "pass"

        # Always keep a legal fallback.
        ordered = _ordered_moves(root_moves, me, opp, None)
        best_sq = ordered[0][0]

        if len(root_moves) == 1:
            return _sq_to_str(best_sq)

        # Conservative time budget for a 1 second limit.
        DEADLINE = time.perf_counter() + 0.88
        NODES = 0
        TT = {}

        occupied = (me | opp).bit_count()
        empties = 64 - occupied
        branching = len(root_moves)

        # Iterative deepening depth schedule. The timeout guard decides final depth.
        if empties <= 12:
            max_depth = empties
        elif empties <= 16:
            max_depth = 12
        elif empties <= 24:
            max_depth = 9
        elif empties <= 44:
            max_depth = 7
        else:
            max_depth = 6

        if branching <= 4:
            max_depth += 2
        elif branching >= 12 and empties > 24:
            max_depth -= 1

        max_depth = max(1, min(max_depth, 64))

        # Iterative deepening: only completed depths update the chosen move.
        for depth in range(1, max_depth + 1):
            try:
                val, sq = _root_search(me, opp, depth, best_sq)
                best_sq = sq

                # If exact endgame result found at full remaining depth, no need to continue.
                if depth >= empties and abs(val) >= WIN:
                    break

                if time.perf_counter() > DEADLINE:
                    break
            except SearchTimeout:
                break

        return _sq_to_str(best_sq)

    except Exception:
        # Last-resort guarantee: never return an illegal non-pass move due to an internal error.
        return _fallback_policy(you, opponent)
