
import time
import numpy as np

popcount = int.bit_count if hasattr(int, "bit_count") else (lambda x: bin(x).count("1"))

FULL = (1 << 64) - 1
NOT_A = 0xFEFEFEFEFEFEFEFE
NOT_H = 0x7F7F7F7F7F7F7F7F

A1 = 1 << 0
B1 = 1 << 1
G1 = 1 << 6
H1 = 1 << 7

A2 = 1 << 8
B2 = 1 << 9
G2 = 1 << 14
H2 = 1 << 15

A7 = 1 << 48
B7 = 1 << 49
G7 = 1 << 54
H7 = 1 << 55

A8 = 1 << 56
B8 = 1 << 57
G8 = 1 << 62
H8 = 1 << 63

CORNERS = A1 | H1 | A8 | H8

CORNER_PATTERNS = (
    (A1, B1 | A2, B2),
    (H1, G1 | H2, G2),
    (A8, A7 | B8, B7),
    (H8, G8 | H7, G7),
)

PSQ = (
    120, -20,  20,   5,   5,  20, -20, 120,
    -20, -40,  -5,  -5,  -5,  -5, -40, -20,
     20,  -5,  15,   3,   3,  15,  -5,  20,
      5,  -5,   3,   3,   3,   3,  -5,   5,
      5,  -5,   3,   3,   3,   3,  -5,   5,
     20,  -5,  15,   3,   3,  15,  -5,  20,
    -20, -40,  -5,  -5,  -5,  -5, -40, -20,
    120, -20,  20,   5,   5,  20, -20, 120,
)

ORDER_PSQ = tuple(v * 100 for v in PSQ)

SQ_TO_STR = tuple(chr(97 + (i & 7)) + str((i >> 3) + 1) for i in range(64))

EXACT, LOWER, UPPER = 0, 1, 2
INF = 10**9
WIN = 1_000_000


def arrays_to_bitboards(you: np.ndarray, opponent: np.ndarray):
    me = 0
    opp = 0
    y = you.ravel()
    o = opponent.ravel()
    for i in range(64):
        if y[i]:
            me |= 1 << i
        elif o[i]:
            opp |= 1 << i
    return me, opp


def bit_to_str(bit: int) -> str:
    return SQ_TO_STR[bit.bit_length() - 1]


def neighbors(bb: int) -> int:
    return (
        ((bb & NOT_H) << 1)
        | ((bb & NOT_A) >> 1)
        | ((bb << 8) & FULL)
        | (bb >> 8)
        | (((bb & NOT_H) << 9) & FULL)
        | (((bb & NOT_A) << 7) & FULL)
        | ((bb & NOT_H) >> 7)
        | ((bb & NOT_A) >> 9)
    ) & FULL


def legal_moves(player: int, opp: int) -> int:
    empty = FULL ^ (player | opp)
    moves = 0

    t = ((player & NOT_H) << 1) & opp
    t |= ((t & NOT_H) << 1) & opp
    t |= ((t & NOT_H) << 1) & opp
    t |= ((t & NOT_H) << 1) & opp
    t |= ((t & NOT_H) << 1) & opp
    t |= ((t & NOT_H) << 1) & opp
    moves |= ((t & NOT_H) << 1) & empty

    t = ((player & NOT_A) >> 1) & opp
    t |= ((t & NOT_A) >> 1) & opp
    t |= ((t & NOT_A) >> 1) & opp
    t |= ((t & NOT_A) >> 1) & opp
    t |= ((t & NOT_A) >> 1) & opp
    t |= ((t & NOT_A) >> 1) & opp
    moves |= ((t & NOT_A) >> 1) & empty

    t = (player >> 8) & opp
    t |= (t >> 8) & opp
    t |= (t >> 8) & opp
    t |= (t >> 8) & opp
    t |= (t >> 8) & opp
    t |= (t >> 8) & opp
    moves |= (t >> 8) & empty

    t = ((player << 8) & FULL) & opp
    t |= ((t << 8) & FULL) & opp
    t |= ((t << 8) & FULL) & opp
    t |= ((t << 8) & FULL) & opp
    t |= ((t << 8) & FULL) & opp
    t |= ((t << 8) & FULL) & opp
    moves |= ((t << 8) & FULL) & empty

    t = ((player & NOT_H) >> 7) & opp
    t |= ((t & NOT_H) >> 7) & opp
    t |= ((t & NOT_H) >> 7) & opp
    t |= ((t & NOT_H) >> 7) & opp
    t |= ((t & NOT_H) >> 7) & opp
    t |= ((t & NOT_H) >> 7) & opp
    moves |= ((t & NOT_H) >> 7) & empty

    t = ((player & NOT_A) >> 9) & opp
    t |= ((t & NOT_A) >> 9) & opp
    t |= ((t & NOT_A) >> 9) & opp
    t |= ((t & NOT_A) >> 9) & opp
    t |= ((t & NOT_A) >> 9) & opp
    t |= ((t & NOT_A) >> 9) & opp
    moves |= ((t & NOT_A) >> 9) & empty

    t = (((player & NOT_H) << 9) & FULL) & opp
    t |= (((t & NOT_H) << 9) & FULL) & opp
    t |= (((t & NOT_H) << 9) & FULL) & opp
    t |= (((t & NOT_H) << 9) & FULL) & opp
    t |= (((t & NOT_H) << 9) & FULL) & opp
    t |= (((t & NOT_H) << 9) & FULL) & opp
    moves |= (((t & NOT_H) << 9) & FULL) & empty

    t = (((player & NOT_A) << 7) & FULL) & opp
    t |= (((t & NOT_A) << 7) & FULL) & opp
    t |= (((t & NOT_A) << 7) & FULL) & opp
    t |= (((t & NOT_A) << 7) & FULL) & opp
    t |= (((t & NOT_A) << 7) & FULL) & opp
    t |= (((t & NOT_A) << 7) & FULL) & opp
    moves |= (((t & NOT_A) << 7) & FULL) & empty

    return moves & FULL


