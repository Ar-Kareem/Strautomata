
import time

# 3x3x3 Tic Tac Toe policy.
# Board values: 1 = us, -1 = opponent, 0 = empty.

_INF = 10 ** 9
_WIN = 10 ** 7
_ALL = (1 << 27) - 1

_DEADLINE = 0.0
_NODES = 0
_TT = {}
_TT_LIMIT = 250000


def _idx(i, j, k):
    return i * 9 + j * 3 + k


def _inside(i, j, k):
    return 0 <= i < 3 and 0 <= j < 3 and 0 <= k < 3


def _build_lines():
    dirs = []
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            for dk in (-1, 0, 1):
                if di == 0 and dj == 0 and dk == 0:
                    continue
                # Canonical direction: first non-zero component is positive.
                if di > 0 or (di == 0 and dj > 0) or (di == 0 and dj == 0 and dk > 0):
                    dirs.append((di, dj, dk))

    lines = []
    seen = set()
    for i in range(3):
        for j in range(3):
            for k in range(3):
                for di, dj, dk in dirs:
                    i2, j2, k2 = i + 2 * di, j + 2 * dj, k + 2 * dk
                    if _inside(i2, j2, k2):
                        mask = 0
                        for t in range(3):
                            mask |= 1 << _idx(i + t * di, j + t * dj, k + t * dk)
                        if mask not in seen:
                            seen.add(mask)
                            lines.append(mask)
    return lines


_LINES = _build_lines()

_CELL_LINES = [[] for _ in range(27)]
for _lm in _LINES:
    _m = _lm
    while _m:
        _b = _m & -_m
        _CELL_LINES[_b.bit_length() - 1].append(_lm)
        _m -= _b

_CELL_VALUE = []
for _p in range(27):
    i, j, k = _p // 9, (_p // 3) % 3, _p % 3
    value = 10 * len(_CELL_LINES[_p])
    if _p == 13:  # absolute center
        value += 40
    if i in (0, 2) and j in (0, 2) and k in (0, 2):  # corners
        value += 6
    _CELL_VALUE.append(value)


def _iter_bits(mask):
    while mask:
        b = mask & -mask
        yield b
        mask -= b


