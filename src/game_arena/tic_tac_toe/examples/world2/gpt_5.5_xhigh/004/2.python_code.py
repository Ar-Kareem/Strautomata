
from __future__ import annotations

import time

# 4x4 board, row-major bit index: bit = 1 << (4 * row + col)
_FULL = (1 << 16) - 1
_INF = 10**9
_WIN_SCORE = 1_000_000

_EXACT = 0
_LOWER = 1
_UPPER = 2

_TT: dict[tuple[int, int, int], tuple[int, int]] = {}
_DEADLINE = 0.0
_NODES = 0


class _SearchTimeout(Exception):
    pass


def _cell_bit(r: int, c: int) -> int:
    return 1 << (4 * r + c)


# Winning masks: 4 rows, 4 columns, 2 long diagonals.
_masks = []
for r in range(4):
    m = 0
    for c in range(4):
        m |= _cell_bit(r, c)
    _masks.append(m)

for c in range(4):
    m = 0
    for r in range(4):
        m |= _cell_bit(r, c)
    _masks.append(m)

m = 0
for i in range(4):
    m |= _cell_bit(i, i)
_masks.append(m)

m = 0
for i in range(4):
    m |= _cell_bit(i, 3 - i)
_masks.append(m)

_WIN_MASKS = tuple(_masks)

# Positional preference. Inner diagonal cells are slightly preferred, then corners.
_POSITION_WEIGHTS = (
    32, 22, 22, 32,
    22, 38, 38, 22,
    22, 38, 38, 22,
    32, 22, 22, 32,
)

_LINES_BY_CELL = tuple(
    tuple(line for line in _WIN_MASKS if line & (1 << i))
    for i in range(16)
)

# Fast lookup tables for wins and immediate completion cells.
_WIN_TABLE = [False] * (1 << 16)
_COMPLETE_TABLE = [0] * (1 << 16)

for bits in range(1 << 16):
    complete = 0
    won = False
    for line in _WIN_MASKS:
        count = (bits & line).bit_count()
        if count == 4:
            won = True
        elif count == 3:
            complete |= line & ~bits
    _WIN_TABLE[bits] = won
    _COMPLETE_TABLE[bits] = complete & _FULL

_POS_SUM = [0] * (1 << 16)
for bits in range(1, 1 << 16):
    b = bits & -bits
    _POS_SUM[bits] = _POS_SUM[bits ^ b] + _POSITION_WEIGHTS[b.bit_length() - 1]

_LINE_SCORE = (0, 12, 90, 1200, _WIN_SCORE)
_OPP_LINE_SCORE = (0, 14, 105, 1350, _WIN_SCORE)
_EXTEND_SCORE = (7, 40, 400, 6000)
_BLOCK_SCORE = (0, 10, 80, 900, 7000)


def _winning_moves(bits: int, other: int) -> int:
    """Empty cells where 'bits' would complete a 4-in-a-row."""
    return _COMPLETE_TABLE[bits] & (_FULL & ~(bits | other))


def _bit_to_move(bit: int) -> tuple[int, int]:
    idx = bit.bit_length() - 1
    return idx // 4, idx % 4


def _parse_board(board: list[list[int]]) -> tuple[int, int]:
    mine = 0
    theirs = 0
    for r in range(4):
        row = board[r]
        for c in range(4):
            v = row[c]
            bit = 1 << (4 * r + c)
            if v == 1:
                mine |= bit
            elif v == -1:
                theirs |= bit
    return mine, theirs


def _move_static_score(bit: int, curr: int, opp: int) -> int:
    idx = bit.bit_length() - 1
    new_curr = curr | bit
    empty_after = _FULL & ~(new_curr | opp)

    score = _POSITION_WEIGHTS[idx]

    # Winning now or blocking the opponent's possible win on this square.
    if _WIN_TABLE[new_curr]:
        score += 100_000
    if _WIN_TABLE[opp | bit]:
        score += 90_000

    my_threats = (_COMPLETE_TABLE[new_curr] & empty_after).bit_count()
    opp_threats = (_COMPLETE_TABLE[opp] & empty_after).bit_count()

    score += 1300 * my_threats
    score -= 1500 * opp_threats

    if my_threats >= 2:
        score += 8000 + 2500 * my_threats
    if opp_threats >= 2:
        score -= 9000 + 3000 * opp_threats

    for line in _LINES_BY_CELL[idx]:
        c = (curr & line).bit_count()
        o = (opp & line).bit_count()

        if o == 0:
            score += _EXTEND_SCORE[c]
        if c == 0:
            score += _BLOCK_SCORE[o]

    return score


def _best_static_bit(mask: int, curr: int, opp: int) -> int:
    best = mask & -mask
    best_score = -_INF

    m = mask
    while m:
        b = m & -m
        s = _move_static_score(b, curr, opp)
        if s > best_score:
            best_score = s
            best = b
        m ^= b

    return best


def _ordered_moves(curr: int, opp: int, moves_mask: int | None = None) -> list[int]:
    if moves_mask is None:
        moves_mask = _FULL & ~(curr | opp)

    scored = []
    m = moves_mask
    while m:
        b = m & -m
        scored.append((_move_static_score(b, curr, opp), b))
        m ^= b

    scored.sort(reverse=True)
    return [b for _, b in scored]


def _fork_moves(bits: int, other: int) -> int:
    """Moves that create at least two distinct immediate winning moves."""
    empty = _FULL & ~(bits | other)
    forks = 0

    m = empty
    while m:
        b = m & -m
        nb = bits | b
        empty_after = _FULL & ~(nb | other)
        if (_COMPLETE_TABLE[nb] & empty_after).bit_count() >= 2:
            forks |= b
        m ^= b

    return forks


