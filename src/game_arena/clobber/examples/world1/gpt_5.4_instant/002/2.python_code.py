
import time
from typing import List, Tuple

# 5x6 board => 30 cells, indexed by idx = r*6 + c
ROWS = 5
COLS = 6
N = ROWS * COLS

# Directions
DIRS = [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]

# Precompute neighbors and move masks
NEI = [[] for _ in range(N)]            # list of (to_idx, dir_char)
ADJ_MASK = [0] * N                      # orthogonal adjacency mask
for r in range(ROWS):
    for c in range(COLS):
        i = r * COLS + c
        for dr, dc, ch in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                j = nr * COLS + nc
                NEI[i].append((j, ch))
                ADJ_MASK[i] |= (1 << j)

# Cell weights: center is usually better than edge/corner
CELL_W = [0] * N
for r in range(ROWS):
    for c in range(COLS):
        i = r * COLS + c
        wr = 2 - abs(r - 2)
        wc = 3 - abs(c - 2.5)
        CELL_W[i] = wr + wc

# Small transposition table
TT = {}

# Time management globals
TIME_LIMIT = 0.92
START_TIME = 0.0
TIMEOUT = False


def bits(x: int):
    while x:
        lsb = x & -x
        yield lsb.bit_length() - 1
        x ^= lsb


def rc_to_idx(r: int, c: int) -> int:
    return r * COLS + c


def idx_to_rc(i: int) -> Tuple[int, int]:
    return divmod(i, COLS)


def arrays_to_masks(you, opp) -> Tuple[int, int]:
    ym = 0
    om = 0
    # Accept list-of-lists or numpy arrays
    for r in range(ROWS):
        rowy = you[r]
        rowo = opp[r]
        for c in range(COLS):
            if int(rowy[c]) == 1:
                ym |= 1 << (r * COLS + c)
            elif int(rowo[c]) == 1:
                om |= 1 << (r * COLS + c)
    return ym, om


