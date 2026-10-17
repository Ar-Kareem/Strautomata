
import time

FULL_MASK = (1 << 64) - 1
INF = 10**15
MATE = 10**9

OTHER = {"w": "b", "b": "w"}

RANK_MASK = [0] * 8
for r in range(8):
    mask = 0
    base = r * 8
    for c in range(8):
        mask |= 1 << (base + c)
    RANK_MASK[r] = mask

BOTTOM_ROW_MASK = RANK_MASK[0]
TOP_ROW_MASK = RANK_MASK[7]
RANK1_MASK = RANK_MASK[1]
RANK6_MASK = RANK_MASK[6]

ROW = [0] * 64
COL = [0] * 64
ADV_B = [0] * 64

W_FWD = [-1] * 64
W_DL = [-1] * 64
W_DR = [-1] * 64
B_FWD = [-1] * 64
B_DL = [-1] * 64
B_DR = [-1] * 64

WHITE_ATTACK_SRC_MASK = [0] * 64
BLACK_ATTACK_SRC_MASK = [0] * 64
WHITE_FRONT_CONE = [0] * 64
BLACK_FRONT_CONE = [0] * 64
WHITE_FILE_AHEAD = [0] * 64
BLACK_FILE_AHEAD = [0] * 64

CENTER_BONUS = [0] * 64
PROG_W = [0] * 64
PROG_B = [0] * 64
PASSED_W = [0] * 64
PASSED_B = [0] * 64

for idx in range(64):
    r = idx >> 3
    c = idx & 7
    ROW[idx] = r
    COL[idx] = c
    ADV_B[idx] = 7 - r

    if r < 7:
        W_FWD[idx] = idx + 8
        if c > 0:
            W_DL[idx] = idx + 7
        if c < 7:
            W_DR[idx] = idx + 9

    if r > 0:
        B_FWD[idx] = idx - 8
        if c > 0:
            B_DL[idx] = idx - 9
        if c < 7:
            B_DR[idx] = idx - 7

    m = 0
    if r > 0:
        if c > 0:
            m |= 1 << (idx - 9)
        if c < 7:
            m |= 1 << (idx - 7)
    WHITE_ATTACK_SRC_MASK[idx] = m

    m = 0
    if r < 7:
        if c > 0:
            m |= 1 << (idx + 7)
        if c < 7:
            m |= 1 << (idx + 9)
    BLACK_ATTACK_SRC_MASK[idx] = m

    m = 0
    for rr in range(r + 1, 8):
        for cc in (c - 1, c, c + 1):
            if 0 <= cc < 8:
                m |= 1 << (rr * 8 + cc)
    WHITE_FRONT_CONE[idx] = m

    m = 0
    for rr in range(0, r):
        for cc in (c - 1, c, c + 1):
            if 0 <= cc < 8:
                m |= 1 << (rr * 8 + cc)
    BLACK_FRONT_CONE[idx] = m

    m = 0
    for rr in range(r + 1, 8):
        m |= 1 << (rr * 8 + c)
    WHITE_FILE_AHEAD[idx] = m

    m = 0
    for rr in range(0, r):
        m |= 1 << (rr * 8 + c)
    BLACK_FILE_AHEAD[idx] = m

    CENTER_BONUS[idx] = 8 if c in (3, 4) else (5 if c in (2, 5) else 0)

    pw = r
    pb = 7 - r
    PROG_W[idx] = 10 * pw * pw + 6 * pw
    PROG_B[idx] = 10 * pb * pb + 6 * pb
    PASSED_W[idx] = 14 * (pw + 1) * (pw + 1)
    PASSED_B[idx] = 14 * (pb + 1) * (pb + 1)

_TT_VAL = {}
_TT_MOVE = {}


def list_to_bitboard(pieces):
    bb = 0
    for r, c in pieces:
        bb |= 1 << (r * 8 + c)
    return bb


def idx_to_rc(idx):
    return (idx >> 3, idx & 7)


def is_singleton(bb):
    return bb != 0 and (bb & (bb - 1)) == 0


