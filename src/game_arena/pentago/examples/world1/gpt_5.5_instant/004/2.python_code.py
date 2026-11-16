
import math
import random

# Pentago policy: fast tactical one-ply / selective two-ply evaluator.

DIRS = ("L", "R")
QUADS = (0, 1, 2, 3)

# All 5-cell segments in 6x6 that can make a win.
LINES5 = []
for r in range(6):
    for c in range(2):
        LINES5.append(tuple((r, c + k) for k in range(5)))
for c in range(6):
    for r in range(2):
        LINES5.append(tuple((r + k, c) for k in range(5)))
for r in range(2):
    for c in range(2):
        LINES5.append(tuple((r + k, c + k) for k in range(5)))
for r in range(2):
    for c in range(4, 6):
        LINES5.append(tuple((r + k, c - k) for k in range(5)))

# Also include full 6-length lines for "5 or more" detection via contained 5s already works,
# but for evaluation it is useful to consider all length-6 rows/cols/diags too.
LINES_EVAL = list(LINES5)
for r in range(6):
    LINES_EVAL.append(tuple((r, c) for c in range(6)))
for c in range(6):
    LINES_EVAL.append(tuple((r, c) for r in range(6)))
LINES_EVAL.append(tuple((i, i) for i in range(6)))
LINES_EVAL.append(tuple((i, 5 - i) for i in range(6)))

# Positional preference: centers of quadrants and global near-center are useful in Pentago.
POS_W = [
    [3, 4, 4, 4, 4, 3],
    [4, 6, 5, 5, 6, 4],
    [4, 5, 7, 7, 5, 4],
    [4, 5, 7, 7, 5, 4],
    [4, 6, 5, 5, 6, 4],
    [3, 4, 4, 4, 4, 3],
]


def _copy_board(b):
    return [list(row) for row in b]


def _bits_from_arrays(you, opp):
    y = 0
    o = 0
    for r in range(6):
        for c in range(6):
            bit = 1 << (r * 6 + c)
            if int(you[r][c]):
                y |= bit
            elif int(opp[r][c]):
                o |= bit
    return y, o


def _has_win(bits):
    for line in LINES5:
        ok = True
        for r, c in line:
            if not (bits >> (r * 6 + c)) & 1:
                ok = False
                break
        if ok:
            return True
    return False


def _rotate_bits(bits, quad, direction):
    qr = 0 if quad < 2 else 3
    qc = 0 if quad % 2 == 0 else 3

    # Clear quadrant bits while remembering local occupancy.
    vals = [[0] * 3 for _ in range(3)]
    mask = 0
    for i in range(3):
        for j in range(3):
            idx = (qr + i) * 6 + (qc + j)
            bit = 1 << idx
            mask |= bit
            vals[i][j] = 1 if (bits & bit) else 0
    bits &= ~mask

    # Clockwise: (i,j)->(j,2-i). Anticlockwise: (i,j)->(2-j,i)
    for i in range(3):
        for j in range(3):
            if vals[i][j]:
                if direction == "R":
                    ni, nj = j, 2 - i
                else:
                    ni, nj = 2 - j, i
                bits |= 1 << ((qr + ni) * 6 + (qc + nj))
    return bits


def _apply_move(y, o, cell, quad, direction):
    y2 = y | (1 << cell)
    return _rotate_bits(y2, quad, direction), _rotate_bits(o, quad, direction)


def _line_score(my_count, op_count, length):
    if my_count and op_count:
        return 0
    if my_count == 0 and op_count == 0:
        return 0

    # Scores intentionally grow sharply for immediate tactical threats.
    if op_count == 0:
        if my_count >= 5:
            return 1000000
        if my_count == 4:
            return 12000 if length >= 5 else 8000
        if my_count == 3:
            return 900
        if my_count == 2:
            return 90
        return 8

    if my_count == 0:
        if op_count >= 5:
            return -1000000
        if op_count == 4:
            return -15000 if length >= 5 else -10000
        if op_count == 3:
            return -1100
        if op_count == 2:
            return -100
        return -9

    return 0


