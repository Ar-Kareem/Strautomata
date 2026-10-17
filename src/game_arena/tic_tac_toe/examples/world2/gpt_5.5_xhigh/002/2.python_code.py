
from __future__ import annotations

import time


# 4x4 board indexing:
#  0  1  2  3
#  4  5  6  7
#  8  9 10 11
# 12 13 14 15

ALL_MASK = (1 << 16) - 1

WIN_MASKS = (
    # rows
    0b0000000000001111,
    0b0000000011110000,
    0b0000111100000000,
    0b1111000000000000,
    # columns
    (1 << 0) | (1 << 4) | (1 << 8) | (1 << 12),
    (1 << 1) | (1 << 5) | (1 << 9) | (1 << 13),
    (1 << 2) | (1 << 6) | (1 << 10) | (1 << 14),
    (1 << 3) | (1 << 7) | (1 << 11) | (1 << 15),
    # diagonals
    (1 << 0) | (1 << 5) | (1 << 10) | (1 << 15),
    (1 << 3) | (1 << 6) | (1 << 9) | (1 << 12),
)

CELL_LINES = [[] for _ in range(16)]
for _line in WIN_MASKS:
    for _i in range(16):
        if _line & (1 << _i):
            CELL_LINES[_i].append(_line)

# Positional preference: cells on diagonals have 3 winning lines.
POS_WEIGHTS = (
    9, 4, 4, 9,
    4, 10, 10, 4,
    4, 10, 10, 4,
    9, 4, 4, 9,
)

PREFERRED_ORDER = (
    5, 10, 6, 9,
    0, 3, 12, 15,
    1, 2, 4, 7, 8, 11, 13, 14,
)

LINE_WEIGHTS = (0, 6, 45, 650, 1000000)

WIN_SCORE = 1_000_000
INF = 10_000_000

# Precomputed tables for fast line checks.
WIN_TABLE = [False] * (1 << 16)
COMPLETE_TABLE = [0] * (1 << 16)
POS_SUM = [0] * (1 << 16)

for mask in range(1 << 16):
    win = False
    completions = 0
    for line in WIN_MASKS:
        cnt = (mask & line).bit_count()
        if cnt == 4:
            win = True
        elif cnt == 3:
            completions |= line & ~mask
    WIN_TABLE[mask] = win
    COMPLETE_TABLE[mask] = completions & ALL_MASK

for mask in range(1, 1 << 16):
    bit = mask & -mask
    idx = bit.bit_length() - 1
    POS_SUM[mask] = POS_SUM[mask ^ bit] + POS_WEIGHTS[idx]


_TT: dict[int, int] = {}
_DEADLINE = 0.0
_NODES = 0


class _Timeout(Exception):
    pass


def _win_moves(player_mask: int, empty: int) -> int:
    """Empty squares where player can immediately complete a 4-line."""
    return COMPLETE_TABLE[player_mask] & empty


def _parse_board(board: list[list[int]]) -> tuple[int, int]:
    mine = 0
    opp = 0
    for r in range(4):
        row = board[r]
        base = 4 * r
        for c in range(4):
            v = row[c]
            bit = 1 << (base + c)
            if v == 1:
                mine |= bit
            elif v == -1:
                opp |= bit
    return mine, opp


def _fallback(board: list[list[int]]) -> tuple[int, int]:
    """Guaranteed legal fallback if at least one empty cell exists."""
    for r in range(4):
        for c in range(4):
            try:
                if board[r][c] == 0:
                    return (r, c)
            except Exception:
                pass
    return (0, 0)


def _best_from_bits(bits: int, smask: int, omask: int, empty: int) -> int:
    """Choose the best move index from a bitset of legal candidate squares."""
    best_m = -1
    best_s = -INF
    b = bits & empty
    while b:
        bit = b & -b
        m = bit.bit_length() - 1
        s = _move_order_score(m, bit, smask, omask, empty)
        if s > best_s:
            best_s = s
            best_m = m
        b ^= bit
    if best_m >= 0:
        return best_m
    return _first_empty_index(empty)


def _first_empty_index(empty: int) -> int:
    for m in PREFERRED_ORDER:
        if empty & (1 << m):
            return m
    bit = empty & -empty
    return bit.bit_length() - 1


def _fork_count(player_mask: int, empty: int, limit: int = 3) -> int:
    """Number of moves that create at least two distinct immediate wins."""
    count = 0
    b = empty
    while b:
        bit = b & -b
        if (_win_moves(player_mask | bit, empty ^ bit)).bit_count() >= 2:
            count += 1
            if count >= limit:
                return count
        b ^= bit
    return count


