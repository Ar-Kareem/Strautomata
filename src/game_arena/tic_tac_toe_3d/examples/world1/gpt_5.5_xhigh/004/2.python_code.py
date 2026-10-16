
from __future__ import annotations

from time import perf_counter

_N = 3
_CELLS = 27
_FULL = (1 << _CELLS) - 1

_WIN_VALUE = 1_000_000
_INF = 1_000_000_000

_EXACT = 0
_LOWER = 1
_UPPER = 2

_TIME_LIMIT = 0.85
_QDEPTH = -6
_MAX_TT_SIZE = 250_000

_COORDS = []
_INDEX = {}
for _i in range(_N):
    for _j in range(_N):
        for _k in range(_N):
            _idx = _i * 9 + _j * 3 + _k
            _COORDS.append((_i, _j, _k))
            _INDEX[(_i, _j, _k)] = _idx

_CENTER_IDX = _INDEX[(1, 1, 1)]
_CENTER_BIT = 1 << _CENTER_IDX


def _build_win_masks():
    masks = set()

    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            for dk in (-1, 0, 1):
                if di == 0 and dj == 0 and dk == 0:
                    continue

                # Keep exactly one of direction d and -d.
                if di != 0:
                    if di < 0:
                        continue
                elif dj != 0:
                    if dj < 0:
                        continue
                elif dk < 0:
                    continue

                for i in range(_N):
                    for j in range(_N):
                        for k in range(_N):
                            mask = 0
                            ok = True
                            for t in range(_N):
                                a = i + di * t
                                b = j + dj * t
                                c = k + dk * t
                                if not (0 <= a < _N and 0 <= b < _N and 0 <= c < _N):
                                    ok = False
                                    break
                                mask |= 1 << _INDEX[(a, b, c)]
                            if ok:
                                masks.add(mask)

    return tuple(sorted(masks))


_WIN_MASKS = _build_win_masks()

_CELL_LINES = [[] for _ in range(_CELLS)]
for _line in _WIN_MASKS:
    _b = _line
    while _b:
        _m = _b & -_b
        _CELL_LINES[_m.bit_length() - 1].append(_line)
        _b ^= _m

_CELL_VALUE = []
_CORNER_INDICES = []
_CORNERS_MASK = 0

for _idx, (_i, _j, _k) in enumerate(_COORDS):
    center_coords = (1 if _i == 1 else 0) + (1 if _j == 1 else 0) + (1 if _k == 1 else 0)

    value = len(_CELL_LINES[_idx]) * 25
    if _idx == _CENTER_IDX:
        value += 300
    elif center_coords == 0:  # corner
        value += 90
        _CORNER_INDICES.append(_idx)
        _CORNERS_MASK |= 1 << _idx
    elif center_coords == 2:  # face center
        value += 40

    _CELL_VALUE.append(value)

_PREFERRED = sorted(range(_CELLS), key=lambda x: _CELL_VALUE[x], reverse=True)

_LINE_SCORE_ME = (0, 14, 260, _WIN_VALUE)
_LINE_SCORE_OPP = (0, 16, 300, _WIN_VALUE)

_TT = {}
_DEADLINE = 0.0
_NODES = 0


def _parse_board(board):
    me = 0
    opp = 0
    idx = 0
    for i in range(_N):
        for j in range(_N):
            for k in range(_N):
                v = board[i][j][k]
                if v == 1:
                    me |= 1 << idx
                elif v == -1:
                    opp |= 1 << idx
                idx += 1
    return me, opp


def _fallback_from_board(board):
    for idx in _PREFERRED:
        i, j, k = _COORDS[idx]
        try:
            if board[i][j][k] == 0:
                return (i, j, k)
        except Exception:
            pass
    return (0, 0, 0)


def _coord_from_bit(bit):
    if not bit:
        return (0, 0, 0)
    return _COORDS[bit.bit_length() - 1]


def _first_legal_bit(empties):
    for idx in _PREFERRED:
        bit = 1 << idx
        if empties & bit:
            return bit
    return empties & -empties


def _has_win(bits):
    for line in _WIN_MASKS:
        if (bits & line) == line:
            return True
    return False


def _winning_moves(player, blocker):
    """All empty cells where player completes a 3-line."""
    res = 0
    for line in _WIN_MASKS:
        if line & blocker:
            continue
        missing = line & ~player
        if missing and (missing & (missing - 1)) == 0:
            res |= missing
    return res


