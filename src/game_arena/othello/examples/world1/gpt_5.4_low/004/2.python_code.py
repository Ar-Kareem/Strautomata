
import time
import numpy as np

MASK64 = (1 << 64) - 1
FILES = "abcdefgh"
DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)]

# Standard strong Othello square weights
WEIGHTS_2D = [
    [120, -20,  20,  5,  5, 20, -20, 120],
    [-20, -40,  -5, -5, -5, -5, -40, -20],
    [ 20,  -5,  15,  3,  3, 15,  -5,  20],
    [  5,  -5,   3,  3,  3,  3,  -5,   5],
    [  5,  -5,   3,  3,  3,  3,  -5,   5],
    [ 20,  -5,  15,  3,  3, 15,  -5,  20],
    [-20, -40,  -5, -5, -5, -5, -40, -20],
    [120, -20,  20,  5,  5, 20, -20, 120],
]
WEIGHTS = [WEIGHTS_2D[r][c] for r in range(8) for c in range(8)]

CORNERS = [0, 7, 56, 63]

# Squares adjacent to corners
X_SQUARES = {0: 9, 7: 14, 56: 49, 63: 54}
C_SQUARES = {
    0: [1, 8],
    7: [6, 15],
    56: [48, 57],
    63: [55, 62],
}

NEIGHBORS = []
for i in range(64):
    r, c = divmod(i, 8)
    nbrs = []
    for dr, dc in DIRS:
        rr, cc = r + dr, c + dc
        if 0 <= rr < 8 and 0 <= cc < 8:
            nbrs.append(rr * 8 + cc)
    NEIGHBORS.append(nbrs)

class Timeout(Exception):
    pass