def winner_of(w, b):
    if w == 0:
        return "b"
    if b == 0:
        return "w"
    if w & TOP_ROW_MASK:
        return "w"
    if b & BOTTOM_ROW_MASK:
        return "b"
    return None


def generate_moves(w, b, side):
    moves = []
    occ = w | b

    if side == "w":
        x = w
        while x:
            lsb = x & -x
            frm = lsb.bit_length() - 1
            x ^= lsb

            to = W_FWD[frm]
            if to != -1:
                tm = 1 << to
                if not (occ & tm):
                    moves.append((frm, to, False))

            to = W_DL[frm]
            if to != -1:
                tm = 1 << to
                if not (w & tm):
                    moves.append((frm, to, bool(b & tm)))

            to = W_DR[frm]
            if to != -1:
                tm = 1 << to
                if not (w & tm):
                    moves.append((frm, to, bool(b & tm)))
    else:
        x = b
        while x:
            lsb = x & -x
            frm = lsb.bit_length() - 1
            x ^= lsb

            to = B_FWD[frm]
            if to != -1:
                tm = 1 << to
                if not (occ & tm):
                    moves.append((frm, to, False))

            to = B_DL[frm]
            if to != -1:
                tm = 1 << to
                if not (b & tm):
                    moves.append((frm, to, bool(w & tm)))

            to = B_DR[frm]
            if to != -1:
                tm = 1 << to
                if not (b & tm):
                    moves.append((frm, to, bool(w & tm)))

    return moves


def make_move(w, b, side, move):
    frm, to, cap = move
    fm = 1 << frm
    tm = 1 << to

    if side == "w":
        w = (w ^ fm) | tm
        if cap:
            b &= ~tm
    else:
        b = (b ^ fm) | tm
        if cap:
            w &= ~tm

    return w, b


def is_winning_move(w, b, side, move):
    _, to, cap = move
    if side == "w":
        return ROW[to] == 7 or (cap and is_singleton(b))
    return ROW[to] == 0 or (cap and is_singleton(w))


def has_immediate_win_fast(w, b, side):
    occ = w | b

    if side == "w":
        x = w & RANK6_MASK
        while x:
            lsb = x & -x
            idx = lsb.bit_length() - 1
            x ^= lsb
            c = COL[idx]

            tm = 1 << (idx + 8)
            if not (occ & tm):
                return True
            if c > 0:
                tm = 1 << (idx + 7)
                if not (w & tm):
                    return True
            if c < 7:
                tm = 1 << (idx + 9)
                if not (w & tm):
                    return True

        if is_singleton(b):
            opp_idx = b.bit_length() - 1
            if w & WHITE_ATTACK_SRC_MASK[opp_idx]:
                return True

        return False

    x = b & RANK1_MASK
    while x:
        lsb = x & -x
        idx = lsb.bit_length() - 1
        x ^= lsb
        c = COL[idx]

        tm = 1 << (idx - 8)
        if not (occ & tm):
            return True
        if c > 0:
            tm = 1 << (idx - 9)
            if not (b & tm):
                return True
        if c < 7:
            tm = 1 << (idx - 7)
            if not (b & tm):
                return True

    if is_singleton(w):
        opp_idx = w.bit_length() - 1
        if b & BLACK_ATTACK_SRC_MASK[opp_idx]:
            return True

    return False


def count_immediate_wins(w, b, side, limit=3):
    cnt = 0
    for mv in generate_moves(w, b, side):
        if is_winning_move(w, b, side, mv):
            cnt += 1
            if cnt >= limit:
                return cnt
    return cnt