def legal_moves_masks(my_mask: int, op_mask: int):
    # Returns list of (from_idx, to_idx, dir_char)
    moves = []
    m = my_mask
    while m:
        f_lsb = m & -m
        f = f_lsb.bit_length() - 1
        occ_enemy_adj = ADJ_MASK[f] & op_mask
        while occ_enemy_adj:
            t_lsb = occ_enemy_adj & -occ_enemy_adj
            t = t_lsb.bit_length() - 1
            # recover direction char
            dr = (t // COLS) - (f // COLS)
            dc = (t % COLS) - (f % COLS)
            if dr == -1:
                ch = 'U'
            elif dr == 1:
                ch = 'D'
            elif dc == 1:
                ch = 'R'
            else:
                ch = 'L'
            moves.append((f, t, ch))
            occ_enemy_adj ^= t_lsb
        m ^= f_lsb
    return moves


def mobility(my_mask: int, op_mask: int) -> int:
    total = 0
    m = my_mask
    while m:
        lsb = m & -m
        i = lsb.bit_length() - 1
        if ADJ_MASK[i] & op_mask:
            total += ((ADJ_MASK[i] & op_mask).bit_count())
        m ^= lsb
    return total


def contact_score(my_mask: int, op_mask: int) -> int:
    # Sum local tactical opportunities minus vulnerabilities
    s = 0
    m = my_mask
    while m:
        lsb = m & -m
        i = lsb.bit_length() - 1
        cnt = (ADJ_MASK[i] & op_mask).bit_count()
        s += 3 * cnt + CELL_W[i]
        m ^= lsb
    e = op_mask
    while e:
        lsb = e & -e
        i = lsb.bit_length() - 1
        cnt = (ADJ_MASK[i] & my_mask).bit_count()
        s -= 3 * cnt + CELL_W[i]
        e ^= lsb
    return s


def evaluate(my_mask: int, op_mask: int) -> int:
    my_moves = mobility(my_mask, op_mask)
    if my_moves == 0:
        return -100000
    op_moves = mobility(op_mask, my_mask)
    if op_moves == 0:
        return 100000

    my_count = my_mask.bit_count()
    op_count = op_mask.bit_count()

    # In Clobber, raw piece count alone is not everything; mobility dominates.
    score = 0
    score += 120 * (my_moves - op_moves)
    score += 10 * (op_count - my_count)  # often good to have fewer own pieces late
    score += contact_score(my_mask, op_mask)

    # Parity-ish nudge
    total = my_count + op_count
    if total <= 10:
        score += 7 if (my_moves % 2) == 1 else -7

    return score


def ordered_moves(my_mask: int, op_mask: int, tt_best=None):
    moves = legal_moves_masks(my_mask, op_mask)
    if not moves:
        return moves

    scored = []
    op_mob_before = mobility(op_mask, my_mask)

    for mv in moves:
        f, t, ch = mv
        new_my = (my_mask ^ (1 << f)) | (1 << t)
        new_op = op_mask ^ (1 << t)

        # Opponent to move after swap of perspective: their mobility
        opp_reply = mobility(new_op, new_my)
        my_future = mobility(new_my, new_op)

        score = 0
        if tt_best is not None and mv == tt_best:
            score += 1000000
        if opp_reply == 0:
            score += 500000
        score += 200 * (op_mob_before - opp_reply)
        score += 80 * my_future
        score += 8 * CELL_W[t] - 5 * CELL_W[f]

        # prefer landing where fewer enemy adjacent attackers remain after swap
        # (in current frame, fewer opponent neighbors around destination after move)
        score -= 15 * ((ADJ_MASK[t] & new_op).bit_count())

        scored.append((score, mv))

    scored.sort(reverse=True, key=lambda x: x[0])
    return [mv for _, mv in scored]


def negamax(my_mask: int, op_mask: int, depth: int, alpha: int, beta: int) -> int:
    global TIMEOUT
    if TIMEOUT:
        return 0
    if time.perf_counter() - START_TIME > TIME_LIMIT:
        TIMEOUT = True
        return 0

    key = (my_mask, op_mask, depth)
    if key in TT:
        entry = TT[key]
        flag, val, best = entry
        if flag == 0:
            return val
        elif flag == -1 and val <= alpha:
            return val
        elif flag == 1 and val >= beta:
            return val

    moves = legal_moves_masks(my_mask, op_mask)
    if not moves:
        return -100000 + (20 - depth)

    if depth == 0:
        return evaluate(my_mask, op_mask)

    alpha_orig = alpha
    best_val = -10**9
    best_move = None

    tt_best = TT.get((my_mask, op_mask, depth - 1), (None, None, None))[2]
    for f, t, ch in ordered_moves(my_mask, op_mask, tt_best):
        new_my = (my_mask ^ (1 << f)) | (1 << t)
        new_op = op_mask ^ (1 << t)

        # swap perspective
        val = -negamax(new_op, new_my, depth - 1, -beta, -alpha)
        if TIMEOUT:
            return 0
        if val > best_val:
            best_val = val
            best_move = (f, t, ch)
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    flag = 0
    if best_val <= alpha_orig:
        flag = -1
    elif best_val >= beta:
        flag = 1
    TT[key] = (flag, best_val, best_move)
    return best_val


def move_to_str(mv) -> str:
    f, t, ch = mv
    r, c = idx_to_rc(f)
    return f"{r},{c},{ch}"


def fallback_legal_move(my_mask: int, op_mask: int) -> str:
    moves = legal_moves_masks(my_mask, op_mask)
    if not moves:
        # No legal move should not occur in valid arena positions, but remain safe.
        # Return any syntactically valid string.
        return "0,0,R"
    best = None
    best_score = -10**9
    for mv in moves:
        f, t, ch = mv
        new_my = (my_mask ^ (1 << f)) | (1 << t)
        new_op = op_mask ^ (1 << t)
        score = 0
        opp_reply = mobility(new_op, new_my)
        if opp_reply == 0:
            return move_to_str(mv)
        score += 100 * (mobility(new_my, new_op) - opp_reply)
        score += 10 * CELL_W[t] - 5 * CELL_W[f]
        score -= 8 * ((ADJ_MASK[t] & new_op).bit_count())
        if score > best_score:
            best_score = score
            best = mv
    return move_to_str(best)


def policy(you: List[List[int]], opponent: List[List[int]]) -> str:
    global START_TIME, TIMEOUT
    START_TIME = time.perf_counter()
    TIMEOUT = False

    my_mask, op_mask = arrays_to_masks(you, opponent)
    root_moves = legal_moves_masks(my_mask, op_mask)
    if not root_moves:
        return "0,0,R"  # emergency fallback for malformed input

    # Immediate win check
    for mv in root_moves:
        f, t, ch = mv
        new_my = (my_mask ^ (1 << f)) | (1 << t)
        new_op = op_mask ^ (1 << t)
        if mobility(new_op, new_my) == 0:
            return move_to_str(mv)

    best_move = ordered_moves(my_mask, op_mask)[0]
    best_val = -10**9

    # Iterative deepening
    # Depths tuned for 1 second budget on tiny board.
    for depth in range(1, 13):
        if time.perf_counter() - START_TIME > TIME_LIMIT:
            break
        current_best = None
        current_best_val = -10**9

        tt_best = TT.get((my_mask, op_mask, depth - 1), (None, None, None))[2]
        moves = ordered_moves(my_mask, op_mask, tt_best)

        alpha = -10**9
        beta = 10**9
        for mv in moves:
            if time.perf_counter() - START_TIME > TIME_LIMIT:
                TIMEOUT = True
                break
            f, t, ch = mv
            new_my = (my_mask ^ (1 << f)) | (1 << t)
            new_op = op_mask ^ (1 << t)
            val = -negamax(new_op, new_my, depth - 1, -beta, -alpha)
            if TIMEOUT:
                break
            if val > current_best_val:
                current_best_val = val
                current_best = mv
            if val > alpha:
                alpha = val

        if current_best is not None and not TIMEOUT:
            best_move = current_best
            best_val = current_best_val
            TT[(my_mask, op_mask, depth)] = (0, best_val, best_move)
        else:
            break

    # Safety: ensure returned move is legal
    if best_move not in root_moves:
        return fallback_legal_move(my_mask, op_mask)
    return move_to_str(best_move)
