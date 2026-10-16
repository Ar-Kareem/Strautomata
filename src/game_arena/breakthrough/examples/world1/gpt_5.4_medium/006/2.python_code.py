
import time

ROW = [i >> 3 for i in range(64)]
COL = [i & 7 for i in range(64)]
BIT = [1 << i for i in range(64)]

TOP_ROW_MASK = sum(1 << i for i in range(56, 64))
BOTTOM_ROW_MASK = sum(1 << i for i in range(8))

CENTER_FILE_BONUS = [0, 2, 4, 6, 6, 4, 2, 0]
ADV_BONUS = [0, 3, 8, 15, 26, 42, 70, 0]

PASS_W = [0] * 64
PASS_B = [0] * 64
DEFEND_W = [0] * 64
DEFEND_B = [0] * 64
THREAT_W = [0] * 64
THREAT_B = [0] * 64

for i in range(64):
    r = ROW[i]
    c = COL[i]

    m = 0
    if r > 0 and c > 0:
        m |= BIT[i - 9]
    if r > 0 and c < 7:
        m |= BIT[i - 7]
    DEFEND_W[i] = m

    m = 0
    if r < 7 and c > 0:
        m |= BIT[i + 7]
    if r < 7 and c < 7:
        m |= BIT[i + 9]
    THREAT_W[i] = m

    m = 0
    if r < 7 and c > 0:
        m |= BIT[i + 7]
    if r < 7 and c < 7:
        m |= BIT[i + 9]
    DEFEND_B[i] = m

    m = 0
    if r > 0 and c > 0:
        m |= BIT[i - 9]
    if r > 0 and c < 7:
        m |= BIT[i - 7]
    THREAT_B[i] = m

    m = 0
    for rr in range(r + 1, 8):
        for cc in (c - 1, c, c + 1):
            if 0 <= cc < 8:
                m |= BIT[rr * 8 + cc]
    PASS_W[i] = m

    m = 0
    for rr in range(0, r):
        for cc in (c - 1, c, c + 1):
            if 0 <= cc < 8:
                m |= BIT[rr * 8 + cc]
    PASS_B[i] = m


def pieces_to_bits(pieces):
    bits = 0
    for r, c in pieces:
        bits |= 1 << (r * 8 + c)
    return bits


def winner(w_bits, b_bits):
    if w_bits & TOP_ROW_MASK:
        return 'w'
    if b_bits & BOTTOM_ROW_MASK:
        return 'b'
    if b_bits == 0:
        return 'w'
    if w_bits == 0:
        return 'b'
    return None


def generate_moves(side, w_bits, b_bits):
    own = w_bits if side == 'w' else b_bits
    occ = w_bits | b_bits
    moves = []

    pieces = own
    if side == 'w':
        while pieces:
            lsb = pieces & -pieces
            frm = lsb.bit_length() - 1
            pieces ^= lsb

            r = ROW[frm]
            c = COL[frm]
            if r >= 7:
                continue

            to = frm + 8
            if not (occ & BIT[to]):
                moves.append((frm, to))

            if c > 0:
                to = frm + 7
                if not (own & BIT[to]):
                    moves.append((frm, to))

            if c < 7:
                to = frm + 9
                if not (own & BIT[to]):
                    moves.append((frm, to))
    else:
        while pieces:
            lsb = pieces & -pieces
            frm = lsb.bit_length() - 1
            pieces ^= lsb

            r = ROW[frm]
            c = COL[frm]
            if r <= 0:
                continue

            to = frm - 8
            if not (occ & BIT[to]):
                moves.append((frm, to))

            if c > 0:
                to = frm - 9
                if not (own & BIT[to]):
                    moves.append((frm, to))

            if c < 7:
                to = frm - 7
                if not (own & BIT[to]):
                    moves.append((frm, to))

    return moves


def apply_move(move, side, w_bits, b_bits):
    frm, to = move
    from_bit = BIT[frm]
    to_bit = BIT[to]

    if side == 'w':
        w_bits = (w_bits ^ from_bit) | to_bit
        b_bits &= ~to_bit
    else:
        b_bits = (b_bits ^ from_bit) | to_bit
        w_bits &= ~to_bit

    return w_bits, b_bits


