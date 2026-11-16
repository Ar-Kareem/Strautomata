
from __future__ import annotations

import time

_INF = 10**9
_WIN = 10**7

_BDIRS = ((-1, -1), (-1, 1))   # black moves toward lower row numbers
_WDIRS = ((1, -1), (1, 1))     # white moves toward higher row numbers
_KDIRS = ((-1, -1), (-1, 1), (1, -1), (1, 1))

_COL_BONUS = (0, 1, 3, 4, 4, 3, 1, 0)
_ROW_BONUS = (0, 1, 3, 4, 4, 3, 1, 0)

_DEADLINE = 0.0
_NODES = 0
_ROOT = "b"
_TT = {}


class _SearchTimeout(Exception):
    pass


def _other(side: str) -> str:
    return "w" if side == "b" else "b"


def _to_bits(squares) -> int:
    bb = 0
    for sq in squares:
        r, c = sq
        r = int(r)
        c = int(c)
        if 0 <= r < 8 and 0 <= c < 8:
            bb |= 1 << (r * 8 + c)
    return bb


def _format_move(move):
    fr, to, _ = move
    return ((fr >> 3, fr & 7), (to >> 3, to & 7))


def _time_check():
    global _NODES
    _NODES += 1
    if (_NODES & 511) == 0 and time.perf_counter() > _DEADLINE:
        raise _SearchTimeout()


def _gen_moves(bm: int, bk: int, wm: int, wk: int, side: str, captures_only: bool = False):
    occ = bm | bk | wm | wk

    if side == "b":
        men = bm
        kings = bk
        opp = wm | wk
        man_dirs = _BDIRS
    else:
        men = wm
        kings = wk
        opp = bm | bk
        man_dirs = _WDIRS

    captures = []

    bits = men
    while bits:
        lsb = bits & -bits
        p = lsb.bit_length() - 1
        bits ^= lsb
        r = p >> 3
        c = p & 7
        for dr, dc in man_dirs:
            mr = r + dr
            mc = c + dc
            lr = r + dr + dr
            lc = c + dc + dc
            if 0 <= lr < 8 and 0 <= lc < 8 and 0 <= mr < 8 and 0 <= mc < 8:
                mid = mr * 8 + mc
                land = lr * 8 + lc
                if (opp & (1 << mid)) and not (occ & (1 << land)):
                    captures.append((p, land, mid))

    bits = kings
    while bits:
        lsb = bits & -bits
        p = lsb.bit_length() - 1
        bits ^= lsb
        r = p >> 3
        c = p & 7
        for dr, dc in _KDIRS:
            mr = r + dr
            mc = c + dc
            lr = r + dr + dr
            lc = c + dc + dc
            if 0 <= lr < 8 and 0 <= lc < 8 and 0 <= mr < 8 and 0 <= mc < 8:
                mid = mr * 8 + mc
                land = lr * 8 + lc
                if (opp & (1 << mid)) and not (occ & (1 << land)):
                    captures.append((p, land, mid))

    if captures or captures_only:
        return captures

    moves = []

    bits = men
    while bits:
        lsb = bits & -bits
        p = lsb.bit_length() - 1
        bits ^= lsb
        r = p >> 3
        c = p & 7
        for dr, dc in man_dirs:
            nr = r + dr
            nc = c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                to = nr * 8 + nc
                if not (occ & (1 << to)):
                    moves.append((p, to, -1))

    bits = kings
    while bits:
        lsb = bits & -bits
        p = lsb.bit_length() - 1
        bits ^= lsb
        r = p >> 3
        c = p & 7
        for dr, dc in _KDIRS:
            nr = r + dr
            nc = c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                to = nr * 8 + nc
                if not (occ & (1 << to)):
                    moves.append((p, to, -1))

    return moves


def _make_move(bm: int, bk: int, wm: int, wk: int, side: str, move):
    fr, to, mid = move
    fm = 1 << fr
    tm = 1 << to

    if mid >= 0:
        cm = ~(1 << mid)
        if side == "b":
            wm &= cm
            wk &= cm
        else:
            bm &= cm
            bk &= cm

    tr = to >> 3

    if side == "b":
        if bm & fm:
            bm &= ~fm
            if tr == 0:
                bk |= tm
            else:
                bm |= tm
        else:
            bk = (bk & ~fm) | tm
    else:
        if wm & fm:
            wm &= ~fm
            if tr == 7:
                wk |= tm
            else:
                wm |= tm
        else:
            wk = (wk & ~fm) | tm

    return bm, bk, wm, wk


