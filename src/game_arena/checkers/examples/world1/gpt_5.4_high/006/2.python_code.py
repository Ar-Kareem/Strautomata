
import time

BLACK = 0
WHITE = 1

INF = 10**9
MATE = 10**6

BIT = [1 << i for i in range(64)]
ROW = [i >> 3 for i in range(64)]
COL = [i & 7 for i in range(64)]
IDX_TO_COORD = [(i >> 3, i & 7) for i in range(64)]

B_SIMPLE = [[] for _ in range(64)]
W_SIMPLE = [[] for _ in range(64)]
K_SIMPLE = [[] for _ in range(64)]

B_CAPTURE = [[] for _ in range(64)]
W_CAPTURE = [[] for _ in range(64)]
K_CAPTURE = [[] for _ in range(64)]

B_MAN_PSQ = [0] * 64
W_MAN_PSQ = [0] * 64
KING_PSQ = [0] * 64

ADJ_MASK = [0] * 64
BLACK_SUPPORT = [0] * 64
WHITE_SUPPORT = [0] * 64

CENTER_BONUS = [0] * 64


def _inside(r: int, c: int) -> bool:
    return 0 <= r < 8 and 0 <= c < 8


def _precompute():
    for idx in range(64):
        r = ROW[idx]
        c = COL[idx]

        # Simple moves
        for dr, dc, arr in [
            (-1, -1, B_SIMPLE),
            (-1,  1, B_SIMPLE),
            ( 1, -1, W_SIMPLE),
            ( 1,  1, W_SIMPLE),
            (-1, -1, K_SIMPLE),
            (-1,  1, K_SIMPLE),
            ( 1, -1, K_SIMPLE),
            ( 1,  1, K_SIMPLE),
        ]:
            nr, nc = r + dr, c + dc
            if _inside(nr, nc):
                arr[idx].append(nr * 8 + nc)

        # Captures
        for dr, dc, arr in [
            (-1, -1, B_CAPTURE),
            (-1,  1, B_CAPTURE),
            ( 1, -1, W_CAPTURE),
            ( 1,  1, W_CAPTURE),
            (-1, -1, K_CAPTURE),
            (-1,  1, K_CAPTURE),
            ( 1, -1, K_CAPTURE),
            ( 1,  1, K_CAPTURE),
        ]:
            mr, mc = r + dr, c + dc
            jr, jc = r + 2 * dr, c + 2 * dc
            if _inside(mr, mc) and _inside(jr, jc):
                arr[idx].append((mr * 8 + mc, jr * 8 + jc))

        # Piece-square tables and local structure masks
        center = 0
        if 2 <= r <= 5 and 2 <= c <= 5:
            center += 4
        if 3 <= r <= 4 and 3 <= c <= 4:
            center += 2
        edge = 2 if c in (0, 7) else 0

        CENTER_BONUS[idx] = center
        B_MAN_PSQ[idx] = (7 - r) * 7 + center + edge
        W_MAN_PSQ[idx] = r * 7 + center + edge
        KING_PSQ[idx] = center * 3 - (1 if c in (0, 7) else 0)

        # Adjacent friendly support / connectivity
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            nr, nc = r + dr, c + dc
            if _inside(nr, nc):
                ADJ_MASK[idx] |= BIT[nr * 8 + nc]

        # Friendly pieces "behind" a man
        for dc in (-1, 1):
            nr, nc = r + 1, c + dc
            if _inside(nr, nc):
                BLACK_SUPPORT[idx] |= BIT[nr * 8 + nc]

            nr, nc = r - 1, c + dc
            if _inside(nr, nc):
                WHITE_SUPPORT[idx] |= BIT[nr * 8 + nc]


_precompute()

EXPECTED_SIG = None
EXPECTED_FORCED = -1

TT = {}
DEADLINE = 0.0
NODE_COUNT = 0


class Timeout(Exception):
    pass