def evaluate_abs(w_bits, b_bits):
    score = 130 * (w_bits.bit_count() - b_bits.bit_count())

    sum_w = 0
    sum_b = 0
    front_w = 0
    front_b = 0

    pieces = w_bits
    while pieces:
        lsb = pieces & -pieces
        i = lsb.bit_length() - 1
        pieces ^= lsb

        r = ROW[i]
        c = COL[i]
        progress = r
        defended = bool(w_bits & DEFEND_W[i])
        threatened = bool(b_bits & THREAT_W[i])

        sum_w += progress
        if progress > front_w:
            front_w = progress

        score += CENTER_FILE_BONUS[c]
        score += ADV_BONUS[progress]

        if defended:
            score += 6

        if threatened:
            score -= 12 if defended else 24

        if (b_bits & PASS_W[i]) == 0:
            bonus = 12 + 8 * progress + (8 if defended else 0)
            score += bonus

    pieces = b_bits
    while pieces:
        lsb = pieces & -pieces
        i = lsb.bit_length() - 1
        pieces ^= lsb

        r = ROW[i]
        c = COL[i]
        progress = 7 - r
        defended = bool(b_bits & DEFEND_B[i])
        threatened = bool(w_bits & THREAT_B[i])

        sum_b += progress
        if progress > front_b:
            front_b = progress

        score -= CENTER_FILE_BONUS[c]
        score -= ADV_BONUS[progress]

        if defended:
            score -= 6

        if threatened:
            score += 12 if defended else 24

        if (w_bits & PASS_B[i]) == 0:
            bonus = 12 + 8 * progress + (8 if defended else 0)
            score -= bonus

    score += 12 * (sum_w - sum_b)
    score += 34 * (front_w - front_b)

    return score


