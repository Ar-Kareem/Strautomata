
from __future__ import annotations

import time

WIDTH = 7
HEIGHT = 6
H1 = HEIGHT + 1
SIZE = WIDTH * HEIGHT
KEY_SHIFT = WIDTH * H1

ORDER = (3, 2, 4, 1, 5, 0, 6)

BOTTOM_MASKS = tuple(1 << (c * H1) for c in range(WIDTH))
TOP_MASKS = tuple(1 << (c * H1 + HEIGHT - 1) for c in range(WIDTH))
COL_MASKS = tuple(((1 << HEIGHT) - 1) << (c * H1) for c in range(WIDTH))

BOTTOM_ALL = sum(BOTTOM_MASKS)
BOARD_MASK = sum(COL_MASKS)

INF = 10**9
WIN = 10**6

LINE_WEIGHTS = (0, 4, 20, 120, 100000)
OPP_LINE_WEIGHTS = (0, 5, 24, 145, 100000)
COLUMN_BONUS = (3, 4, 5, 7, 5, 4, 3)

EXACT = 0
LOWER = 1
UPPER = 2

_deadline = 0.0
_nodes = 0
_tt: dict[int, tuple[int, int, int, int]] = {}


class _Timeout(Exception):
    pass


def _make_line_masks() -> tuple[int, ...]:
    masks = []
    directions = ((1, 0), (0, 1), (1, 1), (-1, 1))  # vertical, horizontal, diagonals

    for r in range(HEIGHT):
        for c in range(WIDTH):
            for dr, dc in directions:
                m = 0
                ok = True
                for k in range(4):
                    rr = r + dr * k
                    cc = c + dc * k
                    if rr < 0 or rr >= HEIGHT or cc < 0 or cc >= WIDTH:
                        ok = False
                        break
                    m |= 1 << (cc * H1 + rr)
                if ok:
                    masks.append(m)

    return tuple(masks)


LINE_MASKS = _make_line_masks()


def _possible(mask: int) -> int:
    """Lowest empty cell in each non-full column."""
    return (mask + BOTTOM_ALL) & BOARD_MASK


def _winning_position(position: int, mask: int) -> int:
    """All empty board cells that would complete four for position."""
    r = (position << 1) & (position << 2) & (position << 3)

    p = (position << H1) & (position << (2 * H1))
    r |= p & (position << (3 * H1))
    r |= p & (position >> H1)
    p = (position >> H1) & (position >> (2 * H1))
    r |= p & (position << H1)
    r |= p & (position >> (3 * H1))

    p = (position << HEIGHT) & (position << (2 * HEIGHT))
    r |= p & (position << (3 * HEIGHT))
    r |= p & (position >> HEIGHT)
    p = (position >> HEIGHT) & (position >> (2 * HEIGHT))
    r |= p & (position << HEIGHT)
    r |= p & (position >> (3 * HEIGHT))

    d = HEIGHT + 2
    p = (position << d) & (position << (2 * d))
    r |= p & (position << (3 * d))
    r |= p & (position >> d)
    p = (position >> d) & (position >> (2 * d))
    r |= p & (position << d)
    r |= p & (position >> (3 * d))

    return r & (BOARD_MASK ^ mask)


def _non_losing_bits(pos: int, mask: int) -> int:
    """
    Legal moves that do not allow the opponent to win immediately.
    Based on the standard Connect-4 bitboard forced-move test.
    """
    possible = _possible(mask)
    opponent = pos ^ mask
    opponent_win = _winning_position(opponent, mask)

    forced = possible & opponent_win
    if forced:
        # If opponent has two distinct immediate winning squares, one move cannot block both.
        if forced & (forced - 1):
            return 0
        possible = forced

    # Do not play directly below an opponent future winning square.
    return possible & ~(opponent_win >> 1)


def _bit_to_col(bits: int) -> int:
    bit = bits & -bits
    if not bit:
        return -1
    return (bit.bit_length() - 1) // H1


def _choose_col(bits: int) -> int:
    for c in ORDER:
        if bits & COL_MASKS[c]:
            return c
    return -1


def _ordered_cols(bits: int, preferred: int = -1) -> list[int]:
    cols: list[int] = []
    if 0 <= preferred < WIDTH and (bits & COL_MASKS[preferred]):
        cols.append(preferred)
    for c in ORDER:
        if c != preferred and (bits & COL_MASKS[c]):
            cols.append(c)
    return cols


def _heuristic(pos: int, mask: int) -> int:
    """Static evaluation from the side-to-move's perspective."""
    opp = pos ^ mask
    score = 0

    # Positional column control, especially the center.
    for c, w in enumerate(COLUMN_BONUS):
        cm = COL_MASKS[c]
        score += w * ((pos & cm).bit_count() - (opp & cm).bit_count())

    # Evaluate every length-4 window.
    for lm in LINE_MASKS:
        mine = pos & lm
        theirs = opp & lm

        if mine and theirs:
            continue
        if mine:
            score += LINE_WEIGHTS[mine.bit_count()]
        elif theirs:
            score -= OPP_LINE_WEIGHTS[theirs.bit_count()]

    # Threat potential.
    my_threats = _winning_position(pos, mask)
    opp_threats = _winning_position(opp, mask)
    score += 35 * (my_threats.bit_count() - opp_threats.bit_count())

    possible = _possible(mask)

    # Playable opponent threats are urgent.
    opp_playable = opp_threats & possible
    n_opp = opp_playable.bit_count()
    if n_opp > 1:
        score -= 20000
    elif n_opp == 1:
        score -= 700

    my_playable = my_threats & possible
    score += 700 * my_playable.bit_count()

    return score


