
from __future__ import annotations

import time

# ---------- Constants and precomputed board data ----------

_WIN = 10_000_000
_INF = 100_000_000
_TIME_LIMIT = 0.86
_TT_LIMIT = 180_000
_EXTENSION_LIMIT = 1

_BOARD_MASK = (1 << 64) - 1
_ROW_MASKS = tuple(0xFF << (8 * r) for r in range(8))

_COL0 = sum(1 << (8 * r) for r in range(8))
_COL7 = _COL0 << 7
_NOT_COL0 = _BOARD_MASK ^ _COL0
_NOT_COL7 = _BOARD_MASK ^ _COL7

_ROW = tuple(sq >> 3 for sq in range(64))
_COL = tuple(sq & 7 for sq in range(64))
_BIT = tuple(1 << sq for sq in range(64))

# Progress for a side moving toward larger rows / smaller rows.
_ADV_POS = _ROW
_ADV_NEG = tuple(7 - r for r in _ROW)

_ADV_BONUS = (0, 8, 25, 60, 130, 280, 650, 0)
_CENTER = (0, 3, 8, 12, 12, 8, 3, 0)

_PST_POS = tuple(
    _ADV_BONUS[_ADV_POS[sq]] + _CENTER[_COL[sq]] * (1 + _ADV_POS[sq] // 2)
    for sq in range(64)
)
_PST_NEG = tuple(
    _ADV_BONUS[_ADV_NEG[sq]] + _CENTER[_COL[sq]] * (1 + _ADV_NEG[sq] // 2)
    for sq in range(64)
)

_PASSED_BONUS = (0, 18, 55, 140, 330, 760, 1700, 0)
_CANDIDATE_BONUS = (0, 5, 18, 45, 110, 260, 650, 0)

# Forward cones and narrow lanes for passed-pawn evaluation.
_cone_pos = []
_cone_neg = []
_narrow_pos = []
_narrow_neg = []

for sq in range(64):
    r = _ROW[sq]
    c = _COL[sq]

    mask = 0
    narrow = 0
    for rr in range(r + 1, 8):
        dist = rr - r
        for cc in range(max(0, c - dist), min(7, c + dist) + 1):
            mask |= _BIT[rr * 8 + cc]
        for cc in range(max(0, c - 1), min(7, c + 1) + 1):
            narrow |= _BIT[rr * 8 + cc]
    _cone_pos.append(mask)
    _narrow_pos.append(narrow)

    mask = 0
    narrow = 0
    for rr in range(r - 1, -1, -1):
        dist = r - rr
        for cc in range(max(0, c - dist), min(7, c + dist) + 1):
            mask |= _BIT[rr * 8 + cc]
        for cc in range(max(0, c - 1), min(7, c + 1) + 1):
            narrow |= _BIT[rr * 8 + cc]
    _cone_neg.append(mask)
    _narrow_neg.append(narrow)

_CONE_POS = tuple(_cone_pos)
_CONE_NEG = tuple(_cone_neg)
_NARROW_POS = tuple(_narrow_pos)
_NARROW_NEG = tuple(_narrow_neg)

_EXACT, _LOWER, _UPPER = 0, 1, 2

_deadline = 0.0
_nodes = 0
_tt = {}


class _Timeout(Exception):
    pass


# ---------- Basic bitboard helpers ----------

def _list_to_bb(pieces):
    bb = 0
    for r, c in pieces:
        if 0 <= r < 8 and 0 <= c < 8:
            bb |= _BIT[(r << 3) | c]
    return bb


def _to_tuple(move):
    fr, to = move
    return ((_ROW[fr], _COL[fr]), (_ROW[to], _COL[to]))


def _attacks(bb, d):
    """Diagonal-forward squares for side moving in direction d."""
    if d > 0:
        return ((((bb & _NOT_COL0) << 7) | ((bb & _NOT_COL7) << 9)) & _BOARD_MASK)
    return (((bb & _NOT_COL0) >> 9) | ((bb & _NOT_COL7) >> 7))


def _straight_targets(bb, d, empty):
    if d > 0:
        return (((bb << 8) & _BOARD_MASK) & empty)
    return ((bb >> 8) & empty)


def _terminal_score(us, opp, d):
    if not us:
        return -_WIN
    if not opp:
        return _WIN

    if d > 0:
        if us & _ROW_MASKS[7]:
            return _WIN
        if opp & _ROW_MASKS[0]:
            return -_WIN
    else:
        if us & _ROW_MASKS[0]:
            return _WIN
        if opp & _ROW_MASKS[7]:
            return -_WIN

    return None


def _gen_moves(us, opp, d):
    occ = us | opp
    moves = []
    bb = us

    if d > 0:
        while bb:
            lsb = bb & -bb
            sq = lsb.bit_length() - 1
            bb ^= lsb

            if sq >= 56:
                continue

            c = sq & 7

            to = sq + 8
            tb = _BIT[to]
            if not (tb & occ):
                moves.append((sq, to))

            if c > 0:
                to = sq + 7
                tb = _BIT[to]
                if not (tb & us):
                    moves.append((sq, to))

            if c < 7:
                to = sq + 9
                tb = _BIT[to]
                if not (tb & us):
                    moves.append((sq, to))
    else:
        while bb:
            lsb = bb & -bb
            sq = lsb.bit_length() - 1
            bb ^= lsb

            if sq < 8:
                continue

            c = sq & 7

            to = sq - 8
            tb = _BIT[to]
            if not (tb & occ):
                moves.append((sq, to))

            if c > 0:
                to = sq - 9
                tb = _BIT[to]
                if not (tb & us):
                    moves.append((sq, to))

            if c < 7:
                to = sq - 7
                tb = _BIT[to]
                if not (tb & us):
                    moves.append((sq, to))

    return moves


def _apply_move(us, opp, move):
    fr, to = move
    fb = _BIT[fr]
    tb = _BIT[to]
    return ((us ^ fb) | tb), (opp & ~tb)


def _has_winning_move(us, opp, d):
    if not us:
        return False
    if not opp:
        return True

    occ = us | opp

    # Promotion in one move.
    if d > 0:
        cand = us & _ROW_MASKS[6]
        while cand:
            lsb = cand & -cand
            sq = lsb.bit_length() - 1
            cand ^= lsb
            c = sq & 7

            to = sq + 8
            if not (_BIT[to] & occ):
                return True
            if c > 0 and not (_BIT[sq + 7] & us):
                return True
            if c < 7 and not (_BIT[sq + 9] & us):
                return True
    else:
        cand = us & _ROW_MASKS[1]
        while cand:
            lsb = cand & -cand
            sq = lsb.bit_length() - 1
            cand ^= lsb
            c = sq & 7

            to = sq - 8
            if not (_BIT[to] & occ):
                return True
            if c > 0 and not (_BIT[sq - 9] & us):
                return True
            if c < 7 and not (_BIT[sq - 7] & us):
                return True

    # Capture the last opposing piece.
    if opp and (opp & (opp - 1)) == 0:
        if _attacks(us, d) & opp:
            return True

    return False


def _is_immediate_win(move, opp, d):
    to = move[1]
    if _ROW[to] == (7 if d > 0 else 0):
        return True
    tb = _BIT[to]
    return bool((opp & tb) and ((opp & ~tb) == 0))


# ---------- Evaluation ----------

def _passed_score(us, enemy, d):
    if d > 0:
        cones = _CONE_POS
        narrow = _NARROW_POS
        adv = _ADV_POS
    else:
        cones = _CONE_NEG
        narrow = _NARROW_NEG
        adv = _ADV_NEG

    total = 0
    bb = us
    while bb:
        lsb = bb & -bb
        sq = lsb.bit_length() - 1
        bb ^= lsb

        a = adv[sq]
        if (enemy & cones[sq]) == 0:
            total += _PASSED_BONUS[a]
        elif (enemy & narrow[sq]) == 0:
            total += _CANDIDATE_BONUS[a]

    return total


def _evaluate(us, opp, d):
    term = _terminal_score(us, opp, d)
    if term is not None:
        return term

    uc = us.bit_count()
    oc = opp.bit_count()

    score = 120 * (uc - oc) + 10  # small tempo bonus

    if d > 0:
        adv_u, pst_u = _ADV_POS, _PST_POS
        adv_o, pst_o = _ADV_NEG, _PST_NEG
    else:
        adv_u, pst_u = _ADV_NEG, _PST_NEG
        adv_o, pst_o = _ADV_POS, _PST_POS

    max_u = 0
    max_o = 0

    bb = us
    while bb:
        lsb = bb & -bb
        sq = lsb.bit_length() - 1
        bb ^= lsb

        a = adv_u[sq]
        if a > max_u:
            max_u = a
        score += pst_u[sq]

    bb = opp
    while bb:
        lsb = bb & -bb
        sq = lsb.bit_length() - 1
        bb ^= lsb

        a = adv_o[sq]
        if a > max_o:
            max_o = a
        score -= pst_o[sq]

    # Race pressure: the most advanced pawn is very important.
    score += 55 * (max_u - max_o)

    pieces = uc + oc
    if pieces <= 12:
        score += (13 - pieces) * 8 * (max_u - max_o)

    # Passed pawns / open lanes.
    score += _passed_score(us, opp, d)
    score -= _passed_score(opp, us, -d)

    us_att = _attacks(us, d)
    opp_att = _attacks(opp, -d)

    us_under = opp_att & us
    opp_under = us_att & opp

    us_def = us_att & us
    opp_def = opp_att & opp

    score += 22 * (opp_under.bit_count() - us_under.bit_count())
    score += 34 * ((opp_under & ~opp_def).bit_count() - (us_under & ~us_def).bit_count())
    score += 10 * (us_def.bit_count() - opp_def.bit_count())

    occ = us | opp
    empty = _BOARD_MASK & ~occ

    mob_u = _straight_targets(us, d, empty).bit_count() + (us_att & ~us).bit_count()
    mob_o = _straight_targets(opp, -d, empty).bit_count() + (opp_att & ~opp).bit_count()
    score += 3 * (mob_u - mob_o)

    # If the opponent threatens to win next turn, this position is urgent.
    if _has_winning_move(opp, us, -d):
        score -= 4000

    return score


# ---------- Move ordering and search ----------

def _order_moves(moves, us, opp, d, tt_best):
    if len(moves) <= 1:
        return moves

    opp_att = _attacks(opp, -d)
    adv_arr = _ADV_POS if d > 0 else _ADV_NEG
    opp_adv_arr = _ADV_NEG if d > 0 else _ADV_POS
    goal_row = 7 if d > 0 else 0
    one_opp_left = opp != 0 and (opp & (opp - 1)) == 0

    scored = []
    for m in moves:
        fr, to = m
        tb = _BIT[to]

        s = adv_arr[to] * 1000 + _CENTER[_COL[to]] * 25

        if _ROW[to] == goal_row:
            s += 10_000_000

        if opp & tb:
            s += 300_000 + opp_adv_arr[to] * 25_000
            if one_opp_left:
                s += 8_000_000

        if adv_arr[to] == 6:
            s += 90_000

        if m == tt_best:
            s += 20_000_000

        if opp_att & _BIT[fr]:
            s += 2500
        if opp_att & tb:
            s -= 1200

        if (to - fr) != (8 * d):
            s += 100

        scored.append((s, m))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored]


def _negamax(us, opp, d, depth, alpha, beta, ext):
    global _nodes

    _nodes += 1
    if (_nodes & 511) == 0 and time.perf_counter() >= _deadline:
        raise _Timeout()

    term = _terminal_score(us, opp, d)
    if term is not None:
        return term

    # Exact tactical shortcut: current side can win immediately.
    if _has_winning_move(us, opp, d):
        return _WIN - 1

    # One-ply "check" extension: if the opponent has a direct win threat,
    # spend one extra ply to see whether it can be parried.
    if depth <= 0:
        if ext > 0 and _has_winning_move(opp, us, -d):
            depth = 1
            ext -= 1
        else:
            return _evaluate(us, opp, d)

    alpha_orig = alpha
    beta_orig = beta

    key = (us, opp, d, ext)
    entry = _tt.get(key)
    tt_best = None

    if entry is not None:
        e_depth, e_score, e_flag, e_best = entry
        tt_best = e_best

        if e_depth >= depth:
            if e_flag == _EXACT:
                return e_score
            if e_flag == _LOWER:
                if e_score > alpha:
                    alpha = e_score
            elif e_flag == _UPPER:
                if e_score < beta:
                    beta = e_score

            if alpha >= beta:
                return e_score

    moves = _gen_moves(us, opp, d)
    if not moves:
        return -_WIN + 1

    moves = _order_moves(moves, us, opp, d, tt_best)

    best_val = -_INF
    best_move = None
    first = True

    for m in moves:
        n_us, n_opp = _apply_move(us, opp, m)

        if first:
            val = -_negamax(n_opp, n_us, -d, depth - 1, -beta, -alpha, ext)
            first = False
        else:
            # Principal variation search.
            val = -_negamax(n_opp, n_us, -d, depth - 1, -alpha - 1, -alpha, ext)
            if alpha < val < beta:
                val = -_negamax(n_opp, n_us, -d, depth - 1, -beta, -alpha, ext)

        if val > best_val:
            best_val = val
            best_move = m

        if val > alpha:
            alpha = val

        if alpha >= beta:
            break

    if best_val <= alpha_orig:
        flag = _UPPER
    elif best_val >= beta_orig:
        flag = _LOWER
    else:
        flag = _EXACT

    if len(_tt) < _TT_LIMIT:
        _tt[key] = (depth, best_val, flag, best_move)

    return best_val


def _search_root(us, opp, d, depth, preferred):
    moves = _gen_moves(us, opp, d)
    if not moves:
        return -_WIN + 1, None

    moves = _order_moves(moves, us, opp, d, preferred)

    alpha = -_INF
    beta = _INF
    best_score = -_INF
    best_move = moves[0]
    first = True

    for m in moves:
        n_us, n_opp = _apply_move(us, opp, m)

        if first:
            score = -_negamax(n_opp, n_us, -d, depth - 1, -beta, -alpha, _EXTENSION_LIMIT)
            first = False
        else:
            score = -_negamax(n_opp, n_us, -d, depth - 1, -alpha - 1, -alpha, _EXTENSION_LIMIT)
            if alpha < score < beta:
                score = -_negamax(n_opp, n_us, -d, depth - 1, -beta, -alpha, _EXTENSION_LIMIT)

        if score > best_score:
            best_score = score
            best_move = m

        if score > alpha:
            alpha = score

        if best_score >= _WIN - 1:
            break

        if time.perf_counter() >= _deadline:
            raise _Timeout()

    return best_score, best_move


def _choose_greedy(us, opp, d, moves):
    ordered = _order_moves(moves, us, opp, d, None)

    best = ordered[0]
    best_score = -_INF

    for m in ordered:
        n_us, n_opp = _apply_move(us, opp, m)

        # Score from our perspective; child node is opponent to move.
        term = _terminal_score(n_opp, n_us, -d)
        if term is not None:
            val = -term
        elif _has_winning_move(n_opp, n_us, -d):
            val = -(_WIN - 1)
        else:
            val = -_evaluate(n_opp, n_us, -d)

        if val > best_score:
            best_score = val
            best = m

    return best


def _max_depth(total_pieces):
    if total_pieces <= 6:
        return 24
    if total_pieces <= 10:
        return 18
    if total_pieces <= 16:
        return 12
    if total_pieces <= 24:
        return 9
    return 7


def _emergency_move(me, opp, d):
    own = {(r, c) for r, c in me}
    enemy = {(r, c) for r, c in opp}
    occ = own | enemy

    for r, c in me:
        nr = r + d
        if 0 <= nr < 8:
            if (nr, c) not in occ:
                return ((r, c), (nr, c))
            if c > 0 and (nr, c - 1) not in own:
                return ((r, c), (nr, c - 1))
            if c < 7 and (nr, c + 1) not in own:
                return ((r, c), (nr, c + 1))

    # This should only occur in terminal or malformed positions.
    if me:
        r, c = me[0]
        nr = max(0, min(7, r + d))
        return ((r, c), (nr, c))
    return ((0, 0), (0, 0))


# ---------- Required API ----------

def policy(
    me: list[tuple[int, int]],
    opp: list[tuple[int, int]],
    color: str,
) -> tuple[tuple[int, int], tuple[int, int]]:
    global _deadline, _nodes, _tt

    d = 1 if str(color).lower().startswith("w") else -1

    us = _list_to_bb(me)
    them = _list_to_bb(opp)

    moves = _gen_moves(us, them, d)
    if not moves:
        return _emergency_move(me, opp, d)

    # Always take an immediate win.
    for m in moves:
        if _is_immediate_win(m, them, d):
            return _to_tuple(m)

    # Legal fallback before any time-consuming search.
    best = moves[0]
    try:
        best = _choose_greedy(us, them, d, moves)
    except Exception:
        best = moves[0]

    _deadline = time.perf_counter() + _TIME_LIMIT
    _nodes = 0
    _tt = {}

    total_pieces = us.bit_count() + them.bit_count()
    max_d = _max_depth(total_pieces)

    try:
        for depth in range(1, max_d + 1):
            if time.perf_counter() >= _deadline:
                break

            score, move = _search_root(us, them, d, depth, best)
            if move is not None:
                best = move

            if score >= _WIN - 1:
                break

    except Exception:
        # Timeout or any unexpected search issue: return the already legal fallback/best.
        pass

    return _to_tuple(best)