def move_to_coords(move):
    frm, to = move
    return ((ROW[frm], COL[frm]), (ROW[to], COL[to]))


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    if color == 'w':
        w_bits = pieces_to_bits(me)
        b_bits = pieces_to_bits(opp)
    else:
        b_bits = pieces_to_bits(me)
        w_bits = pieces_to_bits(opp)

    legal_moves = generate_moves(color, w_bits, b_bits)

    if not legal_moves:
        # Should not happen on a valid non-terminal arena state.
        # Return a placeholder using an existing piece if possible.
        if me:
            r, c = me[0]
            return ((r, c), (r, c))
        return ((0, 0), (0, 0))

    if len(legal_moves) == 1:
        return move_to_coords(legal_moves[0])

    start = time.perf_counter()
    deadline = start + 0.93

    other = 'b' if color == 'w' else 'w'

    # Quick root scan: take immediate wins, and penalize moves allowing immediate loss.
    root_extra = {}
    for mv in legal_moves:
        nw, nb = apply_move(mv, color, w_bits, b_bits)
        win = winner(nw, nb)
        if win == color:
            return move_to_coords(mv)

        opp_moves = generate_moves(other, nw, nb)
        if not opp_moves:
            return move_to_coords(mv)

        penalty = 0
        for omv in opp_moves:
            nnw, nnb = apply_move(omv, other, nw, nb)
            if winner(nnw, nnb) == other:
                penalty = -300000
                break
        root_extra[mv] = penalty

    MATE = 10_000_000
    INF = 10_000_000_000

    TT = {}
    history = [[0] * 64 for _ in range(64)]
    killers = [[None, None] for _ in range(64)]
    nodes = [0]

    class SearchTimeout(Exception):
        pass

    def check_time():
        nodes[0] += 1
        if (nodes[0] & 1023) == 0 and time.perf_counter() >= deadline:
            raise SearchTimeout

    def order_moves(moves, side, sw, sb, tt_move, ply, root_bias=None):
        own = sw if side == 'w' else sb
        opp_bits = sb if side == 'w' else sw
        k1, k2 = killers[ply] if ply < len(killers) else (None, None)

        scored = []
        for mv in moves:
            frm, to = mv
            score = history[frm][to]

            if mv == tt_move:
                score += 10_000_000
            if mv == k1:
                score += 90_000
            elif mv == k2:
                score += 80_000

            cap = bool(opp_bits & BIT[to])
            if cap:
                score += 220_000

            if side == 'w':
                progress = ROW[to]
                if progress == 7:
                    score += 9_000_000
                score += progress * 240 + CENTER_FILE_BONUS[COL[to]] * 12
                defmask = DEFEND_W[to] & ~BIT[frm]
                defended = bool(own & defmask)
                if defended:
                    score += 30
                if (opp_bits & THREAT_W[to]) and not defended:
                    score -= 60
            else:
                progress = 7 - ROW[to]
                if progress == 7:
                    score += 9_000_000
                score += progress * 240 + CENTER_FILE_BONUS[COL[to]] * 12
                defmask = DEFEND_B[to] & ~BIT[frm]
                defended = bool(own & defmask)
                if defended:
                    score += 30
                if (opp_bits & THREAT_B[to]) and not defended:
                    score -= 60

            if root_bias is not None:
                score += root_bias.get(mv, 0)

            scored.append((score, mv))

        scored.sort(reverse=True)
        return [mv for _, mv in scored]

    def negamax(sw, sb, side, depth, alpha, beta, ply):
        check_time()

        win = winner(sw, sb)
        if win is not None:
            return (MATE - ply) if win == side else (-MATE + ply)

        key = (sw, sb, side)
        entry = TT.get(key)
        tt_move = entry[3] if entry is not None else None

        if entry is not None and entry[0] >= depth:
            flag, val = entry[1], entry[2]
            if flag == 'E':
                return val
            if flag == 'L':
                if val > alpha:
                    alpha = val
            else:
                if val < beta:
                    beta = val
            if alpha >= beta:
                return val

        if depth <= 0:
            val = evaluate_abs(sw, sb)
            return val if side == 'w' else -val

        moves = generate_moves(side, sw, sb)
        if not moves:
            return -MATE + ply

        moves = order_moves(moves, side, sw, sb, tt_move, ply)

        orig_alpha = alpha
        beta_orig = beta
        best = -INF
        best_move = moves[0]
        opp_side = 'b' if side == 'w' else 'w'
        opp_bits = sb if side == 'w' else sw

        first = True
        for mv in moves:
            frm, to = mv
            cap = bool(opp_bits & BIT[to])
            progress = ROW[to] if side == 'w' else (7 - ROW[to])
            ext = 1 if (depth == 1 and (cap or progress >= 6)) else 0
            child_depth = depth - 1 + ext

            nw, nb = apply_move(mv, side, sw, sb)

            if first:
                score = -negamax(nw, nb, opp_side, child_depth, -beta, -alpha, ply + 1)
                first = False
            else:
                score = -negamax(nw, nb, opp_side, child_depth, -alpha - 1, -alpha, ply + 1)
                if alpha < score < beta:
                    score = -negamax(nw, nb, opp_side, child_depth, -beta, -alpha, ply + 1)

            if score > best:
                best = score
                best_move = mv

            if score > alpha:
                alpha = score

            if alpha >= beta:
                if not cap and ply < len(killers):
                    if killers[ply][0] != mv:
                        killers[ply][1] = killers[ply][0]
                        killers[ply][0] = mv
                history[frm][to] += depth * depth
                break

        flag = 'E'
        if best <= orig_alpha:
            flag = 'U'
        elif best >= beta_orig:
            flag = 'L'
        TT[key] = (depth, flag, best, best_move)

        return best

    def search_root(depth, alpha, beta):
        entry = TT.get((w_bits, b_bits, color))
        tt_move = entry[3] if entry is not None else None

        moves = order_moves(legal_moves, color, w_bits, b_bits, tt_move, 0, root_extra)
        best_val = -INF
        best_move = moves[0]
        a = alpha
        opp_bits = b_bits if color == 'w' else w_bits

        first = True
        for mv in moves:
            check_time()

            frm, to = mv
            cap = bool(opp_bits & BIT[to])
            progress = ROW[to] if color == 'w' else (7 - ROW[to])
            ext = 1 if (depth == 1 and (cap or progress >= 6)) else 0
            child_depth = depth - 1 + ext

            nw, nb = apply_move(mv, color, w_bits, b_bits)

            if first:
                val = -negamax(nw, nb, other, child_depth, -beta, -a, 1)
                first = False
            else:
                val = -negamax(nw, nb, other, child_depth, -a - 1, -a, 1)
                if a < val < beta:
                    val = -negamax(nw, nb, other, child_depth, -beta, -a, 1)

            if val > best_val:
                best_val = val
                best_move = mv

            if val > a:
                a = val

            if a >= beta:
                break

        TT[(w_bits, b_bits, color)] = (depth, 'E', best_val, best_move)
        return best_val, best_move

    fallback = order_moves(legal_moves, color, w_bits, b_bits, None, 0, root_extra)[0]
    best_move = fallback
    guess = 0

    try:
        for depth in range(1, 11):
            if time.perf_counter() >= deadline:
                break

            alpha = -INF
            beta = INF
            if depth >= 3:
                window = 120
                alpha = guess - window
                beta = guess + window

            val, mv = search_root(depth, alpha, beta)

            if val <= alpha or val >= beta:
                val, mv = search_root(depth, -INF, INF)

            best_move = mv
            guess = val

            if abs(val) >= MATE - 20:
                break

    except SearchTimeout:
        pass

    return move_to_coords(best_move)
