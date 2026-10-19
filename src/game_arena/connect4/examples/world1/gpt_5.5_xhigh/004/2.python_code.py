
from __future__ import annotations

import time as _time

_ROWS = 6
_COLS = 7
_H1 = _ROWS + 1  # one sentinel bit per column
_ORDER = (3, 2, 4, 1, 5, 0, 6)
_ORDERINGS = (_ORDER,) + tuple(
    (c,) + tuple(x for x in _ORDER if x != c) for c in range(_COLS)
)

_BOTTOM_MASKS = tuple(1 << (c * _H1) for c in range(_COLS))
_BOTTOM_ALL = sum(_BOTTOM_MASKS)
_COL_MASKS = tuple(((1 << _ROWS) - 1) << (c * _H1) for c in range(_COLS))
_BOARD_MASK = sum(_COL_MASKS)

_CENTER_MASK = _COL_MASKS[3]
_NEAR_CENTER_MASK = _COL_MASKS[2] | _COL_MASKS[4]

_WIN_SCORE = 1_000_000
_INF = 1_000_000_000
_TIME_LIMIT = 0.88
_TIME_CHECK_MASK = 511
_TT_LIMIT = 180_000
_KEY_SHIFT = _COLS * _H1

_EXACT = 0
_LOWER = 1
_UPPER = 2


class _SearchTimeout(Exception):
    pass


def _make_win_masks() -> tuple[int, ...]:
    masks = []

    # Horizontal
    for r in range(_ROWS):
        for c in range(_COLS - 3):
            m = 0
            for i in range(4):
                m |= 1 << ((c + i) * _H1 + r)
            masks.append(m)

    # Vertical
    for c in range(_COLS):
        for r in range(_ROWS - 3):
            m = 0
            for i in range(4):
                m |= 1 << (c * _H1 + r + i)
            masks.append(m)

    # Diagonal up-right
    for c in range(_COLS - 3):
        for r in range(_ROWS - 3):
            m = 0
            for i in range(4):
                m |= 1 << ((c + i) * _H1 + r + i)
            masks.append(m)

    # Diagonal down-right
    for c in range(_COLS - 3):
        for r in range(3, _ROWS):
            m = 0
            for i in range(4):
                m |= 1 << ((c + i) * _H1 + r - i)
            masks.append(m)

    return tuple(masks)


_WIN_MASKS = _make_win_masks()
_LINE_WEIGHTS = (0, 2, 18, 120, 100_000)
_OPP_LINE_WEIGHTS = (0, 3, 22, 145, 100_000)


def _possible_moves(mask: int) -> int:
    return (mask + _BOTTOM_ALL) & _BOARD_MASK


def _winning_position(position: int, mask: int) -> int:
    """Empty cells that would complete four for position."""
    r = (position << 1) & (position << 2) & (position << 3)

    d = _H1
    p = (position << d) & (position << (2 * d))
    r |= p & (position << (3 * d))
    r |= p & (position >> d)
    p = (position >> d) & (position >> (2 * d))
    r |= p & (position << d)
    r |= p & (position >> (3 * d))

    d = _H1 - 1
    p = (position << d) & (position << (2 * d))
    r |= p & (position << (3 * d))
    r |= p & (position >> d)
    p = (position >> d) & (position >> (2 * d))
    r |= p & (position << d)
    r |= p & (position >> (3 * d))

    d = _H1 + 1
    p = (position << d) & (position << (2 * d))
    r |= p & (position << (3 * d))
    r |= p & (position >> d)
    p = (position >> d) & (position >> (2 * d))
    r |= p & (position << d)
    r |= p & (position >> (3 * d))

    return r & (_BOARD_MASK & ~mask)


def _can_win_next(position: int, mask: int) -> int:
    return _winning_position(position, mask) & _possible_moves(mask)


