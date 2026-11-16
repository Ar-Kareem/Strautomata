
from __future__ import annotations

import time

# Internal side encoding: 0 = black, 1 = white
BLACK = 0
WHITE = 1

INF = 10**18
WIN_SCORE = 10**9

EXACT = 0
LOWER = 1
UPPER = 2

MAX_KILLER_PLY = 64

TT: dict[tuple[int, int, int], tuple[int, int, int, tuple[int, int] | None]] = {}
HISTORY: dict[tuple[int, int, int], int] = {}
KILLERS: list[tuple[tuple[int, int] | None, tuple[int, int] | None]] = [(None, None) for _ in range(MAX_KILLER_PLY)]

DEADLINE = 0.0
NODES = 0

# ---------- Precomputation ----------

ROW_MASK = [0] * 8
for r in range(8):
    mask = 0
    base = r * 8
    for c in range(8):
        mask |= 1 << (base + c)
    ROW_MASK[r] = mask

GOAL_MASK = (ROW_MASK[0], ROW_MASK[7])      # black goal row, white goal row
PREGOAL_MASK = (ROW_MASK[1], ROW_MASK[6])   # one step before goal

CENTER_COL = [0, 1, 2, 3, 3, 2, 1, 0]
RUNNER_BONUS = [0, 1, 3, 6, 10, 16, 25, 40]

PROG_B = [0] * 64
PROG_W = [0] * 64
CENTER = [0] * 64
SIDE_MASK = [0] * 64
BACK_MASK_B = [0] * 64
BACK_MASK_W = [0] * 64
MOVE_OPTIONS_B: list[list[tuple[int, int]]] = [[] for _ in range(64)]
MOVE_OPTIONS_W: list[list[tuple[int, int]]] = [[] for _ in range(64)]

for idx in range(64):
    r = idx >> 3
    c = idx & 7

    PROG_B[idx] = 7 - r
    PROG_W[idx] = r
    CENTER[idx] = CENTER_COL[c]

    # Horizontal neighbors (phalanx / formation)
    sm = 0
    if c > 0:
        sm |= 1 << (r * 8 + (c - 1))
    if c < 7:
        sm |= 1 << (r * 8 + (c + 1))
    SIDE_MASK[idx] = sm

    # Back-diagonal support squares for black (black moves downward, so back is row+1)
    bm = 0
    nr = r + 1
    if nr < 8:
        if c > 0:
            bm |= 1 << (nr * 8 + (c - 1))
        if c < 7:
            bm |= 1 << (nr * 8 + (c + 1))
    BACK_MASK_B[idx] = bm

    # Back-diagonal support squares for white (white moves upward, so back is row-1)
    wm = 0
    nr = r - 1
    if nr >= 0:
        if c > 0:
            wm |= 1 << (nr * 8 + (c - 1))
        if c < 7:
            wm |= 1 << (nr * 8 + (c + 1))
    BACK_MASK_W[idx] = wm

    # Move options for black: to row-1
    opts = []
    nr = r - 1
    if nr >= 0:
        opts.append((nr * 8 + c, 1))  # forward
        if c > 0:
            opts.append((nr * 8 + (c - 1), 0))  # diagonal
        if c < 7:
            opts.append((nr * 8 + (c + 1), 0))  # diagonal
    MOVE_OPTIONS_B[idx] = opts

    # Move options for white: to row+1
    opts = []
    nr = r + 1
    if nr < 8:
        opts.append((nr * 8 + c, 1))  # forward
        if c > 0:
            opts.append((nr * 8 + (c - 1), 0))  # diagonal
        if c < 7:
            opts.append((nr * 8 + (c + 1), 0))  # diagonal
    MOVE_OPTIONS_W[idx] = opts

PROG = (PROG_B, PROG_W)
BACK_MASK = (BACK_MASK_B, BACK_MASK_W)
MOVE_OPTIONS = (MOVE_OPTIONS_B, MOVE_OPTIONS_W)


