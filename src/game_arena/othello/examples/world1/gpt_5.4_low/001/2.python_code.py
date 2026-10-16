
import time
import numpy as np

FULL = (1 << 64) - 1
NOT_A = 0xFEFEFEFEFEFEFEFE
NOT_H = 0x7F7F7F7F7F7F7F7F

INF = 10**18

# Standard Othello positional weights
SQUARE_WEIGHTS = [
    120, -20,  20,   5,   5,  20, -20, 120,
    -20, -40,  -5,  -5,  -5,  -5, -40, -20,
     20,  -5,  15,   3,   3,  15,  -5,  20,
      5,  -5,   3,   3,   3,   3,  -5,   5,
      5,  -5,   3,   3,   3,   3,  -5,   5,
     20,  -5,  15,   3,   3,  15,  -5,  20,
    -20, -40,  -5,  -5,  -5,  -5, -40, -20,
    120, -20,  20,   5,   5,  20, -20, 120,
]

CORNERS = [0, 7, 56, 63]
X_SQUARES = {0: 9, 7: 14, 56: 49, 63: 54}
C_SQUARES = {
    0: (1, 8),
    7: (6, 15),
    56: (48, 57),
    63: (55, 62),
}


class TimeoutSearch(Exception):
    pass


def shift_n(bb):
    return (bb << 8) & FULL


def shift_s(bb):
    return bb >> 8


def shift_e(bb):
    return ((bb & NOT_H) << 1) & FULL


def shift_w(bb):
    return (bb & NOT_A) >> 1


def shift_ne(bb):
    return ((bb & NOT_H) << 9) & FULL


def shift_nw(bb):
    return ((bb & NOT_A) << 7) & FULL


def shift_se(bb):
    return (bb & NOT_H) >> 7


def shift_sw(bb):
    return (bb & NOT_A) >> 9


SHIFTS = (shift_n, shift_s, shift_e, shift_w, shift_ne, shift_nw, shift_se, shift_sw)


def popcount(x: int) -> int:
    return x.bit_count()


def bit_to_index(bit: int) -> int:
    return bit.bit_length() - 1


