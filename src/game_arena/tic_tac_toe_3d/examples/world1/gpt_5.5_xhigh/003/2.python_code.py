
import time

_ALL_MASK = (1 << 27) - 1
_WIN_SCORE = 1_000_000
_INF = 1_000_000_000
_TIME_LIMIT = 0.82
_TT_LIMIT = 160_000

_EXACT = 0
_LOWER = 1
_UPPER = 2


def _idx(i, j, k):
    return i * 9 + j * 3 + k


def _coords(p):
    return (p // 9, (p // 3) % 3, p % 3)


def _build_lines():
    dirs = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == 0 and dy == 0 and dz == 0:
                    continue
                # Keep one direction from each opposite pair.
                if dx < 0 or (dx == 0 and dy < 0) or (dx == 0 and dy == 0 and dz < 0):
                    continue
                dirs.append((dx, dy, dz))

    masks = set()
    for dx, dy, dz in dirs:
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    pi, pj, pk = i - dx, j - dy, k - dz
                    if 0 <= pi < 3 and 0 <= pj < 3 and 0 <= pk < 3:
                        continue

                    cells = []
                    x, y, z = i, j, k
                    while 0 <= x < 3 and 0 <= y < 3 and 0 <= z < 3:
                        cells.append(_idx(x, y, z))
                        x += dx
                        y += dy
                        z += dz

                    if len(cells) == 3:
                        m = 0
                        for c in cells:
                            m |= 1 << c
                        masks.add(m)

    return tuple(sorted(masks))


_LINES = _build_lines()
_CELL_LINES = tuple(tuple(m for m in _LINES if m & (1 << p)) for p in range(27))

_CENTER = _idx(1, 1, 1)
_CENTER_BIT = 1 << _CENTER

_CORNERS_MASK = 0
for _i in (0, 2):
    for _j in (0, 2):
        for _k in (0, 2):
            _CORNERS_MASK |= 1 << _idx(_i, _j, _k)


def _make_values():
    vals = []
    for p in range(27):
        i, j, k = _coords(p)
        dist = abs(i - 1) + abs(j - 1) + abs(k - 1)
        is_corner = (i != 1 and j != 1 and k != 1)

        val = len(_CELL_LINES[p]) * 100 - dist * 6
        if p == _CENTER:
            val += 60
        if is_corner:
            val += 18
        vals.append(val)

    order = tuple(sorted(range(27), key=lambda q: (-vals[q], q)))
    return tuple(vals), order


_POS_VALUES, _BASE_ORDER = _make_values()


def _first_legal(board):
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    return (i, j, k)
    return (0, 0, 0)


def _bits_from_board(board):
    my = 0
    opp = 0
    for i in range(3):
        for j in range(3):
            for k in range(3):
                v = board[i][j][k]
                b = 1 << _idx(i, j, k)
                if v == 1:
                    my |= b
                elif v == -1:
                    opp |= b
    return my, opp


def _mask_to_index(mask):
    return (mask & -mask).bit_length() - 1


def _has_win(bits):
    for m in _LINES:
        if (bits & m) == m:
            return True
    return False


def _winning_moves(bits, occ):
    """All empty cells that immediately complete a line for bits."""
    wins = 0
    for m in _LINES:
        if (m & bits).bit_count() == 2:
            e = m & ~occ
            if e and (e & (e - 1)) == 0:
                wins |= e
    return wins


def _threats_after_move(bits, other, occ, p):
    """
    After bits plays p, return the set of cells that would be immediate
    winning moves for that same side. Existing immediate wins are assumed
    to have already been handled.
    """
    bit = 1 << p
    nbits = bits | bit
    nocc = occ | bit
    threats = 0

    for m in _CELL_LINES[p]:
        if m & other:
            continue
        if (m & nbits).bit_count() == 2:
            e = m & ~nocc
            if e:
                threats |= e

    return threats


def _move_heuristic(p, cur, opp, occ):
    score = _POS_VALUES[p]

    t = _threats_after_move(cur, opp, occ, p).bit_count()
    score += 1200 * t

    for m in _CELL_LINES[p]:
        c = (m & cur).bit_count()
        o = (m & opp).bit_count()

        if o == 0:
            if c == 1:
                score += 45
            elif c == 2:
                score += 5000

        if c == 0:
            if o == 1:
                score += 42
            elif o == 2:
                score += 4800

    return score


def _choose_highest(mask, cur, opp, occ):
    best = -1
    best_score = -_INF

    for p in _BASE_ORDER:
        if mask & (1 << p):
            s = _move_heuristic(p, cur, opp, occ)
            if s > best_score:
                best_score = s
                best = p

    if best < 0:
        best = _mask_to_index(mask)
    return best


def _order_moves(mask, cur, opp, occ):
    scored = []
    best_fork = -1
    best_fork_score = -_INF

    for p in _BASE_ORDER:
        bit = 1 << p
        if not (mask & bit):
            continue

        threat_count = _threats_after_move(cur, opp, occ, p).bit_count()

        score = _POS_VALUES[p] + 1200 * threat_count
        for m in _CELL_LINES[p]:
            c = (m & cur).bit_count()
            o = (m & opp).bit_count()

            if o == 0:
                if c == 1:
                    score += 45
                elif c == 2:
                    score += 5000

            if c == 0:
                if o == 1:
                    score += 42
                elif o == 2:
                    score += 4800

        if threat_count >= 2 and score > best_fork_score:
            best_fork_score = score
            best_fork = p

        scored.append((score, p))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored], best_fork