def _check_time() -> None:
    global _nodes
    _nodes += 1
    if (_nodes & 2047) == 0 and time.perf_counter() > _deadline:
        raise _Timeout()


def _negamax(pos: int, mask: int, depth: int, alpha: int, beta: int) -> int:
    _check_time()

    possible = _possible(mask)
    if possible == 0:
        return 0

    # Current player can win immediately.
    if _winning_position(pos, mask) & possible:
        return WIN + depth

    # If every move loses immediately, this node is tactically lost.
    moves_bits = _non_losing_bits(pos, mask)
    if not moves_bits:
        return -WIN - depth

    if depth <= 0:
        return _heuristic(pos, mask)

    key = pos | (mask << KEY_SHIFT)
    entry = _tt.get(key)
    tt_col = entry[3] if entry is not None else -1

    if entry is not None and entry[0] == depth:
        _, flag, val, _ = entry
        if flag == EXACT:
            return val
        if flag == LOWER:
            alpha = max(alpha, val)
        elif flag == UPPER:
            beta = min(beta, val)
        if alpha >= beta:
            return val

    orig_alpha = alpha
    orig_beta = beta

    best = -INF
    best_col = -1
    next_pos = pos ^ mask

    for col in _ordered_cols(moves_bits, tt_col):
        bit = possible & COL_MASKS[col]
        if not bit:
            continue

        val = -_negamax(next_pos, mask | bit, depth - 1, -beta, -alpha)

        if val > best:
            best = val
            best_col = col
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    if best_col < 0:
        return _heuristic(pos, mask)

    if best <= orig_alpha:
        flag = UPPER
    elif best >= orig_beta:
        flag = LOWER
    else:
        flag = EXACT

    old = _tt.get(key)
    if old is None or depth >= old[0]:
        _tt[key] = (depth, flag, best, best_col)

    return best


def _root_search(pos: int, mask: int, depth: int, preferred: int) -> tuple[int, int]:
    if time.perf_counter() > _deadline:
        raise _Timeout()

    possible = _possible(mask)
    if possible == 0:
        return -1, 0

    win_bits = _winning_position(pos, mask) & possible
    if win_bits:
        return _choose_col(win_bits), WIN + depth

    moves_bits = _non_losing_bits(pos, mask)
    if not moves_bits:
        # Lost tactically, but still must choose a legal move.
        moves_bits = possible

    best_col = _choose_col(moves_bits)
    best = -INF
    alpha = -INF
    next_pos = pos ^ mask

    for col in _ordered_cols(moves_bits, preferred):
        if time.perf_counter() > _deadline:
            raise _Timeout()

        bit = possible & COL_MASKS[col]
        if not bit:
            continue

        val = -_negamax(next_pos, mask | bit, depth - 1, -INF, -alpha)

        if val > best:
            best = val
            best_col = col
        if val > alpha:
            alpha = val

    return best_col, best


def policy(board: list[list[int]]) -> int:
    global _deadline, _nodes, _tt

    try:
        pos = 0
        mask = 0

        # Convert input board to bitboards.
        # Bit rows count upward from the bottom.
        for r in range(HEIGHT):
            br = HEIGHT - 1 - r
            row = board[r]
            for c in range(WIDTH):
                v = row[c]
                if v:
                    bit = 1 << (c * H1 + br)
                    mask |= bit
                    if v == 1:
                        pos |= bit

        legal_bits = _possible(mask)
        if not legal_bits:
            return 0

        fallback = _choose_col(legal_bits)
        if fallback < 0:
            fallback = 0

        # Empty-board opening: center is strongest.
        if mask == 0 and (legal_bits & COL_MASKS[3]):
            return 3

        # Win immediately if possible.
        my_win = _winning_position(pos, mask) & legal_bits
        if my_win:
            move = _choose_col(my_win)
            if move >= 0 and board[0][move] == 0:
                return int(move)

        # If opponent has exactly one immediate win, block it.
        opp = pos ^ mask
        opp_win = _winning_position(opp, mask) & legal_bits
        if opp_win and not (opp_win & (opp_win - 1)):
            move = _bit_to_col(opp_win)
            if 0 <= move < WIDTH and board[0][move] == 0:
                return int(move)

        # Prefer a non-losing fallback even if search times out.
        safe_bits = _non_losing_bits(pos, mask)
        if safe_bits:
            safe_move = _choose_col(safe_bits)
            if safe_move >= 0:
                fallback = safe_move

        _deadline = time.perf_counter() + 0.86
        _nodes = 0
        _tt = {}

        remaining = SIZE - mask.bit_count()
        if remaining <= 12:
            max_depth = remaining
        elif remaining <= 18:
            max_depth = 14
        else:
            max_depth = 12

        best = fallback
        preferred = fallback

        for depth in range(1, max_depth + 1):
            if time.perf_counter() > _deadline:
                break
            try:
                move, score = _root_search(pos, mask, depth, preferred)
                if 0 <= move < WIDTH and (legal_bits & COL_MASKS[move]):
                    best = move
                    preferred = move

                # A proven tactical win inside the searched tree.
                if score >= WIN:
                    break
            except _Timeout:
                break

        if 0 <= best < WIDTH and board[0][best] == 0:
            return int(best)

        # Final legality fail-safe.
        for c in ORDER:
            if board[0][c] == 0:
                return int(c)
        for c in range(WIDTH):
            if board[0][c] == 0:
                return int(c)

        return 0

    except Exception:
        # Absolute fail-safe: never fail to return a column if one is open.
        try:
            for c in ORDER:
                if board[0][c] == 0:
                    return int(c)
            for c in range(WIDTH):
                if board[0][c] == 0:
                    return int(c)
        except Exception:
            pass
        return 0