def _is_protected(p: int, friendly: int) -> bool:
    r = p >> 3
    c = p & 7
    for dr, dc in _KDIRS:
        nr = r + dr
        nc = c + dc
        if 0 <= nr < 8 and 0 <= nc < 8:
            if friendly & (1 << (nr * 8 + nc)):
                return True
    return False


def _feature(men: int, kings: int, side: str, enemy_capture_mask: int) -> int:
    score = 100 * men.bit_count() + 180 * kings.bit_count()
    friendly = men | kings

    bits = men
    while bits:
        lsb = bits & -bits
        p = lsb.bit_length() - 1
        bits ^= lsb

        r = p >> 3
        c = p & 7
        bit = 1 << p

        if side == "b":
            progress = 7 - r
            dist_to_king = r
            home = (r == 7)
        else:
            progress = r
            dist_to_king = 7 - r
            home = (r == 0)

        score += 6 * progress
        if dist_to_king == 1:
            score += 18
        elif dist_to_king == 2:
            score += 7

        if home:
            score += 5

        score += _COL_BONUS[c] + (_ROW_BONUS[r] // 2)

        # Edge men are harder to capture.
        if c == 0 or c == 7:
            score += 2

        if _is_protected(p, friendly):
            score += 4

        if enemy_capture_mask & bit:
            score -= 32

    bits = kings
    while bits:
        lsb = bits & -bits
        p = lsb.bit_length() - 1
        bits ^= lsb

        r = p >> 3
        c = p & 7
        bit = 1 << p

        score += 2 * _COL_BONUS[c] + _ROW_BONUS[r]

        # Kings want mobility; edges restrict them.
        if c == 0 or c == 7 or r == 0 or r == 7:
            score -= 4

        if _is_protected(p, friendly):
            score += 2

        if enemy_capture_mask & bit:
            score -= 42

    return score


def _capture_bonus(caps, opp_kings: int) -> int:
    score = 0
    for _, _, mid in caps:
        score += 55
        if opp_kings & (1 << mid):
            score += 70
    return score


def _captured_mask(caps) -> int:
    mask = 0
    for _, _, mid in caps:
        if mid >= 0:
            mask |= 1 << mid
    return mask


def _evaluate(bm: int, bk: int, wm: int, wk: int, side_to_move: str | None = None) -> int:
    black_pieces = bm | bk
    white_pieces = wm | wk

    if not black_pieces:
        raw = -_WIN // 2
        return raw if _ROOT == "b" else -raw
    if not white_pieces:
        raw = _WIN // 2
        return raw if _ROOT == "b" else -raw

    b_moves = _gen_moves(bm, bk, wm, wk, "b")
    w_moves = _gen_moves(bm, bk, wm, wk, "w")

    if side_to_move == "b" and not b_moves:
        raw = -_WIN // 2
        return raw if _ROOT == "b" else -raw
    if side_to_move == "w" and not w_moves:
        raw = _WIN // 2
        return raw if _ROOT == "b" else -raw

    b_caps = b_moves if b_moves and b_moves[0][2] >= 0 else []
    w_caps = w_moves if w_moves and w_moves[0][2] >= 0 else []

    b_cap_mask = _captured_mask(b_caps)
    w_cap_mask = _captured_mask(w_caps)

    black = _feature(bm, bk, "b", w_cap_mask)
    white = _feature(wm, wk, "w", b_cap_mask)

    black += 4 * len(b_moves) + _capture_bonus(b_caps, wk)
    white += 4 * len(w_moves) + _capture_bonus(w_caps, bk)

    raw = black - white

    # In material-winning positions, simplifying is usually good.
    mat_b = 100 * bm.bit_count() + 180 * bk.bit_count()
    mat_w = 100 * wm.bit_count() + 180 * wk.bit_count()
    total = (black_pieces | white_pieces).bit_count()
    if mat_b > mat_w + 90:
        raw += max(0, 24 - total)
    elif mat_w > mat_b + 90:
        raw -= max(0, 24 - total)

    return raw if _ROOT == "b" else -raw


def _move_order_score(move, bm: int, bk: int, wm: int, wk: int, side: str) -> int:
    fr, to, mid = move
    tr = to >> 3
    tc = to & 7
    score = 0

    if mid >= 0:
        opp_kings = wk if side == "b" else bk
        score += 1000
        if opp_kings & (1 << mid):
            score += 250

    own_men = bm if side == "b" else wm
    if own_men & (1 << fr):
        fr_row = fr >> 3
        if (side == "b" and tr == 0) or (side == "w" and tr == 7):
            score += 350
        else:
            score += 12 * ((fr_row - tr) if side == "b" else (tr - fr_row))

    if 2 <= tr <= 5 and 2 <= tc <= 5:
        score += 20
    if tc == 0 or tc == 7:
        score += 3

    return score


def _order_moves(moves, bm: int, bk: int, wm: int, wk: int, side: str, preferred=None):
    if not moves:
        return moves

    def key(m):
        return (1 if preferred is not None and m == preferred else 0,
                _move_order_score(m, bm, bk, wm, wk, side))

    return sorted(moves, key=key, reverse=True)


def _terminal_material_score(bm: int, bk: int, wm: int, wk: int, ply: int):
    if _ROOT == "b":
        if not (bm | bk):
            return -_WIN + ply
        if not (wm | wk):
            return _WIN - ply
    else:
        if not (wm | wk):
            return -_WIN + ply
        if not (bm | bk):
            return _WIN - ply
    return None


def _alphabeta(bm: int, bk: int, wm: int, wk: int,
               side: str, depth: int, alpha: int, beta: int,
               qleft: int, ply: int) -> int:
    _time_check()

    term = _terminal_material_score(bm, bk, wm, wk, ply)
    if term is not None:
        return term

    key = (bm, bk, wm, wk, side)
    entry = _TT.get(key)
    if entry is not None:
        edepth, eqleft, flag, val, _best = entry
        if edepth >= depth and eqleft >= qleft:
            if flag == 0:
                return val
            if flag == 1 and val >= beta:
                return val
            if flag == 2 and val <= alpha:
                return val

    moves = _gen_moves(bm, bk, wm, wk, side)

    if not moves:
        return (-_WIN + ply) if side == _ROOT else (_WIN - ply)

    if depth <= 0:
        has_capture = moves[0][2] >= 0
        if not (has_capture and qleft > 0):
            return _evaluate(bm, bk, wm, wk, side)

    alpha_orig = alpha
    beta_orig = beta
    tt_best = entry[4] if entry is not None else None
    moves = _order_moves(moves, bm, bk, wm, wk, side, tt_best)

    child_depth = depth - 1 if depth > 0 else 0
    child_qleft = qleft if depth > 0 else qleft - 1

    best_move = None

    if side == _ROOT:
        best_val = -_INF
        for m in moves:
            nbm, nbk, nwm, nwk = _make_move(bm, bk, wm, wk, side, m)
            val = _alphabeta(nbm, nbk, nwm, nwk, _other(side),
                             child_depth, alpha, beta, child_qleft, ply + 1)
            if val > best_val:
                best_val = val
                best_move = m
            if best_val > alpha:
                alpha = best_val
            if alpha >= beta:
                break
    else:
        best_val = _INF
        for m in moves:
            nbm, nbk, nwm, nwk = _make_move(bm, bk, wm, wk, side, m)
            val = _alphabeta(nbm, nbk, nwm, nwk, _other(side),
                             child_depth, alpha, beta, child_qleft, ply + 1)
            if val < best_val:
                best_val = val
                best_move = m
            if best_val < beta:
                beta = best_val
            if alpha >= beta:
                break

    if best_val <= alpha_orig:
        flag = 2   # upper bound
    elif best_val >= beta_orig:
        flag = 1   # lower bound
    else:
        flag = 0   # exact

    if len(_TT) < 150000:
        _TT[key] = (max(depth, 0), max(qleft, 0), flag, best_val, best_move)

    return best_val


def _root_search(bm: int, bk: int, wm: int, wk: int, depth: int, preferred):
    if time.perf_counter() > _DEADLINE:
        raise _SearchTimeout()

    moves = _gen_moves(bm, bk, wm, wk, _ROOT)
    moves = _order_moves(moves, bm, bk, wm, wk, _ROOT, preferred)

    best_move = None
    best_val = -_INF
    alpha = -_INF
    beta = _INF

    for m in moves:
        _time_check()
        nbm, nbk, nwm, nwk = _make_move(bm, bk, wm, wk, _ROOT, m)
        val = _alphabeta(nbm, nbk, nwm, nwk, _other(_ROOT),
                         depth - 1, alpha, beta, 2, 1)
        if val > best_val:
            best_val = val
            best_move = m
        if best_val > alpha:
            alpha = best_val

    return best_val, best_move


def _fallback_best(bm: int, bk: int, wm: int, wk: int, moves):
    ordered = _order_moves(moves, bm, bk, wm, wk, _ROOT, None)
    best = ordered[0]
    best_val = -_INF
    next_side = _other(_ROOT)

    for m in ordered:
        nbm, nbk, nwm, nwk = _make_move(bm, bk, wm, wk, _ROOT, m)
        val = _evaluate(nbm, nbk, nwm, nwk, next_side)
        if val > best_val:
            best_val = val
            best = m

    return best


def _choose_max_depth(total_pieces: int, root_moves) -> int:
    if total_pieces <= 6:
        depth = 12
    elif total_pieces <= 10:
        depth = 11
    elif total_pieces <= 14:
        depth = 10
    elif total_pieces <= 20:
        depth = 8
    else:
        depth = 7

    if root_moves and root_moves[0][2] >= 0:
        depth += 2

    return min(depth, 14)


def _emergency_move(my_men, my_kings, opp_men, opp_kings, color):
    color = "b" if color == "b" else "w"

    men = {(int(r), int(c)) for r, c in my_men}
    kings = {(int(r), int(c)) for r, c in my_kings}
    opp = {(int(r), int(c)) for r, c in opp_men} | {(int(r), int(c)) for r, c in opp_kings}
    occupied = men | kings | opp

    man_dirs = _BDIRS if color == "b" else _WDIRS

    captures = []
    for r, c in sorted(men):
        for dr, dc in man_dirs:
            mid = (r + dr, c + dc)
            land = (r + 2 * dr, c + 2 * dc)
            if 0 <= land[0] < 8 and 0 <= land[1] < 8 and mid in opp and land not in occupied:
                captures.append(((r, c), land))

    for r, c in sorted(kings):
        for dr, dc in _KDIRS:
            mid = (r + dr, c + dc)
            land = (r + 2 * dr, c + 2 * dc)
            if 0 <= land[0] < 8 and 0 <= land[1] < 8 and mid in opp and land not in occupied:
                captures.append(((r, c), land))

    if captures:
        return captures[0]

    moves = []
    for r, c in sorted(men):
        for dr, dc in man_dirs:
            to = (r + dr, c + dc)
            if 0 <= to[0] < 8 and 0 <= to[1] < 8 and to not in occupied:
                moves.append(((r, c), to))

    for r, c in sorted(kings):
        for dr, dc in _KDIRS:
            to = (r + dr, c + dc)
            if 0 <= to[0] < 8 and 0 <= to[1] < 8 and to not in occupied:
                moves.append(((r, c), to))

    if moves:
        return moves[0]

    # Should only happen if the game is already over.
    if men:
        p = next(iter(men))
        return (p, p)
    if kings:
        p = next(iter(kings))
        return (p, p)
    return ((0, 0), (0, 0))


def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    global _DEADLINE, _NODES, _ROOT, _TT

    try:
        color = "b" if color == "b" else "w"
        _ROOT = color
        _NODES = 0
        _TT = {}
        _DEADLINE = time.perf_counter() + 0.82

        if color == "b":
            bm = _to_bits(my_men)
            bk = _to_bits(my_kings)
            wm = _to_bits(opp_men)
            wk = _to_bits(opp_kings)
        else:
            wm = _to_bits(my_men)
            wk = _to_bits(my_kings)
            bm = _to_bits(opp_men)
            bk = _to_bits(opp_kings)

        root_moves = _gen_moves(bm, bk, wm, wk, _ROOT)
        if not root_moves:
            return _emergency_move(my_men, my_kings, opp_men, opp_kings, color)

        if len(root_moves) == 1:
            return _format_move(root_moves[0])

        best_move = _fallback_best(bm, bk, wm, wk, root_moves)

        total_pieces = (bm | bk | wm | wk).bit_count()
        max_depth = _choose_max_depth(total_pieces, root_moves)

        for depth in range(1, max_depth + 1):
            if time.perf_counter() > _DEADLINE:
                break
            try:
                _, move = _root_search(bm, bk, wm, wk, depth, best_move)
                if move is not None:
                    best_move = move
            except _SearchTimeout:
                break

        return _format_move(best_move)

    except Exception:
        return _emergency_move(my_men, my_kings, opp_men, opp_kings, color)