def _bit_to_move(bit):
    p = bit.bit_length() - 1
    return (p // 9, (p // 3) % 3, p % 3)


def _has_win(mask):
    for lm in _LINES:
        if mask & lm == lm:
            return True
    return False


def _winning_moves(own, other):
    """Return bitmask of empty cells where 'own' can win immediately."""
    empty = _ALL ^ (own | other)
    result = 0
    for lm in _LINES:
        if lm & other:
            continue
        e = lm & empty
        # In a 3-cell line with no opponent stones, exactly one empty means
        # exactly two own stones.
        if e and (e & (e - 1)) == 0:
            result |= e
    return result


def _pos_sum(mask):
    s = 0
    while mask:
        b = mask & -mask
        s += _CELL_VALUE[b.bit_length() - 1]
        mask -= b
    return s


def _evaluate(x, o, side=1):
    """Static score from our perspective. Positive is good for us."""
    if _has_win(x):
        return _WIN
    if _has_win(o):
        return -_WIN

    score = 0

    for lm in _LINES:
        xb = x & lm
        ob = o & lm
        if xb and ob:
            continue

        if xb:
            c = xb.bit_count()
            if c == 2:
                score += 220
            elif c == 1:
                score += 18
        elif ob:
            c = ob.bit_count()
            if c == 2:
                score -= 250
            elif c == 1:
                score -= 20

    score += 4 * _pos_sum(x)
    score -= 4 * _pos_sum(o)

    xt = _winning_moves(x, o).bit_count()
    ot = _winning_moves(o, x).bit_count()

    if xt >= 2:
        score += 800000 + 5000 * xt
    elif xt == 1:
        score += 600 if side == 1 else 150

    if ot >= 2:
        score -= 800000 + 5500 * ot
    elif ot == 1:
        score -= 650 if side == -1 else 170

    return score


def _move_order_score(bit, own, other):
    p = bit.bit_length() - 1
    score = _CELL_VALUE[p]

    for lm in _CELL_LINES[p]:
        oc = (own & lm).bit_count()
        pc = (other & lm).bit_count()

        if pc == 0:
            if oc == 2:
                score += 1000000
            elif oc == 1:
                score += 400
            else:
                score += 30

        if oc == 0:
            if pc == 2:
                score += 900000
            elif pc == 1:
                score += 160

    # Prefer moves that create immediate threats, especially forks.
    t = _winning_moves(own | bit, other).bit_count()
    if t >= 2:
        score += 200000 + 10000 * t
    elif t == 1:
        score += 1500

    # Prefer occupying a square where the opponent would create a fork.
    if _winning_moves(other | bit, own).bit_count() >= 2:
        score += 25000

    return score


def _ordered_moves(x, o, side):
    empty = _ALL ^ (x | o)
    if not empty:
        return []

    if side == 1:
        own, other = x, o
    else:
        own, other = o, x

    own_win = _winning_moves(own, other)
    if own_win:
        legal = own_win & empty
    else:
        opp_win = _winning_moves(other, own)
        if opp_win:
            # If opponent has an immediate threat, legal sensible moves are blocks.
            legal = opp_win & empty
        else:
            legal = empty

    moves = list(_iter_bits(legal))
    moves.sort(key=lambda b: _move_order_score(b, own, other), reverse=True)
    return moves


def _best_from_mask(mask, x, o, side=1):
    empty = _ALL ^ (x | o)
    mask &= empty
    if not mask:
        return _first_empty_bit(empty)

    if side == 1:
        own, other = x, o
    else:
        own, other = o, x

    best = 0
    best_score = -_INF
    for b in _iter_bits(mask):
        s = _move_order_score(b, own, other)
        if s > best_score:
            best_score = s
            best = b
    return best


def _first_empty_bit(empty):
    if not empty:
        return 0
    center = 1 << 13
    if empty & center:
        return center

    best = 0
    best_score = -1
    for b in _iter_bits(empty):
        p = b.bit_length() - 1
        if _CELL_VALUE[p] > best_score:
            best_score = _CELL_VALUE[p]
            best = b
    return best


def _fork_moves(own, other):
    empty = _ALL ^ (own | other)
    result = 0
    for b in _iter_bits(empty):
        if _winning_moves(own | b, other).bit_count() >= 2:
            result |= b
    return result


def _search(x, o, side, depth, alpha, beta):
    global _NODES

    _NODES += 1
    if (_NODES & 2047) == 0 and time.perf_counter() > _DEADLINE:
        raise TimeoutError

    if _has_win(x):
        return _WIN + depth
    if _has_win(o):
        return -_WIN - depth

    empty = _ALL ^ (x | o)
    if not empty:
        return 0

    if side == 1:
        own, other = x, o
    else:
        own, other = o, x

    # If the player to move can win immediately, this node is effectively won.
    own_win = _winning_moves(own, other)
    if own_win:
        return (_WIN + depth) if side == 1 else (-_WIN - depth)

    # If the opponent has two distinct immediate winning cells, one move cannot
    # parry both, so this node is effectively lost.
    opp_win = _winning_moves(other, own)
    if opp_win.bit_count() > 1:
        return (-_WIN - depth) if side == 1 else (_WIN + depth)

    if depth <= 0:
        return _evaluate(x, o, side)

    key = (x, o, side, depth)
    if key in _TT:
        return _TT[key]

    moves = _ordered_moves(x, o, side)
    if not moves:
        return _evaluate(x, o, side)

    cut = False

    if side == 1:
        best = -_INF
        for b in moves:
            v = _search(x | b, o, -1, depth - 1, alpha, beta)
            if v > best:
                best = v
            if best > alpha:
                alpha = best
            if alpha >= beta:
                cut = True
                break
    else:
        best = _INF
        for b in moves:
            v = _search(x, o | b, 1, depth - 1, alpha, beta)
            if v < best:
                best = v
            if best < beta:
                beta = best
            if alpha >= beta:
                cut = True
                break

    # Store only exact values, not cutoff bounds.
    if not cut and len(_TT) < _TT_LIMIT:
        _TT[key] = best

    return best


def _heuristic_move(x, o):
    empty = _ALL ^ (x | o)
    if not empty:
        return 0

    # Immediate tactical rules.
    wm = _winning_moves(x, o)
    if wm:
        return _best_from_mask(wm, x, o, 1)

    om = _winning_moves(o, x)
    if om:
        return _best_from_mask(om, x, o, 1)

    center = 1 << 13
    if (x | o).bit_count() <= 1 and (empty & center):
        return center

    fm = _fork_moves(x, o)
    if fm:
        return _best_from_mask(fm, x, o, 1)

    moves = _ordered_moves(x, o, 1)
    if not moves:
        return _first_empty_bit(empty)

    best = moves[0]
    best_score = -_INF

    # Two-ply heuristic: choose the move whose worst opponent reply is best.
    for b in moves:
        nx = x | b
        my_threats = _winning_moves(nx, o).bit_count()

        base = _evaluate(nx, o, -1)
        if my_threats >= 2:
            base += 500000
        elif my_threats == 1:
            base += 1000

        # Bonus for blocking an opponent fork square.
        if _winning_moves(o | b, x).bit_count() >= 2:
            base += 3000

        opp_moves = _ordered_moves(nx, o, -1)
        if opp_moves:
            worst = _INF
            for ob in opp_moves:
                no = o | ob
                if _has_win(no):
                    val = -_WIN
                else:
                    val = _evaluate(nx, no, 1)
                    ot = _winning_moves(no, nx).bit_count()
                    if ot >= 2:
                        val -= 200000 + 1000 * ot
                    elif ot == 1:
                        val -= 400

                    rt = _winning_moves(nx, no).bit_count()
                    if rt:
                        val += 300 * rt

                if val < worst:
                    worst = val

            score = 0.35 * base + worst
        else:
            score = base

        if score > best_score:
            best_score = score
            best = b

    return best


def _choose_move(x, o):
    global _DEADLINE, _NODES

    empty = _ALL ^ (x | o)
    if not empty:
        return 0

    if len(_TT) > _TT_LIMIT:
        _TT.clear()

    # Hard tactical priorities.
    wm = _winning_moves(x, o)
    if wm:
        return _best_from_mask(wm, x, o, 1)

    om = _winning_moves(o, x)
    if om:
        return _best_from_mask(om, x, o, 1)

    center = 1 << 13
    total = (x | o).bit_count()
    if total <= 1 and (empty & center):
        return center

    fm = _fork_moves(x, o)
    if fm:
        return _best_from_mask(fm, x, o, 1)

    fallback = _heuristic_move(x, o)

    _DEADLINE = time.perf_counter() + 0.88
    _NODES = 0

    moves = _ordered_moves(x, o, 1)
    if not moves:
        return fallback if fallback else _first_empty_bit(empty)

    # Try the heuristic move first for stronger alpha-beta pruning.
    if fallback in moves:
        moves = [fallback] + [m for m in moves if m != fallback]

    best = fallback if fallback else moves[0]
    empties = empty.bit_count()

    for depth in range(1, empties + 1):
        try:
            if time.perf_counter() > _DEADLINE:
                break

            alpha = -_INF
            beta = _INF
            depth_best = moves[0]
            depth_best_val = -_INF

            for b in moves:
                if (_NODES & 255) == 0 and time.perf_counter() > _DEADLINE:
                    raise TimeoutError

                v = _search(x | b, o, -1, depth - 1, alpha, beta)

                if v > depth_best_val:
                    depth_best_val = v
                    depth_best = b

                if depth_best_val > alpha:
                    alpha = depth_best_val

            best = depth_best
            moves = [best] + [m for m in moves if m != best]

            if depth_best_val >= _WIN:
                break

        except TimeoutError:
            break

    if best & empty:
        return best
    if fallback & empty:
        return fallback
    return _first_empty_bit(empty)


def _masks_from_board(board):
    x = 0
    o = 0
    for i in range(3):
        for j in range(3):
            for k in range(3):
                v = board[i][j][k]
                bit = 1 << _idx(i, j, k)
                if v == 1:
                    x |= bit
                elif v == -1:
                    o |= bit
    return x, o


def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    try:
        x, o = _masks_from_board(board)
        empty = _ALL ^ (x | o)

        if empty:
            bit = _choose_move(x, o)
            if bit & empty:
                return _bit_to_move(bit)

    except Exception:
        pass

    # Absolute safety fallback: return the first legal move found.
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    return (i, j, k)

    # Should never be reached in a live game with legal moves available.
    return (0, 0, 0)
