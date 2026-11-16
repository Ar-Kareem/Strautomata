
from __future__ import annotations

from time import perf_counter

BLACK = 0
WHITE = 1

INF = 10**9
WIN = 10**7

TIME_LIMIT = 0.85
QUIESCENCE_DEPTH = 5
TT_LIMIT = 250_000

EXACT = 0
LOWER = 1
UPPER = 2

MAN_DIRS = (
    ((-1, -1), (-1, 1)),  # black moves toward lower rows
    ((1, -1), (1, 1)),    # white moves toward higher rows
)
KING_DIRS = ((-1, -1), (-1, 1), (1, -1), (1, 1))

ROW = tuple(sq // 8 for sq in range(64))
COL = tuple(sq % 8 for sq in range(64))
BIT = tuple(1 << sq for sq in range(64))

PROMOTE_ROW = (0, 7)
HOME_ROW = (7, 0)
ROW_MASKS = tuple(sum(BIT[r * 8 + c] for c in range(8)) for r in range(8))
PROMOTE_MASK = (ROW_MASKS[0], ROW_MASKS[7])

CENTER_VALUE = tuple(
    14 - (abs(2 * ROW[sq] - 7) + abs(2 * COL[sq] - 7))
    for sq in range(64)
)
PROGRESS = (
    tuple(7 - ROW[sq] for sq in range(64)),  # black progress toward row 0
    tuple(ROW[sq] for sq in range(64)),      # white progress toward row 7
)


def _in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def _build_tables():
    man_steps = [[[] for _ in range(64)] for _ in range(2)]
    man_jumps = [[[] for _ in range(64)] for _ in range(2)]
    king_steps = [[] for _ in range(64)]
    king_jumps = [[] for _ in range(64)]

    vuln_man = [[[] for _ in range(64)] for _ in range(2)]
    vuln_king = [[] for _ in range(64)]

    for sq in range(64):
        r, c = ROW[sq], COL[sq]

        for color in (BLACK, WHITE):
            for dr, dc in MAN_DIRS[color]:
                r1, c1 = r + dr, c + dc
                r2, c2 = r + 2 * dr, c + 2 * dc

                if _in_bounds(r1, c1):
                    man_steps[color][sq].append(r1 * 8 + c1)
                if _in_bounds(r1, c1) and _in_bounds(r2, c2):
                    man_jumps[color][sq].append((r1 * 8 + c1, r2 * 8 + c2))

                ar, ac = r - dr, c - dc
                lr, lc = r + dr, c + dc
                if _in_bounds(ar, ac) and _in_bounds(lr, lc):
                    vuln_man[color][sq].append((ar * 8 + ac, lr * 8 + lc))

        for dr, dc in KING_DIRS:
            r1, c1 = r + dr, c + dc
            r2, c2 = r + 2 * dr, c + 2 * dc

            if _in_bounds(r1, c1):
                king_steps[sq].append(r1 * 8 + c1)
            if _in_bounds(r1, c1) and _in_bounds(r2, c2):
                king_jumps[sq].append((r1 * 8 + c1, r2 * 8 + c2))

            ar, ac = r - dr, c - dc
            lr, lc = r + dr, c + dc
            if _in_bounds(ar, ac) and _in_bounds(lr, lc):
                vuln_king[sq].append((ar * 8 + ac, lr * 8 + lc))

    return man_steps, man_jumps, king_steps, king_jumps, vuln_man, vuln_king


MAN_STEPS, MAN_JUMPS, KING_STEPS, KING_JUMPS, VULN_MAN, VULN_KING = _build_tables()


class _Timeout(Exception):
    pass


def _color_index(color):
    return BLACK if str(color).lower().startswith("b") else WHITE


def _to_bits(pieces):
    bb = 0
    for r, c in pieces:
        rr, cc = int(r), int(c)
        if 0 <= rr < 8 and 0 <= cc < 8:
            bb |= 1 << (rr * 8 + cc)
    return bb


def _normalize(men, kings, color_idx):
    kings |= men & PROMOTE_MASK[color_idx]
    men &= ~kings
    return men, kings


def _as_tuple(move):
    f, t, _ = move
    return ((ROW[f], COL[f]), (ROW[t], COL[t]))


def _gen_moves(men, kings, emen, ekings, color_idx):
    occ = men | kings | emen | ekings
    enemy = emen | ekings
    B = BIT

    captures = []

    bb = men
    table = MAN_JUMPS[color_idx]
    while bb:
        lsb = bb & -bb
        sq = lsb.bit_length() - 1
        bb ^= lsb
        for mid, dst in table[sq]:
            if (enemy & B[mid]) and not (occ & B[dst]):
                captures.append((sq, dst, mid))

    bb = kings
    while bb:
        lsb = bb & -bb
        sq = lsb.bit_length() - 1
        bb ^= lsb
        for mid, dst in KING_JUMPS[sq]:
            if (enemy & B[mid]) and not (occ & B[dst]):
                captures.append((sq, dst, mid))

    if captures:
        return captures

    moves = []

    bb = men
    table = MAN_STEPS[color_idx]
    while bb:
        lsb = bb & -bb
        sq = lsb.bit_length() - 1
        bb ^= lsb
        for dst in table[sq]:
            if not (occ & B[dst]):
                moves.append((sq, dst, -1))

    bb = kings
    while bb:
        lsb = bb & -bb
        sq = lsb.bit_length() - 1
        bb ^= lsb
        for dst in KING_STEPS[sq]:
            if not (occ & B[dst]):
                moves.append((sq, dst, -1))

    return moves


def _apply(men, kings, emen, ekings, color_idx, move):
    f, t, cap = move
    fb = BIT[f]
    tb = BIT[t]

    if kings & fb:
        kings = (kings ^ fb) | tb
    else:
        men ^= fb
        if ROW[t] == PROMOTE_ROW[color_idx]:
            kings |= tb
        else:
            men |= tb

    if cap >= 0:
        cb = BIT[cap]
        if emen & cb:
            emen ^= cb
        else:
            ekings &= ~cb

    return men, kings, emen, ekings


def _mobility_count(men, kings, emen, ekings, color_idx):
    occ = men | kings | emen | ekings
    enemy = emen | ekings
    B = BIT

    caps = 0

    bb = men
    table = MAN_JUMPS[color_idx]
    while bb:
        lsb = bb & -bb
        sq = lsb.bit_length() - 1
        bb ^= lsb
        for mid, dst in table[sq]:
            if (enemy & B[mid]) and not (occ & B[dst]):
                caps += 1

    bb = kings
    while bb:
        lsb = bb & -bb
        sq = lsb.bit_length() - 1
        bb ^= lsb
        for mid, dst in KING_JUMPS[sq]:
            if (enemy & B[mid]) and not (occ & B[dst]):
                caps += 1

    if caps:
        return caps

    moves = 0

    bb = men
    table = MAN_STEPS[color_idx]
    while bb:
        lsb = bb & -bb
        sq = lsb.bit_length() - 1
        bb ^= lsb
        for dst in table[sq]:
            if not (occ & B[dst]):
                moves += 1

    bb = kings
    while bb:
        lsb = bb & -bb
        sq = lsb.bit_length() - 1
        bb ^= lsb
        for dst in KING_STEPS[sq]:
            if not (occ & B[dst]):
                moves += 1

    return moves


def _square_attacked_by(sq, amen, akings, att_color, occ):
    B = BIT

    for attacker, landing in VULN_MAN[att_color][sq]:
        if (amen & B[attacker]) and not (occ & B[landing]):
            return True

    for attacker, landing in VULN_KING[sq]:
        if (akings & B[attacker]) and not (occ & B[landing]):
            return True

    return False


def _vulnerability_score(vmen, vkings, amen, akings, att_color):
    occ = vmen | vkings | amen | akings
    score = 0

    bb = vmen
    while bb:
        lsb = bb & -bb
        sq = lsb.bit_length() - 1
        bb ^= lsb
        if _square_attacked_by(sq, amen, akings, att_color, occ):
            score += 30

    bb = vkings
    while bb:
        lsb = bb & -bb
        sq = lsb.bit_length() - 1
        bb ^= lsb
        if _square_attacked_by(sq, amen, akings, att_color, occ):
            score += 52

    return score


def _men_pos_score(bb, color_idx, advance_weight):
    score = 0
    home = HOME_ROW[color_idx]

    while bb:
        lsb = bb & -bb
        sq = lsb.bit_length() - 1
        bb ^= lsb

        r, c = ROW[sq], COL[sq]
        score += advance_weight * PROGRESS[color_idx][sq]
        score += CENTER_VALUE[sq]

        if c == 0 or c == 7:
            score += 3
        if r == home:
            score += 5
        if (color_idx == BLACK and r == 1) or (color_idx == WHITE and r == 6):
            score += 10

    return score


def _king_pos_score(bb):
    score = 0

    while bb:
        lsb = bb & -bb
        sq = lsb.bit_length() - 1
        bb ^= lsb

        r, c = ROW[sq], COL[sq]
        score += 2 * CENTER_VALUE[sq]
        if c == 0 or c == 7:
            score -= 4
        if r == 0 or r == 7:
            score -= 2

    return score


def _evaluate(men, kings, emen, ekings, color_idx):
    mm = men.bit_count()
    mk = kings.bit_count()
    om = emen.bit_count()
    ok = ekings.bit_count()

    if mm + mk == 0:
        return -WIN
    if om + ok == 0:
        return WIN

    total_pieces = mm + mk + om + ok
    opp_color = color_idx ^ 1

    king_value = 180 if total_pieces > 8 else 195
    material = 100 * (mm - om) + king_value * (mk - ok)
    score = material

    advance_weight = 5 if total_pieces > 10 else 8

    score += _men_pos_score(men, color_idx, advance_weight)
    score -= _men_pos_score(emen, opp_color, advance_weight)

    score += _king_pos_score(kings)
    score -= _king_pos_score(ekings)

    my_mob = _mobility_count(men, kings, emen, ekings, color_idx)
    op_mob = _mobility_count(emen, ekings, men, kings, opp_color)
    score += 3 * (my_mob - op_mob)

    my_vuln = _vulnerability_score(men, kings, emen, ekings, opp_color)
    op_vuln = _vulnerability_score(emen, ekings, men, kings, color_idx)
    score += op_vuln - my_vuln

    # When ahead, exchanges are usually good; when behind, preserve material.
    if material > 120:
        score -= 2 * total_pieces
    elif material < -120:
        score += 2 * total_pieces

    return score


def _move_order_score(move, men, kings, emen, ekings, color_idx):
    f, t, cap = move
    moving_king = bool(kings & BIT[f])
    score = 0

    if cap >= 0:
        score += 10_000
        score += 800 if (ekings & BIT[cap]) else 400
        if not moving_king and ROW[t] == PROMOTE_ROW[color_idx]:
            score += 700
        if moving_king:
            score -= 20
    else:
        if not moving_king:
            score += 20 * (PROGRESS[color_idx][t] - PROGRESS[color_idx][f])
            if ROW[t] == PROMOTE_ROW[color_idx]:
                score += 700

    if moving_king:
        score += 3 * CENTER_VALUE[t]
        if COL[t] == 0 or COL[t] == 7:
            score -= 8
    else:
        score += 2 * CENTER_VALUE[t]
        if COL[t] == 0 or COL[t] == 7:
            score += 4

    return score


def _root_static_choice(moves, men, kings, emen, ekings, color_idx):
    opp_color = color_idx ^ 1
    best = moves[0]
    best_val = -INF

    for mv in moves:
        m2, k2, e2, ek2 = _apply(men, kings, emen, ekings, color_idx, mv)

        if not (e2 | ek2):
            val = WIN
        else:
            opp_moves = _gen_moves(e2, ek2, m2, k2, opp_color)
            if not opp_moves:
                val = WIN // 2
            else:
                val = _evaluate(m2, k2, e2, ek2, color_idx)
                if opp_moves[0][2] >= 0:
                    worst_capture = 0
                    for omv in opp_moves:
                        cap = omv[2]
                        if cap >= 0:
                            captured_value = 180 if (k2 & BIT[cap]) else 100
                            if captured_value > worst_capture:
                                worst_capture = captured_value
                    val -= worst_capture // 2

        val += _move_order_score(mv, men, kings, emen, ekings, color_idx) // 30

        if val > best_val:
            best_val = val
            best = mv

    return best


def _choose_depth_limit(total_pieces, root_move_count, root_is_capture):
    if total_pieces <= 4:
        depth = 16
    elif total_pieces <= 8:
        depth = 13
    elif total_pieces <= 12:
        depth = 11
    elif total_pieces <= 18:
        depth = 9
    else:
        depth = 7

    if root_is_capture:
        depth += 2
    if root_move_count >= 10 and total_pieces >= 18:
        depth -= 1

    return max(4, depth)


def _panic_move(men, kings, emen, ekings, color_idx):
    moves = _gen_moves(men, kings, emen, ekings, color_idx)
    if moves:
        return _as_tuple(moves[0])

    occ = men | kings | emen | ekings

    # Last-resort fallback. In a non-terminal legal call this should not be reached.
    own = men | kings
    if own:
        lsb = own & -own
        sq = lsb.bit_length() - 1

        for dst in KING_STEPS[sq]:
            if not (occ & BIT[dst]):
                return ((ROW[sq], COL[sq]), (ROW[dst], COL[dst]))

        return ((ROW[sq], COL[sq]), (ROW[sq], COL[sq]))

    return ((0, 0), (0, 0))


def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    try:
        color_idx = _color_index(color)
        opp_color = color_idx ^ 1

        men = _to_bits(my_men)
        kings = _to_bits(my_kings)
        emen = _to_bits(opp_men)
        ekings = _to_bits(opp_kings)

        men, kings = _normalize(men, kings, color_idx)
        emen, ekings = _normalize(emen, ekings, opp_color)

        # Prefer our pieces if malformed overlapping input ever occurs.
        own_occ = men | kings
        emen &= ~own_occ
        ekings &= ~own_occ

        root_moves = _gen_moves(men, kings, emen, ekings, color_idx)
        if not root_moves:
            return _panic_move(men, kings, emen, ekings, color_idx)

        if len(root_moves) == 1:
            return _as_tuple(root_moves[0])

        best_move = _root_static_choice(root_moves, men, kings, emen, ekings, color_idx)

        clock = perf_counter
        deadline = clock() + TIME_LIMIT
        nodes = 0
        tt = {}

        def search(s_men, s_kings, s_emen, s_ekings, side_color, depth, alpha, beta, qleft):
            nonlocal nodes

            nodes += 1
            if (nodes & 1023) == 0 and clock() >= deadline:
                raise _Timeout()

            if not (s_men | s_kings):
                return -WIN
            if not (s_emen | s_ekings):
                return WIN

            key = (s_men, s_kings, s_emen, s_ekings, side_color)
            tt_move = None
            entry = tt.get(key)
            if entry is not None:
                e_depth, e_qleft, e_val, e_flag, e_best = entry
                tt_move = e_best
                if e_depth >= depth and e_qleft >= qleft:
                    if e_flag == EXACT:
                        return e_val
                    if e_flag == LOWER and e_val >= beta:
                        return e_val
                    if e_flag == UPPER and e_val <= alpha:
                        return e_val

            moves = _gen_moves(s_men, s_kings, s_emen, s_ekings, side_color)
            if not moves:
                return -WIN

            is_capture_node = moves[0][2] >= 0

            if depth <= 0 and (not is_capture_node or qleft <= 0):
                val = _evaluate(s_men, s_kings, s_emen, s_ekings, side_color)
                if len(tt) < TT_LIMIT or key in tt:
                    tt[key] = (depth, qleft, val, EXACT, tt_move)
                return val

            if len(moves) > 1:
                moves.sort(
                    key=lambda mv: (
                        (1_000_000 if mv == tt_move else 0)
                        + _move_order_score(mv, s_men, s_kings, s_emen, s_ekings, side_color)
                    ),
                    reverse=True,
                )

            alpha_orig = alpha
            value = -INF
            best_local = moves[0]
            next_color = side_color ^ 1

            if depth > 0:
                next_depth = depth - 1
                next_qleft = qleft
            else:
                next_depth = 0
                next_qleft = qleft - 1

            for mv in moves:
                m2, k2, e2, ek2 = _apply(
                    s_men, s_kings, s_emen, s_ekings, side_color, mv
                )
                score = -search(
                    e2,
                    ek2,
                    m2,
                    k2,
                    next_color,
                    next_depth,
                    -beta,
                    -alpha,
                    next_qleft,
                )

                if score > value:
                    value = score
                    best_local = mv
                if score > alpha:
                    alpha = score
                if alpha >= beta:
                    break

            if value <= alpha_orig:
                flag = UPPER
            elif value >= beta:
                flag = LOWER
            else:
                flag = EXACT

            if len(tt) < TT_LIMIT or key in tt:
                tt[key] = (depth, qleft, value, flag, best_local)

            return value

        total_pieces = (men | kings | emen | ekings).bit_count()
        max_depth = _choose_depth_limit(total_pieces, len(root_moves), root_moves[0][2] >= 0)

        root_order = list(root_moves)
        root_order.sort(
            key=lambda mv: (
                (1_000_000 if mv == best_move else 0)
                + _move_order_score(mv, men, kings, emen, ekings, color_idx)
            ),
            reverse=True,
        )

        last_scores = {}

        for depth in range(1, max_depth + 1):
            if clock() >= deadline:
                break

            if last_scores:
                root_order.sort(key=lambda mv: last_scores.get(mv, -INF), reverse=True)

            depth_scores = {}
            depth_best = best_move
            depth_best_score = -INF
            alpha = -INF
            qdepth = 2 if depth == 1 else QUIESCENCE_DEPTH

            try:
                for mv in root_order:
                    if clock() >= deadline:
                        raise _Timeout()

                    m2, k2, e2, ek2 = _apply(men, kings, emen, ekings, color_idx, mv)
                    score = -search(
                        e2,
                        ek2,
                        m2,
                        k2,
                        opp_color,
                        depth - 1,
                        -INF,
                        -alpha,
                        qdepth,
                    )

                    depth_scores[mv] = score

                    if score > depth_best_score:
                        depth_best_score = score
                        depth_best = mv

                    if score > alpha:
                        alpha = score

            except _Timeout:
                break

            best_move = depth_best
            last_scores = depth_scores

            if depth_best_score >= WIN // 2:
                break

        return _as_tuple(best_move)

    except Exception:
        try:
            color_idx = _color_index(color)
            opp_color = color_idx ^ 1
            men = _to_bits(my_men)
            kings = _to_bits(my_kings)
            emen = _to_bits(opp_men)
            ekings = _to_bits(opp_kings)
            men, kings = _normalize(men, kings, color_idx)
            emen, ekings = _normalize(emen, ekings, opp_color)
            own_occ = men | kings
            emen &= ~own_occ
            ekings &= ~own_occ
            return _panic_move(men, kings, emen, ekings, color_idx)
        except Exception:
            return ((0, 0), (0, 0))
