
from __future__ import annotations

import time

# Standard 4x4 Tic Tac Toe: win by completing any row, column, or main diagonal.
_FULL_MASK = (1 << 16) - 1
_INF = 10**9
_WIN_SCORE = 1_000_000


def _mask(cells):
    value = 0
    for cell in cells:
        value |= 1 << cell
    return value


_WIN_MASKS = (
    # rows
    _mask((0, 1, 2, 3)),
    _mask((4, 5, 6, 7)),
    _mask((8, 9, 10, 11)),
    _mask((12, 13, 14, 15)),
    # columns
    _mask((0, 4, 8, 12)),
    _mask((1, 5, 9, 13)),
    _mask((2, 6, 10, 14)),
    _mask((3, 7, 11, 15)),
    # diagonals
    _mask((0, 5, 10, 15)),
    _mask((3, 6, 9, 12)),
)

# Prefer the four central diagonal cells, then corners, then other edge cells.
_STATIC_ORDER = (5, 6, 9, 10, 0, 3, 12, 15, 1, 2, 4, 7, 8, 11, 13, 14)
_POSITION_BONUS = (
    10, 4, 4, 10,
    4, 12, 12, 4,
    4, 12, 12, 4,
    10, 4, 4, 10,
)

_ATTACK = (0, 7, 55, 900, 200000)
_DEFENSE = (0, 6, 65, 1100, 0)
_LINE_EVAL = (0, 10, 90, 3000, 0)

_CELL_LINES = tuple(
    tuple(w for w in _WIN_MASKS if w & (1 << i))
    for i in range(16)
)

# Precompute winning masks.
_WIN = bytearray(1 << 16)
for _m in range(1 << 16):
    for _w in _WIN_MASKS:
        if (_m & _w) == _w:
            _WIN[_m] = 1
            break

# Precompute positional sums for heuristic evaluation.
_POS_SUM = [0] * (1 << 16)
for _m in range(1, 1 << 16):
    _lsb = _m & -_m
    _idx = _lsb.bit_length() - 1
    _POS_SUM[_m] = _POS_SUM[_m ^ _lsb] + _POSITION_BONUS[_idx]


def _build_transform_tables():
    """Tables for the 8 board symmetries, used by the transposition table."""
    index_maps = []
    for t in range(8):
        mp = []
        for i in range(16):
            r, c = divmod(i, 4)
            if t == 0:      # identity
                nr, nc = r, c
            elif t == 1:    # rotate 90
                nr, nc = c, 3 - r
            elif t == 2:    # rotate 180
                nr, nc = 3 - r, 3 - c
            elif t == 3:    # rotate 270
                nr, nc = 3 - c, r
            elif t == 4:    # mirror vertical
                nr, nc = r, 3 - c
            elif t == 5:    # mirror horizontal
                nr, nc = 3 - r, c
            elif t == 6:    # main diagonal reflection
                nr, nc = c, r
            else:           # anti-diagonal reflection
                nr, nc = 3 - c, 3 - r
            mp.append(4 * nr + nc)
        index_maps.append(tuple(mp))

    tables = []
    for mp in index_maps:
        table = [0] * (1 << 16)
        for mask in range(1, 1 << 16):
            lsb = mask & -mask
            i = lsb.bit_length() - 1
            table[mask] = table[mask ^ lsb] | (1 << mp[i])
        tables.append(table)
    return tuple(tables)


_TRANS_TABLES = _build_transform_tables()

_EXACT, _LOWER, _UPPER = 0, 1, 2
_VALUE_OFFSET = 2_000_000
_CACHE = {}
_MAX_CACHE = 600_000

_DEADLINE = 0.0
_NODES = 0


def _check_time():
    if time.perf_counter() >= _DEADLINE:
        raise TimeoutError


def _canon_key(x: int, o: int, turn: int) -> int:
    best = 1 << 40
    for table in _TRANS_TABLES:
        k = (table[x] << 16) | table[o]
        if k < best:
            best = k
    return (best << 1) | (1 if turn == 1 else 0)