def _possible_non_losing_moves(current: int, opponent: int, mask: int) -> int:
    """Legal moves that do not allow the opponent to win immediately."""
    possible = _possible_moves(mask)
    opponent_wins = _winning_position(opponent, mask)

    forced = possible & opponent_wins
    if forced:
        if forced & (forced - 1):
            return 0
        possible = forced

    return possible & ~(opponent_wins >> 1)


def _parse_board(board):
    current = 0
    opponent = 0

    for r in range(_ROWS):
        bit_row = _ROWS - 1 - r
        row = board[r]
        for c in range(_COLS):
            v = row[c]
            if v > 0:
                current |= 1 << (c * _H1 + bit_row)
            elif v < 0:
                opponent |= 1 << (c * _H1 + bit_row)

    return current, opponent, current | opponent


def _is_legal_on_board(board, col: int) -> bool:
    try:
        if col < 0 or col >= _COLS:
            return False
        for r in range(_ROWS):
            if board[r][col] == 0:
                return True
    except Exception:
        return False
    return False


def _safe_fallback(board) -> int:
    for c in _ORDER:
        if _is_legal_on_board(board, c):
            return c
    return 0


def _first_col_from_bits(bits: int) -> int:
    for c in _ORDER:
        if bits & _COL_MASKS[c]:
            return c
    return -1


def _evaluate(current: int, opponent: int, mask: int) -> int:
    score = 0

    score += 10 * (
        (current & _CENTER_MASK).bit_count()
        - (opponent & _CENTER_MASK).bit_count()
    )
    score += 4 * (
        (current & _NEAR_CENTER_MASK).bit_count()
        - (opponent & _NEAR_CENTER_MASK).bit_count()
    )

    possible = _possible_moves(mask)
    current_wins = _winning_position(current, mask)
    opponent_wins = _winning_position(opponent, mask)

    current_playable = current_wins & possible
    opponent_playable = opponent_wins & possible

    if current_playable:
        score += 9000 * current_playable.bit_count()

    if opponent_playable:
        if opponent_playable & (opponent_playable - 1):
            score -= 60_000
        else:
            score -= 9000

    score += 35 * current_wins.bit_count()
    score -= 45 * opponent_wins.bit_count()

    for line in _WIN_MASKS:
        cc = (current & line).bit_count()
        oc = (opponent & line).bit_count()
        if cc and oc:
            continue
        if cc:
            score += _LINE_WEIGHTS[cc]
        elif oc:
            score -= _OPP_LINE_WEIGHTS[oc]

    return score