def evaluate_white(w, b):
    if w == 0:
        return -MATE
    if b == 0:
        return MATE
    if w & TOP_ROW_MASK:
        return MATE
    if b & BOTTOM_ROW_MASK:
        return -MATE

    occ = w | b
    score = 160 * (w.bit_count() - b.bit_count())

    white_front = 0
    black_front = 0

    x = w
    while x:
        lsb = x & -x
        idx = lsb.bit_length() - 1
        x ^= lsb

        r = ROW[idx]
        if r > white_front:
            white_front = r

        score += PROG_W[idx] + CENTER_BONUS[idx]

        defenders = (w & WHITE_ATTACK_SRC_MASK[idx]).bit_count()
        attackers = (b & BLACK_ATTACK_SRC_MASK[idx]).bit_count()
        score += 12 * defenders - 14 * attackers
        if defenders == 0 and attackers:
            score -= 10

        if (b & WHITE_FRONT_CONE[idx]) == 0:
            score += PASSED_W[idx]
        elif (occ & WHITE_FILE_AHEAD[idx]) == 0:
            score += 8 * r

        if r == 6:
            score += 120

    x = b
    while x:
        lsb = x & -x
        idx = lsb.bit_length() - 1
        x ^= lsb

        prog = ADV_B[idx]
        if prog > black_front:
            black_front = prog

        score -= PROG_B[idx] + CENTER_BONUS[idx]

        defenders = (b & BLACK_ATTACK_SRC_MASK[idx]).bit_count()
        attackers = (w & WHITE_ATTACK_SRC_MASK[idx]).bit_count()
        score -= 12 * defenders
        score += 14 * attackers
        if defenders == 0 and attackers:
            score += 10

        if (w & BLACK_FRONT_CONE[idx]) == 0:
            score -= PASSED_B[idx]
        elif (occ & BLACK_FILE_AHEAD[idx]) == 0:
            score -= 8 * prog

        if ROW[idx] == 1:
            score -= 120

    score += 40 * (white_front - black_front)
    return score


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    if len(_TT_VAL) > 250000:
        _TT_VAL.clear()
    if len(_TT_MOVE) > 120000:
        _TT_MOVE.clear()

    if color == "w":
        w = list_to_bitboard(me)
        b = list_to_bitboard(opp)
    else:
        b = list_to_bitboard(me)
        w = list_to_bitboard(opp)

    root_moves = generate_moves(w, b, color)

    if not root_moves:
        # Should only happen on terminal positions.
        if me:
            r, c = me[0]
            return ((r, c), (r, c))
        return ((0, 0), (0, 0))

    if len(root_moves) == 1:
        mv = root_moves[0]
        return idx_to_rc(mv[0]), idx_to_rc(mv[1])

    for mv in root_moves:
        if is_winning_move(w, b, color, mv):
            return idx_to_rc(mv[0]), idx_to_rc(mv[1])

    history = [[0] * 64 for _ in range(64)]
    tt_val = _TT_VAL
    tt_move = _TT_MOVE

    start = time.perf_counter()
    deadline = start + 0.93
    nodes = 0

    def move_priority_score(wb, bb, side, mv, hint=None):
        frm, to, cap = mv
        score = history[frm][to]
        if hint is not None and mv == hint:
            score += 5_000_000

        fm = 1 << frm
        tm = 1 << to

        if side == "w":
            row = ROW[to]
            score += 160 * row + CENTER_BONUS[to]
            if row == 7:
                score += 20_000_000
            if cap:
                score += 3000
                if is_singleton(bb):
                    score += 15_000_000

            nw = (wb ^ fm) | tm
            nb = bb & ~tm if cap else bb

            defended = bool(nw & WHITE_ATTACK_SRC_MASK[to])
            attacked = bool(nb & BLACK_ATTACK_SRC_MASK[to])

            if defended:
                score += 120
            if attacked:
                score -= 160
                if not defended:
                    score -= 120

            if (nb & WHITE_FRONT_CONE[to]) == 0:
                score += 100 + 18 * row
            elif ((nw | nb) & WHITE_FILE_AHEAD[to]) == 0:
                score += 10 * row

        else:
            prog = ADV_B[to]
            score += 160 * prog + CENTER_BONUS[to]
            if ROW[to] == 0:
                score += 20_000_000
            if cap:
                score += 3000
                if is_singleton(wb):
                    score += 15_000_000

            nb = (bb ^ fm) | tm
            nw = wb & ~tm if cap else wb

            defended = bool(nb & BLACK_ATTACK_SRC_MASK[to])
            attacked = bool(nw & WHITE_ATTACK_SRC_MASK[to])

            if defended:
                score += 120
            if attacked:
                score -= 160
                if not defended:
                    score -= 120

            if (nw & BLACK_FRONT_CONE[to]) == 0:
                score += 100 + 18 * prog
            elif ((nw | nb) & BLACK_FILE_AHEAD[to]) == 0:
                score += 10 * prog

        return score

    def ordered_moves(wb, bb, side, moves, hint=None):
        if len(moves) <= 1:
            return moves
        scored = [(move_priority_score(wb, bb, side, mv, hint), mv) for mv in moves]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [mv for _, mv in scored]

    def choose_fallback():
        hint = tt_move.get((w, b, color))
        opp_side = OTHER[color]
        opp_threats_now = count_immediate_wins(w, b, opp_side, limit=3)

        ordered = ordered_moves(w, b, color, root_moves, hint)
        best_mv = ordered[0]
        best_score = -INF

        for mv in ordered:
            nw, nb = make_move(w, b, color, mv)
            win = winner_of(nw, nb)
            if win == color:
                return mv

            score = move_priority_score(w, b, color, mv, hint)
            opp_wins = count_immediate_wins(nw, nb, opp_side, limit=3)

            if opp_wins:
                score -= 400_000 * opp_wins
            elif opp_threats_now:
                score += 20_000

            ev = evaluate_white(nw, nb)
            score += (ev if color == "w" else -ev) // 4

            if score > best_score:
                best_score = score
                best_mv = mv

        return best_mv

    fallback_move = choose_fallback()
    best_move = fallback_move

    def negamax(wb, bb, side, depth, alpha, beta):
        nonlocal nodes
        nodes += 1
        if (nodes & 1023) == 0 and time.perf_counter() >= deadline:
            raise TimeoutError

        winner = winner_of(wb, bb)
        if winner is not None:
            return MATE if winner == side else -MATE

        if depth == 0:
            if has_immediate_win_fast(wb, bb, side):
                return MATE - 1
            val = evaluate_white(wb, bb)
            return val if side == "w" else -val

        keyd = (wb, bb, side, depth)
        cached = tt_val.get(keyd)
        if cached is not None:
            return cached

        moves = generate_moves(wb, bb, side)
        if not moves:
            return -MATE

        hint = tt_move.get((wb, bb, side))
        moves = ordered_moves(wb, bb, side, moves, hint)

        opp_side = OTHER[side]
        best = -INF
        best_mv = moves[0]

        for mv in moves:
            nw, nb = make_move(wb, bb, side, mv)
            score = -negamax(nw, nb, opp_side, depth - 1, -beta, -alpha)

            if score > best:
                best = score
                best_mv = mv
                if score > alpha:
                    alpha = score

            if alpha >= beta:
                history[mv[0]][mv[1]] += depth * depth
                tt_move[(wb, bb, side)] = mv
                return best

        tt_move[(wb, bb, side)] = best_mv
        tt_val[keyd] = best
        return best

    def search_root(depth, current_best):
        if time.perf_counter() >= deadline:
            raise TimeoutError

        hint = current_best if current_best is not None else tt_move.get((w, b, color))
        moves = ordered_moves(w, b, color, root_moves, hint)

        alpha = -INF
        beta = INF
        best = -INF
        best_mv = moves[0]
        opp_side = OTHER[color]

        for mv in moves:
            if time.perf_counter() >= deadline:
                raise TimeoutError

            nw, nb = make_move(w, b, color, mv)
            score = -negamax(nw, nb, opp_side, depth - 1, -beta, -alpha)

            if score > best:
                best = score
                best_mv = mv
                if score > alpha:
                    alpha = score

        tt_move[(w, b, color)] = best_mv
        tt_val[(w, b, color, depth)] = best
        return best, best_mv

    total_pieces = (w | b).bit_count()
    if total_pieces <= 8:
        max_depth = 10
    elif total_pieces <= 12:
        max_depth = 9
    elif total_pieces <= 18:
        max_depth = 8
    elif total_pieces <= 24:
        max_depth = 7
    else:
        max_depth = 6

    for depth in range(2, max_depth + 1):
        try:
            val, mv = search_root(depth, best_move)
            best_move = mv
            if val >= MATE - 1:
                break
        except TimeoutError:
            break

    return idx_to_rc(best_move[0]), idx_to_rc(best_move[1])
