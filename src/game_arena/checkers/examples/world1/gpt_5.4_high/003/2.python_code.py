
import time

BLACK = 0
WHITE = 1

INF = 10**9
MATE = 10**6

EXACT = 0
LOWER = 1
UPPER = 2

BIT = [1 << i for i in range(64)]
ROW = [i // 8 for i in range(64)]
COL = [i % 8 for i in range(64)]

KING_DIRS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
MAN_DIRS = {
    BLACK: [(-1, -1), (-1, 1)],
    WHITE: [(1, -1), (1, 1)],
}

SIMPLE_MAN = [[[] for _ in range(64)] for _ in range(2)]
JUMPS_MAN = [[[] for _ in range(64)] for _ in range(2)]
SIMPLE_KING = [[] for _ in range(64)]
JUMPS_KING = [[] for _ in range(64)]

PST_MAN = [[0] * 64 for _ in range(2)]
PST_KING = [0] * 64

for s in range(64):
    r, c = divmod(s, 8)

    for side in (BLACK, WHITE):
        for dr, dc in MAN_DIRS[side]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                SIMPLE_MAN[side][s].append(nr * 8 + nc)

            mr, mc = r + dr, c + dc
            lr, lc = r + 2 * dr, c + 2 * dc
            if 0 <= mr < 8 and 0 <= mc < 8 and 0 <= lr < 8 and 0 <= lc < 8:
                JUMPS_MAN[side][s].append((mr * 8 + mc, lr * 8 + lc))

    for dr, dc in KING_DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 8 and 0 <= nc < 8:
            SIMPLE_KING[s].append(nr * 8 + nc)

        mr, mc = r + dr, c + dc
        lr, lc = r + 2 * dr, c + 2 * dc
        if 0 <= mr < 8 and 0 <= mc < 8 and 0 <= lr < 8 and 0 <= lc < 8:
            JUMPS_KING[s].append((mr * 8 + mc, lr * 8 + lc))

    center = 6 if (2 <= r <= 5 and 2 <= c <= 5) else 3 if (1 <= r <= 6 and 1 <= c <= 6) else 0
    edge = 1 if (r in (0, 7) or c in (0, 7)) else 0

    PST_MAN[WHITE][s] = 5 * r + center + (8 if r == 6 else 0) + (4 if r == 0 else 0) + edge
    PST_MAN[BLACK][s] = 5 * (7 - r) + center + (8 if r == 1 else 0) + (4 if r == 7 else 0) + edge

    PST_KING[s] = (10 if (2 <= r <= 5 and 2 <= c <= 5) else 5 if (1 <= r <= 6 and 1 <= c <= 6) else 0) - edge

TT = {}
DEADLINE = 0.0
NODE_COUNT = 0


class SearchTimeout(Exception):
    pass


def iter_bits(mask):
    while mask:
        lsb = mask & -mask
        s = lsb.bit_length() - 1
        yield s
        mask ^= lsb


def idx_to_rc(idx):
    return (ROW[idx], COL[idx])


def squares_to_mask(squares):
    m = 0
    for r, c in squares:
        m |= BIT[r * 8 + c]
    return m


def apply_capture(bm, bk, wm, wk, turn, s, is_king, over, land):
    bs = BIT[s]
    bo = BIT[over]
    bl = BIT[land]

    if turn == BLACK:
        if is_king:
            nbm = bm
            nbk = (bk ^ bs) | bl
        else:
            nbm = bm ^ bs
            nbk = bk

        if wm & bo:
            nwm = wm ^ bo
            nwk = wk
            gain = 100
        else:
            nwm = wm
            nwk = wk ^ bo
            gain = 185

        if not is_king:
            if ROW[land] == 0:
                nbk |= bl
                next_is_king = True
                promoted = True
            else:
                nbm |= bl
                next_is_king = False
                promoted = False
        else:
            next_is_king = True
            promoted = False

    else:
        if is_king:
            nwm = wm
            nwk = (wk ^ bs) | bl
        else:
            nwm = wm ^ bs
            nwk = wk

        if bm & bo:
            nbm = bm ^ bo
            nbk = bk
            gain = 100
        else:
            nbm = bm
            nbk = bk ^ bo
            gain = 185

        if not is_king:
            if ROW[land] == 7:
                nwk |= bl
                next_is_king = True
                promoted = True
            else:
                nwm |= bl
                next_is_king = False
                promoted = False
        else:
            next_is_king = True
            promoted = False

    return nbm, nbk, nwm, nwk, next_is_king, promoted, gain


def apply_move(bm, bk, wm, wk, turn, s, is_king, land):
    bs = BIT[s]
    bl = BIT[land]

    if turn == BLACK:
        if is_king:
            return bm, (bk ^ bs) | bl, wm, wk
        nbm = bm ^ bs
        if ROW[land] == 0:
            return nbm, bk | bl, wm, wk
        return nbm | bl, bk, wm, wk

    else:
        if is_king:
            return bm, bk, wm, (wk ^ bs) | bl
        nwm = wm ^ bs
        if ROW[land] == 7:
            return bm, bk, nwm, wk | bl
        return bm, bk, nwm | bl, wk


def any_capture(bm, bk, wm, wk, turn):
    occ = bm | bk | wm | wk
    if turn == BLACK:
        opp = wm | wk
        for s in iter_bits(bm):
            for over, land in JUMPS_MAN[BLACK][s]:
                if (opp & BIT[over]) and not (occ & BIT[land]):
                    return True
        for s in iter_bits(bk):
            for over, land in JUMPS_KING[s]:
                if (opp & BIT[over]) and not (occ & BIT[land]):
                    return True
    else:
        opp = bm | bk
        for s in iter_bits(wm):
            for over, land in JUMPS_MAN[WHITE][s]:
                if (opp & BIT[over]) and not (occ & BIT[land]):
                    return True
        for s in iter_bits(wk):
            for over, land in JUMPS_KING[s]:
                if (opp & BIT[over]) and not (occ & BIT[land]):
                    return True
    return False


def _continue_captures(bm, bk, wm, wk, turn, s, is_king, start_from, first_to, cap_value, moves):
    occ = bm | bk | wm | wk
    opp = (wm | wk) if turn == BLACK else (bm | bk)
    jumps = JUMPS_KING[s] if is_king else JUMPS_MAN[turn][s]

    found = False
    for over, land in jumps:
        if (opp & BIT[over]) and not (occ & BIT[land]):
            found = True
            nbm, nbk, nwm, nwk, next_is_king, promoted, gain = apply_capture(
                bm, bk, wm, wk, turn, s, is_king, over, land
            )
            if promoted:
                hint = cap_value + gain + 90 + PST_KING[land]
                moves.append((start_from, first_to, nbm, nbk, nwm, nwk, 1 - turn, hint))
            else:
                _continue_captures(
                    nbm, nbk, nwm, nwk, turn, land, next_is_king,
                    start_from, first_to, cap_value + gain, moves
                )

    if not found:
        pos_bonus = PST_KING[s] + 20 if is_king else PST_MAN[turn][s]
        moves.append((start_from, first_to, bm, bk, wm, wk, 1 - turn, cap_value + pos_bonus))


def gen_moves(bm, bk, wm, wk, turn):
    occ = bm | bk | wm | wk
    moves = []

    if turn == BLACK:
        opp = wm | wk

        for s in iter_bits(bm):
            for over, land in JUMPS_MAN[BLACK][s]:
                if (opp & BIT[over]) and not (occ & BIT[land]):
                    nbm, nbk, nwm, nwk, next_is_king, promoted, gain = apply_capture(
                        bm, bk, wm, wk, BLACK, s, False, over, land
                    )
                    if promoted:
                        hint = gain + 90 + PST_KING[land]
                        moves.append((s, land, nbm, nbk, nwm, nwk, WHITE, hint))
                    else:
                        _continue_captures(nbm, nbk, nwm, nwk, BLACK, land, next_is_king, s, land, gain, moves)

        for s in iter_bits(bk):
            for over, land in JUMPS_KING[s]:
                if (opp & BIT[over]) and not (occ & BIT[land]):
                    nbm, nbk, nwm, nwk, next_is_king, promoted, gain = apply_capture(
                        bm, bk, wm, wk, BLACK, s, True, over, land
                    )
                    _continue_captures(nbm, nbk, nwm, nwk, BLACK, land, next_is_king, s, land, gain, moves)

        if moves:
            return moves

        for s in iter_bits(bm):
            for land in SIMPLE_MAN[BLACK][s]:
                if not (occ & BIT[land]):
                    nbm, nbk, nwm, nwk = apply_move(bm, bk, wm, wk, BLACK, s, False, land)
                    promoted = (ROW[land] == 0)
                    hint = (80 if promoted else 0) + (PST_KING[land] if promoted else PST_MAN[BLACK][land])
                    moves.append((s, land, nbm, nbk, nwm, nwk, WHITE, hint))

        for s in iter_bits(bk):
            for land in SIMPLE_KING[s]:
                if not (occ & BIT[land]):
                    nbm, nbk, nwm, nwk = apply_move(bm, bk, wm, wk, BLACK, s, True, land)
                    hint = PST_KING[land] + 15
                    moves.append((s, land, nbm, nbk, nwm, nwk, WHITE, hint))

    else:
        opp = bm | bk

        for s in iter_bits(wm):
            for over, land in JUMPS_MAN[WHITE][s]:
                if (opp & BIT[over]) and not (occ & BIT[land]):
                    nbm, nbk, nwm, nwk, next_is_king, promoted, gain = apply_capture(
                        bm, bk, wm, wk, WHITE, s, False, over, land
                    )
                    if promoted:
                        hint = gain + 90 + PST_KING[land]
                        moves.append((s, land, nbm, nbk, nwm, nwk, BLACK, hint))
                    else:
                        _continue_captures(nbm, nbk, nwm, nwk, WHITE, land, next_is_king, s, land, gain, moves)

        for s in iter_bits(wk):
            for over, land in JUMPS_KING[s]:
                if (opp & BIT[over]) and not (occ & BIT[land]):
                    nbm, nbk, nwm, nwk, next_is_king, promoted, gain = apply_capture(
                        bm, bk, wm, wk, WHITE, s, True, over, land
                    )
                    _continue_captures(nbm, nbk, nwm, nwk, WHITE, land, next_is_king, s, land, gain, moves)

        if moves:
            return moves

        for s in iter_bits(wm):
            for land in SIMPLE_MAN[WHITE][s]:
                if not (occ & BIT[land]):
                    nbm, nbk, nwm, nwk = apply_move(bm, bk, wm, wk, WHITE, s, False, land)
                    promoted = (ROW[land] == 7)
                    hint = (80 if promoted else 0) + (PST_KING[land] if promoted else PST_MAN[WHITE][land])
                    moves.append((s, land, nbm, nbk, nwm, nwk, BLACK, hint))

        for s in iter_bits(wk):
            for land in SIMPLE_KING[s]:
                if not (occ & BIT[land]):
                    nbm, nbk, nwm, nwk = apply_move(bm, bk, wm, wk, WHITE, s, True, land)
                    hint = PST_KING[land] + 15
                    moves.append((s, land, nbm, nbk, nwm, nwk, BLACK, hint))

    return moves


def mobility(bm, bk, wm, wk, side):
    occ = bm | bk | wm | wk
    count = 0
    if side == BLACK:
        for s in iter_bits(bm):
            for land in SIMPLE_MAN[BLACK][s]:
                if not (occ & BIT[land]):
                    count += 1
        for s in iter_bits(bk):
            for land in SIMPLE_KING[s]:
                if not (occ & BIT[land]):
                    count += 1
    else:
        for s in iter_bits(wm):
            for land in SIMPLE_MAN[WHITE][s]:
                if not (occ & BIT[land]):
                    count += 1
        for s in iter_bits(wk):
            for land in SIMPLE_KING[s]:
                if not (occ & BIT[land]):
                    count += 1
    return count


def threatened_value_side(bm, bk, wm, wk, side):
    occ = bm | bk | wm | wk
    threatened_m = 0
    threatened_k = 0

    if side == BLACK:
        target_m = bm
        target_k = bk
        target = bm | bk

        for s in iter_bits(wm):
            for over, land in JUMPS_MAN[WHITE][s]:
                bo = BIT[over]
                if (target & bo) and not (occ & BIT[land]):
                    if target_m & bo:
                        threatened_m |= bo
                    else:
                        threatened_k |= bo

        for s in iter_bits(wk):
            for over, land in JUMPS_KING[s]:
                bo = BIT[over]
                if (target & bo) and not (occ & BIT[land]):
                    if target_m & bo:
                        threatened_m |= bo
                    else:
                        threatened_k |= bo

    else:
        target_m = wm
        target_k = wk
        target = wm | wk

        for s in iter_bits(bm):
            for over, land in JUMPS_MAN[BLACK][s]:
                bo = BIT[over]
                if (target & bo) and not (occ & BIT[land]):
                    if target_m & bo:
                        threatened_m |= bo
                    else:
                        threatened_k |= bo

        for s in iter_bits(bk):
            for over, land in JUMPS_KING[s]:
                bo = BIT[over]
                if (target & bo) and not (occ & BIT[land]):
                    if target_m & bo:
                        threatened_m |= bo
                    else:
                        threatened_k |= bo

    return 18 * threatened_m.bit_count() + 32 * threatened_k.bit_count()


def static_eval_signed(bm, bk, wm, wk, turn):
    score = 0

    score += 100 * (wm.bit_count() - bm.bit_count())
    score += 185 * (wk.bit_count() - bk.bit_count())

    for s in iter_bits(wm):
        score += PST_MAN[WHITE][s]
    for s in iter_bits(bm):
        score -= PST_MAN[BLACK][s]
    for s in iter_bits(wk):
        score += 10 + PST_KING[s]
    for s in iter_bits(bk):
        score -= 10 + PST_KING[s]

    total = (bm | bk | wm | wk).bit_count()

    if total <= 16:
        score += threatened_value_side(bm, bk, wm, wk, BLACK)
        score -= threatened_value_side(bm, bk, wm, wk, WHITE)

    if total <= 10:
        score += 2 * (mobility(bm, bk, wm, wk, WHITE) - mobility(bm, bk, wm, wk, BLACK))

    return score if turn == WHITE else -score


def order_moves(moves, preferred):
    if preferred is None:
        moves.sort(key=lambda m: m[7], reverse=True)
    else:
        moves.sort(key=lambda m: (0 if (m[0], m[1]) == preferred else 1, -m[7]))


def search(bm, bk, wm, wk, turn, depth, alpha, beta, ply):
    global NODE_COUNT, DEADLINE, TT

    NODE_COUNT += 1
    if (NODE_COUNT & 1023) == 0 and time.perf_counter() >= DEADLINE:
        raise SearchTimeout

    orig_alpha = alpha
    orig_beta = beta
    key = (bm, bk, wm, wk, turn)

    entry = TT.get(key)
    tt_move = None
    if entry is not None:
        edepth, escore, eflag, emove = entry
        tt_move = emove
        if edepth >= depth:
            if eflag == EXACT:
                return escore
            if eflag == LOWER and escore > alpha:
                alpha = escore
            elif eflag == UPPER and escore < beta:
                beta = escore
            if alpha >= beta:
                return escore

    if depth <= 0:
        if not any_capture(bm, bk, wm, wk, turn):
            return static_eval_signed(bm, bk, wm, wk, turn)
        depth = 1

    moves = gen_moves(bm, bk, wm, wk, turn)
    if not moves:
        return -MATE + ply

    order_moves(moves, tt_move)

    best = -INF
    best_first = (moves[0][0], moves[0][1])

    for m in moves:
        score = -search(m[2], m[3], m[4], m[5], m[6], depth - 1, -beta, -alpha, ply + 1)
        if score > best:
            best = score
            best_first = (m[0], m[1])
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break

    if best <= orig_alpha:
        flag = UPPER
    elif best >= orig_beta:
        flag = LOWER
    else:
        flag = EXACT

    TT[key] = (depth, best, flag, best_first)
    return best


def search_root(bm, bk, wm, wk, turn, depth, preferred):
    moves = gen_moves(bm, bk, wm, wk, turn)
    order_moves(moves, preferred)

    alpha = -INF
    beta = INF
    best_score = -INF
    best_move = moves[0]

    for m in moves:
        if time.perf_counter() >= DEADLINE:
            raise SearchTimeout
        score = -search(m[2], m[3], m[4], m[5], m[6], depth - 1, -beta, -alpha, 1)
        if score > best_score:
            best_score = score
            best_move = m
        if score > alpha:
            alpha = score

    return best_score, best_move


def emergency_fallback(my_men, my_kings, opp_men, opp_kings, color):
    my_set = set(my_men) | set(my_kings)
    opp_set = set(opp_men) | set(opp_kings)
    occ = my_set | opp_set

    forward = [(-1, -1), (-1, 1)] if color == 'b' else [(1, -1), (1, 1)]
    all_dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

    captures = []

    for r, c in my_men:
        for dr, dc in all_dirs:
            mr, mc = r + dr, c + dc
            lr, lc = r + 2 * dr, c + 2 * dc
            if 0 <= mr < 8 and 0 <= mc < 8 and 0 <= lr < 8 and 0 <= lc < 8:
                if (mr, mc) in opp_set and (lr, lc) not in occ:
                    captures.append(((r, c), (lr, lc)))

    for r, c in my_kings:
        for dr, dc in all_dirs:
            mr, mc = r + dr, c + dc
            lr, lc = r + 2 * dr, c + 2 * dc
            if 0 <= mr < 8 and 0 <= mc < 8 and 0 <= lr < 8 and 0 <= lc < 8:
                if (mr, mc) in opp_set and (lr, lc) not in occ:
                    captures.append(((r, c), (lr, lc)))

    if captures:
        return captures[0]

    moves = []

    for r, c in my_men:
        for dr, dc in forward:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8 and (nr, nc) not in occ:
                moves.append(((r, c), (nr, nc)))

    for r, c in my_kings:
        for dr, dc in all_dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8 and (nr, nc) not in occ:
                moves.append(((r, c), (nr, nc)))

    if moves:
        return moves[0]

    if my_men:
        return (my_men[0], my_men[0])
    if my_kings:
        return (my_kings[0], my_kings[0])
    return ((0, 0), (0, 0))


def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    global DEADLINE, NODE_COUNT, TT

    my_men_mask = squares_to_mask(my_men)
    my_kings_mask = squares_to_mask(my_kings)
    opp_men_mask = squares_to_mask(opp_men)
    opp_kings_mask = squares_to_mask(opp_kings)

    if color == 'b':
        bm, bk, wm, wk = my_men_mask, my_kings_mask, opp_men_mask, opp_kings_mask
        turn = BLACK
    else:
        bm, bk, wm, wk = opp_men_mask, opp_kings_mask, my_men_mask, my_kings_mask
        turn = WHITE

    root_moves = gen_moves(bm, bk, wm, wk, turn)
    if not root_moves:
        return emergency_fallback(my_men, my_kings, opp_men, opp_kings, color)

    if len(root_moves) == 1:
        return idx_to_rc(root_moves[0][0]), idx_to_rc(root_moves[0][1])

    if len(TT) > 250000:
        TT.clear()

    NODE_COUNT = 0
    DEADLINE = time.perf_counter() + 0.95

    order_moves(root_moves, None)
    best_move = root_moves[0]
    best_pref = (best_move[0], best_move[1])

    total_pieces = (bm | bk | wm | wk).bit_count()
    if total_pieces <= 6:
        max_depth = 14
    elif total_pieces <= 10:
        max_depth = 12
    elif total_pieces <= 16:
        max_depth = 10
    else:
        max_depth = 8

    for depth in range(1, max_depth + 1):
        try:
            _, move = search_root(bm, bk, wm, wk, turn, depth, best_pref)
            best_move = move
            best_pref = (move[0], move[1])
        except SearchTimeout:
            break

    return idx_to_rc(best_move[0]), idx_to_rc(best_move[1])