def _tt_lookup(key: int, alpha: int, beta: int):
    entry = _CACHE.get(key)
    if entry is None:
        return None
    flag = entry & 3
    value = (entry >> 2) - _VALUE_OFFSET
    if flag == _EXACT:
        return value
    if flag == _LOWER and value >= beta:
        return value
    if flag == _UPPER and value <= alpha:
        return value
    return None


def _store_tt(key: int, value: int, flag: int):
    if key is None:
        return
    if key in _CACHE or len(_CACHE) < _MAX_CACHE:
        _CACHE[key] = ((value + _VALUE_OFFSET) << 2) | flag


def _store_window(key: int, value: int, alpha_orig: int, beta_orig: int):
    if value <= alpha_orig:
        flag = _UPPER
    elif value >= beta_orig:
        flag = _LOWER
    else:
        flag = _EXACT
    _store_tt(key, value, flag)


def _win_cells(me: int, opp: int) -> int:
    """Empty cells where 'me' can win immediately."""
    cells = 0
    for w in _WIN_MASKS:
        if (w & opp) == 0:
            need = w & ~me
            if need and (need & (need - 1)) == 0:
                cells |= need
    return cells & _FULL_MASK


def _move_order_score(me: int, opp: int, bit: int) -> int:
    idx = bit.bit_length() - 1
    score = _POSITION_BONUS[idx]
    for w in _CELL_LINES[idx]:
        mc = (me & w).bit_count()
        oc = (opp & w).bit_count()
        if oc == 0:
            score += _ATTACK[mc + 1]
        if mc == 0:
            score += _DEFENSE[oc]
    return score


def _ordered_bits(x: int, o: int, turn: int):
    empty = _FULL_MASK & ~(x | o)
    if turn == 1:
        me, opp = x, o
    else:
        me, opp = o, x

    scored = []
    for rank, idx in enumerate(_STATIC_ORDER):
        bit = 1 << idx
        if empty & bit:
            scored.append((_move_order_score(me, opp, bit), -rank, bit))
    scored.sort(reverse=True)
    return [b for _, __, b in scored]


def _best_bit_from_mask(mask: int, x: int, o: int, turn: int) -> int:
    if mask == 0:
        return 0
    if turn == 1:
        me, opp = x, o
    else:
        me, opp = o, x

    best = mask & -mask
    best_score = -_INF
    m = mask
    while m:
        bit = m & -m
        score = _move_order_score(me, opp, bit)
        if score > best_score:
            best_score = score
            best = bit
        m ^= bit
    return best


def _has_fork_move(me: int, opp: int) -> bool:
    empty = _FULL_MASK & ~(me | opp)
    for idx in _STATIC_ORDER:
        bit = 1 << idx
        if empty & bit:
            if _win_cells(me | bit, opp).bit_count() >= 2:
                return True
    return False