def _maybe_timeout():
    global NODE_COUNT
    NODE_COUNT += 1
    if (NODE_COUNT & 255) == 0 and time.perf_counter() > DEADLINE:
        raise Timeout


def _bits_from_squares(squares) -> int:
    bb = 0
    for sq in squares:
        r, c = sq
        bb |= BIT[r * 8 + c]
    return bb


def _iter_bits(bb: int):
    while bb:
        lsb = bb & -bb
        yield lsb.bit_length() - 1
        bb ^= lsb


def _piece_has_capture(bm: int, bk: int, wm: int, wk: int, turn: int, idx: int, is_king: bool) -> bool:
    occ = bm | bk | wm | wk
    opp = (wm | wk) if turn == BLACK else (bm | bk)
    arr = K_CAPTURE[idx] if is_king else (B_CAPTURE[idx] if turn == BLACK else W_CAPTURE[idx])
    for mid, to in arr:
        if (opp & BIT[mid]) and not (occ & BIT[to]):
            return True
    return False


def _generate_moves(state):
    bm, bk, wm, wk, turn, forced = state
    occ = bm | bk | wm | wk
    own_men = bm if turn == BLACK else wm
    own_kings = bk if turn == BLACK else wk
    opp = (wm | wk) if turn == BLACK else (bm | bk)

    # Forced continuation from a previous jump sequence
    if forced != -1:
        fbit = BIT[forced]
        if own_men & fbit:
            arr = B_CAPTURE[forced] if turn == BLACK else W_CAPTURE[forced]
            caps = []
            for mid, to in arr:
                if (opp & BIT[mid]) and not (occ & BIT[to]):
                    caps.append((forced, to, mid))
            if caps:
                return caps, True
        elif own_kings & fbit:
            caps = []
            for mid, to in K_CAPTURE[forced]:
                if (opp & BIT[mid]) and not (occ & BIT[to]):
                    caps.append((forced, to, mid))
            if caps:
                return caps, True

    captures = []

    arr_cap = B_CAPTURE if turn == BLACK else W_CAPTURE
    bb = own_men
    while bb:
        lsb = bb & -bb
        idx = lsb.bit_length() - 1
        bb ^= lsb
        for mid, to in arr_cap[idx]:
            if (opp & BIT[mid]) and not (occ & BIT[to]):
                captures.append((idx, to, mid))

    bb = own_kings
    while bb:
        lsb = bb & -bb
        idx = lsb.bit_length() - 1
        bb ^= lsb
        for mid, to in K_CAPTURE[idx]:
            if (opp & BIT[mid]) and not (occ & BIT[to]):
                captures.append((idx, to, mid))

    if captures:
        return captures, True

    moves = []

    arr_simple = B_SIMPLE if turn == BLACK else W_SIMPLE
    bb = own_men
    while bb:
        lsb = bb & -bb
        idx = lsb.bit_length() - 1
        bb ^= lsb
        for to in arr_simple[idx]:
            if not (occ & BIT[to]):
                moves.append((idx, to, -1))

    bb = own_kings
    while bb:
        lsb = bb & -bb
        idx = lsb.bit_length() - 1
        bb ^= lsb
        for to in K_SIMPLE[idx]:
            if not (occ & BIT[to]):
                moves.append((idx, to, -1))

    return moves, False


