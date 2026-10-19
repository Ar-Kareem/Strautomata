
from time import perf_counter
from typing import List, Tuple

# --- Constants and precomputation ---

FULL_MASK = (1 << 16) - 1
INF = 10 ** 9
WIN_SCORE = 10 ** 6

EXACT = 0
LOWER = 1
UPPER = 2

# Preferred cells:
# inner diagonal cells first, then corners, then edges
PREFERRED_ORDER = [5, 6, 9, 10, 0, 3, 12, 15, 1, 2, 4, 7, 8, 11, 13, 14]

POS_WEIGHTS = [
    6, 3, 3, 6,
    3, 7, 7, 3,
    3, 7, 7, 3,
    6, 3, 3, 6,
]

WIN_MASKS = []

# Rows
for r in range(4):
    m = 0
    for c in range(4):
        m |= 1 << (r * 4 + c)
    WIN_MASKS.append(m)

# Cols
for c in range(4):
    m = 0
    for r in range(4):
        m |= 1 << (r * 4 + c)
    WIN_MASKS.append(m)

# Diagonals
WIN_MASKS.append((1 << 0) | (1 << 5) | (1 << 10) | (1 << 15))
WIN_MASKS.append((1 << 3) | (1 << 6) | (1 << 9) | (1 << 12))
WIN_MASKS = tuple(WIN_MASKS)

CELL_MASKS = [[] for _ in range(16)]
for mask in WIN_MASKS:
    for i in range(16):
        if mask & (1 << i):
            CELL_MASKS[i].append(mask)
CELL_MASKS = tuple(tuple(x) for x in CELL_MASKS)

# Precompute win lookup for all 16-bit states
IS_WIN = [False] * (1 << 16)
for s in range(1 << 16):
    for wm in WIN_MASKS:
        if (s & wm) == wm:
            IS_WIN[s] = True
            break

# Precompute positional score for all 16-bit states
PSUM = [0] * (1 << 16)
for s in range(1, 1 << 16):
    lsb = s & -s
    idx = lsb.bit_length() - 1
    PSUM[s] = PSUM[s ^ lsb] + POS_WEIGHTS[idx]

# Transposition table: key = (me_bits, opp_bits, extended_flag)
# value = (depth, flag, score, best_move)
TT = {}
TT_MAX = 300000

_deadline = 0.0
_nodes = 0


class _Timeout(Exception):
    pass


