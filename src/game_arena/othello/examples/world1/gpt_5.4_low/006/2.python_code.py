
import time
import numpy as np

FULL = 0xFFFFFFFFFFFFFFFF

NOT_A = 0xFEFEFEFEFEFEFEFE
NOT_H = 0x7F7F7F7F7F7F7F7F

CORNERS = (1 << 0) | (1 << 7) | (1 << 56) | (1 << 63)
X_SQUARES = (1 << 9) | (1 << 14) | (1 << 49) | (1 << 54)

# Standard strong Othello square table
SQ_WEIGHTS = [
    120, -20,  20,   5,   5,  20, -20, 120,
    -20, -40,  -5,  -5,  -5,  -5, -40, -20,
     20,  -5,  15,   3,   3,  15,  -5,  20,
      5,  -5,   3,   3,   3,   3,  -5,   5,
      5,  -5,   3,   3,   3,   3,  -5,   5,
     20,  -5,  15,   3,   3,  15,  -5,  20,
    -20, -40,  -5,  -5,  -5,  -5, -40, -20,
    120, -20,  20,   5,   5,  20, -20, 120,
]

# Corner-adjacent danger squares when the corner is empty
CORNER_ADJ = {
    0:  [1, 8, 9],
    7:  [6, 14, 15],
    56: [48, 49, 57],
    63: [54, 55, 62],
}

INF = 10**18


def shift_e(x):  return ((x << 1) & NOT_A) & FULL
def shift_w(x):  return ((x >> 1) & NOT_H) & FULL
def shift_n(x):  return (x << 8) & FULL
def shift_s(x):  return (x >> 8) & FULL
def shift_ne(x): return ((x << 9) & NOT_A) & FULL
def shift_nw(x): return ((x << 7) & NOT_H) & FULL
def shift_se(x): return ((x >> 7) & NOT_A) & FULL
def shift_sw(x): return ((x >> 9) & NOT_H) & FULL

DIRS = (shift_e, shift_w, shift_n, shift_s, shift_ne, shift_nw, shift_se, shift_sw)


class Timeout(Exception):
    pass


def bit_to_index(bit: int) -> int:
    return bit.bit_length() - 1


def move_to_str(bit: int) -> str:
    i = bit_to_index(bit)
    r, c = divmod(i, 8)
    return chr(ord('a') + c) + str(r + 1)


def iter_bits(x: int):
    while x:
        b = x & -x
        yield b
        x ^= b


def board_to_bitboard(arr: np.ndarray) -> int:
    flat = arr.ravel()
    bb = 0
    for i in range(64):
        if int(flat[i]) != 0:
            bb |= 1 << i
    return bb


def legal_moves(player: int, opp: int) -> int:
    empty = (~(player | opp)) & FULL
    moves = 0

    for shift in DIRS:
        x = shift(player) & opp
        for _ in range(5):
            x |= shift(x) & opp
        moves |= shift(x) & empty

    return moves & FULL


def flips_for_move(move: int, player: int, opp: int) -> int:
    flips = 0
    for shift in DIRS:
        x = shift(move)
        captured = 0
        while x and (x & opp):
            captured |= x
            x = shift(x)
        if x & player:
            flips |= captured
    return flips


def apply_move(move: int, player: int, opp: int):
    flips = flips_for_move(move, player, opp)
    player2 = player | move | flips
    opp2 = opp & ~flips
    return opp2, player2  # swap side to move


def positional_score(player: int, opp: int) -> int:
    s = 0
    p = player
    while p:
        b = p & -p
        s += SQ_WEIGHTS[bit_to_index(b)]
        p ^= b
    o = opp
    while o:
        b = o & -o
        s -= SQ_WEIGHTS[bit_to_index(b)]
        o ^= b
    return s


def frontier_count(player: int, opp: int) -> int:
    occupied = player | opp
    empty = (~occupied) & FULL

    adj_empty = (
        shift_e(empty) | shift_w(empty) | shift_n(empty) | shift_s(empty) |
        shift_ne(empty) | shift_nw(empty) | shift_se(empty) | shift_sw(empty)
    )
    return (player & adj_empty).bit_count()


def corner_closeness(player: int, opp: int) -> int:
    score = 0
    occupied = player | opp
    for corner, adj in CORNER_ADJ.items():
        cbit = 1 << corner
        if not (occupied & cbit):
            for sq in adj:
                b = 1 << sq
                if player & b:
                    score -= 12
                elif opp & b:
                    score += 12
    return score