def _apply_move(state, move):
    bm, bk, wm, wk, turn, forced = state
    fr, to, cap = move
    fbit = BIT[fr]
    tbit = BIT[to]

    if turn == BLACK:
        if bm & fbit:
            bm ^= fbit
            promoted = ROW[to] == 0
            if cap != -1:
                cbit = BIT[cap]
                if wm & cbit:
                    wm ^= cbit
                else:
                    wk ^= cbit
            if promoted:
                bk |= tbit
            else:
                bm |= tbit
                if cap != -1 and _piece_has_capture(bm, bk, wm, wk, BLACK, to, False):
                    return (bm, bk, wm, wk, BLACK, to)
            return (bm, bk, wm, wk, WHITE, -1)
        else:
            bk ^= fbit
            if cap != -1:
                cbit = BIT[cap]
                if wm & cbit:
                    wm ^= cbit
                else:
                    wk ^= cbit
            bk |= tbit
            if cap != -1 and _piece_has_capture(bm, bk, wm, wk, BLACK, to, True):
                return (bm, bk, wm, wk, BLACK, to)
            return (bm, bk, wm, wk, WHITE, -1)

    else:
        if wm & fbit:
            wm ^= fbit
            promoted = ROW[to] == 7
            if cap != -1:
                cbit = BIT[cap]
                if bm & cbit:
                    bm ^= cbit
                else:
                    bk ^= cbit
            if promoted:
                wk |= tbit
            else:
                wm |= tbit
                if cap != -1 and _piece_has_capture(bm, bk, wm, wk, WHITE, to, False):
                    return (bm, bk, wm, wk, WHITE, to)
            return (bm, bk, wm, wk, BLACK, -1)
        else:
            wk ^= fbit
            if cap != -1:
                cbit = BIT[cap]
                if bm & cbit:
                    bm ^= cbit
                else:
                    bk ^= cbit
            wk |= tbit
            if cap != -1 and _piece_has_capture(bm, bk, wm, wk, WHITE, to, True):
                return (bm, bk, wm, wk, WHITE, to)
            return (bm, bk, wm, wk, BLACK, -1)


def _pseudo_mobility(bm: int, bk: int, wm: int, wk: int, side: int) -> int:
    occ = bm | bk | wm | wk
    total = 0

    own_men = bm if side == BLACK else wm
    own_kings = bk if side == BLACK else wk
    arr = B_SIMPLE if side == BLACK else W_SIMPLE

    bb = own_men
    while bb:
        lsb = bb & -bb
        idx = lsb.bit_length() - 1
        bb ^= lsb
        for to in arr[idx]:
            if not (occ & BIT[to]):
                total += 1

    bb = own_kings
    while bb:
        lsb = bb & -bb
        idx = lsb.bit_length() - 1
        bb ^= lsb
        for to in K_SIMPLE[idx]:
            if not (occ & BIT[to]):
                total += 1

    return total


def _capture_options(bm: int, bk: int, wm: int, wk: int, side: int) -> int:
    occ = bm | bk | wm | wk
    opp = (wm | wk) if side == BLACK else (bm | bk)
    total = 0

    own_men = bm if side == BLACK else wm
    own_kings = bk if side == BLACK else wk
    arr = B_CAPTURE if side == BLACK else W_CAPTURE

    bb = own_men
    while bb:
        lsb = bb & -bb
        idx = lsb.bit_length() - 1
        bb ^= lsb
        for mid, to in arr[idx]:
            if (opp & BIT[mid]) and not (occ & BIT[to]):
                total += 1

    bb = own_kings
    while bb:
        lsb = bb & -bb
        idx = lsb.bit_length() - 1
        bb ^= lsb
        for mid, to in K_CAPTURE[idx]:
            if (opp & BIT[mid]) and not (occ & BIT[to]):
                total += 1

    return total


