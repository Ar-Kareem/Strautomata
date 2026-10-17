
import time
from functools import lru_cache

INF = 10**9
MATE = 10**6

DIR_B = ((-1, -1), (-1, 1))  # black moves downward (toward lower rows)
DIR_W = ((1, -1), (1, 1))    # white moves upward (toward higher rows)
DIR_K = ((-1, -1), (-1, 1), (1, -1), (1, 1))

ROWS = tuple(i >> 3 for i in range(64))
COLS = tuple(i & 7 for i in range(64))
ROW_MASK = tuple(sum(1 << (r * 8 + c) for c in range(8)) for r in range(8))


def _inside(r: int, c: int) -> bool:
    return 0 <= r < 8 and 0 <= c < 8


def _make_tables():
    move_b = []
    move_w = []
    move_k = []
    cap_b = []
    cap_w = []
    cap_k = []
    backcap_b = []
    backcap_w = []

    for sq in range(64):
        r = sq >> 3
        c = sq & 7

        def steps(dirs):
            out = []
            for dr, dc in dirs:
                r1, c1 = r + dr, c + dc
                if _inside(r1, c1):
                    out.append((r1 << 3) + c1)
            return tuple(out)

        def jumps(dirs):
            out = []
            for dr, dc in dirs:
                r1, c1 = r + dr, c + dc
                r2, c2 = r + 2 * dr, c + 2 * dc
                if _inside(r1, c1) and _inside(r2, c2):
                    out.append((((r1 << 3) + c1), ((r2 << 3) + c2)))
            return tuple(out)

        move_b.append(steps(DIR_B))
        move_w.append(steps(DIR_W))
        move_k.append(steps(DIR_K))
        cap_b.append(jumps(DIR_B))
        cap_w.append(jumps(DIR_W))
        cap_k.append(jumps(DIR_K))
        backcap_b.append(jumps(DIR_W))  # fallback only if no standard move exists
        backcap_w.append(jumps(DIR_B))

    return (
        tuple(move_b),
        tuple(move_w),
        tuple(move_k),
        tuple(cap_b),
        tuple(cap_w),
        tuple(cap_k),
        tuple(backcap_b),
        tuple(backcap_w),
    )


MOVE_B, MOVE_W, MOVE_K, CAP_B, CAP_W, CAP_K, BACKCAP_B, BACKCAP_W = _make_tables()

CENTER_BONUS = []
MEN_PST_B = []
MEN_PST_W = []
KING_PST = []

for sq in range(64):
    r = ROWS[sq]
    c = COLS[sq]

    center = int(7 - (abs(3.5 - r) + abs(3.5 - c)))
    if center < 0:
        center = 0

    men_center = 2 * center
    king_center = 4 * center

    MEN_PST_B.append(4 * (7 - r) + men_center)
    MEN_PST_W.append(4 * r + men_center)
    KING_PST.append(king_center)

CENTER_BONUS = tuple(CENTER_BONUS if CENTER_BONUS else [int(7 - (abs(3.5 - ROWS[sq]) + abs(3.5 - COLS[sq]))) for sq in range(64)])
MEN_PST_B = tuple(MEN_PST_B)
MEN_PST_W = tuple(MEN_PST_W)
KING_PST = tuple(KING_PST)


def _iter_bits(bb: int):
    while bb:
        lsb = bb & -bb
        yield lsb.bit_length() - 1
        bb ^= lsb


def _coord_to_sq(rc):
    return rc[0] * 8 + rc[1]


def _sq_to_coord(sq: int):
    return (sq >> 3, sq & 7)


def _coords_to_bb(pieces) -> int:
    bb = 0
    for r, c in pieces:
        bb |= 1 << (r * 8 + c)
    return bb


def _sum_from_table(bb: int, table) -> int:
    s = 0
    while bb:
        lsb = bb & -bb
        sq = lsb.bit_length() - 1
        s += table[sq]
        bb ^= lsb
    return s


@lru_cache(maxsize=65536)
def _men_b_score(bb: int) -> int:
    return _sum_from_table(bb, MEN_PST_B)


@lru_cache(maxsize=65536)
def _men_w_score(bb: int) -> int:
    return _sum_from_table(bb, MEN_PST_W)


@lru_cache(maxsize=65536)
def _king_score(bb: int) -> int:
    return _sum_from_table(bb, KING_PST)


def _move_key(move, turn: str, opp_k: int) -> int:
    fr, to, cap, is_king = move
    score = 0

    if cap != -1:
        score += 1000
        score += 260 if ((opp_k >> cap) & 1) else 150

    if is_king:
        score += 30 + KING_PST[to]
    else:
        if turn == 'b':
            score += MEN_PST_B[to]
            if ROWS[to] == 0:
                score += 200
        else:
            score += MEN_PST_W[to]
            if ROWS[to] == 7:
                score += 200

    return score


