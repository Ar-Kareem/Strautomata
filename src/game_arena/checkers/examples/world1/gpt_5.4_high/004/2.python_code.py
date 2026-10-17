
import time

# Directions: (dr, dc)
# 0: NW (+1, -1), 1: NE (+1, +1), 2: SW (-1, -1), 3: SE (-1, +1)
DIRS = ((1, -1), (1, 1), (-1, -1), (-1, 1))
WHITE_DIRS = (0, 1)
BLACK_DIRS = (2, 3)
KING_DIRS = (0, 1, 2, 3)

ROW = [i // 8 for i in range(64)]
COL = [i % 8 for i in range(64)]
BIT = [1 << i for i in range(64)]

STEP = [[-1] * 4 for _ in range(64)]
JUMP = [[-1] * 4 for _ in range(64)]

for sq in range(64):
    r, c = ROW[sq], COL[sq]
    for d, (dr, dc) in enumerate(DIRS):
        r1, c1 = r + dr, c + dc
        if 0 <= r1 < 8 and 0 <= c1 < 8:
            STEP[sq][d] = r1 * 8 + c1
        r2, c2 = r + 2 * dr, c + 2 * dc
        if 0 <= r2 < 8 and 0 <= c2 < 8 and 0 <= r1 < 8 and 0 <= c1 < 8:
            JUMP[sq][d] = r2 * 8 + c2

# Piece-square values
MAN_W = [0] * 64
MAN_B = [0] * 64
KING_PST = [0] * 64

for sq in range(64):
    r, c = ROW[sq], COL[sq]

    if 2 <= r <= 5 and 2 <= c <= 5:
        center = 6
    elif 1 <= r <= 6 and 1 <= c <= 6:
        center = 3
    else:
        center = 0

    edge_col = 2 if c in (0, 7) else 0
    edge_any = 4 if (r in (0, 7) or c in (0, 7)) else 0

    MAN_W[sq] = 100 + 10 * r + center + edge_col + (12 if r == 6 else 0) + (6 if r == 0 else 0)
    MAN_B[sq] = 100 + 10 * (7 - r) + center + edge_col + (12 if r == 1 else 0) + (6 if r == 7 else 0)
    KING_PST[sq] = 184 + 2 * center - edge_any

INF = 10**9
WIN = 10**6

EXACT = 0
LOWER = 1
UPPER = 2


class SearchTimeout(Exception):
    pass


def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    BIT_ = BIT
    ROW_ = ROW
    COL_ = COL
    STEP_ = STEP
    JUMP_ = JUMP
    MAN_W_ = MAN_W
    MAN_B_ = MAN_B
    KING_ = KING_PST

    def squares_to_bb(squares):
        bb = 0
        for r, c in squares:
            if 0 <= r < 8 and 0 <= c < 8:
                bb |= 1 << (r * 8 + c)
        return bb

    # Absolute board representation
    if color == 'w':
        wm = squares_to_bb(my_men)
        wk = squares_to_bb(my_kings)
        bm = squares_to_bb(opp_men)
        bk = squares_to_bb(opp_kings)
    else:
        bm = squares_to_bb(my_men)
        bk = squares_to_bb(my_kings)
        wm = squares_to_bb(opp_men)
        wk = squares_to_bb(opp_kings)

    root_color = color
    TT = {}

    total_pieces = bm.bit_count() + bk.bit_count() + wm.bit_count() + wk.bit_count()
    if total_pieces <= 6:
        max_depth = 12
    elif total_pieces <= 10:
        max_depth = 10
    elif total_pieces <= 16:
        max_depth = 8
    else:
        max_depth = 7

    deadline = time.perf_counter() + 0.92
    nodes = [0]

    def check_time():
        nodes[0] += 1
        if (nodes[0] & 511) == 0 and time.perf_counter() >= deadline:
            raise SearchTimeout

    def generate_moves(bm_, bk_, wm_, wk_, turn, captures_only=False):
        occ = bm_ | bk_ | wm_ | wk_

        if turn == 'w':
            my_men, my_kings = wm_, wk_
            opp_men, opp_kings = bm_, bk_
            man_dirs = WHITE_DIRS
            man_pst = MAN_W_
            promote_row = 7
        else:
            my_men, my_kings = bm_, bk_
            opp_men, opp_kings = wm_, wk_
            man_dirs = BLACK_DIRS
            man_pst = MAN_B_
            promote_row = 0

        opp_occ = opp_men | opp_kings
        captures = []

        bb = my_men
        while bb:
            lsb = bb & -bb
            sq = lsb.bit_length() - 1
            bb ^= lsb

            for d in man_dirs:
                mid = STEP_[sq][d]
                to = JUMP_[sq][d]
                if to != -1 and (opp_occ & BIT_[mid]) and not (occ & BIT_[to]):
                    victim = 175 if (opp_kings & BIT_[mid]) else 100
                    promote = (ROW_[to] == promote_row)
                    score = 1000 + victim + (120 if promote else 0) + (man_pst[to] - man_pst[sq])
                    captures.append((score, sq, to, mid, 0, promote))

        bb = my_kings
        while bb:
            lsb = bb & -bb
            sq = lsb.bit_length() - 1
            bb ^= lsb

            for d in KING_DIRS:
                mid = STEP_[sq][d]
                to = JUMP_[sq][d]
                if to != -1 and (opp_occ & BIT_[mid]) and not (occ & BIT_[to]):
                    victim = 175 if (opp_kings & BIT_[mid]) else 100
                    score = 1000 + victim + (KING_[to] - KING_[sq])
                    captures.append((score, sq, to, mid, 1, False))

        if captures:
            captures.sort(key=lambda m: m[0], reverse=True)
            return captures

        if captures_only:
            return []

        quiets = []

        bb = my_men
        while bb:
            lsb = bb & -bb
            sq = lsb.bit_length() - 1
            bb ^= lsb

            for d in man_dirs:
                to = STEP_[sq][d]
                if to != -1 and not (occ & BIT_[to]):
                    promote = (ROW_[to] == promote_row)
                    score = (220 if promote else 0) + (man_pst[to] - man_pst[sq])
                    quiets.append((score, sq, to, -1, 0, promote))

        bb = my_kings
        while bb:
            lsb = bb & -bb
            sq = lsb.bit_length() - 1
            bb ^= lsb

            for d in KING_DIRS:
                to = STEP_[sq][d]
                if to != -1 and not (occ & BIT_[to]):
                    score = KING_[to] - KING_[sq]
                    quiets.append((score, sq, to, -1, 1, False))

        quiets.sort(key=lambda m: m[0], reverse=True)
        return quiets

    def apply_move(bm_, bk_, wm_, wk_, turn, move):
        _, fr, to, mid, kind, promote = move
        fr_mask = BIT_[fr]
        to_mask = BIT_[to]

        if turn == 'w':
            if kind == 0:
                wm_ ^= fr_mask
                if mid != -1:
                    mid_mask = BIT_[mid]
                    if bm_ & mid_mask:
                        bm_ ^= mid_mask
                    else:
                        bk_ ^= mid_mask
                if promote:
                    wk_ |= to_mask
                else:
                    wm_ |= to_mask
            else:
                wk_ ^= fr_mask
                if mid != -1:
                    mid_mask = BIT_[mid]
                    if bm_ & mid_mask:
                        bm_ ^= mid_mask
                    else:
                        bk_ ^= mid_mask
                wk_ |= to_mask
            return bm_, bk_, wm_, wk_, 'b'

        else:
            if kind == 0:
                bm_ ^= fr_mask
                if mid != -1:
                    mid_mask = BIT_[mid]
                    if wm_ & mid_mask:
                        wm_ ^= mid_mask
                    else:
                        wk_ ^= mid_mask
                if promote:
                    bk_ |= to_mask
                else:
                    bm_ |= to_mask
            else:
                bk_ ^= fr_mask
                if mid != -1:
                    mid_mask = BIT_[mid]
                    if wm_ & mid_mask:
                        wm_ ^= mid_mask
                    else:
                        wk_ ^= mid_mask
                bk_ |= to_mask
            return bm_, bk_, wm_, wk_, 'w'

    def evaluate(bm_, bk_, wm_, wk_):
        white_score = 0
        black_score = 0

        bb = wm_
        while bb:
            lsb = bb & -bb
            sq = lsb.bit_length() - 1
            bb ^= lsb
            white_score += MAN_W_[sq]

        bb = wk_
        while bb:
            lsb = bb & -bb
            sq = lsb.bit_length() - 1
            bb ^= lsb
            white_score += KING_[sq]

        bb = bm_
        while bb:
            lsb = bb & -bb
            sq = lsb.bit_length() - 1
            bb ^= lsb
            black_score += MAN_B_[sq]

        bb = bk_
        while bb:
            lsb = bb & -bb
            sq = lsb.bit_length() - 1
            bb ^= lsb
            black_score += KING_[sq]

        score = white_score - black_score
        return score if root_color == 'w' else -score

    def order_moves(moves, best_sig):
        if best_sig is None or not moves:
            return
        for i, mv in enumerate(moves):
            if mv[1:] == best_sig:
                if i:
                    moves[0], moves[i] = moves[i], moves[0]
                return

    def qsearch(bm_, bk_, wm_, wk_, turn, alpha, beta, qdepth, capmoves=None):
        check_time()

        if capmoves is None:
            capmoves = generate_moves(bm_, bk_, wm_, wk_, turn, captures_only=True)

        if not capmoves:
            legal = generate_moves(bm_, bk_, wm_, wk_, turn, captures_only=False)
            if not legal:
                return -WIN if turn == root_color else WIN
            return evaluate(bm_, bk_, wm_, wk_)

        if qdepth <= 0:
            return evaluate(bm_, bk_, wm_, wk_)

        if turn == root_color:
            best = -INF
            for mv in capmoves:
                child = apply_move(bm_, bk_, wm_, wk_, turn, mv)
                val = qsearch(*child, alpha, beta, qdepth - 1, None)
                if val > best:
                    best = val
                if best > alpha:
                    alpha = best
                if alpha >= beta:
                    break
            return best
        else:
            best = INF
            for mv in capmoves:
                child = apply_move(bm_, bk_, wm_, wk_, turn, mv)
                val = qsearch(*child, alpha, beta, qdepth - 1, None)
                if val < best:
                    best = val
                if best < beta:
                    beta = best
                if alpha >= beta:
                    break
            return best

    def search(bm_, bk_, wm_, wk_, turn, depth, alpha, beta):
        check_time()

        if depth <= 0:
            legal = generate_moves(bm_, bk_, wm_, wk_, turn, captures_only=False)
            if not legal:
                return -WIN if turn == root_color else WIN
            if legal[0][3] != -1:
                return qsearch(bm_, bk_, wm_, wk_, turn, alpha, beta, 6, legal)
            return evaluate(bm_, bk_, wm_, wk_)

        key = (bm_, bk_, wm_, wk_, turn)
        alpha_orig, beta_orig = alpha, beta

        tt_sig = None
        entry = TT.get(key)
        if entry is not None:
            e_depth, e_flag, e_val, e_sig = entry
            tt_sig = e_sig
            if e_depth >= depth:
                if e_flag == EXACT:
                    return e_val
                elif e_flag == LOWER:
                    if e_val > alpha:
                        alpha = e_val
                else:
                    if e_val < beta:
                        beta = e_val
                if alpha >= beta:
                    return e_val

        moves = generate_moves(bm_, bk_, wm_, wk_, turn, captures_only=False)
        if not moves:
            return -WIN if turn == root_color else WIN

        order_moves(moves, tt_sig)
        forced = (len(moves) == 1)

        if turn == root_color:
            best_val = -INF
            best_sig = moves[0][1:]

            for mv in moves:
                child = apply_move(bm_, bk_, wm_, wk_, turn, mv)
                ext = 1 if (depth <= 2 and (forced or mv[5])) else 0
                val = search(*child, depth - 1 + ext, alpha, beta)

                if val > best_val:
                    best_val = val
                    best_sig = mv[1:]
                if best_val > alpha:
                    alpha = best_val
                if alpha >= beta:
                    break
        else:
            best_val = INF
            best_sig = moves[0][1:]

            for mv in moves:
                child = apply_move(bm_, bk_, wm_, wk_, turn, mv)
                ext = 1 if (depth <= 2 and (forced or mv[5])) else 0
                val = search(*child, depth - 1 + ext, alpha, beta)

                if val < best_val:
                    best_val = val
                    best_sig = mv[1:]
                if best_val < beta:
                    beta = best_val
                if alpha >= beta:
                    break

        flag = EXACT
        if best_val <= alpha_orig:
            flag = UPPER
        elif best_val >= beta_orig:
            flag = LOWER

        TT[key] = (depth, flag, best_val, best_sig)
        return best_val

    legal_moves = generate_moves(bm, bk, wm, wk, root_color, captures_only=False)

    if not legal_moves:
        # Should not normally happen unless already lost.
        for seq in (my_men, my_kings):
            if len(seq):
                r, c = seq[0]
                for dr in (1, -1):
                    for dc in (1, -1):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < 8 and 0 <= nc < 8:
                            return ((int(r), int(c)), (int(nr), int(nc)))
                return ((int(r), int(c)), (int(r), int(c)))
        return ((0, 0), (0, 0))

    if len(legal_moves) == 1:
        mv = legal_moves[0]
        return ((ROW_[mv[1]], COL_[mv[1]]), (ROW_[mv[2]], COL_[mv[2]]))

    best_move = legal_moves[0]
    pv_sig = best_move[1:]

    def search_root(depth, pv_best_sig):
        moves = list(legal_moves)
        order_moves(moves, pv_best_sig)

        alpha = -INF
        beta = INF
        best_val = -INF
        best_mv = moves[0]
        forced = (len(moves) == 1)

        for mv in moves:
            child = apply_move(bm, bk, wm, wk, root_color, mv)
            ext = 1 if (depth <= 2 and (forced or mv[5])) else 0
            val = search(*child, depth - 1 + ext, alpha, beta)
            if val > best_val:
                best_val = val
                best_mv = mv
            if best_val > alpha:
                alpha = best_val

        return best_mv, best_val

    for depth in range(1, max_depth + 1):
        try:
            mv, val = search_root(depth, pv_sig)
            best_move = mv
            pv_sig = mv[1:]
            if abs(val) >= WIN:
                break
        except SearchTimeout:
            break

    return ((ROW_[best_move[1]], COL_[best_move[1]]), (ROW_[best_move[2]], COL_[best_move[2]]))