def _find_fork_move(mask, cur, opp, occ):
    _, fork = _order_moves(mask, cur, opp, occ)
    if fork >= 0:
        return fork
    return None


def _evaluate(cur, opp):
    occ = cur | opp
    score = 0

    b = cur
    while b:
        lsb = b & -b
        score += _POS_VALUES[lsb.bit_length() - 1]
        b ^= lsb

    b = opp
    while b:
        lsb = b & -b
        score -= _POS_VALUES[lsb.bit_length() - 1]
        b ^= lsb

    for m in _LINES:
        c = (m & cur).bit_count()
        o = (m & opp).bit_count()

        if c and o:
            continue

        if c == 1:
            score += 12
        elif c == 2:
            score += 450
        elif c == 3:
            score += _WIN_SCORE

        if o == 1:
            score -= 13
        elif o == 2:
            score -= 500
        elif o == 3:
            score -= _WIN_SCORE

    empty = _ALL_MASK & ~occ
    cur_threat_potential = 0
    opp_threat_potential = 0
    cur_forks = 0
    opp_forks = 0

    for p in _BASE_ORDER:
        if not (empty & (1 << p)):
            continue

        tc = _threats_after_move(cur, opp, occ, p).bit_count()
        to = _threats_after_move(opp, cur, occ, p).bit_count()

        cur_threat_potential += tc
        opp_threat_potential += to

        if tc >= 2:
            cur_forks += 1
        if to >= 2:
            opp_forks += 1

    score += 70 * (cur_threat_potential - opp_threat_potential)
    score += 4000 * (cur_forks - opp_forks)

    return score


def _depth_limit(empty_count):
    if empty_count <= 9:
        return empty_count
    if empty_count <= 13:
        return 11
    if empty_count <= 17:
        return 9
    if empty_count <= 21:
        return 7
    return 6