def _tactical_status(me, opp):
    """
    Returns (my_immediate_win_bit, opponent_immediate_win_mask).

    my_immediate_win_bit is nonzero if side-to-move can win now.
    opponent_immediate_win_mask is collected only enough to identify
    zero/one/multiple distinct threats.
    """
    opp_wins = 0
    opp_many = False

    for line in _WIN_MASKS:
        if (line & opp) == 0:
            missing = line & ~me
            if missing and (missing & (missing - 1)) == 0:
                return missing, 0

        if not opp_many and (line & me) == 0:
            missing = line & ~opp
            if missing and (missing & (missing - 1)) == 0:
                opp_wins |= missing
                if opp_wins & (opp_wins - 1):
                    opp_many = True

    return 0, opp_wins


def _fork_moves(player, blocker):
    """Moves that create at least two distinct immediate winning moves."""
    occ = player | blocker
    empties = _FULL & ~occ
    res = 0

    b = empties
    while b:
        m = b & -b
        b ^= m
        wins = _winning_moves(player | m, blocker)
        if wins & (wins - 1):
            res |= m

    return res


def _evaluate(me, opp):
    score = 0

    for line in _WIN_MASKS:
        mc = (me & line).bit_count()
        oc = (opp & line).bit_count()

        if mc and oc:
            continue
        if mc:
            score += _LINE_SCORE_ME[mc]
        elif oc:
            score -= _LINE_SCORE_OPP[oc]

    b = me
    while b:
        m = b & -b
        score += _CELL_VALUE[m.bit_length() - 1]
        b ^= m

    b = opp
    while b:
        m = b & -b
        score -= _CELL_VALUE[m.bit_length() - 1]
        b ^= m

    return score


def _move_score_idx(idx, me, opp):
    score = _CELL_VALUE[idx]

    for line in _CELL_LINES[idx]:
        if (line & opp) == 0:
            c = (line & me).bit_count()
            if c == 2:
                score += 100_000
            elif c == 1:
                score += 1_600
            else:
                score += 80

        if (line & me) == 0:
            c = (line & opp).bit_count()
            if c == 2:
                score += 95_000
            elif c == 1:
                score += 900
            else:
                score += 30

    return score


def _root_move_score_idx(idx, me, opp, opp_forks_before=0):
    m = 1 << idx
    after = me | m

    score = _move_score_idx(idx, me, opp)

    if opp_forks_before & m:
        score += 45_000

    wins_after = _winning_moves(after, opp)
    wc = wins_after.bit_count()
    if wc >= 2:
        score += 700_000 + 20_000 * wc
    elif wc == 1:
        score += 12_000

    opp_wins = _winning_moves(opp, after)
    owc = opp_wins.bit_count()
    if owc >= 2:
        score -= 700_000
    elif owc == 1:
        score -= 15_000

    opp_forks_after = _fork_moves(opp, after)
    ofc = opp_forks_after.bit_count()
    if ofc:
        score -= (55_000 if wc == 0 else 12_000) * ofc

    score += _evaluate(after, opp) // 4
    return score


def _best_from_mask(mask, me, opp):
    empties = _FULL & ~(me | opp)
    mask &= empties
    if not mask:
        return _first_legal_bit(empties)

    opp_forks = _fork_moves(opp, me)

    best = 0
    best_score = -_INF
    b = mask
    while b:
        m = b & -b
        b ^= m
        idx = m.bit_length() - 1
        s = _root_move_score_idx(idx, me, opp, opp_forks)
        if s > best_score:
            best_score = s
            best = m

    return best


def _ordered_moves(me, opp, empties, first=0):
    scored = []
    b = empties
    while b:
        m = b & -b
        b ^= m
        idx = m.bit_length() - 1
        s = _move_score_idx(idx, me, opp)
        if m == first:
            s += 10_000_000
        scored.append((s, m))

    scored.sort(reverse=True)
    return [m for _, m in scored]


def _root_ordered_moves(me, opp, empties):
    opp_forks = _fork_moves(opp, me)

    scored = []
    b = empties
    while b:
        m = b & -b
        b ^= m
        idx = m.bit_length() - 1
        scored.append((_root_move_score_idx(idx, me, opp, opp_forks), m))

    scored.sort(reverse=True)
    return [m for _, m in scored]


def _max_depth_for(empty_count):
    if empty_count <= 10:
        return empty_count
    if empty_count <= 14:
        return 10
    if empty_count <= 18:
        return 8
    if empty_count <= 22:
        return 7
    return 6


