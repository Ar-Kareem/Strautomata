
from __future__ import annotations

from time import perf_counter


INF = 10**9
WIN = 10**6
TT_LIMIT = 250_000
QDEPTH = 3

_ROW = [i >> 3 for i in range(64)]
_COL = [i & 7 for i in range(64)]
_BITS = [1 << i for i in range(64)]

_CENTER = [0] * 64
_CENTER_MAN = [0] * 64
_CENTER_KING = [0] * 64
_ADJ_MASK = [0] * 64

for _i in range(64):
    _r = _ROW[_i]
    _c = _COL[_i]
    # 0 on corners, 12 near the center.
    _center = 14 - (abs(2 * _r - 7) + abs(2 * _c - 7))
    _CENTER[_i] = _center
    _CENTER_MAN[_i] = _center
    _CENTER_KING[_i] = 2 * _center

    _mask = 0
    for _dr in (-1, 1):
        for _dc in (-1, 1):
            _nr = _r + _dr
            _nc = _c + _dc
            if 0 <= _nr < 8 and 0 <= _nc < 8:
                _mask |= 1 << ((_nr << 3) + _nc)
    _ADJ_MASK[_i] = _mask


_ROOT_COLOR = "b"
_OPP_COLOR = "w"
_DEADLINE = 0.0
_NODES = 0
_TT = {}


class _Timeout(Exception):
    pass


def _to_bits(squares):
    bits = 0
    for r, c in squares:
        r = int(r)
        c = int(c)
        if 0 <= r < 8 and 0 <= c < 8:
            bits |= _BITS[(r << 3) + c]
    return bits


def _coords(idx):
    return (_ROW[idx], _COL[idx])


def _is_promotion(idx, color):
    r = idx >> 3
    return r == 0 if color == "b" else r == 7


def _gen_captures(men, kings, opp_men, opp_kings, color):
    occ = men | kings | opp_men | opp_kings
    opp = opp_men | opp_kings
    moves = []
    bits = _BITS

    step = -1 if color == "b" else 1

    b = men
    while b:
        lsb = b & -b
        i = lsb.bit_length() - 1
        b ^= lsb

        r = i >> 3
        c = i & 7
        mr = r + step
        tr = r + 2 * step

        if 0 <= tr < 8:
            nc = c - 1
            tc = c - 2
            if tc >= 0:
                mi = (mr << 3) + nc
                ti = (tr << 3) + tc
                if (opp & bits[mi]) and not (occ & bits[ti]):
                    moves.append((i, ti, mi, 0))

            nc = c + 1
            tc = c + 2
            if tc < 8:
                mi = (mr << 3) + nc
                ti = (tr << 3) + tc
                if (opp & bits[mi]) and not (occ & bits[ti]):
                    moves.append((i, ti, mi, 0))

    b = kings
    while b:
        lsb = b & -b
        i = lsb.bit_length() - 1
        b ^= lsb

        r = i >> 3
        c = i & 7

        for dr in (-1, 1):
            mr = r + dr
            tr = r + 2 * dr
            if 0 <= tr < 8:
                nc = c - 1
                tc = c - 2
                if tc >= 0:
                    mi = (mr << 3) + nc
                    ti = (tr << 3) + tc
                    if (opp & bits[mi]) and not (occ & bits[ti]):
                        moves.append((i, ti, mi, 1))

                nc = c + 1
                tc = c + 2
                if tc < 8:
                    mi = (mr << 3) + nc
                    ti = (tr << 3) + tc
                    if (opp & bits[mi]) and not (occ & bits[ti]):
                        moves.append((i, ti, mi, 1))

    return moves


def _gen_quiet_moves(men, kings, opp_men, opp_kings, color):
    occ = men | kings | opp_men | opp_kings
    moves = []
    bits = _BITS

    step = -1 if color == "b" else 1

    b = men
    while b:
        lsb = b & -b
        i = lsb.bit_length() - 1
        b ^= lsb

        r = i >> 3
        c = i & 7
        nr = r + step

        if 0 <= nr < 8:
            if c > 0:
                ti = (nr << 3) + c - 1
                if not (occ & bits[ti]):
                    moves.append((i, ti, -1, 0))
            if c < 7:
                ti = (nr << 3) + c + 1
                if not (occ & bits[ti]):
                    moves.append((i, ti, -1, 0))

    b = kings
    while b:
        lsb = b & -b
        i = lsb.bit_length() - 1
        b ^= lsb

        r = i >> 3
        c = i & 7

        for dr in (-1, 1):
            nr = r + dr
            if 0 <= nr < 8:
                if c > 0:
                    ti = (nr << 3) + c - 1
                    if not (occ & bits[ti]):
                        moves.append((i, ti, -1, 1))
                if c < 7:
                    ti = (nr << 3) + c + 1
                    if not (occ & bits[ti]):
                        moves.append((i, ti, -1, 1))

    return moves