def _find_winning_fork(smask: int, omask: int, empty: int) -> int | None:
    """Return a move that creates an unavoidable double threat, if one exists."""
    best_m = None
    best_s = -INF

    # If opponent already has an immediate win, a fork is not enough unless it blocks;
    # immediate blocks are handled before this function is called.
    if _win_moves(omask, empty):
        return None

    for m in _ordered_moves(smask, omask, empty):
        bit = 1 << m
        new_empty = empty ^ bit
        if WIN_TABLE[smask | bit]:
            return m
        if (_win_moves(smask | bit, new_empty)).bit_count() >= 2:
            s = _move_order_score(m, bit, smask, omask, empty)
            if s > best_s:
                best_s = s
                best_m = m

    return best_m


def _move_order_score(m: int, bit: int, smask: int, omask: int, empty: int) -> int:
    """High score means search this move earlier."""
    new_s = smask | bit
    new_empty = empty ^ bit

    if WIN_TABLE[new_s]:
        return 9_000_000

    score = POS_WEIGHTS[m] * 120

    # Blocking an existing immediate opponent win is critical.
    if bit & _win_moves(omask, empty):
        score += 1_000_000

    # Creating threats/forks is very strong.
    my_threats = (_win_moves(new_s, new_empty)).bit_count()
    if my_threats >= 2:
        score += 750_000
    elif my_threats == 1:
        score += 35_000

    # Occupying a square where opponent would create a fork is valuable defense.
    opp_if_here = omask | bit
    opp_threats_if_here = (_win_moves(opp_if_here, new_empty)).bit_count()
    if opp_threats_if_here >= 2:
        score += 90_000
    elif opp_threats_if_here == 1:
        score += 4_000

    # Local line building and blocking.
    for line in CELL_LINES[m]:
        s_before = (smask & line).bit_count()
        o_before = (omask & line).bit_count()
        s_after = s_before + 1

        if o_before == 0:
            score += (0, 25, 260, 6000, 0)[s_after]

        # Defensive credit for blocking opponent's clean line.
        if s_before == 0 and o_before > 0:
            score += (0, 20, 230, 7000, 0)[o_before]

    return score


def _ordered_moves(smask: int, omask: int, empty: int, preferred: int = -1) -> list[int]:
    # If there is exactly one immediate opponent win, non-blocking moves lose.
    opp_wins = _win_moves(omask, empty)
    if opp_wins and opp_wins.bit_count() == 1 and not _win_moves(smask, empty):
        return [opp_wins.bit_length() - 1]

    scored = []
    b = empty
    while b:
        bit = b & -b
        m = bit.bit_length() - 1
        s = _move_order_score(m, bit, smask, omask, empty)
        if m == preferred:
            s += 2_000_000
        scored.append((s, m))
        b ^= bit

    scored.sort(reverse=True)
    return [m for _, m in scored]


def _evaluate(smask: int, omask: int, empty: int) -> int:
    """Static evaluation from the side-to-move perspective."""
    score = 0

    for line in WIN_MASKS:
        s = (smask & line).bit_count()
        o = (omask & line).bit_count()

        if o == 0:
            score += LINE_WEIGHTS[s]
        elif s == 0:
            score -= LINE_WEIGHTS[o]

    score += 4 * (POS_SUM[smask] - POS_SUM[omask])

    # Fork potential is expensive but useful in the smaller mid/endgame.
    if empty.bit_count() <= 11:
        score += 120 * _fork_count(smask, empty)
        score -= 145 * _fork_count(omask, empty)

    return score


def _check_time() -> None:
    global _NODES
    _NODES += 1
    if (_NODES & 2047) == 0 and time.perf_counter() > _DEADLINE:
        raise _Timeout()


def _tt_key(smask: int, omask: int, depth: int) -> int:
    return smask | (omask << 16) | (depth << 32)