@lru_cache(maxsize=200000)
def _get_moves(bm: int, bk: int, wm: int, wk: int, turn: str):
    if turn == 'b':
        my_m, my_k, opp_m, opp_k = bm, bk, wm, wk
        man_moves = MOVE_B
        man_caps = CAP_B
        back_caps = BACKCAP_B
    else:
        my_m, my_k, opp_m, opp_k = wm, wk, bm, bk
        man_moves = MOVE_W
        man_caps = CAP_W
        back_caps = BACKCAP_W

    occ = bm | bk | wm | wk
    opp = opp_m | opp_k

    captures = []

    x = my_m
    while x:
        lsb = x & -x
        fr = lsb.bit_length() - 1
        x ^= lsb
        for mid, to in man_caps[fr]:
            if ((opp >> mid) & 1) and not ((occ >> to) & 1):
                captures.append((fr, to, mid, 0))

    x = my_k
    while x:
        lsb = x & -x
        fr = lsb.bit_length() - 1
        x ^= lsb
        for mid, to in CAP_K[fr]:
            if ((opp >> mid) & 1) and not ((occ >> to) & 1):
                captures.append((fr, to, mid, 1))

    if captures:
        captures.sort(key=lambda mv: _move_key(mv, turn, opp_k), reverse=True)
        return tuple(captures)

    quiet = []

    x = my_m
    while x:
        lsb = x & -x
        fr = lsb.bit_length() - 1
        x ^= lsb
        for to in man_moves[fr]:
            if not ((occ >> to) & 1):
                quiet.append((fr, to, -1, 0))

    x = my_k
    while x:
        lsb = x & -x
        fr = lsb.bit_length() - 1
        x ^= lsb
        for to in MOVE_K[fr]:
            if not ((occ >> to) & 1):
                quiet.append((fr, to, -1, 1))

    if quiet:
        quiet.sort(key=lambda mv: _move_key(mv, turn, opp_k), reverse=True)
        return tuple(quiet)

    # Fallback: if no standard legal move exists, allow backward-capture lookup.
    # This is only for robustness against edge-case rule implementations.
    fallback_caps = []

    x = my_m
    while x:
        lsb = x & -x
        fr = lsb.bit_length() - 1
        x ^= lsb
        for mid, to in back_caps[fr]:
            if ((opp >> mid) & 1) and not ((occ >> to) & 1):
                fallback_caps.append((fr, to, mid, 0))

    if fallback_caps:
        fallback_caps.sort(key=lambda mv: _move_key(mv, turn, opp_k), reverse=True)
        return tuple(fallback_caps)

    return ()


def _apply_move(bm: int, bk: int, wm: int, wk: int, turn: str, move):
    fr, to, cap, is_king = move
    fr_mask = 1 << fr
    to_mask = 1 << to

    if turn == 'b':
        if is_king:
            bk = (bk ^ fr_mask) | to_mask
        else:
            bm ^= fr_mask
            if ROWS[to] == 0:
                bk |= to_mask
            else:
                bm |= to_mask

        if cap != -1:
            cap_mask = 1 << cap
            if wm & cap_mask:
                wm ^= cap_mask
            else:
                wk ^= cap_mask

        return bm, bk, wm, wk, 'w'

    else:
        if is_king:
            wk = (wk ^ fr_mask) | to_mask
        else:
            wm ^= fr_mask
            if ROWS[to] == 7:
                wk |= to_mask
            else:
                wm |= to_mask

        if cap != -1:
            cap_mask = 1 << cap
            if bm & cap_mask:
                bm ^= cap_mask
            else:
                bk ^= cap_mask

        return bm, bk, wm, wk, 'b'


def _evaluate_abs(bm: int, bk: int, wm: int, wk: int) -> int:
    nbm = bm.bit_count()
    nbk = bk.bit_count()
    nwm = wm.bit_count()
    nwk = wk.bit_count()
    total = nbm + nbk + nwm + nwk

    king_val = 180
    if total <= 8:
        king_val += 20
    if total <= 4:
        king_val += 10

    score = 100 * (nbm - nwm) + king_val * (nbk - nwk)
    score += _men_b_score(bm) - _men_w_score(wm)
    score += _king_score(bk) - _king_score(wk)

    # Early: preserve back rank. Late: reward men near promotion.
    if total > 12:
        score += 5 * (((bm & ROW_MASK[7]).bit_count()) - ((wm & ROW_MASK[0]).bit_count()))
    else:
        score += 4 * (((bm & ROW_MASK[1]).bit_count()) - ((wm & ROW_MASK[6]).bit_count()))

    # Endgame mobility matters more.
    if total <= 10:
        mb = len(_get_moves(bm, bk, wm, wk, 'b'))
        mw = len(_get_moves(bm, bk, wm, wk, 'w'))
        score += 3 * (mb - mw)

    return score