# ---------- Utility ----------

def _to_side(color: str) -> int:
    return WHITE if color == "w" else BLACK


def _to_color(side: int) -> str:
    return "w" if side == WHITE else "b"


def _bb_from_list(pieces: list[tuple[int, int]]) -> int:
    bb = 0
    for r, c in pieces:
        bb |= 1 << (r * 8 + c)
    return bb


def _decode_move(fr: int, to: int) -> tuple[tuple[int, int], tuple[int, int]]:
    return ((fr >> 3, fr & 7), (to >> 3, to & 7))


def _terminal_value(my: int, opp: int, side: int) -> int | None:
    opp_side = 1 - side
    if my == 0 or (opp & GOAL_MASK[opp_side]):
        return -WIN_SCORE
    if opp == 0 or (my & GOAL_MASK[side]):
        return WIN_SCORE
    return None


# ---------- Tactical helpers ----------

def has_immediate_win(my: int, opp: int, side: int) -> bool:
    occ = my | opp
    goal_mask = GOAL_MASK[side]
    single_opp = (opp.bit_count() == 1)
    bb = my if single_opp else (my & PREGOAL_MASK[side])

    move_options = MOVE_OPTIONS[side]

    while bb:
        b = bb & -bb
        fr = b.bit_length() - 1
        bb ^= b

        for to, is_forward in move_options[fr]:
            tb = 1 << to
            if is_forward:
                if occ & tb:
                    continue
            else:
                if my & tb:
                    continue

            if (tb & goal_mask) or (single_opp and (opp & tb)):
                return True
    return False


def winning_move_count(my: int, opp: int, side: int) -> int:
    # Count, but cap early because eval only needs "how many dangerous threats", not exact large counts.
    occ = my | opp
    goal_mask = GOAL_MASK[side]
    single_opp = (opp.bit_count() == 1)
    bb = my if single_opp else (my & PREGOAL_MASK[side])

    move_options = MOVE_OPTIONS[side]
    count = 0

    while bb:
        b = bb & -bb
        fr = b.bit_length() - 1
        bb ^= b

        for to, is_forward in move_options[fr]:
            tb = 1 << to
            if is_forward:
                if occ & tb:
                    continue
            else:
                if my & tb:
                    continue

            if (tb & goal_mask) or (single_opp and (opp & tb)):
                count += 1
                if count >= 3:
                    return 3
    return count


def legal_move_count(my: int, opp: int, side: int) -> int:
    occ = my | opp
    move_options = MOVE_OPTIONS[side]
    count = 0
    bb = my

    while bb:
        b = bb & -bb
        fr = b.bit_length() - 1
        bb ^= b

        for to, is_forward in move_options[fr]:
            tb = 1 << to
            if is_forward:
                if not (occ & tb):
                    count += 1
            else:
                if not (my & tb):
                    count += 1
    return count


# ---------- Evaluation ----------