def policy(board: list[list[int]]) -> int:
    fallback = _safe_fallback(board)

    try:
        current, opponent, mask = _parse_board(board)
        legal_bits = _possible_moves(mask)

        if legal_bits == 0:
            return int(fallback)

        legal_col = _first_col_from_bits(legal_bits)
        if _is_legal_on_board(board, legal_col):
            fallback = legal_col

        if legal_bits & (legal_bits - 1) == 0:
            only = _first_col_from_bits(legal_bits)
            if _is_legal_on_board(board, only):
                return int(only)

        # Immediate win.
        win_bits = _can_win_next(current, mask)
        if win_bits:
            col = _first_col_from_bits(win_bits)
            if _is_legal_on_board(board, col):
                return int(col)

        # Tactical fallback: prefer moves that do not lose instantly.
        nonlose_bits = _possible_non_losing_moves(current, opponent, mask)
        if nonlose_bits:
            col = _first_col_from_bits(nonlose_bits)
            if _is_legal_on_board(board, col):
                fallback = col
        else:
            block_bits = _can_win_next(opponent, mask)
            if block_bits:
                col = _first_col_from_bits(block_bits)
                if _is_legal_on_board(board, col):
                    fallback = col

        # Opening rule: center is strongest and avoids wasting time on empty/near-empty boards.
        if mask.bit_count() <= 1 and _is_legal_on_board(board, 3):
            return 3

        root_move_bits = nonlose_bits if nonlose_bits else legal_bits
        remaining = _ROWS * _COLS - mask.bit_count()

        perf_counter = _time.perf_counter
        deadline = perf_counter() + _TIME_LIMIT

        can_win_next = _can_win_next
        possible_non_losing = _possible_non_losing_moves
        evaluate = _evaluate
        col_masks = _COL_MASKS
        orderings = _ORDERINGS
        win_score = _WIN_SCORE
        inf = _INF

        tt = {}
        nodes = 0

        def negamax(cur: int, opp: int, msk: int, depth: int,
                    alpha: int, beta: int, ply: int) -> int:
            nonlocal nodes

            nodes += 1
            if (nodes & _TIME_CHECK_MASK) == 0 and perf_counter() >= deadline:
                raise _SearchTimeout

            if msk == _BOARD_MASK:
                return 0

            if can_win_next(cur, msk):
                return win_score - ply

            if depth <= 0:
                if possible_non_losing(cur, opp, msk) == 0:
                    return -win_score + ply + 1
                return evaluate(cur, opp, msk)

            alpha_orig = alpha
            beta_orig = beta
            key = cur | (opp << _KEY_SHIFT)
            entry = tt.get(key)
            tt_col = -1

            if entry is not None:
                e_depth, e_flag, e_value, e_col = entry
                tt_col = e_col

                if e_depth >= depth:
                    if e_flag == _EXACT:
                        return e_value
                    if e_flag == _LOWER:
                        if e_value > alpha:
                            alpha = e_value
                    else:
                        if e_value < beta:
                            beta = e_value
                    if alpha >= beta:
                        return e_value

            moves = possible_non_losing(cur, opp, msk)
            if moves == 0:
                return -win_score + ply + 1

            best_value = -inf
            best_col = -1
            ordering = orderings[tt_col + 1] if 0 <= tt_col < _COLS else orderings[0]
            next_depth = depth - 1
            next_ply = ply + 1

            for c in ordering:
                move = moves & col_masks[c]
                if not move:
                    continue

                new_cur = cur | move
                new_mask = msk | move
                value = -negamax(
                    opp, new_cur, new_mask,
                    next_depth, -beta, -alpha, next_ply
                )

                if value > best_value:
                    best_value = value
                    best_col = c

                if value > alpha:
                    alpha = value
                    if alpha >= beta:
                        break

            if best_col < 0:
                return 0

            if best_value <= alpha_orig:
                flag = _UPPER
            elif best_value >= beta_orig:
                flag = _LOWER
            else:
                flag = _EXACT

            if len(tt) < _TT_LIMIT:
                tt[key] = (depth, flag, best_value, best_col)

            return best_value

        def root_search(depth: int, first_col: int) -> tuple[int, int]:
            if perf_counter() >= deadline:
                raise _SearchTimeout

            alpha = -inf
            beta = inf
            best_value = -inf
            best_col = -1
            ordering = orderings[first_col + 1] if 0 <= first_col < _COLS else orderings[0]

            for c in ordering:
                move = root_move_bits & col_masks[c]
                if not move:
                    continue

                if perf_counter() >= deadline:
                    raise _SearchTimeout

                new_current = current | move
                new_mask = mask | move
                value = -negamax(
                    opponent, new_current, new_mask,
                    depth - 1, -beta, -alpha, 1
                )

                if value > best_value:
                    best_value = value
                    best_col = c

                if value > alpha:
                    alpha = value

                if best_value > win_score // 2:
                    break

            return best_value, best_col

        best_col = fallback
        best_score = -inf

        for depth in range(1, remaining + 1):
            if perf_counter() >= deadline:
                break

            try:
                value, col = root_search(depth, best_col)
            except _SearchTimeout:
                break

            if col >= 0 and _is_legal_on_board(board, col):
                best_col = col
                best_score = value

            if best_score > win_score // 2:
                break

        if _is_legal_on_board(board, best_col):
            return int(best_col)

        return int(fallback)

    except Exception:
        return int(fallback)
