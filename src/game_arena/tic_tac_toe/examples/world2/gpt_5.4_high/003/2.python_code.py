from __future__ import annotations

import time
from functools import lru_cache

FULL_MASK = (1 << 16) - 1
WIN_SCORE = 1_000_000
INF = 10**9
TIME_LIMIT = 0.93

# Positional preference: centers > corners > edges
POS_WEIGHTS = (
    6, 3, 3, 6,
    3, 7, 7, 3,
    3, 7, 7, 3,
    6, 3, 3, 6,
)
ORDER_BASE = tuple(w * 8 for w in POS_WEIGHTS)

# Heuristic scores for open lines with 1/2/3 marks.
LINE_SCORES = (0, 4, 22, 140, 0)
ATTACK_ORDER = (0, 4, 16, 120, 0)
BLOCK_ORDER = (0, 2, 10, 90, 0)

IDX_TO_RC = tuple((i // 4, i % 4) for i in range(16))

# Winning masks: 4 rows, 4 cols, 2 diagonals.
WIN_MASKS = []
for r in range(4):
    m = 0
    for c in range(4):
        m |= 1 << (4 * r + c)
    WIN_MASKS.append(m)
for c in range(4):
    m = 0
    for r in range(4):
        m |= 1 << (4 * r + c)
    WIN_MASKS.append(m)
WIN_MASKS.append((1 << 0) | (1 << 5) | (1 << 10) | (1 << 15))
WIN_MASKS.append((1 << 3) | (1 << 6) | (1 << 9) | (1 << 12))
WIN_MASKS = tuple(WIN_MASKS)

CELL_TO_LINES = [[] for _ in range(16)]
for mask in WIN_MASKS:
    m = mask
    while m:
        bit = m & -m
        m ^= bit
        CELL_TO_LINES[bit.bit_length() - 1].append(mask)
CELL_TO_LINES = tuple(tuple(v) for v in CELL_TO_LINES)

# Precompute win states for all 16-bit boards.
WIN_STATE = [False] * 65536
for b in range(65536):
    for mask in WIN_MASKS:
        if (b & mask) == mask:
            WIN_STATE[b] = True
            break

# Precompute positional sums for all 16-bit boards.
POS_SUM = [0] * 65536
for b in range(1, 65536):
    lsb = b & -b
    POS_SUM[b] = POS_SUM[b ^ lsb] + POS_WEIGHTS[lsb.bit_length() - 1]

# Transposition table: key -> (depth, flag, value, best_move_bit)
# flag: 0 exact, 1 lower bound, 2 upper bound
TT: dict[int, tuple[int, int, int, int]] = {}
HISTORY = [0] * 16

_CALL_COUNT = 0
_DEADLINE = 0.0
_NODE_COUNTER = 0


class SearchTimeout(Exception):
    pass


def has_win(bits: int) -> bool:
    return WIN_STATE[bits]


@lru_cache(maxsize=200_000)
def winning_moves_mask(player: int, other: int) -> int:
    occupied = player | other
    empties = FULL_MASK ^ occupied
    result = 0
    for mask in WIN_MASKS:
        if mask & other:
            continue
        pm = player & mask
        if pm.bit_count() == 3:
            result |= (mask ^ pm) & empties
    return result


@lru_cache(maxsize=200_000)
def evaluate(me: int, opp: int) -> int:
    score = POS_SUM[me] - POS_SUM[opp]

    for mask in WIN_MASKS:
        mc = (me & mask).bit_count()
        oc = (opp & mask).bit_count()
        if mc and oc:
            continue
        if mc:
            score += LINE_SCORES[mc]
        elif oc:
            score -= LINE_SCORES[oc]

    # Distinct immediate winning cells are very important.
    score += 150 * winning_moves_mask(me, opp).bit_count()
    score -= 170 * winning_moves_mask(opp, me).bit_count()

    return score


def order_moves(legal_mask: int, me: int, opp: int, tt_move: int = 0) -> list[int]:
    moves: list[tuple[int, int]] = []

    while legal_mask:
        bit = legal_mask & -legal_mask
        legal_mask ^= bit
        idx = bit.bit_length() - 1

        score = ORDER_BASE[idx] + HISTORY[idx]
        if bit == tt_move:
            score += 50_000

        # Prefer moves that extend our lines or block theirs.
        for mask in CELL_TO_LINES[idx]:
            mc = (me & mask).bit_count()
            oc = (opp & mask).bit_count()
            if oc == 0:
                score += ATTACK_ORDER[mc + 1]
            elif mc == 0:
                score += BLOCK_ORDER[oc]

        moves.append((score, bit))

    moves.sort(reverse=True)
    return [bit for score, bit in moves]


def negamax(me: int, opp: int, depth: int, alpha: int, beta: int) -> int:
    global _NODE_COUNTER
    _NODE_COUNTER += 1
    if (_NODE_COUNTER & 255) == 0 and time.perf_counter() >= _DEADLINE:
        raise SearchTimeout

    occupied = me | opp
    empties_mask = FULL_MASK ^ occupied
    empties_count = empties_mask.bit_count()

    # Terminal checks.
    if has_win(opp):
        return -(WIN_SCORE + empties_count)
    if has_win(me):
        return WIN_SCORE + empties_count
    if empties_mask == 0:
        return 0

    # Immediate tactical checks.
    own_wins = winning_moves_mask(me, opp)
    if own_wins:
        return WIN_SCORE + empties_count

    opp_wins = winning_moves_mask(opp, me)
    if opp_wins and (opp_wins & (opp_wins - 1)):
        # Opponent has multiple distinct immediate wins next turn.
        return -(WIN_SCORE + max(0, empties_count - 1))

    # Quiescence-like extension for forced blocks.
    if depth <= 0:
        if opp_wins:
            depth = 1
        else:
            return evaluate(me, opp)

    key = (me << 16) | opp
    entry = TT.get(key)
    tt_move = 0
    if entry is not None:
        entry_depth, flag, value, move = entry
        tt_move = move
        if entry_depth >= depth:
            if flag == 0:
                return value
            if flag == 1:
                alpha = max(alpha, value)
            else:
                beta = min(beta, value)
            if alpha >= beta:
                return value

    alpha_orig = alpha
    beta_orig = beta
    best = -INF
    best_move = 0

    # If opponent has a single immediate winning move, only blocking it matters.
    legal_mask = opp_wins if opp_wins else empties_mask

    for bit in order_moves(legal_mask, me, opp, tt_move):
        value = -negamax(opp, me | bit, depth - 1, -beta, -alpha)

        if value > best:
            best = value
            best_move = bit
        if value > alpha:
            alpha = value

        if alpha >= beta:
            idx = bit.bit_length() - 1
            if HISTORY[idx] < 100_000:
                HISTORY[idx] += depth * depth
            break

    if best <= alpha_orig:
        flag = 2
    elif best >= beta_orig:
        flag = 1
    else:
        flag = 0
    TT[key] = (depth, flag, best, best_move)

    return best


def root_search(me: int, opp: int, depth: int) -> tuple[int, int]:
    if time.perf_counter() >= _DEADLINE:
        raise SearchTimeout

    empties_mask = FULL_MASK ^ (me | opp)
    opp_wins = winning_moves_mask(opp, me)
    legal_mask = opp_wins if opp_wins else empties_mask

    key = (me << 16) | opp
    entry = TT.get(key)
    tt_move = entry[3] if entry is not None else 0

    moves = order_moves(legal_mask, me, opp, tt_move)
    best_move = moves[0]
    best = -INF
    alpha = -INF
    beta = INF

    for bit in moves:
        if time.perf_counter() >= _DEADLINE:
            raise SearchTimeout

        value = -negamax(opp, me | bit, depth - 1, -beta, -alpha)

        if value > best:
            best = value
            best_move = bit
        if value > alpha:
            alpha = value

    TT[key] = (depth, 0, best, best_move)
    return best, best_move


def policy(board: list[list[int]]) -> tuple[int, int]:
    global _CALL_COUNT, _DEADLINE, _NODE_COUNTER

    _CALL_COUNT += 1
    if (_CALL_COUNT & 63) == 0:
        for i in range(16):
            HISTORY[i] //= 2

    if len(TT) > 300_000:
        TT.clear()
        winning_moves_mask.cache_clear()
        evaluate.cache_clear()

    me = 0
    opp = 0
    empties: list[tuple[int, int, int]] = []

    for r in range(4):
        for c in range(4):
            v = board[r][c]
            bit = 1 << (4 * r + c)
            if v == 1:
                me |= bit
            elif v == -1:
                opp |= bit
            else:
                empties.append((r, c, bit))

    # Safety fallback for malformed terminal calls.
    if not empties:
        return (0, 0)

    # Opening book: one of the strongest symmetric starts.
    if len(empties) == 16:
        return (1, 1)

    if len(empties) == 1:
        return (empties[0][0], empties[0][1])

    # Immediate win always takes priority.
    own_wins = winning_moves_mask(me, opp)
    if own_wins:
        bit = order_moves(own_wins, me, opp)[0]
        idx = bit.bit_length() - 1
        return IDX_TO_RC[idx]

    empties_mask = FULL_MASK ^ (me | opp)
    key = (me << 16) | opp
    entry = TT.get(key)
    tt_move = entry[3] if entry is not None else 0
    opp_wins = winning_moves_mask(opp, me)

    # Safe always-legal fallback, used if search times out.
    fallback_mask = opp_wins if opp_wins else empties_mask
    best_bit = order_moves(fallback_mask, me, opp, tt_move)[0]

    _DEADLINE = time.perf_counter() + TIME_LIMIT
    _NODE_COUNTER = 0

    max_depth = empties_mask.bit_count()

    try:
        for depth in range(1, max_depth + 1):
            _, move = root_search(me, opp, depth)
            best_bit = move
    except SearchTimeout:
        pass

    idx = best_bit.bit_length() - 1
    r, c = IDX_TO_RC[idx]
    if board[r][c] == 0:
        return (r, c)

    # Final legal-move guard.
    for rr in range(4):
        for cc in range(4):
            if board[rr][cc] == 0:
                return (rr, cc)

    return (0, 0)