def evaluate(my: int, opp: int, side: int) -> int:
    opp_side = 1 - side

    prog_my = PROG[side]
    prog_opp = PROG[opp_side]
    back_my = BACK_MASK[side]
    back_opp = BACK_MASK[opp_side]

    my_count = my.bit_count()
    opp_count = opp.bit_count()

    score = 95 * (my_count - opp_count)

    my_sum = my_max = my_center = my_support = my_phalanx = my_vuln = my_runner = 0
    bb = my
    while bb:
        b = bb & -bb
        idx = b.bit_length() - 1
        bb ^= b

        p = prog_my[idx]
        my_sum += p
        if p > my_max:
            my_max = p
        my_runner += RUNNER_BONUS[p]
        my_center += CENTER[idx]
        if my & back_my[idx]:
            my_support += 1
        if my & SIDE_MASK[idx]:
            my_phalanx += 1
        if opp & back_opp[idx]:
            my_vuln += 1

    opp_sum = opp_max = opp_center = opp_support = opp_phalanx = opp_vuln = opp_runner = 0
    bb = opp
    while bb:
        b = bb & -bb
        idx = b.bit_length() - 1
        bb ^= b

        p = prog_opp[idx]
        opp_sum += p
        if p > opp_max:
            opp_max = p
        opp_runner += RUNNER_BONUS[p]
        opp_center += CENTER[idx]
        if opp & back_opp[idx]:
            opp_support += 1
        if opp & SIDE_MASK[idx]:
            opp_phalanx += 1
        if my & back_my[idx]:
            opp_vuln += 1

    score += 14 * (my_sum - opp_sum)
    score += 46 * (my_max - opp_max)
    score += 12 * (my_runner - opp_runner)
    score += 3 * (my_center - opp_center)
    score += 6 * (my_support - opp_support)
    score += 4 * (my_phalanx - opp_phalanx)
    score += 8 * (opp_vuln - my_vuln)

    score += 2 * (legal_move_count(my, opp, side) - legal_move_count(opp, my, opp_side))

    my_threats = winning_move_count(my, opp, side)
    opp_threats = winning_move_count(opp, my, opp_side)
    score += 15000 * (my_threats - opp_threats)

    score += 90 * ((my & PREGOAL_MASK[side]).bit_count() - (opp & PREGOAL_MASK[opp_side]).bit_count())

    return score


# ---------- Move ordering ----------

def ordered_moves(my: int, opp: int, side: int, tt_move: tuple[int, int] | None = None, ply: int = 0) -> list[tuple[int, int, int]]:
    occ = my | opp
    opp_side = 1 - side

    prog = PROG[side]
    prog_opp = PROG[opp_side]
    back_self = BACK_MASK[side]
    back_enemy = BACK_MASK[opp_side]
    goal_mask = GOAL_MASK[side]
    pregoal_mask = PREGOAL_MASK[side]
    move_options = MOVE_OPTIONS[side]

    single_opp = (opp.bit_count() == 1)
    hist_get = HISTORY.get

    if ply < MAX_KILLER_PLY:
        killer1, killer2 = KILLERS[ply]
    else:
        killer1, killer2 = (None, None)

    moves: list[tuple[int, int, int]] = []
    bb = my

    while bb:
        from_bit = bb & -bb
        fr = from_bit.bit_length() - 1
        bb ^= from_bit

        src_threat = bool(opp & back_enemy[fr])
        src_prog = prog[fr]

        for to, is_forward in move_options[fr]:
            tb = 1 << to

            if is_forward:
                if occ & tb:
                    continue
            else:
                if my & tb:
                    continue

            cap = bool(opp & tb)
            win = bool(tb & goal_mask) or (cap and single_opp)

            h = prog[to] * 100 + CENTER[to] * 10 + src_prog * 4

            if cap:
                h += 5000 + prog_opp[to] * 50

            if tb & pregoal_mask:
                h += 1000

            if (my ^ from_bit) & back_self[to]:
                h += 120

            dest_threat = bool(opp & back_enemy[to])
            if dest_threat:
                h -= 100
            if src_threat and not dest_threat:
                h += 150

            mv = (fr, to)

            if win:
                h += 1_000_000_000
            if tt_move == mv:
                h += 500_000_000
            if mv == killer1:
                h += 80_000
            elif mv == killer2:
                h += 40_000

            h += hist_get((side, fr, to), 0)
            moves.append((h, fr, to))

    moves.sort(reverse=True)
    return moves


# ---------- Search ----------