def _evaluate(y, o):
    yw = _has_win(y)
    ow = _has_win(o)
    if yw and ow:
        return 0
    if yw:
        return 10**9
    if ow:
        return -10**9

    score = 0

    # Line potential.
    for line in LINES_EVAL:
        mc = 0
        oc = 0
        for r, c in line:
            idx = r * 6 + c
            if (y >> idx) & 1:
                mc += 1
            elif (o >> idx) & 1:
                oc += 1
        score += _line_score(mc, oc, len(line))

    # Positional control.
    for r in range(6):
        for c in range(6):
            idx = r * 6 + c
            if (y >> idx) & 1:
                score += POS_W[r][c]
            elif (o >> idx) & 1:
                score -= POS_W[r][c]

    return score


def _all_moves(y, o):
    occupied = y | o
    moves = []
    for cell in range(36):
        if not ((occupied >> cell) & 1):
            r = cell // 6
            c = cell % 6
            for q in QUADS:
                for d in DIRS:
                    moves.append((cell, q, d, r, c))
    return moves


def _opponent_can_win_next(y, o):
    # From position where opponent is to move, check if opponent has any move
    # that wins without also giving us a win. Here opponent bits are 'o'.
    occupied = y | o
    for cell in range(36):
        if not ((occupied >> cell) & 1):
            for q in QUADS:
                for d in DIRS:
                    o2, y2 = _apply_move(o, y, cell, q, d)
                    ow = _has_win(o2)
                    yw = _has_win(y2)
                    if ow and not yw:
                        return True
    return False


def _best_opponent_reply_score(y, o, limit=72):
    # Opponent minimizes our evaluation. Used only selectively on candidates.
    moves = _all_moves(o, y)
    scored = []
    for cell, q, d, r, c in moves:
        o2, y2 = _apply_move(o, y, cell, q, d)
        val = _evaluate(y2, o2)
        if _has_win(o2) and not _has_win(y2):
            return -10**8
        scored.append(val)
    if not scored:
        return _evaluate(y, o)
    return min(scored)


def _move_to_str(cell, q, d):
    return f"{cell // 6 + 1},{cell % 6 + 1},{q},{d}"


def policy(you, opponent) -> str:
    try:
        y, o = _bits_from_arrays(you, opponent)
        legal = _all_moves(y, o)
        if not legal:
            return "1,1,0,L"  # Should never be reached by contract.

        best_immediate = None
        safe_candidates = []
        all_scored = []

        # First pass: immediate wins and static scoring.
        for cell, q, d, r, c in legal:
            y2, o2 = _apply_move(y, o, cell, q, d)
            yw = _has_win(y2)
            ow = _has_win(o2)

            # A pure win is always best. If both win, it is only a draw.
            if yw and not ow:
                return _move_to_str(cell, q, d)

            val = _evaluate(y2, o2)

            # Prefer drawing immediate result over losing, but not over playable attacks.
            if yw and ow:
                val = max(val, 50000)

            # Penalize allowing an immediate opponent win, but keep as fallback if all moves do.
            allows = False
            if not yw:
                allows = _opponent_can_win_next(y2, o2)
                if allows:
                    val -= 250000

            all_scored.append((val, cell, q, d, y2, o2, allows))
            if not allows:
                safe_candidates.append((val, cell, q, d, y2, o2, allows))

        pool = safe_candidates if safe_candidates else all_scored
        pool.sort(reverse=True, key=lambda x: x[0])

        # Selective two-ply check for the best static candidates.
        best = None
        best_val = -10**18
        check_n = min(10, len(pool))
        for item in pool[:check_n]:
            val, cell, q, d, y2, o2, allows = item
            reply_val = _best_opponent_reply_score(y2, o2)
            combined = val * 0.35 + reply_val * 0.65
            if combined > best_val:
                best_val = combined
                best = item

        if best is None:
            best = pool[0]

        return _move_to_str(best[1], best[2], best[3])

    except Exception:
        # Absolute safety fallback: scan for first empty and return a syntactically legal move.
        for r in range(6):
            for c in range(6):
                try:
                    if int(you[r][c]) == 0 and int(opponent[r][c]) == 0:
                        return f"{r+1},{c+1},0,L"
                except Exception:
                    pass
        return "1,1,0,L"
