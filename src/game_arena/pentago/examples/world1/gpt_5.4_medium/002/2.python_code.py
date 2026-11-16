
from typing import Iterable

# =========================
# Precomputed board geometry
# =========================

BOARD_N = 6
FULL_MASK = (1 << 36) - 1
WIN_SCORE = 100_000_000
DIR_CHARS = ("L", "R")

# Positional weights: mild preference for strong central influence.
CELL_WEIGHTS = [
    3, 4, 5, 5, 4, 3,
    4, 6, 7, 7, 6, 4,
    5, 7, 8, 8, 7, 5,
    5, 7, 8, 8, 7, 5,
    4, 6, 7, 7, 6, 4,
    3, 4, 5, 5, 4, 3,
]

# Order placements from strongest-looking cells first.
CELL_ORDER = sorted(range(36), key=lambda i: (-CELL_WEIGHTS[i], i))
BIT = [1 << i for i in range(36)]

# Heuristic scores for uncontested 5-cell windows with k stones.
LINE_SCORE = [0, 4, 15, 70, 450, 0]

# Quadrant cells in local row-major order.
QUAD_POS = [
    (0, 1, 2, 6, 7, 8, 12, 13, 14),        # top-left
    (3, 4, 5, 9, 10, 11, 15, 16, 17),      # top-right
    (18, 19, 20, 24, 25, 26, 30, 31, 32),  # bottom-left
    (21, 22, 23, 27, 28, 29, 33, 34, 35),  # bottom-right
]

QUAD_MASKS = []
for qpos in QUAD_POS:
    m = 0
    for p in qpos:
        m |= 1 << p
    QUAD_MASKS.append(m)

# Rotation maps on a 3x3 local board, destination index -> source index.
# Local row-major indices:
# 0 1 2
# 3 4 5
# 6 7 8
CCW_SRC = (2, 5, 8, 1, 4, 7, 0, 3, 6)  # L
CW_SRC = (6, 3, 0, 7, 4, 1, 8, 5, 2)   # R

# ROT_GLOBAL[quad][dir][occ] = rotated occupancy placed into global 36-bit board space
ROT_GLOBAL = [[[0] * 512 for _ in range(2)] for _ in range(4)]

for q in range(4):
    qpos = QUAD_POS[q]
    for occ in range(512):
        # Left / CCW
        rocc = 0
        for dst in range(9):
            if (occ >> CCW_SRC[dst]) & 1:
                rocc |= 1 << dst
        g = 0
        for i in range(9):
            if (rocc >> i) & 1:
                g |= 1 << qpos[i]
        ROT_GLOBAL[q][0][occ] = g

        # Right / CW
        rocc = 0
        for dst in range(9):
            if (occ >> CW_SRC[dst]) & 1:
                rocc |= 1 << dst
        g = 0
        for i in range(9):
            if (rocc >> i) & 1:
                g |= 1 << qpos[i]
        ROT_GLOBAL[q][1][occ] = g

# All 5-in-a-row masks.
WIN_MASKS = []
for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
    for r in range(BOARD_N):
        for c in range(BOARD_N):
            rr = r + 4 * dr
            cc = c + 4 * dc
            if 0 <= rr < BOARD_N and 0 <= cc < BOARD_N:
                mask = 0
                for k in range(5):
                    idx = (r + k * dr) * BOARD_N + (c + k * dc)
                    mask |= 1 << idx
                WIN_MASKS.append(mask)

# =========================
# Core helpers
# =========================

def board_to_bits(arr) -> int:
    bits = 0
    for r in range(6):
        row = arr[r]
        base = r * 6
        for c in range(6):
            if row[c]:
                bits |= 1 << (base + c)
    return bits

def has_five(bits: int) -> bool:
    for m in WIN_MASKS:
        if (bits & m) == m:
            return True
    return False

def terminal_score(y_bits: int, o_bits: int):
    y_win = has_five(y_bits)
    o_win = has_five(o_bits)

    if y_win and o_win:
        return 0, True
    if y_win:
        return WIN_SCORE, True
    if o_win:
        return -WIN_SCORE, True
    if (y_bits | o_bits) == FULL_MASK:
        return 0, True
    return 0, False

def rotate_bits(bits: int, quad: int, d: int) -> int:
    qpos = QUAD_POS[quad]
    occ = 0
    # Extract 9-bit local occupancy.
    if bits & (1 << qpos[0]): occ |= 1 << 0
    if bits & (1 << qpos[1]): occ |= 1 << 1
    if bits & (1 << qpos[2]): occ |= 1 << 2
    if bits & (1 << qpos[3]): occ |= 1 << 3
    if bits & (1 << qpos[4]): occ |= 1 << 4
    if bits & (1 << qpos[5]): occ |= 1 << 5
    if bits & (1 << qpos[6]): occ |= 1 << 6
    if bits & (1 << qpos[7]): occ |= 1 << 7
    if bits & (1 << qpos[8]): occ |= 1 << 8
    return (bits & ~QUAD_MASKS[quad]) | ROT_GLOBAL[quad][d][occ]