def evaluate(player: int, opp: int) -> int:
    pm = legal_moves(player, opp)
    om = legal_moves(opp, player)

    if pm == 0 and om == 0:
        diff = player.bit_count() - opp.bit_count()
        if diff > 0:
            return 100000 + diff
        if diff < 0:
            return -100000 + diff
        return 0

    empties = 64 - (player | opp).bit_count()

    disc_diff = player.bit_count() - opp.bit_count()
    mob_diff = pm.bit_count() - om.bit_count()
    corner_diff = (player & CORNERS).bit_count() - (opp & CORNERS).bit_count()
    pos = positional_score(player, opp)
    front_diff = frontier_count(opp, player) - frontier_count(player, opp)  # fewer own frontier discs is better
    close = corner_closeness(player, opp)

    # Phase-aware weighting
    if empties > 40:
        return (
            8 * mob_diff +
            20 * corner_diff +
            1 * pos +
            4 * front_diff +
            2 * close
        )
    elif empties > 16:
        return (
            10 * mob_diff +
            30 * corner_diff +
            2 * pos +
            5 * front_diff +
            2 * close +
            1 * disc_diff
        )
    else:
        return (
            6 * mob_diff +
            40 * corner_diff +
            2 * pos +
            3 * front_diff +
            8 * disc_diff +
            1 * close
        )


def move_order_key(move: int, player: int, opp: int) -> int:
    idx = bit_to_index(move)
    score = 0

    if move & CORNERS:
        score += 100000

    # Penalize X-squares if corner empty
    if move & X_SQUARES:
        if idx == 9 and not ((player | opp) & (1 << 0)):
            score -= 1500
        elif idx == 14 and not ((player | opp) & (1 << 7)):
            score -= 1500
        elif idx == 49 and not ((player | opp) & (1 << 56)):
            score -= 1500
        elif idx == 54 and not ((player | opp) & (1 << 63)):
            score -= 1500

    # Positional weight
    score += 20 * SQ_WEIGHTS[idx]

    # Immediate mobility suppression heuristic
    n_opp, n_player = apply_move(move, player, opp)
    opp_moves = legal_moves(n_opp, n_player).bit_count()
    my_moves = legal_moves(n_player, n_opp).bit_count()
    score += 15 * my_moves
    score -= 18 * opp_moves

    # Prefer larger flips slightly in the endgame, less so early
    flips = flips_for_move(move, player, opp).bit_count()
    empties = 64 - (player | opp).bit_count()
    if empties <= 14:
        score += 10 * flips
    else:
        score += 2 * flips

    return score


def ordered_moves(player: int, opp: int):
    moves = legal_moves(player, opp)
    lst = list(iter_bits(moves))
    lst.sort(key=lambda m: move_order_key(m, player, opp), reverse=True)
    return lst


def choose_max_depth(empties: int) -> int:
    if empties <= 10:
        return 64  # effectively exact
    if empties <= 14:
        return 10
    if empties <= 20:
        return 7
    if empties <= 32:
        return 5
    return 4


def negamax(player: int, opp: int, depth: int, alpha: int, beta: int,
            end_time: float, tt: dict, passed: bool = False) -> int:
    if time.perf_counter() >= end_time:
        raise Timeout

    key = (player, opp, depth, passed)
    if key in tt:
        return tt[key]

    moves = legal_moves(player, opp)

    if depth == 0:
        val = evaluate(player, opp)
        tt[key] = val
        return val

    if moves == 0:
        opp_moves = legal_moves(opp, player)
        if opp_moves == 0:
            val = evaluate(player, opp)
            tt[key] = val
            return val
        val = -negamax(opp, player, depth, -beta, -alpha, end_time, tt, True)
        tt[key] = val
        return val

    best = -INF
    for move in ordered_moves(player, opp):
        n_opp, n_player = apply_move(move, player, opp)
        score = -negamax(n_opp, n_player, depth - 1, -beta, -alpha, end_time, tt, False)
        if score > best:
            best = score
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    tt[key] = best
    return best


def best_move(player: int, opp: int, time_limit: float) -> int:
    moves = ordered_moves(player, opp)
    if not moves:
        return 0
    if len(moves) == 1:
        return moves[0]

    empties = 64 - (player | opp).bit_count()
    max_depth = choose_max_depth(empties)

    # Safe fallback: best heuristic move
    best = moves[0]
    best_score = -INF

    end_time = time.perf_counter() + time_limit
    tt = {}

    # Iterative deepening
    for depth in range(1, max_depth + 1):
        if time.perf_counter() >= end_time:
            break

        current_best = best
        current_score = -INF

        try:
            alpha = -INF
            beta = INF
            for move in moves:
                if time.perf_counter() >= end_time:
                    raise Timeout
                n_opp, n_player = apply_move(move, player, opp)
                score = -negamax(n_opp, n_player, depth - 1, -beta, -alpha, end_time, tt, False)
                if score > current_score:
                    current_score = score
                    current_best = move
                if score > alpha:
                    alpha = score

            best = current_best
            best_score = current_score

            # Reorder next iteration around principal variation guess
            moves.sort(key=lambda m: (m == best, move_order_key(m, player, opp)), reverse=True)

        except Timeout:
            break

    return best


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    player = board_to_bitboard(you)
    opp = board_to_bitboard(opponent)

    moves = legal_moves(player, opp)
    if moves == 0:
        return "pass"

    # Keep a little margin under the arena limit.
    move = best_move(player, opp, time_limit=0.92)

    # Absolute legality guard
    if move == 0 or not (move & moves):
        move = next(iter_bits(moves))

    return move_to_str(move)