def _evaluate(curr: int, opp: int) -> int:
    if _WIN_TABLE[curr]:
        return _WIN_SCORE
    if _WIN_TABLE[opp]:
        return -_WIN_SCORE

    score = _POS_SUM[curr] - _POS_SUM[opp]

    for line in _WIN_MASKS:
        c = (curr & line).bit_count()
        o = (opp & line).bit_count()

        if o == 0:
            score += _LINE_SCORE[c]
        if c == 0:
            score -= _OPP_LINE_SCORE[o]

    my_wins = _winning_moves(curr, opp).bit_count()
    opp_wins = _winning_moves(opp, curr).bit_count()

    if my_wins:
        score += 10_000 * my_wins
        if my_wins >= 2:
            score += 35_000

    if opp_wins:
        # One opponent threat is blockable; multiple threats are usually fatal.
        score -= 3500 * opp_wins
        if opp_wins >= 2:
            score -= 45_000

    return score


def _negamax(curr: int, opp: int, depth: int, alpha: int, beta: int) -> int:
    global _NODES

    _NODES += 1
    if (_NODES & 2047) == 0 and time.perf_counter() > _DEADLINE:
        raise _SearchTimeout()

    if _WIN_TABLE[opp]:
        return -_WIN_SCORE - depth
    if _WIN_TABLE[curr]:
        return _WIN_SCORE + depth

    occupied = curr | opp
    if occupied == _FULL:
        return 0

    # Tactical quiescence.
    curr_wins = _winning_moves(curr, opp)
    if curr_wins:
        return _WIN_SCORE + depth

    opp_wins = _winning_moves(opp, curr)
    opp_win_count = opp_wins.bit_count()

    # If the opponent has two separate immediate wins, this side cannot block both.
    if opp_win_count > 1:
        return -_WIN_SCORE - depth

    # At horizon, extend only forced single blocks; otherwise evaluate.
    if depth <= 0:
        if opp_win_count == 1:
            return -_negamax(opp, curr | opp_wins, 0, -beta, -alpha)
        return _evaluate(curr, opp)

    alpha_orig = alpha
    beta_orig = beta
    key = (curr, opp, depth)

    entry = _TT.get(key)
    if entry is not None:
        val, flag = entry
        if flag == _EXACT:
            return val
        if flag == _LOWER:
            alpha = max(alpha, val)
        elif flag == _UPPER:
            beta = min(beta, val)
        if alpha >= beta:
            return val

    if opp_win_count == 1:
        moves_mask = opp_wins
    else:
        moves_mask = _FULL & ~occupied

    best = -_INF

    for b in _ordered_moves(curr, opp, moves_mask):
        val = -_negamax(opp, curr | b, depth - 1, -beta, -alpha)

        if val > best:
            best = val
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    if best <= alpha_orig:
        flag = _UPPER
    elif best >= beta_orig:
        flag = _LOWER
    else:
        flag = _EXACT

    _TT[key] = (best, flag)
    return best


def policy(board: list[list[int]]) -> tuple[int, int]:
    global _DEADLINE, _NODES

    mine, theirs = _parse_board(board)
    legal = _FULL & ~(mine | theirs)

    # No legal move should occur in a live game. Return a valid-shaped fallback.
    if legal == 0:
        return (0, 0)

    if legal & (legal - 1) == 0:
        return _bit_to_move(legal)

    # If called after a terminal state, still return a legal move.
    if _WIN_TABLE[mine] or _WIN_TABLE[theirs]:
        return _bit_to_move(legal & -legal)

    # Strong deterministic opening.
    if legal == _FULL:
        return (1, 1)

    # Immediate win.
    my_wins = _winning_moves(mine, theirs) & legal
    if my_wins:
        return _bit_to_move(_best_static_bit(my_wins, mine, theirs))

    # Immediate block.
    opp_wins = _winning_moves(theirs, mine) & legal
    opp_win_count = opp_wins.bit_count()

    if opp_win_count == 1:
        return _bit_to_move(opp_wins & -opp_wins)

    if opp_win_count > 1:
        # Lost against perfect play, but block the most promising threat.
        return _bit_to_move(_best_static_bit(opp_wins, mine, theirs))

    # Forced fork win.
    forks = _fork_moves(mine, theirs)
    if forks:
        return _bit_to_move(_best_static_bit(forks, mine, theirs))

    root_moves = _ordered_moves(mine, theirs, legal)
    best_bit = root_moves[0]
    best_score = -_INF

    # Keep the transposition table bounded for long-running arenas.
    if len(_TT) > 500_000:
        _TT.clear()

    empties = legal.bit_count()
    budget = 0.86 if empties > 8 else 0.92
    _DEADLINE = time.perf_counter() + budget
    _NODES = 0

    try:
        depth = 1
        while depth <= empties:
            if time.perf_counter() > _DEADLINE:
                break

            alpha = -_INF
            local_best = root_moves[0]
            local_best_score = -_INF
            scored: list[tuple[int, int]] = []

            for b in root_moves:
                val = -_negamax(theirs, mine | b, depth - 1, -_INF, -alpha)
                scored.append((val, b))

                if val > local_best_score:
                    local_best_score = val
                    local_best = b

                if val > alpha:
                    alpha = val

            # Only accept fully completed depths.
            best_bit = local_best
            best_score = local_best_score

            scored.sort(reverse=True)
            root_moves = [b for _, b in scored]

            if best_score > _WIN_SCORE // 2:
                break

            depth += 1

    except _SearchTimeout:
        pass

    if not (best_bit & legal):
        best_bit = legal & -legal

    return _bit_to_move(best_bit)