def _has_quiet_move(men, kings, opp_men, opp_kings, color):
    occ = men | kings | opp_men | opp_kings
    bits = _BITS
    step = -1 if color == "b" else 1

    b = men
    while b:
        lsb = b & -b
        i = lsb.bit_length() - 1
        b ^= lsb

        r = i >> 3
        c = i & 7
        nr = r + step

        if 0 <= nr < 8:
            if c > 0 and not (occ & bits[(nr << 3) + c - 1]):
                return True
            if c < 7 and not (occ & bits[(nr << 3) + c + 1]):
                return True

    b = kings
    while b:
        lsb = b & -b
        i = lsb.bit_length() - 1
        b ^= lsb

        r = i >> 3
        c = i & 7

        for dr in (-1, 1):
            nr = r + dr
            if 0 <= nr < 8:
                if c > 0 and not (occ & bits[(nr << 3) + c - 1]):
                    return True
                if c < 7 and not (occ & bits[(nr << 3) + c + 1]):
                    return True

    return False


def _gen_moves(men, kings, opp_men, opp_kings, color):
    captures = _gen_captures(men, kings, opp_men, opp_kings, color)
    if captures:
        return captures
    return _gen_quiet_moves(men, kings, opp_men, opp_kings, color)


def _apply_move(m0, k0, m1, k1, side, move):
    if side == 0:
        cm, ck, om, ok = m0, k0, m1, k1
        color = _ROOT_COLOR
    else:
        cm, ck, om, ok = m1, k1, m0, k0
        color = _OPP_COLOR

    fr, to, cap, is_king = move
    fbit = _BITS[fr]
    tbit = _BITS[to]

    if is_king:
        ck = (ck & ~fbit) | tbit
    else:
        cm &= ~fbit
        if _is_promotion(to, color):
            ck |= tbit
        else:
            cm |= tbit

    if cap >= 0:
        cbit = _BITS[cap]
        om &= ~cbit
        ok &= ~cbit

    if side == 0:
        return cm, ck, om, ok
    return om, ok, cm, ck


def _move_order_score(move, cm, ck, om, ok, color, tt_move=None):
    if tt_move is not None and move == tt_move:
        return 1_000_000_000

    fr, to, cap, is_king = move

    if cap >= 0:
        cbit = _BITS[cap]
        score = 100_000
        score += 5_000 if (ok & cbit) else 2_500
        score += 120 if not is_king else 0
        score += _CENTER[to] * 20
        if not is_king and _is_promotion(to, color):
            score += 1_800
    else:
        score = 0
        if not is_king:
            rfr = fr >> 3
            rto = to >> 3
            adv = (rfr - rto) if color == "b" else (rto - rfr)
            score += adv * 100
            if _is_promotion(to, color):
                score += 4_000
            elif (color == "b" and rto <= 2) or (color == "w" and rto >= 5):
                score += 80
        else:
            score += 50

        score += (_CENTER[to] - _CENTER[fr]) * 30
        if (to & 7) in (0, 7):
            score += 15

    # Prefer landing next to friendly support.
    if _ADJ_MASK[to] & ((cm | ck) & ~_BITS[fr]):
        score += 35

    return score


def _capture_list_score(moves, opp_men, opp_kings):
    seen = 0
    unique_total = 0
    best = 0

    for move in moves:
        cap = move[2]
        if cap < 0:
            continue
        cbit = _BITS[cap]
        val = 185 if (opp_kings & cbit) else 105
        if val > best:
            best = val
        if not (seen & cbit):
            seen |= cbit
            unique_total += val

    return best + (len(moves) - 1) * 12 + unique_total // 5


def _side_static(men, kings, color, king_value, total_pieces):
    val = men.bit_count() * 100 + kings.bit_count() * king_value

    back_row = 7 if color == "b" else 0
    pre_king_row = 1 if color == "b" else 6
    adv_weight = 5 if total_pieces > 10 else 7

    b = men
    while b:
        lsb = b & -b
        i = lsb.bit_length() - 1
        b ^= lsb

        r = i >> 3
        c = i & 7
        adv = (7 - r) if color == "b" else r

        val += adv * adv_weight
        val += _CENTER_MAN[i]

        if r == pre_king_row:
            val += 22
        elif (color == "b" and r == 2) or (color == "w" and r == 5):
            val += 10

        # Back-row guards are useful early, less important late.
        if r == back_row:
            val += 7 if total_pieces > 8 else 2

        # Edges are harder to capture.
        if c == 0 or c == 7:
            val += 3

    b = kings
    while b:
        lsb = b & -b
        i = lsb.bit_length() - 1
        b ^= lsb

        c = i & 7
        val += _CENTER_KING[i] if total_pieces > 6 else _CENTER_KING[i] // 2
        if c == 0 or c == 7:
            val -= 1

    # Reward compact, mutually supporting formations.
    own = men | kings
    b = own
    connected = 0
    while b:
        lsb = b & -b
        i = lsb.bit_length() - 1
        b ^= lsb
        connected += (_ADJ_MASK[i] & own).bit_count()
    val += connected

    return val