def _search(my, opp, legal):
    occ0 = my | opp
    end_time = time.perf_counter() + _TIME_LIMIT
    tt = {}
    nodes = 0

    root_order, root_fork = _order_moves(legal, my, opp, occ0)
    if root_fork >= 0:
        return root_fork
    if not root_order:
        return _mask_to_index(legal)

    best_idx = root_order[0]
    max_depth = _depth_limit(legal.bit_count())

    def negamax(cur, other, depth, alpha, beta):
        nonlocal nodes
        nodes += 1
        if (nodes & 511) == 0 and time.perf_counter() > end_time:
            raise TimeoutError

        occ = cur | other
        empty = _ALL_MASK & ~occ

        if _has_win(other):
            return -_WIN_SCORE - depth
        if empty == 0:
            return 0

        key = (cur, other, depth)
        alpha_orig = alpha
        beta_orig = beta

        entry = tt.get(key)
        if entry is not None:
            val, flag = entry
            if flag == _EXACT:
                return val
            if flag == _LOWER and val > alpha:
                alpha = val
            elif flag == _UPPER and val < beta:
                beta = val
            if alpha >= beta:
                return val

        cur_wins = _winning_moves(cur, occ)
        if cur_wins:
            val = _WIN_SCORE + depth + cur_wins.bit_count()
            if len(tt) < _TT_LIMIT:
                tt[key] = (val, _EXACT)
            return val

        other_wins = _winning_moves(other, occ)
        forced = False

        if other_wins:
            if other_wins.bit_count() > 1:
                val = -_WIN_SCORE - depth - other_wins.bit_count()
                if len(tt) < _TT_LIMIT:
                    tt[key] = (val, _EXACT)
                return val
            moves_mask = other_wins
            forced = True
        else:
            moves_mask = empty

        if moves_mask & (moves_mask - 1) == 0:
            p = _mask_to_index(moves_mask)
            ordered = [p]
            if _threats_after_move(cur, other, occ, p).bit_count() >= 2:
                val = _WIN_SCORE + depth - 1
                if len(tt) < _TT_LIMIT:
                    tt[key] = (val, _EXACT)
                return val
        else:
            ordered, fork = _order_moves(moves_mask, cur, other, occ)
            if fork >= 0:
                val = _WIN_SCORE + depth - 1
                if len(tt) < _TT_LIMIT:
                    tt[key] = (val, _EXACT)
                return val

        if depth <= 0 and not forced:
            val = _evaluate(cur, other)
            if len(tt) < _TT_LIMIT:
                tt[key] = (val, _EXACT)
            return val

        best = -_INF

        for p in ordered:
            bit = 1 << p
            val = -negamax(other, cur | bit, depth - 1, -beta, -alpha)

            if val > best:
                best = val
            if val > alpha:
                alpha = val
            if alpha >= beta:
                break

        if best == -_INF:
            best = 0

        if best <= alpha_orig:
            flag = _UPPER
        elif best >= beta_orig:
            flag = _LOWER
        else:
            flag = _EXACT

        if len(tt) < _TT_LIMIT:
            tt[key] = (best, flag)

        return best

    for depth in range(1, max_depth + 1):
        try:
            if time.perf_counter() > end_time:
                break

            if best_idx in root_order:
                order = [best_idx] + [p for p in root_order if p != best_idx]
            else:
                order = root_order

            alpha = -_INF
            beta = _INF
            iter_best = best_idx
            iter_score = -_INF

            for p in order:
                if time.perf_counter() > end_time:
                    raise TimeoutError

                bit = 1 << p
                val = -negamax(opp, my | bit, depth - 1, -beta, -alpha)

                if val > iter_score:
                    iter_score = val
                    iter_best = p
                if val > alpha:
                    alpha = val

            best_idx = iter_best

            if iter_score >= _WIN_SCORE // 2:
                break

        except TimeoutError:
            break

    return best_idx


def _as_move(p, board, legal):
    if isinstance(p, int) and 0 <= p < 27 and (legal & (1 << p)):
        return _coords(p)
    return _first_legal(board)


def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    try:
        my, opp = _bits_from_board(board)
        occ = my | opp
        legal = _ALL_MASK & ~occ

        if legal == 0:
            return _first_legal(board)

        # If somehow called on a terminal board, still return a legal empty cell.
        if _has_win(my) or _has_win(opp):
            return _as_move(_choose_highest(legal, my, opp, occ), board, legal)

        # Best universal opening.
        if occ == 0 and (legal & _CENTER_BIT):
            return (1, 1, 1)

        # Win immediately if possible.
        my_wins = _winning_moves(my, occ) & legal
        if my_wins:
            return _as_move(_choose_highest(my_wins, my, opp, occ), board, legal)

        # Otherwise block an immediate opponent win.
        opp_wins = _winning_moves(opp, occ) & legal
        if opp_wins:
            if opp_wins.bit_count() == 1:
                return _as_move(_mask_to_index(opp_wins), board, legal)
            return _as_move(_choose_highest(opp_wins, my, opp, occ), board, legal)

        # If this is our first stone, take center if possible; otherwise a corner.
        if my == 0:
            if legal & _CENTER_BIT:
                return (1, 1, 1)
            corners = _CORNERS_MASK & legal
            if corners:
                return _as_move(_choose_highest(corners, my, opp, occ), board, legal)

        # A move creating two distinct immediate wins is a forced win.
        fork = _find_fork_move(legal, my, opp, occ)
        if fork is not None:
            return _as_move(fork, board, legal)

        if legal & (legal - 1) == 0:
            return _as_move(_mask_to_index(legal), board, legal)

        move = _search(my, opp, legal)
        return _as_move(move, board, legal)

    except Exception:
        try:
            return _first_legal(board)
        except Exception:
            return (0, 0, 0)