def _evaluate(state) -> int:
    bm, bk, wm, wk, turn, forced = state

    black_occ = bm | bk
    white_occ = wm | wk
    total_pieces = (black_occ | white_occ).bit_count()

    man_val = 100
    king_val = 185 if total_pieces > 8 else 195

    black_score = 0
    white_score = 0

    bb = bm
    while bb:
        lsb = bb & -bb
        idx = lsb.bit_length() - 1
        bb ^= lsb
        s = man_val + B_MAN_PSQ[idx]
        if total_pieces > 12 and ROW[idx] == 7:
            s += 8  # back-rank guard early
        if black_occ & BLACK_SUPPORT[idx]:
            s += 4
        if not (black_occ & ADJ_MASK[idx]):
            s -= 3
        black_score += s

    bb = wm
    while bb:
        lsb = bb & -bb
        idx = lsb.bit_length() - 1
        bb ^= lsb
        s = man_val + W_MAN_PSQ[idx]
        if total_pieces > 12 and ROW[idx] == 0:
            s += 8
        if white_occ & WHITE_SUPPORT[idx]:
            s += 4
        if not (white_occ & ADJ_MASK[idx]):
            s -= 3
        white_score += s

    bb = bk
    while bb:
        lsb = bb & -bb
        idx = lsb.bit_length() - 1
        bb ^= lsb
        s = king_val + KING_PSQ[idx]
        if black_occ & ADJ_MASK[idx]:
            s += 2
        black_score += s

    bb = wk
    while bb:
        lsb = bb & -bb
        idx = lsb.bit_length() - 1
        bb ^= lsb
        s = king_val + KING_PSQ[idx]
        if white_occ & ADJ_MASK[idx]:
            s += 2
        white_score += s

    # Endgame-ish dynamic terms
    if total_pieces <= 12:
        black_score += 2 * _pseudo_mobility(bm, bk, wm, wk, BLACK)
        white_score += 2 * _pseudo_mobility(bm, bk, wm, wk, WHITE)

    if total_pieces <= 10:
        black_score += 8 * _capture_options(bm, bk, wm, wk, BLACK)
        white_score += 8 * _capture_options(bm, bk, wm, wk, WHITE)

    score = black_score - white_score
    return score if turn == BLACK else -score


def _move_score(state, move) -> int:
    bm, bk, wm, wk, turn, forced = state
    fr, to, cap = move
    fbit = BIT[fr]
    score = 0

    if turn == BLACK:
        is_king = bool(bk & fbit)
        if cap != -1:
            score += 1000
            cbit = BIT[cap]
            score += 150 if (wk & cbit) else 100
        if not is_king:
            if ROW[to] == 0:
                score += 250
            score += (ROW[fr] - ROW[to]) * 8
            score += B_MAN_PSQ[to] - B_MAN_PSQ[fr]
        else:
            score += KING_PSQ[to] - KING_PSQ[fr]
    else:
        is_king = bool(wk & fbit)
        if cap != -1:
            score += 1000
            cbit = BIT[cap]
            score += 150 if (bk & cbit) else 100
        if not is_king:
            if ROW[to] == 7:
                score += 250
            score += (ROW[to] - ROW[fr]) * 8
            score += W_MAN_PSQ[to] - W_MAN_PSQ[fr]
        else:
            score += KING_PSQ[to] - KING_PSQ[fr]

    score += CENTER_BONUS[to]
    if COL[to] in (0, 7):
        score += 2

    return score


def _order_moves(state, moves, pv_move=None):
    scored = []
    for mv in moves:
        s = _move_score(state, mv)
        if pv_move is not None and mv == pv_move:
            s += 20000
        scored.append((s, mv))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [mv for _, mv in scored]


def _qsearch(state, alpha: int, beta: int, qdepth: int) -> int:
    _maybe_timeout()

    moves, is_capture = _generate_moves(state)
    if not moves:
        return -MATE
    if not is_capture or qdepth <= 0:
        return _evaluate(state)

    turn = state[4]
    best = -INF
    a = alpha

    for mv in _order_moves(state, moves):
        child = _apply_move(state, mv)
        if child[4] == turn:
            score = _qsearch(child, a, beta, qdepth - 1)
        else:
            score = -_qsearch(child, -beta, -a, qdepth - 1)

        if score > best:
            best = score
        if best > a:
            a = best
        if a >= beta:
            break

    return best