def _negamax(smask: int, omask: int, empty: int, depth: int, alpha: int, beta: int) -> int:
    _check_time()

    # Previous player has already won.
    if WIN_TABLE[omask]:
        return -WIN_SCORE - depth

    if empty == 0:
        return 0

    # Current side can win immediately.
    if _win_moves(smask, empty):
        return WIN_SCORE + depth

    opp_wins = _win_moves(omask, empty)
    opp_win_count = opp_wins.bit_count()

    # Cannot block two distinct immediate wins.
    if opp_win_count >= 2:
        return -WIN_SCORE - depth

    key = _tt_key(smask, omask, depth)
    cached = _TT.get(key)
    if cached is not None:
        return cached

    # Quiescence: even at depth 0, forced single-threat blocks are resolved.
    if depth <= 0:
        if opp_win_count == 1:
            bit = opp_wins & -opp_wins
            val = -_negamax(omask, smask | bit, empty ^ bit, 0, -beta, -alpha)
        else:
            val = _evaluate(smask, omask, empty)
        _TT[key] = val
        return val

    # Forced block.
    if opp_win_count == 1:
        bit = opp_wins & -opp_wins
        val = -_negamax(omask, smask | bit, empty ^ bit, depth - 1, -beta, -alpha)
        _TT[key] = val
        return val

    best = -INF
    searched_all = True

    for m in _ordered_moves(smask, omask, empty):
        bit = 1 << m
        val = -_negamax(omask, smask | bit, empty ^ bit, depth - 1, -beta, -alpha)

        if val > best:
            best = val
        if val > alpha:
            alpha = val
        if alpha >= beta:
            searched_all = False
            break

    if searched_all:
        _TT[key] = best

    return best


def _heuristic_move(smask: int, omask: int, empty: int) -> int:
    my_wins = _win_moves(smask, empty)
    if my_wins:
        return _best_from_bits(my_wins, smask, omask, empty)

    opp_wins = _win_moves(omask, empty)
    if opp_wins:
        return _best_from_bits(opp_wins, smask, omask, empty)

    fork = _find_winning_fork(smask, omask, empty)
    if fork is not None:
        return fork

    moves = _ordered_moves(smask, omask, empty)
    return moves[0] if moves else _first_empty_index(empty)


def _root_search(smask: int, omask: int, empty: int, depth: int, preferred: int) -> tuple[int, int]:
    my_wins = _win_moves(smask, empty)
    if my_wins:
        m = _best_from_bits(my_wins, smask, omask, empty)
        return m, WIN_SCORE + depth

    opp_wins = _win_moves(omask, empty)
    if opp_wins.bit_count() == 1:
        moves = [opp_wins.bit_length() - 1]
    else:
        moves = _ordered_moves(smask, omask, empty, preferred)

    best_m = preferred
    best_v = -INF
    alpha = -INF
    beta = INF

    for m in moves:
        bit = 1 << m
        v = -_negamax(omask, smask | bit, empty ^ bit, depth - 1, -beta, -alpha)

        if v > best_v:
            best_v = v
            best_m = m
        if v > alpha:
            alpha = v

    return best_m, best_v


def _search_best(smask: int, omask: int, empty: int, fallback: int) -> int:
    global _DEADLINE, _NODES, _TT

    # Keep memory bounded across many games.
    if len(_TT) > 400_000:
        _TT.clear()

    best = fallback
    empties = empty.bit_count()

    # Conservative time budget under the 1 second limit.
    _DEADLINE = time.perf_counter() + 0.86

    # Full search is feasible in the late game; early game uses as many
    # completed iterative-deepening depths as the budget permits.
    max_depth = empties

    for depth in range(1, max_depth + 1):
        _NODES = 0
        try:
            m, v = _root_search(smask, omask, empty, depth, best)
            if empty & (1 << m):
                best = m

            # A forced win found by search/tactics is already decisive.
            if v >= WIN_SCORE // 2:
                break

            if time.perf_counter() > _DEADLINE:
                break
        except _Timeout:
            break

    return best


def policy(board: list[list[int]]) -> tuple[int, int]:
    try:
        smask, omask = _parse_board(board)
        empty = ALL_MASK & ~(smask | omask)

        if empty == 0:
            return _fallback(board)

        # Opening: take a highly connected central diagonal square.
        if smask == 0 and omask == 0 and (empty & (1 << 5)):
            return (1, 1)

        # Immediate tactics first.
        my_wins = _win_moves(smask, empty)
        if my_wins:
            m = _best_from_bits(my_wins, smask, omask, empty)
            return (m // 4, m % 4)

        opp_wins = _win_moves(omask, empty)
        if opp_wins:
            m = _best_from_bits(opp_wins, smask, omask, empty)
            return (m // 4, m % 4)

        fork = _find_winning_fork(smask, omask, empty)
        if fork is not None and (empty & (1 << fork)):
            return (fork // 4, fork % 4)

        fallback_move = _heuristic_move(smask, omask, empty)
        best = _search_best(smask, omask, empty, fallback_move)

        if empty & (1 << best):
            return (best // 4, best % 4)

        return _fallback(board)

    except Exception:
        return _fallback(board)