def apply_move(me: int, opp: int, move: int):
    flips = 0

    x = ((move & NOT_H) << 1) & FULL
    captured = 0
    while x & opp:
        captured |= x
        x = ((x & NOT_H) << 1) & FULL
    if x & me:
        flips |= captured

    x = (move & NOT_A) >> 1
    captured = 0
    while x & opp:
        captured |= x
        x = (x & NOT_A) >> 1
    if x & me:
        flips |= captured

    x = move >> 8
    captured = 0
    while x & opp:
        captured |= x
        x >>= 8
    if x & me:
        flips |= captured

    x = (move << 8) & FULL
    captured = 0
    while x & opp:
        captured |= x
        x = (x << 8) & FULL
    if x & me:
        flips |= captured

    x = (move & NOT_H) >> 7
    captured = 0
    while x & opp:
        captured |= x
        x = (x & NOT_H) >> 7
    if x & me:
        flips |= captured

    x = (move & NOT_A) >> 9
    captured = 0
    while x & opp:
        captured |= x
        x = (x & NOT_A) >> 9
    if x & me:
        flips |= captured

    x = ((move & NOT_H) << 9) & FULL
    captured = 0
    while x & opp:
        captured |= x
        x = ((x & NOT_H) << 9) & FULL
    if x & me:
        flips |= captured

    x = ((move & NOT_A) << 7) & FULL
    captured = 0
    while x & opp:
        captured |= x
        x = ((x & NOT_A) << 7) & FULL
    if x & me:
        flips |= captured

    me2 = (me | move | flips) & FULL
    opp2 = (opp & ~flips) & FULL
    return me2, opp2


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    me, opp = arrays_to_bitboards(you, opponent)

    lm = legal_moves
    am = apply_move
    nb = neighbors
    pc = popcount

    legal = lm(me, opp)
    if not legal:
        return "pass"

    if (legal & (legal - 1)) == 0:
        return bit_to_str(legal)

    start = time.perf_counter()
    deadline = start + 0.94

    tt = {}
    stable_cache = {}
    pos_cache = {}
    history = [0] * 64
    nodes = 0

    def check_time():
        nonlocal nodes
        nodes += 1
        if (nodes & 1023) == 0 and time.perf_counter() >= deadline:
            raise TimeoutError

    def stable_edge_count(player: int) -> int:
        v = stable_cache.get(player)
        if v is not None:
            return v

        stable = 0

        if player & A1:
            stable |= A1
            for idx in (1, 2, 3, 4, 5, 6, 7):
                bit = 1 << idx
                if player & bit:
                    stable |= bit
                else:
                    break
            for idx in (8, 16, 24, 32, 40, 48, 56):
                bit = 1 << idx
                if player & bit:
                    stable |= bit
                else:
                    break

        if player & H1:
            stable |= H1
            for idx in (6, 5, 4, 3, 2, 1, 0):
                bit = 1 << idx
                if player & bit:
                    stable |= bit
                else:
                    break
            for idx in (15, 23, 31, 39, 47, 55, 63):
                bit = 1 << idx
                if player & bit:
                    stable |= bit
                else:
                    break

        if player & A8:
            stable |= A8
            for idx in (57, 58, 59, 60, 61, 62, 63):
                bit = 1 << idx
                if player & bit:
                    stable |= bit
                else:
                    break
            for idx in (48, 40, 32, 24, 16, 8, 0):
                bit = 1 << idx
                if player & bit:
                    stable |= bit
                else:
                    break

        if player & H8:
            stable |= H8
            for idx in (62, 61, 60, 59, 58, 57, 56):
                bit = 1 << idx
                if player & bit:
                    stable |= bit
                else:
                    break
            for idx in (55, 47, 39, 31, 23, 15, 7):
                bit = 1 << idx
                if player & bit:
                    stable |= bit
                else:
                    break

        v = pc(stable)
        stable_cache[player] = v
        return v

    def positional_sum(player: int) -> int:
        v = pos_cache.get(player)
        if v is not None:
            return v
        s = 0
        b = player
        while b:
            lsb = b & -b
            s += PSQ[lsb.bit_length() - 1]
            b ^= lsb
        pos_cache[player] = s
        return s

    def evaluate(me_b: int, opp_b: int, legal_me: int = None, legal_opp: int = None) -> int:
        if legal_me is None:
            legal_me = lm(me_b, opp_b)
        if legal_opp is None:
            legal_opp = lm(opp_b, me_b)

        discs_me = pc(me_b)
        discs_opp = pc(opp_b)
        occupied = me_b | opp_b
        empty = FULL ^ occupied
        empties = 64 - discs_me - discs_opp

        mob_diff = pc(legal_me) - pc(legal_opp)
        pmob_diff = pc(empty & nb(opp_b)) - pc(empty & nb(me_b))

        my_corners = pc(me_b & CORNERS)
        opp_corners = pc(opp_b & CORNERS)
        corner_term = 350 * (my_corners - opp_corners)

        adj_term = 0
        for corner, c_mask, x_mask in CORNER_PATTERNS:
            if not (occupied & corner):
                adj_term += 20 * (pc(opp_b & c_mask) - pc(me_b & c_mask))
                adj_term += 40 * (((opp_b & x_mask) != 0) - ((me_b & x_mask) != 0))

        stable_diff = stable_edge_count(me_b) - stable_edge_count(opp_b)

        near_empty = nb(empty)
        frontier_diff = pc(opp_b & near_empty) - pc(me_b & near_empty)

        pos_diff = positional_sum(me_b) - positional_sum(opp_b)
        disc_diff = discs_me - discs_opp

        if empties > 44:
            score = (
                18 * mob_diff
                + 8 * pmob_diff
                + corner_term
                + adj_term
                + pos_diff
                + 20 * stable_diff
                + 10 * frontier_diff
            )
        elif empties > 20:
            score = (
                22 * mob_diff
                + 5 * pmob_diff
                + corner_term
                + adj_term
                + pos_diff
                + 26 * stable_diff
                + 8 * frontier_diff
                + 2 * disc_diff
            )
        else:
            parity = 10 if (empties & 1) else -10
            score = (
                10 * mob_diff
                + 2 * pmob_diff
                + corner_term
                + adj_term
                + pos_diff
                + 32 * stable_diff
                + 4 * frontier_diff
                + 18 * disc_diff
                + parity
            )
        return int(score)

    def generate_ordered_moves(me_b: int, opp_b: int, legal_b: int, tt_move: int = 0, pv_move: int = 0):
        occupied = me_b | opp_b
        ordered = []
        moves = legal_b

        while moves:
            m = moves & -moves
            moves ^= m

            idx = m.bit_length() - 1
            new_me, new_opp = am(me_b, opp_b, m)
            child_legal = lm(new_opp, new_me)

            s = ORDER_PSQ[idx] + history[idx]

            if m == pv_move:
                s += 700_000
            elif m == tt_move:
                s += 500_000

            if m & CORNERS:
                s += 200_000

            if child_legal == 0:
                s += 30_000

            child_corner_moves = child_legal & CORNERS
            if child_corner_moves:
                s -= 150_000 * pc(child_corner_moves)

            if not (occupied & A1):
                if m & B2:
                    s -= 90_000
                elif m & (B1 | A2):
                    s -= 40_000

            if not (occupied & H1):
                if m & G2:
                    s -= 90_000
                elif m & (G1 | H2):
                    s -= 40_000

            if not (occupied & A8):
                if m & B7:
                    s -= 90_000
                elif m & (A7 | B8):
                    s -= 40_000

            if not (occupied & H8):
                if m & G7:
                    s -= 90_000
                elif m & (G8 | H7):
                    s -= 40_000

            s -= 100 * pc(child_legal)

            ordered.append((s, idx, m, new_me, new_opp, child_legal))

        ordered.sort(key=lambda x: x[0], reverse=True)
        return ordered

    def search(me_b: int, opp_b: int, depth: int, alpha: int, beta: int, legal_b: int = None) -> int:
        check_time()

        orig_alpha = alpha
        orig_beta = beta
        key = (me_b, opp_b)

        entry = tt.get(key)
        tt_best = 0
        if entry is not None:
            tt_best = entry[3]
            stored_depth, stored_flag, stored_val, _ = entry
            if stored_depth >= depth:
                if stored_flag == EXACT:
                    return stored_val
                if stored_flag == LOWER:
                    if stored_val > alpha:
                        alpha = stored_val
                else:
                    if stored_val < beta:
                        beta = stored_val
                if alpha >= beta:
                    return stored_val

        if legal_b is None:
            legal_b = lm(me_b, opp_b)

        if not legal_b:
            opp_legal = lm(opp_b, me_b)
            if not opp_legal:
                diff = pc(me_b) - pc(opp_b)
                if diff > 0:
                    return WIN + diff
                if diff < 0:
                    return -WIN + diff
                return 0
            val = -search(opp_b, me_b, depth, -beta, -alpha, opp_legal)
            tt[key] = (depth, EXACT, val, 0)
            return val

        if depth == 0:
            opp_legal = lm(opp_b, me_b)
            val = evaluate(me_b, opp_b, legal_b, opp_legal)
            tt[key] = (depth, EXACT, val, 0)
            return val

        best_val = -INF
        best_move = 0

        for _, idx, m, new_me, new_opp, child_legal in generate_ordered_moves(me_b, opp_b, legal_b, tt_best, 0):
            val = -search(new_opp, new_me, depth - 1, -beta, -alpha, child_legal)

            if val > best_val:
                best_val = val
                best_move = m

            if val > alpha:
                alpha = val

            if alpha >= beta:
                history[idx] += 200 * depth * depth
                break

        if best_val <= orig_alpha:
            flag = UPPER
        elif best_val >= orig_beta:
            flag = LOWER
        else:
            flag = EXACT
        tt[key] = (depth, flag, best_val, best_move)
        return best_val

    def root_search(depth: int, preferred_move: int):
        alpha = -INF
        beta = INF
        best_val = -INF

        root_entry = tt.get((me, opp))
        tt_best = root_entry[3] if root_entry is not None else 0

        ordered = generate_ordered_moves(me, opp, legal, tt_best, preferred_move)
        best_move = ordered[0][2]

        for _, _, m, new_me, new_opp, child_legal in ordered:
            val = -search(new_opp, new_me, depth - 1, -beta, -alpha, child_legal)

            if val > best_val:
                best_val = val
                best_move = m

            if val > alpha:
                alpha = val

        tt[(me, opp)] = (depth, EXACT, best_val, best_move)
        return best_move, best_val

    empties = 64 - pc(me | opp)

    if empties <= 12:
        depth_seq = []
        for d in (4, 6, 8, 10, empties):
            if d <= empties and d not in depth_seq:
                depth_seq.append(d)
    elif empties <= 18:
        depth_seq = [4, 6, 8, 10]
    elif empties <= 28:
        depth_seq = [4, 5, 6, 7, 8]
    elif empties <= 40:
        depth_seq = [4, 5, 6, 7]
    else:
        depth_seq = [4, 5, 6]

    default_order = generate_ordered_moves(me, opp, legal)
    best_move = default_order[0][2]

    for depth in depth_seq:
        if time.perf_counter() >= deadline:
            break
        try:
            move, val = root_search(depth, best_move)
            best_move = move
            if abs(val) >= WIN and depth >= empties:
                break
        except TimeoutError:
            break

    return bit_to_str(best_move)