def _evaluate(m0, k0, m1, k1, side):
    if not (m0 | k0):
        return -WIN // 2
    if not (m1 | k1):
        return WIN // 2

    total = (m0 | k0 | m1 | k1).bit_count()
    king_value = 175
    if total <= 10:
        king_value += (11 - total) * 4
    if total <= 4:
        king_value += 12

    score = _side_static(m0, k0, _ROOT_COLOR, king_value, total)
    score -= _side_static(m1, k1, _OPP_COLOR, king_value, total)

    root_moves = _gen_moves(m0, k0, m1, k1, _ROOT_COLOR)
    opp_moves = _gen_moves(m1, k1, m0, k0, _OPP_COLOR)

    if side == 0 and not root_moves:
        return -WIN // 2
    if side == 1 and not opp_moves:
        return WIN // 2

    if not root_moves:
        score -= 500
    if not opp_moves:
        score += 500

    score += 4 * (len(root_moves) - len(opp_moves))

    if root_moves and root_moves[0][2] >= 0:
        cscore = _capture_list_score(root_moves, m1, k1)
        score += (cscore // 2 + cscore // 16) if side == 0 else cscore // 5

    if opp_moves and opp_moves[0][2] >= 0:
        cscore = _capture_list_score(opp_moves, m0, k0)
        score -= (cscore // 2 + cscore // 16) if side == 1 else cscore // 5

    score += 3 if side == 0 else -3
    return score


def _store_tt(key, depth, qdepth, flag, value, best_move):
    old = _TT.get(key)
    if old is None:
        if len(_TT) < TT_LIMIT:
            _TT[key] = (depth, qdepth, flag, value, best_move)
    else:
        old_depth, old_qdepth = old[0], old[1]
        if depth > old_depth or (depth == old_depth and qdepth >= old_qdepth):
            _TT[key] = (depth, qdepth, flag, value, best_move)


def _alphabeta(m0, k0, m1, k1, side, depth, alpha, beta, qdepth, ply):
    global _NODES

    _NODES += 1
    if (_NODES & 1023) == 0 and perf_counter() >= _DEADLINE:
        raise _Timeout()

    key = (m0, k0, m1, k1, side)
    alpha_orig = alpha
    beta_orig = beta

    tt_move = None
    entry = _TT.get(key)
    if entry is not None:
        e_depth, e_qdepth, flag, value, tt_move = entry
        if e_depth >= depth and e_qdepth >= qdepth:
            if flag == 0:  # exact
                return value
            if flag == 1:  # lower bound
                if value >= beta:
                    return value
                if value > alpha:
                    alpha = value
            elif flag == 2:  # upper bound
                if value <= alpha:
                    return value
                if value < beta:
                    beta = value
            if alpha >= beta:
                return value

    if side == 0:
        cm, ck, om, ok = m0, k0, m1, k1
        color = _ROOT_COLOR
    else:
        cm, ck, om, ok = m1, k1, m0, k0
        color = _OPP_COLOR

    if depth <= 0:
        captures = _gen_captures(cm, ck, om, ok, color)
        if captures and qdepth > 0:
            moves = captures
        else:
            if not captures and not _has_quiet_move(cm, ck, om, ok, color):
                val = (-WIN + ply) if side == 0 else (WIN - ply)
            else:
                val = _evaluate(m0, k0, m1, k1, side)
            _store_tt(key, depth, qdepth, 0, val, None)
            return val
    else:
        moves = _gen_moves(cm, ck, om, ok, color)
        if not moves:
            val = (-WIN + ply) if side == 0 else (WIN - ply)
            _store_tt(key, depth, qdepth, 0, val, None)
            return val

    if len(moves) > 1:
        moves.sort(
            key=lambda mv: _move_order_score(mv, cm, ck, om, ok, color, tt_move),
            reverse=True,
        )

    best_move = moves[0]

    if side == 0:
        best_val = -INF
        for mv in moves:
            nm0, nk0, nm1, nk1 = _apply_move(m0, k0, m1, k1, side, mv)
            if depth <= 0:
                val = _alphabeta(nm0, nk0, nm1, nk1, 1, 0, alpha, beta, qdepth - 1, ply + 1)
            else:
                val = _alphabeta(nm0, nk0, nm1, nk1, 1, depth - 1, alpha, beta, qdepth, ply + 1)

            if val > best_val:
                best_val = val
                best_move = mv
            if best_val > alpha:
                alpha = best_val
            if alpha >= beta:
                break
    else:
        best_val = INF
        for mv in moves:
            nm0, nk0, nm1, nk1 = _apply_move(m0, k0, m1, k1, side, mv)
            if depth <= 0:
                val = _alphabeta(nm0, nk0, nm1, nk1, 0, 0, alpha, beta, qdepth - 1, ply + 1)
            else:
                val = _alphabeta(nm0, nk0, nm1, nk1, 0, depth - 1, alpha, beta, qdepth, ply + 1)

            if val < best_val:
                best_val = val
                best_move = mv
            if best_val < beta:
                beta = best_val
            if alpha >= beta:
                break

    if best_val <= alpha_orig:
        flag = 2
    elif best_val >= beta_orig:
        flag = 1
    else:
        flag = 0

    _store_tt(key, depth, qdepth, flag, best_val, best_move)
    return best_val


def _search_root(m0, k0, m1, k1, moves, depth, preferred):
    ordered = list(moves)
    ordered.sort(
        key=lambda mv: _move_order_score(mv, m0, k0, m1, k1, _ROOT_COLOR, preferred),
        reverse=True,
    )

    alpha = -INF
    beta = INF
    best_move = ordered[0]
    best_val = -INF

    for mv in ordered:
        if perf_counter() >= _DEADLINE:
            raise _Timeout()

        nm0, nk0, nm1, nk1 = _apply_move(m0, k0, m1, k1, 0, mv)
        val = _alphabeta(nm0, nk0, nm1, nk1, 1, depth - 1, alpha, beta, QDEPTH, 1)

        if val > best_val:
            best_val = val
            best_move = mv
        if val > alpha:
            alpha = val

    return best_val, best_move


def _choose_heuristic(moves, m0, k0, m1, k1):
    best = moves[0]
    best_score = -INF

    for mv in moves:
        nm0, nk0, nm1, nk1 = _apply_move(m0, k0, m1, k1, 0, mv)
        score = _evaluate(nm0, nk0, nm1, nk1, 1)
        score += _move_order_score(mv, m0, k0, m1, k1, _ROOT_COLOR, None) // 20
        if score > best_score:
            best_score = score
            best = mv

    return best


def _move_to_return(move):
    fr, to = move[0], move[1]
    return (_coords(fr), _coords(to))


def _no_legal_fallback(m0, k0):
    # This should only happen in a terminal position, where no legal move exists.
    pieces = m0 | k0
    if pieces:
        lsb = pieces & -pieces
        i = lsb.bit_length() - 1
        sq = _coords(i)
        return (sq, sq)
    return ((0, 0), (0, 0))


def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    global _ROOT_COLOR, _OPP_COLOR, _DEADLINE, _NODES, _TT

    c = str(color).lower()
    _ROOT_COLOR = "b" if c.startswith("b") else "w"
    _OPP_COLOR = "w" if _ROOT_COLOR == "b" else "b"

    m0 = _to_bits(my_men)
    k0 = _to_bits(my_kings)
    m1 = _to_bits(opp_men)
    k1 = _to_bits(opp_kings)

    # Valid inputs should already be disjoint, but this makes the bitboards robust.
    m0 &= ~k0
    m1 &= ~k1
    own = m0 | k0
    m1 &= ~own
    k1 &= ~own

    root_moves = _gen_moves(m0, k0, m1, k1, _ROOT_COLOR)
    if not root_moves:
        return _no_legal_fallback(m0, k0)

    if len(root_moves) == 1:
        return _move_to_return(root_moves[0])

    _DEADLINE = perf_counter() + 0.86
    _NODES = 0
    _TT = {}

    best_move = root_moves[0]

    try:
        best_move = _choose_heuristic(root_moves, m0, k0, m1, k1)
    except Exception:
        best_move = root_moves[0]

    total = (m0 | k0 | m1 | k1).bit_count()

    if total <= 6:
        max_depth = 14
    elif total <= 10:
        max_depth = 12
    elif total <= 14:
        max_depth = 10
    elif total <= 18:
        max_depth = 8
    else:
        max_depth = 7

    if root_moves[0][2] >= 0:
        max_depth += 2
    if len(root_moves) <= 3:
        max_depth += 2

    preferred = best_move

    for depth in range(1, max_depth + 1):
        try:
            val, move = _search_root(m0, k0, m1, k1, root_moves, depth, preferred)
            best_move = move
            preferred = move

            if abs(val) > WIN // 2:
                break
            if perf_counter() >= _DEADLINE - 0.03:
                break
        except _Timeout:
            break
        except Exception:
            break

    return _move_to_return(best_move)
