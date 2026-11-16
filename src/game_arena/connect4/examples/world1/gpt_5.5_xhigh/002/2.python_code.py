
import time

_WIDTH = 7
_HEIGHT = 6
_H1 = _HEIGHT + 1

_INF = 10**9
_WIN_SCORE = 1_000_000
_TIME_LIMIT = 0.90

_ORDER = (3, 2, 4, 1, 5, 0, 6)

_COL_MASKS = tuple(((1 << _HEIGHT) - 1) << (c * _H1) for c in range(_WIDTH))
_BOTTOM_MASKS = tuple(1 << (c * _H1) for c in range(_WIDTH))
_TOP_MASKS = tuple(1 << (c * _H1 + _HEIGHT - 1) for c in range(_WIDTH))

_BOARD_MASK = 0
_BOTTOM_MASK = 0
for _m in _COL_MASKS:
    _BOARD_MASK |= _m
for _m in _BOTTOM_MASKS:
    _BOTTOM_MASK |= _m

_COL_WEIGHTS = (1, 2, 3, 5, 3, 2, 1)
_COLUMN_EVAL = tuple((_COL_MASKS[c], _COL_WEIGHTS[c]) for c in range(_WIDTH))
_WINDOW_WEIGHTS = (0, 2, 15, 90, 5000)

_EXACT = 0
_LOWER = 1
_UPPER = 2
_TT_LIMIT = 250000

_TT = {}
_DEADLINE = 0.0
_NODES = 0


class _SearchTimeout(Exception):
    pass


def _make_win_masks():
    masks = []
    for c in range(_WIDTH):
        for r in range(_HEIGHT):
            if c <= _WIDTH - 4:
                m = 0
                for i in range(4):
                    m |= 1 << ((c + i) * _H1 + r)
                masks.append(m)

            if r <= _HEIGHT - 4:
                m = 0
                for i in range(4):
                    m |= 1 << (c * _H1 + r + i)
                masks.append(m)

            if c <= _WIDTH - 4 and r <= _HEIGHT - 4:
                m = 0
                for i in range(4):
                    m |= 1 << ((c + i) * _H1 + r + i)
                masks.append(m)

            if c <= _WIDTH - 4 and r >= 3:
                m = 0
                for i in range(4):
                    m |= 1 << ((c + i) * _H1 + r - i)
                masks.append(m)
    return tuple(masks)


_WIN_MASKS = _make_win_masks()


def _has_won(pos):
    m = pos & (pos >> 1)
    if m & (m >> 2):
        return True

    m = pos & (pos >> 7)
    if m & (m >> 14):
        return True

    m = pos & (pos >> 6)
    if m & (m >> 12):
        return True

    m = pos & (pos >> 8)
    return bool(m & (m >> 16))


def _possible_moves(mask):
    return (mask + _BOTTOM_MASK) & _BOARD_MASK


def _winning_positions(pos, mask):
    r = (pos << 1) & (pos << 2) & (pos << 3)

    p = (pos << 7) & (pos << 14)
    r |= p & (pos << 21)
    r |= p & (pos >> 7)
    p = (pos >> 7) & (pos >> 14)
    r |= p & (pos << 7)
    r |= p & (pos >> 21)

    p = (pos << 6) & (pos << 12)
    r |= p & (pos << 18)
    r |= p & (pos >> 6)
    p = (pos >> 6) & (pos >> 12)
    r |= p & (pos << 6)
    r |= p & (pos >> 18)

    p = (pos << 8) & (pos << 16)
    r |= p & (pos << 24)
    r |= p & (pos >> 8)
    p = (pos >> 8) & (pos >> 16)
    r |= p & (pos << 8)
    r |= p & (pos >> 24)

    return r & (_BOARD_MASK ^ mask)


def _non_losing_moves(pos, mask, possible=None):
    if possible is None:
        possible = _possible_moves(mask)

    opp = mask ^ pos
    opp_wins = _winning_positions(opp, mask)

    forced = possible & opp_wins
    if forced:
        if forced & (forced - 1):
            return 0
        possible = forced

    return possible & ~(opp_wins >> 1)


def _first_col(move_mask):
    for c in _ORDER:
        if move_mask & _COL_MASKS[c]:
            return c
    return 0


def _evaluate(pos, mask):
    opp = mask ^ pos
    score = 0

    for cm, w in _COLUMN_EVAL:
        score += w * ((pos & cm).bit_count() - (opp & cm).bit_count())

    for wm in _WIN_MASKS:
        pc = (pos & wm).bit_count()
        oc = (opp & wm).bit_count()
        if oc == 0:
            score += _WINDOW_WEIGHTS[pc]
        elif pc == 0:
            score -= _WINDOW_WEIGHTS[oc]

    my_spots = _winning_positions(pos, mask)
    op_spots = _winning_positions(opp, mask)
    playable = _possible_moves(mask)

    score += 24 * (my_spots.bit_count() - op_spots.bit_count())
    score += 180 * ((my_spots & playable).bit_count())
    score -= 220 * ((op_spots & playable).bit_count())

    return score