def _heuristic_value(x: int, o: int) -> int:
    occ = x | o
    n_empty = 16 - occ.bit_count()

    if _WIN[x]:
        return _WIN_SCORE + n_empty
    if _WIN[o]:
        return -_WIN_SCORE - n_empty

    score = _POS_SUM[x] - _POS_SUM[o]

    x_threats = _win_cells(x, o).bit_count()
    o_threats = _win_cells(o, x).bit_count()
    score += 18000 * x_threats
    score -= 21000 * o_threats

    for w in _WIN_MASKS:
        xc = (x & w).bit_count()
        oc = (o & w).bit_count()
        if oc == 0:
            score += _LINE_EVAL[xc]
        if xc == 0:
            score -= _LINE_EVAL[oc] + (_LINE_EVAL[oc] // 8)

    return score


def _search(x: int, o: int, turn: int, depth: int, alpha: int, beta: int) -> int:
    """
    Alpha-beta search.
    depth < 0 means exact search to terminal.
    depth >= 0 means depth-limited heuristic search with tactical extensions.
    """
    global _NODES
    _NODES += 1
    if (_NODES & 1023) == 0:
        _check_time()

    occ = x | o
    n_empty = 16 - occ.bit_count()

    if _WIN[x]:
        return _WIN_SCORE + n_empty
    if _WIN[o]:
        return -_WIN_SCORE - n_empty
    if n_empty == 0:
        return 0

    exact = depth < 0
    key = None
    alpha_orig, beta_orig = alpha, beta

    if exact:
        key = _canon_key(x, o, turn)
        cached = _tt_lookup(key, alpha, beta)
        if cached is not None:
            return cached

    child_depth = -1 if exact else (depth - 1 if depth > 0 else 0)

    if turn == 1:
        # X/us to move: maximize.
        own_threats = _win_cells(x, o)
        if own_threats:
            value = _WIN_SCORE + (n_empty - 1)
            if exact:
                _store_tt(key, value, _EXACT)
            return value

        opp_threats = _win_cells(o, x)
        if opp_threats:
            if opp_threats.bit_count() > 1:
                value = -_WIN_SCORE - max(n_empty - 2, 0)
                if exact:
                    _store_tt(key, value, _EXACT)
                return value
            value = _search(x | opp_threats, o, -1, child_depth, alpha, beta)
            if exact:
                _store_window(key, value, alpha_orig, beta_orig)
            return value

        moves = _ordered_bits(x, o, 1)

        # A move creating two distinct immediate wins is a forced win.
        for bit in moves:
            if _win_cells(x | bit, o).bit_count() >= 2:
                value = _WIN_SCORE + max(n_empty - 3, 0)
                if exact:
                    _store_tt(key, value, _EXACT)
                return value

        if not exact and depth <= 0:
            return _heuristic_value(x, o)

        best = -_INF
        nd = -1 if exact else depth - 1
        for bit in moves:
            value = _search(x | bit, o, -1, nd, alpha, beta)
            if value > best:
                best = value
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        if best == -_INF:
            best = 0
        if exact:
            _store_window(key, best, alpha_orig, beta_orig)
        return best

    else:
        # O/opponent to move: minimize X/us score.
        own_threats = _win_cells(o, x)
        if own_threats:
            value = -_WIN_SCORE - (n_empty - 1)
            if exact:
                _store_tt(key, value, _EXACT)
            return value

        opp_threats = _win_cells(x, o)
        if opp_threats:
            if opp_threats.bit_count() > 1:
                value = _WIN_SCORE + max(n_empty - 2, 0)
                if exact:
                    _store_tt(key, value, _EXACT)
                return value
            value = _search(x, o | opp_threats, 1, child_depth, alpha, beta)
            if exact:
                _store_window(key, value, alpha_orig, beta_orig)
            return value

        moves = _ordered_bits(x, o, -1)

        # Opponent fork means forced loss for us.
        for bit in moves:
            if _win_cells(o | bit, x).bit_count() >= 2:
                value = -_WIN_SCORE - max(n_empty - 3, 0)
                if exact:
                    _store_tt(key, value, _EXACT)
                return value

        if not exact and depth <= 0:
            return _heuristic_value(x, o)

        best = _INF
        nd = -1 if exact else depth - 1
        for bit in moves:
            value = _search(x, o | bit, 1, nd, alpha, beta)
            if value < best:
                best = value
            if best < beta:
                beta = best
            if alpha >= beta:
                break

        if best == _INF:
            best = 0
        if exact:
            _store_window(key, best, alpha_orig, beta_orig)
        return best


def _choose_heuristic(x: int, o: int) -> int:
    empty = _FULL_MASK & ~(x | o)
    if not empty:
        return 0

    # Win immediately.
    own_win = _win_cells(x, o) & empty
    if own_win:
        return _best_bit_from_mask(own_win, x, o, 1)

    # Block immediate opponent win.
    opp_win = _win_cells(o, x) & empty
    if opp_win:
        return _best_bit_from_mask(opp_win, x, o, 1)

    moves = _ordered_bits(x, o, 1)
    if not moves:
        return empty & -empty

    # Create a forced fork win if possible.
    for bit in moves:
        if _win_cells(x | bit, o).bit_count() >= 2:
            return bit

    # Prefer moves that do not allow an opponent fork.
    safe_moves = []
    for bit in moves:
        nx = x | bit
        my_threats = _win_cells(nx, o)
        tcount = my_threats.bit_count()

        if tcount == 1:
            # Opponent is forced to block this cell.
            forced_block = my_threats
            if _win_cells(o | forced_block, nx).bit_count() < 2:
                safe_moves.append(bit)
        else:
            if not _has_fork_move(o, nx):
                safe_moves.append(bit)

    if safe_moves:
        moves = safe_moves

    # One-ply minimax heuristic.
    best = moves[0]
    best_score = -_INF

    for bit in moves:
        nx = x | bit
        threats = _win_cells(nx, o)
        tc = threats.bit_count()

        if tc >= 2:
            value = _WIN_SCORE
        elif tc == 1:
            value = _heuristic_value(nx, o | threats)
        else:
            omoves = _ordered_bits(nx, o, -1)
            if not omoves:
                value = _heuristic_value(nx, o)
            else:
                worst = _INF
                for obit in omoves:
                    no = o | obit
                    v = _heuristic_value(nx, no)
                    if _win_cells(no, nx).bit_count() >= 2:
                        v -= 80000
                    if v < worst:
                        worst = v
                value = worst

        value += _move_order_score(x, o, bit) // 4

        if value > best_score:
            best_score = value
            best = bit

    return best


def _choose_limited(x: int, o: int, depth: int, fallback: int) -> int:
    moves = _ordered_bits(x, o, 1)
    if not moves:
        return fallback

    best = fallback
    best_score = -_INF
    alpha = -_INF

    try:
        for bit in moves:
            _check_time()
            value = _search(x | bit, o, -1, max(depth - 1, 0), alpha, _INF)
            if value > best_score:
                best_score = value
                best = bit
            if best_score > alpha:
                alpha = best_score
            if best_score >= _WIN_SCORE:
                break
    except TimeoutError:
        return best

    return best


def _choose_exact(x: int, o: int, fallback: int) -> int:
    moves = _ordered_bits(x, o, 1)
    if not moves:
        return fallback

    best = fallback
    best_score = -_INF
    alpha = -_INF

    for bit in moves:
        _check_time()
        value = _search(x | bit, o, -1, -1, alpha, _INF)
        if value > best_score:
            best_score = value
            best = bit
        if best_score > alpha:
            alpha = best_score
        if best_score >= _WIN_SCORE:
            break

    return best


def _bit_to_move(bit: int) -> tuple[int, int]:
    idx = bit.bit_length() - 1
    return (idx // 4, idx % 4)


def _parse_board(board: list[list[int]]) -> tuple[int, int]:
    x = 0
    o = 0
    for r in range(4):
        for c in range(4):
            v = board[r][c]
            bit = 1 << (4 * r + c)
            if v == 1:
                x |= bit
            elif v == -1:
                o |= bit
    return x, o


def _first_empty_board(board: list[list[int]]) -> tuple[int, int]:
    try:
        for r in range(4):
            for c in range(4):
                if board[r][c] == 0:
                    return (r, c)
    except Exception:
        pass
    return (0, 0)


def policy(board: list[list[int]]) -> tuple[int, int]:
    global _DEADLINE, _NODES

    try:
        x, o = _parse_board(board)
        occ = x | o
        empty = _FULL_MASK & ~occ

        if not empty:
            return _first_empty_board(board)

        # Strong, fast opening. The exact solver is used after some information exists.
        if occ == 0:
            return (1, 1)

        start = time.perf_counter()

        fallback = _choose_heuristic(x, o)
        if not (fallback & empty):
            fallback = empty & -empty

        total_moves = occ.bit_count()

        # Quick depth-limited search for very early positions, used as a safe fallback.
        if total_moves < 4:
            _DEADLINE = start + 0.12
            _NODES = 0
            fallback = _choose_limited(x, o, 6, fallback)
            if not (fallback & empty):
                fallback = empty & -empty

        # Try exact minimax. If it times out, the fallback remains legal and tactical.
        _DEADLINE = start + 0.88
        _NODES = 0
        try:
            exact_move = _choose_exact(x, o, fallback)
            if exact_move & empty:
                fallback = exact_move
        except TimeoutError:
            pass

        if not (fallback & empty):
            fallback = empty & -empty

        return _bit_to_move(fallback)

    except Exception:
        return _first_empty_board(board)