def apply_move(y_bits: int, o_bits: int, idx: int, quad: int, d: int, player: int):
    if player == 0:
        y_bits |= 1 << idx
    else:
        o_bits |= 1 << idx
    y_bits = rotate_bits(y_bits, quad, d)
    o_bits = rotate_bits(o_bits, quad, d)
    return y_bits, o_bits

def eval_position(y_bits: int, o_bits: int) -> int:
    score = 0

    # Window-based evaluation.
    for m in WIN_MASKS:
        y = (y_bits & m).bit_count()
        o = (o_bits & m).bit_count()
        if o == 0:
            score += LINE_SCORE[y]
        elif y == 0:
            score -= LINE_SCORE[o]

    # Positional weights.
    b = y_bits
    while b:
        lsb = b & -b
        idx = lsb.bit_length() - 1
        score += CELL_WEIGHTS[idx]
        b ^= lsb

    b = o_bits
    while b:
        lsb = b & -b
        idx = lsb.bit_length() - 1
        score -= CELL_WEIGHTS[idx]
        b ^= lsb

    return score

def count_opponent_winning_replies(y_bits: int, o_bits: int, limit: int = 3) -> int:
    occ = y_bits | o_bits
    count = 0

    for idx in CELL_ORDER:
        if occ & BIT[idx]:
            continue
        for q in range(4):
            for d in (0, 1):
                y2, o2 = apply_move(y_bits, o_bits, idx, q, d, 1)
                o_win = has_five(o2)
                if not o_win:
                    continue
                y_win = has_five(y2)
                if not y_win:
                    count += 1
                    if count >= limit:
                        return count
    return count

def worst_opponent_reply_score(y_bits: int, o_bits: int, cutoff: int) -> int:
    occ = y_bits | o_bits
    worst = WIN_SCORE * 2

    for idx in CELL_ORDER:
        if occ & BIT[idx]:
            continue
        for q in range(4):
            for d in (0, 1):
                y2, o2 = apply_move(y_bits, o_bits, idx, q, d, 1)
                s, term = terminal_score(y2, o2)
                if not term:
                    s = eval_position(y2, o2)
                if s < worst:
                    worst = s
                    if worst <= cutoff:
                        return worst
    return worst

def move_to_str(idx: int, quad: int, d: int) -> str:
    r = idx // 6 + 1
    c = idx % 6 + 1
    return f"{r},{c},{quad},{DIR_CHARS[d]}"

def fallback_move(you, opponent) -> str:
    for r in range(6):
        for c in range(6):
            if not you[r][c] and not opponent[r][c]:
                return f"{r+1},{c+1},0,L"
    return "1,1,0,L"

# =========================
# Main policy
# =========================

def policy(you, opponent) -> str:
    safe_fallback = fallback_move(you, opponent)

    try:
        y_bits = board_to_bits(you)
        o_bits = board_to_bits(opponent)
        occ = y_bits | o_bits

        # Simple opening.
        if occ == 0:
            return "2,2,0,L"

        candidates = []
        best_draw_move = None

        for idx in CELL_ORDER:
            if occ & BIT[idx]:
                continue

            for quad in range(4):
                for d in (0, 1):
                    y2, o2 = apply_move(y_bits, o_bits, idx, quad, d, 0)
                    tscore, term = terminal_score(y2, o2)

                    # Immediate win: take it.
                    if term and tscore == WIN_SCORE:
                        return move_to_str(idx, quad, d)

                    if term:
                        # Draw is often a valuable bailout; immediate loss is terrible.
                        if tscore == 0 and best_draw_move is None:
                            best_draw_move = (idx, quad, d)
                        candidates.append({
                            "idx": idx,
                            "quad": quad,
                            "d": d,
                            "y": y2,
                            "o": o2,
                            "score": tscore,
                            "terminal": True,
                            "opp_wins": 0,
                        })
                    else:
                        h = eval_position(y2, o2)
                        opp_wins = count_opponent_winning_replies(y2, o2, limit=3)
                        score = h - opp_wins * 1_000_000
                        candidates.append({
                            "idx": idx,
                            "quad": quad,
                            "d": d,
                            "y": y2,
                            "o": o2,
                            "score": score,
                            "terminal": False,
                            "opp_wins": opp_wins,
                        })

        if not candidates:
            return safe_fallback

        best_score = -10**18
        best_move = None

        # Draw is better than a forced loss.
        if best_draw_move is not None:
            best_score = 0
            best_move = best_draw_move

        # Safe nonterminal moves get deeper evaluation.
        safe_moves = [c for c in candidates if (not c["terminal"]) and c["opp_wins"] == 0]
        if safe_moves:
            safe_moves.sort(key=lambda c: c["score"], reverse=True)
            top = safe_moves[:10]

            for c in top:
                worst = worst_opponent_reply_score(c["y"], c["o"], best_score)
                if worst > best_score:
                    best_score = worst
                    best_move = (c["idx"], c["quad"], c["d"])

        if best_move is not None:
            return move_to_str(*best_move)

        # No safe move found: choose the least bad tactical option.
        best = max(candidates, key=lambda c: c["score"])
        return move_to_str(best["idx"], best["quad"], best["d"])

    except Exception:
        return safe_fallback