def _negamax(state, depth: int, alpha: int, beta: int) -> int:
    _maybe_timeout()

    key = state
    orig_alpha = alpha

    entry = TT.get(key)
    tt_move = None
    if entry is not None:
        e_depth, e_val, e_flag, e_move = entry
        tt_move = e_move
        if e_depth >= depth:
            if e_flag == 0:
                return e_val
            elif e_flag > 0:
                if e_val > alpha:
                    alpha = e_val
            else:
                if e_val < beta:
                    beta = e_val
            if alpha >= beta:
                return e_val

    moves, is_capture = _generate_moves(state)
    if not moves:
        return -MATE + depth

    if depth <= 0:
        if is_capture:
            return _qsearch(state, alpha, beta, 6)
        return _evaluate(state)

    turn = state[4]
    best = -INF
    best_move = moves[0]
    a = alpha

    for mv in _order_moves(state, moves, tt_move):
        child = _apply_move(state, mv)
        if child[4] == turn:
            score = _negamax(child, depth, a, beta)
        else:
            score = -_negamax(child, depth - 1, -beta, -a)

        if score > best:
            best = score
            best_move = mv
        if best > a:
            a = best
        if a >= beta:
            break

    flag = 0
    if best <= orig_alpha:
        flag = -1
    elif best >= beta:
        flag = 1

    TT[key] = (depth, best, flag, best_move)
    return best


def _search_root(state, depth: int, pv_move=None):
    if time.perf_counter() > DEADLINE:
        raise Timeout

    moves, _ = _generate_moves(state)
    if not moves:
        return -MATE, None

    entry = TT.get(state)
    tt_move = entry[3] if entry is not None else None
    ordered = _order_moves(state, moves, tt_move if tt_move is not None else pv_move)

    turn = state[4]
    alpha = -INF
    beta = INF
    best = -INF
    best_move = ordered[0]

    for mv in ordered:
        if time.perf_counter() > DEADLINE:
            raise Timeout

        child = _apply_move(state, mv)
        if child[4] == turn:
            score = _negamax(child, depth, alpha, beta)
        else:
            score = -_negamax(child, depth - 1, -beta, -alpha)

        if score > best:
            best = score
            best_move = mv
        if best > alpha:
            alpha = best

    TT[state] = (depth, best, 0, best_move)
    return best, best_move


def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    global EXPECTED_SIG, EXPECTED_FORCED, TT, DEADLINE, NODE_COUNT

    turn = BLACK if color == 'b' else WHITE

    if color == 'b':
        bm = _bits_from_squares(my_men)
        bk = _bits_from_squares(my_kings)
        wm = _bits_from_squares(opp_men)
        wk = _bits_from_squares(opp_kings)
    else:
        wm = _bits_from_squares(my_men)
        wk = _bits_from_squares(my_kings)
        bm = _bits_from_squares(opp_men)
        bk = _bits_from_squares(opp_kings)

    current_sig = (bm, bk, wm, wk, turn)
    forced = EXPECTED_FORCED if EXPECTED_SIG == current_sig else -1
    if EXPECTED_SIG != current_sig:
        EXPECTED_SIG = None
        EXPECTED_FORCED = -1

    state = (bm, bk, wm, wk, turn, forced)

    legal_moves, _ = _generate_moves(state)
    if not legal_moves:
        # Should not happen in a normal arena call, but keep a total fallback.
        if my_men:
            r, c = my_men[0]
            return ((r, c), (r, c))
        if my_kings:
            r, c = my_kings[0]
            return ((r, c), (r, c))
        return ((0, 0), (0, 0))

    best_move = _order_moves(state, legal_moves)[0]

    if len(legal_moves) > 1:
        TT = {}
        NODE_COUNT = 0
        DEADLINE = time.perf_counter() + 0.92

        max_depth = 10
        for depth in range(1, max_depth + 1):
            try:
                _, mv = _search_root(state, depth, best_move)
                if mv is not None:
                    best_move = mv
            except Timeout:
                break

    child = _apply_move(state, best_move)
    if child[4] == turn and child[5] != -1:
        EXPECTED_SIG = child[:5]
        EXPECTED_FORCED = child[5]
    else:
        EXPECTED_SIG = None
        EXPECTED_FORCED = -1

    return IDX_TO_COORD[best_move[0]], IDX_TO_COORD[best_move[1]]