def _negamax(pos, mask, depth, alpha, beta, ply):
    global _NODES

    _NODES += 1
    if (_NODES & 2047) == 0 and time.perf_counter() >= _DEADLINE:
        raise _SearchTimeout()

    if _has_won(mask ^ pos):
        return -_WIN_SCORE + ply

    possible = _possible_moves(mask)
    if not possible:
        return 0

    if _winning_positions(pos, mask) & possible:
        return _WIN_SCORE - ply

    safe = _non_losing_moves(pos, mask, possible)
    if not safe:
        return -_WIN_SCORE + ply

    key = pos | (mask << 49)
    tt = _TT
    entry = tt.get(key)
    tt_col = -1

    alpha_orig = alpha
    beta_orig = beta

    if entry is not None:
        e_depth, e_value, e_flag, e_col = entry
        tt_col = e_col
        if e_depth >= depth:
            if e_flag == _EXACT:
                return e_value
            if e_flag == _LOWER:
                if e_value > alpha:
                    alpha = e_value
            elif e_flag == _UPPER:
                if e_value < beta:
                    beta = e_value
            if alpha >= beta:
                return e_value

    if depth <= 0:
        val = _evaluate(pos, mask)
        if entry is None and len(tt) < _TT_LIMIT:
            tt[key] = (0, val, _EXACT, -1)
        return val

    best_val = -_INF
    best_col = -1
    next_pos = mask ^ pos
    col_masks = _COL_MASKS

    if 0 <= tt_col < _WIDTH:
        move = safe & col_masks[tt_col]
        if move:
            score = -_negamax(next_pos, mask | move, depth - 1, -beta, -alpha, ply + 1)
            best_val = score
            best_col = tt_col
            if score > alpha:
                alpha = score

    if alpha < beta:
        for c in _ORDER:
            if c == tt_col:
                continue
            move = safe & col_masks[c]
            if not move:
                continue

            score = -_negamax(next_pos, mask | move, depth - 1, -beta, -alpha, ply + 1)

            if score > best_val:
                best_val = score
                best_col = c
            if score > alpha:
                alpha = score
            if alpha >= beta:
                break

    flag = _EXACT
    if best_val <= alpha_orig:
        flag = _UPPER
    elif best_val >= beta_orig:
        flag = _LOWER

    if entry is None:
        if len(tt) < _TT_LIMIT:
            tt[key] = (depth, best_val, flag, best_col)
    elif depth >= entry[0]:
        tt[key] = (depth, best_val, flag, best_col)

    return best_val


def _root_search(pos, mask, depth, preferred_col):
    if time.perf_counter() >= _DEADLINE:
        raise _SearchTimeout()

    possible = _possible_moves(mask)
    if not possible:
        return 0, 0

    safe = _non_losing_moves(pos, mask, possible)
    moves = safe if safe else possible

    best_col = _first_col(moves)
    best_val = -_INF
    alpha = -_INF
    beta = _INF
    next_pos = mask ^ pos

    if 0 <= preferred_col < _WIDTH:
        move = moves & _COL_MASKS[preferred_col]
        if move:
            if _has_won(pos | move):
                score = _WIN_SCORE
            else:
                score = -_negamax(next_pos, mask | move, depth - 1, -beta, -alpha, 1)
            best_val = score
            best_col = preferred_col
            if score > alpha:
                alpha = score

    for c in _ORDER:
        if c == preferred_col:
            continue
        move = moves & _COL_MASKS[c]
        if not move:
            continue

        if time.perf_counter() >= _DEADLINE:
            raise _SearchTimeout()

        if _has_won(pos | move):
            score = _WIN_SCORE
        else:
            score = -_negamax(next_pos, mask | move, depth - 1, -beta, -alpha, 1)

        if score > best_val:
            best_val = score
            best_col = c
        if score > alpha:
            alpha = score

    return best_col, best_val


def policy(board: list[list[int]]) -> int:
    global _TT, _DEADLINE, _NODES

    fallback = 0
    mask = 0

    try:
        pos = 0
        mask = 0

        for r in range(_HEIGHT):
            br = _HEIGHT - 1 - r
            row = board[r]
            for c in range(_WIDTH):
                v = row[c]
                if v:
                    bit = 1 << (c * _H1 + br)
                    mask |= bit
                    if v > 0:
                        pos |= bit

        possible = _possible_moves(mask)
        if not possible:
            return 0

        fallback = _first_col(possible)

        if mask == 0 and (possible & _COL_MASKS[3]):
            return 3

        for c in _ORDER:
            move = possible & _COL_MASKS[c]
            if move and _has_won(pos | move):
                return int(c)

        safe = _non_losing_moves(pos, mask, possible)
        if safe:
            fallback = _first_col(safe)
            if safe & (safe - 1) == 0:
                return int(fallback)
        else:
            opp_immediate = _winning_positions(mask ^ pos, mask) & possible
            if opp_immediate:
                fallback = _first_col(opp_immediate)

        _TT = {}
        _NODES = 0
        _DEADLINE = time.perf_counter() + _TIME_LIMIT

        best_col = fallback
        max_depth = 42 - mask.bit_count()

        for depth in range(1, max_depth + 1):
            if time.perf_counter() >= _DEADLINE:
                break
            try:
                col, score = _root_search(pos, mask, depth, best_col)
                if 0 <= col < _WIDTH and not (mask & _TOP_MASKS[col]):
                    best_col = col
                if abs(score) >= _WIN_SCORE - 64:
                    break
            except _SearchTimeout:
                break

        if 0 <= best_col < _WIDTH and not (mask & _TOP_MASKS[best_col]):
            return int(best_col)

        return int(_first_col(possible))

    except Exception:
        try:
            for c in _ORDER:
                if board[0][c] == 0:
                    return int(c)
        except Exception:
            pass
        return int(fallback)