def _negamax(me, opp, depth, alpha, beta):
    global _NODES

    _NODES += 1
    if (_NODES & 2047) == 0 and perf_counter() > _DEADLINE:
        raise TimeoutError

    empties = _FULL & ~(me | opp)
    if not empties:
        return 0

    my_win, opp_wins = _tactical_status(me, opp)

    if my_win:
        return _WIN_VALUE + depth

    if opp_wins and (opp_wins & (opp_wins - 1)):
        return -_WIN_VALUE - depth

    # Quiescence: if the only legal tactical response is to block one
    # immediate threat, extend a few forced plies beyond nominal depth.
    if depth <= 0 and (not opp_wins or depth <= _QDEPTH):
        return _evaluate(me, opp)

    key = (me, opp, depth)
    entry = _TT.get(key)
    tt_move = 0

    if entry is not None:
        val, flag, tt_move = entry
        if flag == _EXACT:
            return val
        if flag == _LOWER:
            if val > alpha:
                alpha = val
        elif flag == _UPPER:
            if val < beta:
                beta = val
        if alpha >= beta:
            return val

    alpha0 = alpha
    beta0 = beta

    if opp_wins:
        moves = (opp_wins,)
    else:
        moves = _ordered_moves(me, opp, empties, tt_move)

    best = -_INF
    best_move = 0

    for m in moves:
        val = -_negamax(opp, me | m, depth - 1, -beta, -alpha)

        if val > best:
            best = val
            best_move = m

        if val > alpha:
            alpha = val

        if alpha >= beta:
            break

    if best <= alpha0:
        flag = _UPPER
    elif best >= beta0:
        flag = _LOWER
    else:
        flag = _EXACT

    _TT[key] = (best, flag, best_move)
    return best


def _iterative_search(me, opp, root_moves, max_depth):
    if not root_moves:
        return 0

    best = root_moves[0]
    order = list(root_moves)

    for depth in range(1, max_depth + 1):
        if perf_counter() > _DEADLINE:
            break

        if best in order:
            order = [best] + [m for m in order if m != best]

        alpha = -_INF
        local_best = best
        local_score = -_INF
        scored = []

        try:
            for m in order:
                val = -_negamax(opp, me | m, depth - 1, -_INF, -alpha)
                scored.append((val, m))

                if val > local_score:
                    local_score = val
                    local_best = m

                if val > alpha:
                    alpha = val

                if val >= _WIN_VALUE // 2:
                    return m

                if perf_counter() > _DEADLINE:
                    raise TimeoutError

        except TimeoutError:
            break

        best = local_best
        scored.sort(reverse=True)
        order = [m for _, m in scored]

    return best


def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    global _DEADLINE, _NODES, _TT

    try:
        me, opp = _parse_board(board)
        empties = _FULL & ~(me | opp)

        if not empties:
            return (0, 0, 0)

        if len(_TT) > _MAX_TT_SIZE:
            _TT.clear()

        if empties & (empties - 1) == 0:
            return _coord_from_bit(empties)

        # Immediate win.
        my_wins = _winning_moves(me, opp)
        if my_wins:
            move = _best_from_mask(my_wins, me, opp)
            return _coord_from_bit(move)

        # Immediate block.
        opp_wins = _winning_moves(opp, me)
        if opp_wins:
            if not (opp_wins & (opp_wins - 1)):
                return _coord_from_bit(opp_wins)
            move = _best_from_mask(opp_wins, me, opp)
            return _coord_from_bit(move)

        my_count = me.bit_count()
        opp_count = opp.bit_count()
        total = my_count + opp_count

        # Opening: center is the strongest first claim; if opponent already
        # owns center and we have no stones, take a corner.
        if total == 0:
            return _COORDS[_CENTER_IDX]

        if my_count == 0 and total == 1:
            if empties & _CENTER_BIT:
                return _COORDS[_CENTER_IDX]
            corner_empties = _CORNERS_MASK & empties
            move = _best_from_mask(corner_empties if corner_empties else empties, me, opp)
            return _coord_from_bit(move)

        # If we can create a two-threat fork now, it is a forced win.
        forks = _fork_moves(me, opp)
        if forks:
            move = _best_from_mask(forks, me, opp)
            return _coord_from_bit(move)

        _NODES = 0
        _DEADLINE = perf_counter() + _TIME_LIMIT

        root_moves = _root_ordered_moves(me, opp, empties)
        if not root_moves:
            move = _first_legal_bit(empties)
            return _coord_from_bit(move)

        max_depth = _max_depth_for(empties.bit_count())
        move = _iterative_search(me, opp, root_moves, max_depth)

        if not move or not (move & empties):
            move = _first_legal_bit(empties)

        return _coord_from_bit(move)

    except Exception:
        return _fallback_from_board(board)