def negamax(my: int, opp: int, side: int, depth: int, alpha: int, beta: int, ply: int) -> int:
    global NODES

    NODES += 1
    if (NODES & 1023) == 0 and time.perf_counter() >= DEADLINE:
        raise TimeoutError

    term = _terminal_value(my, opp, side)
    if term is not None:
        return term

    if depth <= 0:
        return evaluate(my, opp, side)

    key = (my, opp, side)
    entry = TT.get(key)
    tt_move = None

    alpha_in = alpha
    beta_in = beta

    if entry is not None:
        entry_depth, flag, value, best_mv = entry
        tt_move = best_mv
        if entry_depth >= depth:
            if flag == EXACT:
                return value
            if flag == LOWER:
                if value > alpha:
                    alpha = value
            else:  # UPPER
                if value < beta:
                    beta = value
            if alpha >= beta:
                return value

    moves = ordered_moves(my, opp, side, tt_move, ply)
    if not moves:
        return -WIN_SCORE

    best = -INF
    best_move = (moves[0][1], moves[0][2])
    opp_side = 1 - side
    first = True

    for _, fr, to in moves:
        tb = 1 << to
        new_self = ((my ^ (1 << fr)) | tb)
        new_opp = opp & ~tb

        if first:
            score = -negamax(new_opp, new_self, opp_side, depth - 1, -beta, -alpha, ply + 1)
            first = False
        else:
            score = -negamax(new_opp, new_self, opp_side, depth - 1, -alpha - 1, -alpha, ply + 1)
            if alpha < score < beta:
                score = -negamax(new_opp, new_self, opp_side, depth - 1, -beta, -alpha, ply + 1)

        if score > best:
            best = score
            best_move = (fr, to)

        if score > alpha:
            alpha = score

        if alpha >= beta:
            if not (opp & (1 << to)):  # quiet cutoff
                if ply < MAX_KILLER_PLY:
                    k1, k2 = KILLERS[ply]
                    mv = (fr, to)
                    if mv != k1:
                        KILLERS[ply] = (mv, k1)
                hist_key = (side, fr, to)
                HISTORY[hist_key] = min(HISTORY.get(hist_key, 0) + depth * depth, 1_000_000)
            break

    if best <= alpha_in:
        flag = UPPER
    elif best >= beta_in:
        flag = LOWER
    else:
        flag = EXACT

    TT[key] = (depth, flag, best, best_move)
    return best


def search_root(
    my: int,
    opp: int,
    side: int,
    depth: int,
    moves: list[tuple[int, int, int]],
    pv_move: tuple[int, int] | None = None,
) -> tuple[int, tuple[int, int]]:
    key = (my, opp, side)
    entry = TT.get(key)
    tt_move = entry[3] if entry is not None else None

    ordered: list[tuple[int, int, int]] = []
    for h, fr, to in moves:
        bonus = 0
        if pv_move is not None and (fr, to) == pv_move:
            bonus += 500_000_000
        if tt_move is not None and (fr, to) == tt_move:
            bonus += 250_000_000
        ordered.append((h + bonus, fr, to))
    ordered.sort(reverse=True)

    alpha = -INF
    beta = INF
    best = -INF
    best_move = (ordered[0][1], ordered[0][2])
    opp_side = 1 - side
    first = True

    for _, fr, to in ordered:
        tb = 1 << to
        new_self = ((my ^ (1 << fr)) | tb)
        new_opp = opp & ~tb

        if first:
            score = -negamax(new_opp, new_self, opp_side, depth - 1, -beta, -alpha, 1)
            first = False
        else:
            score = -negamax(new_opp, new_self, opp_side, depth - 1, -alpha - 1, -alpha, 1)
            if alpha < score < beta:
                score = -negamax(new_opp, new_self, opp_side, depth - 1, -beta, -alpha, 1)

        if score > best:
            best = score
            best_move = (fr, to)

        if score > alpha:
            alpha = score

    return best, best_move


# ---------- Emergency legal fallback ----------