def index_to_move(idx: int) -> str:
    return chr(ord('a') + (idx % 8)) + str((idx // 8) + 1)


def arrays_to_bitboards(you: np.ndarray, opponent: np.ndarray):
    y = 0
    o = 0
    flat_y = np.asarray(you, dtype=np.uint8).ravel()
    flat_o = np.asarray(opponent, dtype=np.uint8).ravel()
    for i in range(64):
        if flat_y[i]:
            y |= 1 << i
        elif flat_o[i]:
            o |= 1 << i
    return y, o


def flips_for_move(move_bit: int, me: int, opp: int) -> int:
    if move_bit & (me | opp):
        return 0
    flips = 0
    for sh in SHIFTS:
        x = sh(move_bit) & opp
        captured = 0
        while x:
            captured |= x
            y = sh(x)
            if y & me:
                flips |= captured
                break
            x = y & opp
    return flips


def legal_moves_list(me: int, opp: int):
    empty = (~(me | opp)) & FULL
    moves = []
    e = empty
    while e:
        move = e & -e
        if flips_for_move(move, me, opp):
            moves.append(move)
        e ^= move
    return moves


def apply_move(me: int, opp: int, move_bit: int):
    flips = flips_for_move(move_bit, me, opp)
    new_me = me | move_bit | flips
    new_opp = opp & ~flips
    return new_me, new_opp


def neighbor_mask(bb: int) -> int:
    return (
        shift_n(bb) | shift_s(bb) | shift_e(bb) | shift_w(bb) |
        shift_ne(bb) | shift_nw(bb) | shift_se(bb) | shift_sw(bb)
    )


def positional_score(me: int, opp: int) -> int:
    score = 0
    b = me
    while b:
        bit = b & -b
        score += SQUARE_WEIGHTS[bit_to_index(bit)]
        b ^= bit
    b = opp
    while b:
        bit = b & -b
        score -= SQUARE_WEIGHTS[bit_to_index(bit)]
        b ^= bit
    return score


def corner_score(me: int, opp: int) -> int:
    score = 0
    for c in CORNERS:
        bit = 1 << c
        if me & bit:
            score += 1
        elif opp & bit:
            score -= 1
    return score


def corner_closeness_score(me: int, opp: int) -> int:
    score = 0
    occupied = me | opp
    for c in CORNERS:
        cbit = 1 << c
        if occupied & cbit:
            continue
        x = 1 << X_SQUARES[c]
        c1 = 1 << C_SQUARES[c][0]
        c2 = 1 << C_SQUARES[c][1]
        if me & x:
            score -= 3
        elif opp & x:
            score += 3
        if me & c1:
            score -= 2
        elif opp & c1:
            score += 2
        if me & c2:
            score -= 2
        elif opp & c2:
            score += 2
    return score


def frontier_score(me: int, opp: int) -> int:
    empty = (~(me | opp)) & FULL
    near_empty = neighbor_mask(empty)
    my_front = popcount(me & near_empty)
    opp_front = popcount(opp & near_empty)
    return opp_front - my_front


def evaluate(me: int, opp: int) -> int:
    occupied = me | opp
    empties = 64 - popcount(occupied)

    my_moves = len(legal_moves_list(me, opp))
    opp_moves = len(legal_moves_list(opp, me))

    if my_moves == 0 and opp_moves == 0:
        diff = popcount(me) - popcount(opp)
        if diff > 0:
            return 100000 + diff
        if diff < 0:
            return -100000 + diff
        return 0

    pos = positional_score(me, opp)
    corners = corner_score(me, opp)
    close = corner_closeness_score(me, opp)
    frontier = frontier_score(me, opp)
    disc_diff = popcount(me) - popcount(opp)

    mobility = 0
    total_moves = my_moves + opp_moves
    if total_moves:
        mobility = 100 * (my_moves - opp_moves) / total_moves

    # Phase-dependent weights
    if empties > 44:       # opening
        return int(
            8 * corners +
            3.5 * mobility +
            1.2 * pos +
            2.0 * close +
            1.5 * frontier +
            0.1 * disc_diff
        )
    elif empties > 20:     # midgame
        return int(
            18 * corners +
            4.5 * mobility +
            1.0 * pos +
            2.0 * close +
            2.0 * frontier +
            0.3 * disc_diff
        )
    else:                  # late game
        return int(
            30 * corners +
            3.0 * mobility +
            0.6 * pos +
            1.0 * close +
            1.0 * frontier +
            2.5 * disc_diff
        )


def move_order_key(move: int, me: int, opp: int) -> int:
    idx = bit_to_index(move)
    score = SQUARE_WEIGHTS[idx] * 4 + popcount(flips_for_move(move, me, opp))

    if idx in CORNERS:
        score += 10000

    # Avoid dangerous moves near empty corners
    for c in CORNERS:
        if idx == X_SQUARES[c] or idx in C_SQUARES[c]:
            if ((me | opp) & (1 << c)) == 0:
                score -= 500

    return score


def negamax(me: int, opp: int, depth: int, alpha: int, beta: int, passed: bool,
            start_time: float, time_limit: float) -> int:
    if time.perf_counter() - start_time > time_limit:
        raise TimeoutSearch

    moves = legal_moves_list(me, opp)

    if depth == 0:
        return evaluate(me, opp)

    if not moves:
        opp_moves = legal_moves_list(opp, me)
        if passed or not opp_moves:
            diff = popcount(me) - popcount(opp)
            if diff > 0:
                return 100000 + diff
            if diff < 0:
                return -100000 + diff
            return 0
        return -negamax(opp, me, depth - 1, -beta, -alpha, True, start_time, time_limit)

    moves.sort(key=lambda m: move_order_key(m, me, opp), reverse=True)

    best = -INF
    for move in moves:
        new_me, new_opp = apply_move(me, opp, move)
        score = -negamax(new_opp, new_me, depth - 1, -beta, -alpha, False, start_time, time_limit)

        if score > best:
            best = score
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    return best


def choose_depth(empties: int) -> int:
    if empties <= 10:
        return 12
    if empties <= 14:
        return 10
    if empties <= 20:
        return 8
    if empties <= 30:
        return 6
    if empties <= 44:
        return 5
    return 4


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    me, opp = arrays_to_bitboards(you, opponent)
    moves = legal_moves_list(me, opp)

    if not moves:
        return "pass"

    if len(moves) == 1:
        return index_to_move(bit_to_index(moves[0]))

    # Fast tactical shortcut: take a corner immediately if available.
    corner_moves = [m for m in moves if bit_to_index(m) in CORNERS]
    if corner_moves:
        best_corner = max(corner_moves, key=lambda m: move_order_key(m, me, opp))
        return index_to_move(bit_to_index(best_corner))

    occupied = me | opp
    empties = 64 - popcount(occupied)
    max_depth = choose_depth(empties)

    start_time = time.perf_counter()
    time_limit = 0.92

    # Guaranteed legal fallback
    moves.sort(key=lambda m: move_order_key(m, me, opp), reverse=True)
    best_move = moves[0]

    # Iterative deepening
    for depth in range(1, max_depth + 1):
        try:
            current_best_move = best_move
            alpha = -INF
            beta = INF

            ordered_moves = sorted(moves, key=lambda m: (
                10**9 if m == best_move else move_order_key(m, me, opp)
            ), reverse=True)

            local_best_score = -INF
            for move in ordered_moves:
                new_me, new_opp = apply_move(me, opp, move)
                score = -negamax(new_opp, new_me, depth - 1, -beta, -alpha, False, start_time, time_limit)

                if score > local_best_score:
                    local_best_score = score
                    current_best_move = move
                if score > alpha:
                    alpha = score

            best_move = current_best_move

        except TimeoutSearch:
            break

    return index_to_move(bit_to_index(best_move))
