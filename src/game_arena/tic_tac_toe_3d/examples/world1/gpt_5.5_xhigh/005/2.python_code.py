
from __future__ import annotations

from itertools import product
from time import perf_counter

_ALL = (1 << 27) - 1
_CENTER = 13
_CENTER_BIT = 1 << _CENTER

_INF = 10**12
_WIN = 10_000_000

_TIME_LIMIT = 0.88
_TT_LIMIT = 200_000

_EXACT, _LOWER, _UPPER = 0, 1, 2

_TT = {}
_deadline = 0.0
_nodes = 0


class _Timeout(Exception):
    pass


def _idx(i, j, k):
    return i * 9 + j * 3 + k


def _coord(p):
    return (p // 9, (p // 3) % 3, p % 3)


def _inside(i, j, k):
    return 0 <= i < 3 and 0 <= j < 3 and 0 <= k < 3


def _make_lines():
    dirs = []
    for dx, dy, dz in product((-1, 0, 1), repeat=3):
        if dx == 0 and dy == 0 and dz == 0:
            continue
        for v in (dx, dy, dz):
            if v != 0:
                if v > 0:
                    dirs.append((dx, dy, dz))
                break

    lines = set()
    for dx, dy, dz in dirs:
        for i, j, k in product(range(3), repeat=3):
            if _inside(i - dx, j - dy, k - dz):
                continue

            cells = []
            ok = True
            for t in range(3):
                ni, nj, nk = i + dx * t, j + dy * t, k + dz * t
                if not _inside(ni, nj, nk):
                    ok = False
                    break
                cells.append(_idx(ni, nj, nk))

            if ok:
                lines.add(tuple(cells))

    return tuple(sorted(lines))


def _line_to_mask(line):
    m = 0
    for p in line:
        m |= 1 << p
    return m


_WIN_LINES = _make_lines()
_WIN_MASKS = tuple(_line_to_mask(line) for line in _WIN_LINES)

_tmp_cell_lines = [[] for _ in range(27)]
for _line, _mask in zip(_WIN_LINES, _WIN_MASKS):
    for _p in _line:
        _tmp_cell_lines[_p].append(_mask)

_CELL_LINES = tuple(tuple(x) for x in _tmp_cell_lines)
_POS_WEIGHT = tuple(len(_CELL_LINES[p]) for p in range(27))

_CORNERS = 0
for _i in (0, 2):
    for _j in (0, 2):
        for _k in (0, 2):
            _CORNERS |= 1 << _idx(_i, _j, _k)


def _first_index(mask):
    bit = mask & -mask
    return bit.bit_length() - 1


def _has_win(bits):
    for mask in _WIN_MASKS:
        if (bits & mask) == mask:
            return True
    return False


def _is_win_after(bits, p):
    for mask in _CELL_LINES[p]:
        if (bits & mask) == mask:
            return True
    return False


def _winning_moves(my, opp):
    """Bit mask of empty cells that complete a line for 'my'."""
    occ = my | opp
    wins = 0
    for mask in _WIN_MASKS:
        if mask & opp:
            continue
        empty = mask & ~occ
        if empty and (empty & (empty - 1)) == 0:
            wins |= empty
    return wins


def _created_threat_bits(move, my, opp):
    """Winning cells created by placing 'my' at move, excluding pre-existing threats."""
    bit = 1 << move
    occ_after = my | opp | bit
    threats = 0

    for mask in _CELL_LINES[move]:
        if mask & opp:
            continue
        if (mask & my).bit_count() == 1:
            threats |= mask & ~occ_after

    return threats


def _move_score_for_side(move, my, opp):
    bit = 1 << move
    occ_after = my | opp | bit

    score = _POS_WEIGHT[move] * 25
    if move == _CENTER:
        score += 700
    elif bit & _CORNERS:
        score += 180

    threat_bits = 0

    for mask in _CELL_LINES[move]:
        mc = (mask & my).bit_count()
        oc = (mask & opp).bit_count()

        if oc == 0:
            if mc == 2:
                score += 1_000_000
            elif mc == 1:
                score += 1_800
                threat_bits |= mask & ~occ_after
            else:
                score += 80
        elif mc == 0:
            if oc == 2:
                score += 300_000
            elif oc == 1:
                score += 300
        else:
            score -= 25

    tc = threat_bits.bit_count()
    if tc >= 2:
        score += 80_000 + 5_000 * tc
    elif tc == 1:
        score += 3_000

    return score


def _fork_moves_bits(my, opp):
    """Moves that win immediately or create at least two distinct immediate threats."""
    legal = _ALL & ~(my | opp)
    result = 0

    while legal:
        bit = legal & -legal
        move = bit.bit_length() - 1
        new_my = my | bit

        if _is_win_after(new_my, move):
            result |= bit
        elif _created_threat_bits(move, my, opp).bit_count() >= 2:
            result |= bit

        legal ^= bit

    return result


def _root_move_score(move, x, o):
    bit = 1 << move
    nx = x | bit

    score = _move_score_for_side(move, x, o)

    if _is_win_after(nx, move):
        return score + 100_000_000

    threats = _created_threat_bits(move, x, o).bit_count()
    if threats >= 2:
        score += 2_000_000 + 100_000 * threats
    elif threats == 1:
        score += 25_000

    opp_wins = _winning_moves(o, nx).bit_count()
    if opp_wins:
        score -= 2_500_000 * opp_wins

    opp_forks = _fork_moves_bits(o, nx).bit_count()
    if opp_forks:
        score -= (8_000 if threats else 40_000) * opp_forks

    return score


def _choose_best_from_mask(mask, x, o):
    legal = mask & (_ALL & ~(x | o))
    if not legal:
        legal = _ALL & ~(x | o)

    if not legal:
        return 0

    best = -1
    best_score = -_INF

    while legal:
        bit = legal & -legal
        move = bit.bit_length() - 1
        score = _root_move_score(move, x, o)

        if score > best_score:
            best_score = score
            best = move

        legal ^= bit

    return best if best >= 0 else 0


def _heuristic_move(x, o):
    legal = _ALL & ~(x | o)
    if not legal:
        return 0

    wins = _winning_moves(x, o)
    if wins:
        return _choose_best_from_mask(wins, x, o)

    blocks = _winning_moves(o, x)
    if blocks:
        return _choose_best_from_mask(blocks, x, o)

    forks = _fork_moves_bits(x, o)
    if forks:
        return _choose_best_from_mask(forks, x, o)

    if x == 0:
        if legal & _CENTER_BIT:
            return _CENTER
        corners = legal & _CORNERS
        if corners:
            return _choose_best_from_mask(corners, x, o)

    total = (x | o).bit_count()
    best = -1
    best_score = -_INF
    mask = legal

    while mask:
        bit = mask & -mask
        move = bit.bit_length() - 1
        score = _root_move_score(move, x, o)

        if move == _CENTER and total <= 4:
            score += 20_000
        elif bit & _CORNERS and total <= 4:
            score += 2_000

        if score > best_score:
            best_score = score
            best = move

        mask ^= bit

    return best if best >= 0 else _first_index(legal)


def _evaluate(x, o, side):
    score = 0

    for mask in _WIN_MASKS:
        xb = x & mask
        ob = o & mask

        if xb and ob:
            continue

        if xb:
            c = xb.bit_count()
            if c == 3:
                return _WIN
            if c == 2:
                score += 720
            else:
                score += 34
        elif ob:
            c = ob.bit_count()
            if c == 3:
                return -_WIN
            if c == 2:
                score -= 820
            else:
                score -= 38

    bits = x
    while bits:
        bit = bits & -bits
        p = bit.bit_length() - 1
        score += _POS_WEIGHT[p] * 9
        if p == _CENTER:
            score += 60
        bits ^= bit

    bits = o
    while bits:
        bit = bits & -bits
        p = bit.bit_length() - 1
        score -= _POS_WEIGHT[p] * 10
        if p == _CENTER:
            score -= 70
        bits ^= bit

    xw = _winning_moves(x, o).bit_count()
    ow = _winning_moves(o, x).bit_count()

    if xw >= 2:
        score += 12_000 + 2_000 * xw
    elif xw == 1:
        score += 2_000

    if ow >= 2:
        score -= 13_000 + 2_200 * ow
    elif ow == 1:
        score -= 2_300

    if side == 1:
        if ow == 1:
            score += 800
        if xw:
            score += 4_000 * xw
        score += 20
    else:
        if xw == 1:
            score -= 800
        if ow:
            score -= 4_200 * ow
        score -= 20

    return score


def _check_time():
    if perf_counter() >= _deadline:
        raise _Timeout()


def _ordered_root_moves(x, o, preferred):
    legal = _ALL & ~(x | o)
    scored = []

    while legal:
        bit = legal & -legal
        move = bit.bit_length() - 1
        score = _root_move_score(move, x, o)
        if move == preferred:
            score += 10_000
        scored.append((score, move))
        legal ^= bit

    scored.sort(reverse=True)
    return [move for _, move in scored]


def _ordered_moves(x, o, side, depth, tt_move):
    legal = _ALL & ~(x | o)
    if not legal:
        return [], False

    if side == 1:
        my, opp = x, o
    else:
        my, opp = o, x

    opp_wins = _winning_moves(opp, my)
    if opp_wins.bit_count() == 1:
        return [_first_index(opp_wins)], False

    scored = []
    mask = legal
    while mask:
        bit = mask & -mask
        move = bit.bit_length() - 1
        score = _move_score_for_side(move, my, opp)
        if move == tt_move:
            score += 2_000_000
        scored.append((score, move))
        mask ^= bit

    scored.sort(reverse=True)
    moves = [move for _, move in scored]

    pruned = False
    n = len(moves)
    limit = n

    if depth >= 7 and n > 14:
        limit = 14
    elif depth >= 5 and n > 18:
        limit = 18

    if limit < n:
        moves = moves[:limit]
        pruned = True

    return moves, pruned


def _alphabeta(x, o, side, depth, alpha, beta, last_move):
    global _nodes

    _nodes += 1
    if (_nodes & 2047) == 0:
        _check_time()

    if last_move >= 0:
        if side == -1:
            if _is_win_after(x, last_move):
                return _WIN + depth + 1
        else:
            if _is_win_after(o, last_move):
                return -_WIN - depth - 1

    if (x | o) == _ALL:
        return 0

    if side == 1:
        my_wins = _winning_moves(x, o)
        if my_wins:
            return _WIN + depth

        opp_wins = _winning_moves(o, x)
        if opp_wins.bit_count() >= 2:
            return -_WIN - (depth - 1 if depth > 0 else 0)
    else:
        opp_wins = _winning_moves(o, x)
        if opp_wins:
            return -_WIN - depth

        my_wins = _winning_moves(x, o)
        if my_wins.bit_count() >= 2:
            return _WIN + (depth - 1 if depth > 0 else 0)

    if depth <= 0:
        return _evaluate(x, o, side)

    key = (x, o, side, depth)
    alpha_orig, beta_orig = alpha, beta

    entry = _TT.get(key)
    tt_move = -1

    if entry is not None:
        e_depth, e_value, e_flag, e_move = entry
        tt_move = e_move

        if e_depth >= depth:
            if e_flag == _EXACT:
                return e_value
            if e_flag == _LOWER:
                alpha = max(alpha, e_value)
            elif e_flag == _UPPER:
                beta = min(beta, e_value)
            if alpha >= beta:
                return e_value

    moves, pruned = _ordered_moves(x, o, side, depth, tt_move)

    if not moves:
        return 0

    best_move = moves[0]

    if side == 1:
        value = -_INF

        for move in moves:
            bit = 1 << move
            nx = x | bit

            if _is_win_after(nx, move):
                child = _WIN + depth
            else:
                child = _alphabeta(nx, o, -1, depth - 1, alpha, beta, move)

            if child > value:
                value = child
                best_move = move

            alpha = max(alpha, value)
            if alpha >= beta:
                break
    else:
        value = _INF

        for move in moves:
            bit = 1 << move
            no = o | bit

            if _is_win_after(no, move):
                child = -_WIN - depth
            else:
                child = _alphabeta(x, no, 1, depth - 1, alpha, beta, move)

            if child < value:
                value = child
                best_move = move

            beta = min(beta, value)
            if alpha >= beta:
                break

    if not pruned and len(_TT) < _TT_LIMIT:
        if value <= alpha_orig:
            flag = _UPPER
        elif value >= beta_orig:
            flag = _LOWER
        else:
            flag = _EXACT
        _TT[key] = (depth, value, flag, best_move)

    return value


def _search_root_depth(x, o, depth, preferred):
    moves = _ordered_root_moves(x, o, preferred)
    if not moves:
        return 0, None

    alpha = -_INF
    beta = _INF
    best_move = moves[0]
    best_value = -_INF

    for n, move in enumerate(moves):
        if (n & 3) == 0:
            _check_time()

        bit = 1 << move
        nx = x | bit

        if _is_win_after(nx, move):
            value = _WIN + depth
        else:
            value = _alphabeta(nx, o, -1, depth - 1, alpha, beta, move)

        if value > best_value:
            best_value = value
            best_move = move

        alpha = max(alpha, best_value)

    return best_value, best_move


def _max_depth_for(legal_count):
    if legal_count <= 0:
        return 0
    if legal_count <= 14:
        return legal_count
    if legal_count <= 18:
        return 11
    if legal_count <= 22:
        return 8
    if legal_count <= 25:
        return 6
    return 5


def _iterative_search(x, o, fallback):
    global _TT, _deadline, _nodes

    _TT = {}
    _deadline = perf_counter() + _TIME_LIMIT
    _nodes = 0

    legal = _ALL & ~(x | o)
    max_depth = _max_depth_for(legal.bit_count())

    best = fallback

    for depth in range(1, max_depth + 1):
        try:
            _check_time()
            score, move = _search_root_depth(x, o, depth, best)
        except _Timeout:
            break

        if move is not None and (legal & (1 << move)):
            best = move

        if score >= _WIN - 1000:
            break

    return best


def _parse(board):
    x = 0
    o = 0

    for i in range(3):
        for j in range(3):
            for k in range(3):
                bit = 1 << _idx(i, j, k)
                v = board[i][j][k]
                if v == 1:
                    x |= bit
                elif v == -1:
                    o |= bit

    return x, o


def _scan_first_empty(board):
    try:
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    if board[i][j][k] == 0:
                        return (i, j, k)
    except Exception:
        pass
    return (0, 0, 0)


def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    try:
        x, o = _parse(board)
        legal = _ALL & ~(x | o)

        if not legal:
            return (0, 0, 0)

        wins = _winning_moves(x, o)
        if wins:
            return _coord(_choose_best_from_mask(wins, x, o))

        blocks = _winning_moves(o, x)
        if blocks:
            return _coord(_choose_best_from_mask(blocks, x, o))

        forks = _fork_moves_bits(x, o)
        if forks:
            return _coord(_choose_best_from_mask(forks, x, o))

        if x == 0:
            if legal & _CENTER_BIT:
                return _coord(_CENTER)
            corners = legal & _CORNERS
            if corners:
                return _coord(_choose_best_from_mask(corners, x, o))

        fallback = _heuristic_move(x, o)
        move = _iterative_search(x, o, fallback)

        if move is None or move < 0 or not (legal & (1 << move)):
            move = _first_index(legal)

        return _coord(move)

    except Exception:
        return _scan_first_empty(board)