def emergency_legal_move(
    me: list[tuple[int, int]],
    opp: list[tuple[int, int]],
    color: str,
) -> tuple[tuple[int, int], tuple[int, int]]:
    my_set = set(me)
    opp_set = set(opp)
    occ = my_set | opp_set

    side = _to_side(color)
    goal_row = 7 if side == WHITE else 0
    dr = 1 if side == WHITE else -1

    best_move = None
    best_key = None

    for r, c in me:
        nr = r + dr
        if not (0 <= nr < 8):
            continue

        # forward
        if (nr, c) not in occ:
            cap = False
            win = (nr == goal_row)
            key = (win, cap, nr if side == WHITE else -nr, CENTER_COL[c])
            mv = ((r, c), (nr, c))
            if best_key is None or key > best_key:
                best_key = key
                best_move = mv

        # diag left
        nc = c - 1
        if nc >= 0 and (nr, nc) not in my_set:
            cap = (nr, nc) in opp_set
            win = (nr == goal_row) or (cap and len(opp) == 1)
            key = (win, cap, nr if side == WHITE else -nr, CENTER_COL[nc])
            mv = ((r, c), (nr, nc))
            if best_key is None or key > best_key:
                best_key = key
                best_move = mv

        # diag right
        nc = c + 1
        if nc < 8 and (nr, nc) not in my_set:
            cap = (nr, nc) in opp_set
            win = (nr == goal_row) or (cap and len(opp) == 1)
            key = (win, cap, nr if side == WHITE else -nr, CENTER_COL[nc])
            mv = ((r, c), (nr, nc))
            if best_key is None or key > best_key:
                best_key = key
                best_move = mv

    if best_move is not None:
        return best_move

    # Should not happen on valid non-terminal states.
    if me:
        r, c = me[0]
        nr = max(0, min(7, r + dr))
        return ((r, c), (nr, c))
    return ((0, 0), (0, 0))


# ---------- Required API ----------

def policy(
    me: list[tuple[int, int]],
    opp: list[tuple[int, int]],
    color: str,
) -> tuple[tuple[int, int], tuple[int, int]]:
    try:
        side = _to_side(color)
        my_bb = _bb_from_list(me)
        opp_bb = _bb_from_list(opp)

        if len(TT) > 300000:
            TT.clear()

        # Reset killers each move; history and TT can still help across calls.
        for i in range(MAX_KILLER_PLY):
            KILLERS[i] = (None, None)

        root_moves = ordered_moves(my_bb, opp_bb, side, None, 0)
        if not root_moves:
            return emergency_legal_move(me, opp, color)

        # Immediate winning move?
        single_opp = (opp_bb.bit_count() == 1)
        for _, fr, to in root_moves:
            tb = 1 << to
            if (tb & GOAL_MASK[side]) or (single_opp and (opp_bb & tb)):
                return _decode_move(fr, to)

        if len(root_moves) == 1:
            return _decode_move(root_moves[0][1], root_moves[0][2])

        # If opponent has an immediate win, restrict to moves that stop all immediate wins if possible.
        opp_side = 1 - side
        candidate_moves = root_moves
        if has_immediate_win(opp_bb, my_bb, opp_side):
            safe_moves: list[tuple[int, int, int]] = []
            for mv in root_moves:
                _, fr, to = mv
                tb = 1 << to
                new_self = ((my_bb ^ (1 << fr)) | tb)
                new_opp = opp_bb & ~tb
                if not has_immediate_win(new_opp, new_self, opp_side):
                    safe_moves.append(mv)
            if safe_moves:
                candidate_moves = safe_moves

        best_move = (candidate_moves[0][1], candidate_moves[0][2])
        best_score = -INF

        total_pieces = len(me) + len(opp)
        if total_pieces <= 6:
            max_depth = 24
        elif total_pieces <= 10:
            max_depth = 14
        else:
            max_depth = 8

        global DEADLINE, NODES
        DEADLINE = time.perf_counter() + 0.92
        NODES = 0

        for depth in range(1, max_depth + 1):
            if time.perf_counter() >= DEADLINE:
                break
            try:
                score, mv = search_root(my_bb, opp_bb, side, depth, candidate_moves, best_move)
                best_score = score
                best_move = mv
                if best_score >= WIN_SCORE // 2:
                    break
            except TimeoutError:
                break

        return _decode_move(best_move[0], best_move[1])

    except Exception:
        return emergency_legal_move(me, opp, color)