def idx_to_move(idx: int) -> str:
    return FILES[idx % 8] + str(idx // 8 + 1)


def arrays_to_bitboards(you: np.ndarray, opponent: np.ndarray):
    me = 0
    opp = 0
    for r in range(8):
        for c in range(8):
            bit = 1 << (r * 8 + c)
            if int(you[r][c]) == 1:
                me |= bit
            elif int(opponent[r][c]) == 1:
                opp |= bit
    return me, opp


def bit_count(x: int) -> int:
    return x.bit_count()


def iter_bits(bits: int):
    while bits:
        lsb = bits & -bits
        yield lsb.bit_length() - 1
        bits ^= lsb


def flips_for_move(me: int, opp: int, idx: int) -> int:
    if ((me | opp) >> idx) & 1:
        return 0

    r, c = divmod(idx, 8)
    flipped = 0

    for dr, dc in DIRS:
        rr, cc = r + dr, c + dc
        line = 0
        found_opp = False

        while 0 <= rr < 8 and 0 <= cc < 8:
            j = rr * 8 + cc
            bj = 1 << j
            if opp & bj:
                found_opp = True
                line |= bj
            elif me & bj:
                if found_opp:
                    flipped |= line
                break
            else:
                break
            rr += dr
            cc += dc

    return flipped


def legal_moves(me: int, opp: int):
    empty = (~(me | opp)) & MASK64
    moves = []
    for idx in iter_bits(empty):
        if flips_for_move(me, opp, idx):
            moves.append(idx)
    return moves


def apply_move(me: int, opp: int, idx: int):
    flips = flips_for_move(me, opp, idx)
    move_bit = 1 << idx
    me2 = me | move_bit | flips
    opp2 = opp & ~flips
    return me2, opp2


def frontier_count(player: int, empty: int) -> int:
    cnt = 0
    for idx in iter_bits(player):
        for n in NEIGHBORS[idx]:
            if (empty >> n) & 1:
                cnt += 1
                break
    return cnt


def eval_position(me: int, opp: int) -> int:
    my_discs = bit_count(me)
    opp_discs = bit_count(opp)
    empty = (~(me | opp)) & MASK64
    empties = bit_count(empty)

    my_moves = legal_moves(me, opp)
    opp_moves = legal_moves(opp, me)

    # Terminal positions: exact result matters most
    if empties == 0 or (not my_moves and not opp_moves):
        diff = my_discs - opp_discs
        if diff > 0:
            return 100000 + diff
        if diff < 0:
            return -100000 + diff
        return 0

    score = 0

    # Positional weights
    pos = 0
    for i in iter_bits(me):
        pos += WEIGHTS[i]
    for i in iter_bits(opp):
        pos -= WEIGHTS[i]
    score += 2 * pos

    # Corners
    my_corners = sum(1 for c in CORNERS if (me >> c) & 1)
    opp_corners = sum(1 for c in CORNERS if (opp >> c) & 1)
    score += 200 * (my_corners - opp_corners)

    # Corner-adjacent penalties if corner is empty
    for corner in CORNERS:
        corner_taken = ((me | opp) >> corner) & 1
        if not corner_taken:
            x = X_SQUARES[corner]
            if (me >> x) & 1:
                score -= 60
            elif (opp >> x) & 1:
                score += 60

            for csq in C_SQUARES[corner]:
                if (me >> csq) & 1:
                    score -= 25
                elif (opp >> csq) & 1:
                    score += 25

    # Mobility
    if my_moves or opp_moves:
        score += 18 * (len(my_moves) - len(opp_moves))

    # Frontier discs: fewer is usually better
    my_front = frontier_count(me, empty)
    opp_front = frontier_count(opp, empty)
    score += 6 * (opp_front - my_front)

    # Disc parity matters more late
    if empties <= 16:
        score += 12 * (my_discs - opp_discs)
    elif empties <= 28:
        score += 4 * (my_discs - opp_discs)

    return score


def move_order_key(me: int, opp: int, idx: int):
    # High is better
    val = 0
    if idx in CORNERS:
        val += 100000
    val += 200 * WEIGHTS[idx]

    flips = flips_for_move(me, opp, idx)
    val += 3 * bit_count(flips)

    # Slight preference for reducing opponent mobility
    me2, opp2 = apply_move(me, opp, idx)
    opp_mob = len(legal_moves(opp2, me2))
    val -= 15 * opp_mob

    return val


def choose_depth(empties: int) -> int:
    if empties <= 10:
        return empties
    if empties <= 14:
        return 8
    if empties <= 20:
        return 6
    if empties <= 40:
        return 5
    return 4


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    me, opp = arrays_to_bitboards(you, opponent)
    root_moves = legal_moves(me, opp)
    if not root_moves:
        return "pass"

    # Fast tactical shortcut: take a corner immediately if available
    for m in root_moves:
        if m in CORNERS:
            return idx_to_move(m)

    start = time.time()
    time_limit = 0.92
    trans = {}

    def time_check():
        if time.time() - start > time_limit:
            raise Timeout()

    def negamax(cur_me: int, cur_opp: int, depth: int, alpha: int, beta: int, passed: bool):
        time_check()
        key = (cur_me, cur_opp, depth, passed)
        if key in trans:
            return trans[key]

        moves = legal_moves(cur_me, cur_opp)
        empty_count = 64 - bit_count(cur_me | cur_opp)

        if depth == 0:
            val = eval_position(cur_me, cur_opp)
            trans[key] = val
            return val

        if not moves:
            if passed or empty_count == 0:
                val = eval_position(cur_me, cur_opp)
                trans[key] = val
                return val
            val = -negamax(cur_opp, cur_me, depth, -beta, -alpha, True)
            trans[key] = val
            return val

        ordered = sorted(moves, key=lambda m: move_order_key(cur_me, cur_opp, m), reverse=True)

        best = -10**18
        for mv in ordered:
            me2, opp2 = apply_move(cur_me, cur_opp, mv)
            val = -negamax(opp2, me2, depth - 1, -beta, -alpha, False)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        trans[key] = best
        return best

    empties = 64 - bit_count(me | opp)
    target_depth = choose_depth(empties)

    # Good fallback move in case time runs out immediately
    best_move = max(root_moves, key=lambda m: move_order_key(me, opp, m))

    # Iterative deepening
    try:
        for depth in range(2, target_depth + 1):
            ordered_root = sorted(root_moves, key=lambda m: move_order_key(me, opp, m), reverse=True)
            alpha = -10**18
            beta = 10**18
            current_best_move = ordered_root[0]
            current_best_val = -10**18

            for mv in ordered_root:
                time_check()
                me2, opp2 = apply_move(me, opp, mv)
                val = -negamax(opp2, me2, depth - 1, -beta, -alpha, False)
                if val > current_best_val:
                    current_best_val = val
                    current_best_move = mv
                if val > alpha:
                    alpha = val

            best_move = current_best_move
    except Timeout:
        pass

    # Final safety: ensure legality
    if best_move not in root_moves:
        best_move = root_moves[0]

    return idx_to_move(best_move)