def _move_to_tuple(mv: int) -> Tuple[int, int]:
    return (mv // 4, mv % 4)


def _first_empty_from_occ(occ: int) -> int:
    for mv in PREFERRED_ORDER:
        if not (occ & (1 << mv)):
            return mv
    return 0


def _winning_moves(player: int, other: int) -> List[int]:
    occ = player | other
    res = []
    for mv in PREFERRED_ORDER:
        bit = 1 << mv
        if not (occ & bit) and IS_WIN[player | bit]:
            res.append(mv)
    return res


def _count_immediate_wins(player: int, other: int) -> int:
    occ = player | other
    cnt = 0
    for mv in PREFERRED_ORDER:
        bit = 1 << mv
        if not (occ & bit) and IS_WIN[player | bit]:
            cnt += 1
    return cnt


def _evaluate(me: int, opp: int) -> int:
    # Base positional score
    score = PSUM[me] - PSUM[opp]

    # Open-line scores
    # Blocked lines are worth 0
    for mask in WIN_MASKS:
        mc = (me & mask).bit_count()
        oc = (opp & mask).bit_count()
        if mc and oc:
            continue
        if mc:
            if mc == 1:
                score += 4
            elif mc == 2:
                score += 18
            elif mc == 3:
                score += 120
        elif oc:
            if oc == 1:
                score -= 4
            elif oc == 2:
                score -= 18
            elif oc == 3:
                score -= 120

    return score


def _has_open_three(me: int, opp: int) -> bool:
    for mask in WIN_MASKS:
        mc = (me & mask).bit_count()
        oc = (opp & mask).bit_count()
        if (oc == 0 and mc == 3) or (mc == 0 and oc == 3):
            return True
    return False


def _ordered_moves(me: int, opp: int, tt_move: int = None) -> List[int]:
    occ = me | opp
    scored = []

    for mv in PREFERRED_ORDER:
        bit = 1 << mv
        if occ & bit:
            continue

        total = POS_WEIGHTS[mv]
        if tt_move == mv:
            total += 50000

        win_now = 0
        block3 = 0
        create3 = 0
        extend2 = 0
        block2 = 0

        for mask in CELL_MASKS[mv]:
            mc = (me & mask).bit_count()
            oc = (opp & mask).bit_count()

            if oc == 0:
                if mc == 3:
                    win_now = 1
                elif mc == 2:
                    create3 += 1
                elif mc == 1:
                    extend2 += 1

            if mc == 0:
                if oc == 3:
                    block3 += 1
                elif oc == 2:
                    block2 += 1

        total += 100000 * win_now
        total += 9000 * block3
        total += 1800 * create3
        total += 2500 if create3 >= 2 else 0
        total += 100 * extend2
        total += 80 * block2

        scored.append((total, mv))

    scored.sort(reverse=True)
    return [mv for _, mv in scored]


def _negamax(me: int, opp: int, depth: int, alpha: int, beta: int, ply: int, extended: bool) -> int:
    global _nodes, _deadline

    _nodes += 1
    if (_nodes & 255) == 0 and perf_counter() >= _deadline:
        raise _Timeout

    # If opponent already won on previous move, current side loses
    if IS_WIN[opp]:
        return -WIN_SCORE + ply

    occ = me | opp
    if occ == FULL_MASK:
        return 0

    if depth == 0:
        if not extended and _has_open_three(me, opp):
            depth = 1
            extended = True
        else:
            return _evaluate(me, opp)

    key = (me, opp, 1 if extended else 0)
    entry = TT.get(key)

    orig_alpha = alpha
    orig_beta = beta
    tt_move = None

    if entry is not None:
        e_depth, e_flag, e_score, e_move = entry
        tt_move = e_move
        if e_depth >= depth:
            if e_flag == EXACT:
                return e_score
            elif e_flag == LOWER:
                if e_score > alpha:
                    alpha = e_score
            else:  # UPPER
                if e_score < beta:
                    beta = e_score
            if alpha >= beta:
                return e_score

    best_score = -INF
    best_move = None

    for mv in _ordered_moves(me, opp, tt_move):
        bit = 1 << mv
        score = -_negamax(opp, me | bit, depth - 1, -beta, -alpha, ply + 1, extended)

        if score > best_score:
            best_score = score
            best_move = mv

        if score > alpha:
            alpha = score

        if alpha >= beta:
            break

    if best_move is None:
        return _evaluate(me, opp)

    if best_score <= orig_alpha:
        flag = UPPER
    elif best_score >= orig_beta:
        flag = LOWER
    else:
        flag = EXACT

    TT[key] = (depth, flag, best_score, best_move)
    return best_score


def _search_root(me: int, opp: int, depth: int) -> Tuple[int, int]:
    key = (me, opp, 0)
    entry = TT.get(key)
    tt_move = entry[3] if entry is not None else None

    moves = _ordered_moves(me, opp, tt_move)
    best_move = moves[0]
    best_score = -INF

    alpha = -INF
    beta = INF

    for mv in moves:
        bit = 1 << mv
        score = -_negamax(opp, me | bit, depth - 1, -beta, -alpha, 1, False)

        if score > best_score:
            best_score = score
            best_move = mv

        if score > alpha:
            alpha = score

    TT[key] = (depth, EXACT, best_score, best_move)
    return best_move, best_score


def _tactical_fallback(me: int, opp: int) -> int:
    occ = me | opp
    empties = [mv for mv in PREFERRED_ORDER if not (occ & (1 << mv))]
    if not empties:
        return 0

    opp_wins = set(_winning_moves(opp, me))

    best_mv = empties[0]
    best_score = -10**18

    for mv in empties:
        bit = 1 << mv
        new_me = me | bit

        my_next = _count_immediate_wins(new_me, opp)
        opp_next = _count_immediate_wins(opp, new_me)

        create3 = 0
        block3 = 0
        extend2 = 0
        block2 = 0

        for mask in CELL_MASKS[mv]:
            mc = (me & mask).bit_count()
            oc = (opp & mask).bit_count()

            if oc == 0:
                if mc == 2:
                    create3 += 1
                elif mc == 1:
                    extend2 += 1

            if mc == 0:
                if oc == 3:
                    block3 += 1
                elif oc == 2:
                    block2 += 1

        score = 0
        score += 2500 * my_next
        score -= 3000 * opp_next
        score += 1500 * block3
        score += 500 * create3
        score += 80 * extend2
        score += 70 * block2
        score += POS_WEIGHTS[mv]
        if mv in opp_wins:
            score += 1200

        if score > best_score:
            best_score = score
            best_mv = mv

    return best_mv


def _policy_impl(board: List[List[int]]) -> Tuple[int, int]:
    global _deadline, _nodes, TT

    if len(TT) > TT_MAX:
        TT.clear()

    me = 0
    opp = 0
    for r in range(4):
        row = board[r]
        for c in range(4):
            v = row[c]
            bit = 1 << (r * 4 + c)
            if v == 1:
                me |= bit
            elif v == -1:
                opp |= bit

    occ = me | opp

    # Always provide a legal move if possible
    if occ == FULL_MASK:
        return (0, 0)

    # If the position is already terminal/invalid, just return any legal move
    if IS_WIN[me] or IS_WIN[opp]:
        return _move_to_tuple(_first_empty_from_occ(occ))

    my_wins = _winning_moves(me, opp)
    if my_wins:
        return _move_to_tuple(my_wins[0])

    opp_wins = _winning_moves(opp, me)
    if len(opp_wins) == 1:
        return _move_to_tuple(opp_wins[0])

    # If the opponent has multiple immediate wins, this is effectively lost;
    # still return a strong legal fallback immediately.
    fallback = _tactical_fallback(me, opp)
    if len(opp_wins) > 1:
        return _move_to_tuple(fallback)

    best_move = fallback

    _deadline = perf_counter() + 0.92
    _nodes = 0

    empties = 16 - occ.bit_count()

    # Iterative deepening. If time runs out, use the last completed result.
    for depth in range(1, empties + 1):
        try:
            mv, _ = _search_root(me, opp, depth)
            best_move = mv
        except _Timeout:
            break

    return _move_to_tuple(best_move)


def policy(board: List[List[int]]) -> Tuple[int, int]:
    try:
        return _policy_impl(board)
    except Exception:
        # Emergency legal fallback
        for r in range(4):
            for c in range(4):
                if board[r][c] == 0:
                    return (r, c)
        return (0, 0)