def _evaluate_rel(bm: int, bk: int, wm: int, wk: int, turn: str) -> int:
    s = _evaluate_abs(bm, bk, wm, wk)
    return s if turn == 'b' else -s


TT = {}
DEADLINE = 0.0
NODE_COUNTER = 0


def _negamax(bm: int, bk: int, wm: int, wk: int, turn: str, depth: int, alpha: int, beta: int) -> int:
    global TT, DEADLINE, NODE_COUNTER

    NODE_COUNTER += 1
    if (NODE_COUNTER & 511) == 0 and time.perf_counter() >= DEADLINE:
        raise TimeoutError

    key = (bm, bk, wm, wk, turn)
    alpha_orig = alpha

    entry = TT.get(key)
    tt_move = entry[3] if entry is not None else None

    if entry is not None and entry[0] >= depth:
        flag = entry[1]
        val = entry[2]
        if flag == 0:
            return val
        elif flag == 1:  # lower bound
            if val > alpha:
                alpha = val
        else:  # upper bound
            if val < beta:
                beta = val
        if alpha >= beta:
            return val

    moves = _get_moves(bm, bk, wm, wk, turn)

    if not moves:
        return -MATE

    if depth <= 0:
        # Small capture extension to reduce tactical horizon issues.
        if moves[0][2] != -1:
            depth = 1
        else:
            return _evaluate_rel(bm, bk, wm, wk, turn)

    if tt_move is not None and tt_move in moves and moves[0] != tt_move:
        ordered = (tt_move,) + tuple(m for m in moves if m != tt_move)
    else:
        ordered = moves

    best = -INF
    best_move = ordered[0]

    for mv in ordered:
        child = _apply_move(bm, bk, wm, wk, turn, mv)
        val = -_negamax(*child, depth - 1, -beta, -alpha)

        if val > best:
            best = val
            best_move = mv

        if val > alpha:
            alpha = val

        if alpha >= beta:
            break

    if best >= beta:
        flag = 1  # lower bound
    elif best <= alpha_orig:
        flag = 2  # upper bound
    else:
        flag = 0  # exact

    TT[key] = (depth, flag, best, best_move)
    return best


def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    global TT, DEADLINE, NODE_COUNTER

    if color == 'b':
        bm = _coords_to_bb(my_men)
        bk = _coords_to_bb(my_kings)
        wm = _coords_to_bb(opp_men)
        wk = _coords_to_bb(opp_kings)
        turn = 'b'
    else:
        wm = _coords_to_bb(my_men)
        wk = _coords_to_bb(my_kings)
        bm = _coords_to_bb(opp_men)
        bk = _coords_to_bb(opp_kings)
        turn = 'w'

    moves = _get_moves(bm, bk, wm, wk, turn)

    if not moves:
        pieces = list(my_men) + list(my_kings)
        if pieces:
            fr = pieces[0]
            for dr in (-1, 1):
                for dc in (-1, 1):
                    tr, tc = fr[0] + dr, fr[1] + dc
                    if 0 <= tr < 8 and 0 <= tc < 8:
                        return (fr, (tr, tc))
            return (fr, fr)
        return ((0, 0), (0, 0))

    if len(moves) == 1:
        mv = moves[0]
        return (_sq_to_coord(mv[0]), _sq_to_coord(mv[1]))

    TT = {}
    NODE_COUNTER = 0
    DEADLINE = time.perf_counter() + 0.92

    best_move = moves[0]
    root_order = list(moves)
    last_score = -INF

    max_depth = 18

    for depth in range(1, max_depth + 1):
        try:
            if time.perf_counter() >= DEADLINE:
                break

            alpha = -INF
            beta = INF
            scored = []
            current_best = best_move
            current_best_score = -INF

            for mv in root_order:
                if time.perf_counter() >= DEADLINE:
                    raise TimeoutError

                child = _apply_move(bm, bk, wm, wk, turn, mv)
                val = -_negamax(*child, depth - 1, -beta, -alpha)
                scored.append((val, mv))

                if val > current_best_score:
                    current_best_score = val
                    current_best = mv

                if val > alpha:
                    alpha = val

            scored.sort(key=lambda x: x[0], reverse=True)
            root_order = [mv for _, mv in scored]
            best_move = current_best
            last_score = current_best_score

            if abs(last_score) >= MATE // 2:
                break

        except TimeoutError:
            break

    return (_sq_to_coord(best_move[0]), _sq_to_coord(best_move[1]))
