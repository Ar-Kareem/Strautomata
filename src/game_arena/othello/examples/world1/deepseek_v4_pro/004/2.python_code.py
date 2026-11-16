
import numpy as np
import time

# 64-bit full mask
FULL_MASK = 0xFFFFFFFFFFFFFFFF

# Precomputed masks for corners, X-squares, C-squares, and other edges
CORNERS_MASK = sum(1 << i for i in [0, 7, 56, 63])  
X_MASK       = sum(1 << i for i in [9, 14, 49, 54])
C_MASK       = sum(1 << i for i in [1, 8, 6, 15, 48, 57, 55, 62])

EDGE_OTHER_MASK = 0
for r in (0, 7):
    for c in range(8):
        bit = r * 8 + c
        if not (CORNERS_MASK & (1 << bit) or X_MASK & (1 << bit) or C_MASK & (1 << bit)):
            EDGE_OTHER_MASK |= 1 << bit
for c in (0, 7):
    for r in range(1, 7):
        bit = r * 8 + c
        if not (CORNERS_MASK & (1 << bit) or X_MASK & (1 << bit) or C_MASK & (1 << bit)):
            EDGE_OTHER_MASK |= 1 << bit

# Maps a corner to its associated X-square and C-squares
CORNER_X_MAP = {0: 9, 7: 14, 56: 49, 63: 54}
CORNER_C_MAP = {
    0: [1, 8],
    7: [6, 15],
    56: [48, 57],
    63: [55, 62],
}

# Static move ordering weights (classic Othello square values)
MOVE_WEIGHTS = [
    100, -20, 10,  5,  5, 10, -20, 100,
    -20, -50, -2, -2, -2, -2, -50, -20,
    10,  -2,  0,  0,  0,  0,  -2,  10,
    5,   -2,  0,  0,  0,  0,  -2,   5,
    5,   -2,  0,  0,  0,  0,  -2,   5,
    10,  -2,  0,  0,  0,  0,  -2,  10,
    -20, -50, -2, -2, -2, -2, -50, -20,
    100, -20, 10,  5,  5, 10, -20, 100,
]

class TimeoutError(Exception):
    pass

def get_moves(player: int, opponent: int) -> int:
    """Returns a bitboard of all legal moves for the player."""
    empty = FULL_MASK ^ (player | opponent)
    moves = 0

    # North (+8)
    x = ((player << 8) & FULL_MASK) & opponent
    x |= ((x << 8) & FULL_MASK) & opponent
    x |= ((x << 8) & FULL_MASK) & opponent
    x |= ((x << 8) & FULL_MASK) & opponent
    x |= ((x << 8) & FULL_MASK) & opponent
    x |= ((x << 8) & FULL_MASK) & opponent
    moves |= ((x << 8) & FULL_MASK) & empty

    # South (-8)
    x = (player >> 8) & opponent
    x |= (x >> 8) & opponent
    x |= (x >> 8) & opponent
    x |= (x >> 8) & opponent
    x |= (x >> 8) & opponent
    x |= (x >> 8) & opponent
    moves |= (x >> 8) & empty

    # East (+1), mask H file
    pre = 0x7F7F7F7F7F7F7F7F
    x = ((player & pre) << 1) & FULL_MASK & opponent
    x |= ((x & pre) << 1) & FULL_MASK & opponent
    x |= ((x & pre) << 1) & FULL_MASK & opponent
    x |= ((x & pre) << 1) & FULL_MASK & opponent
    x |= ((x & pre) << 1) & FULL_MASK & opponent
    x |= ((x & pre) << 1) & FULL_MASK & opponent
    moves |= ((x & pre) << 1) & FULL_MASK & empty

    # West (-1), mask A file
    pre = 0xFEFEFEFEFEFEFEFE
    x = ((player & pre) >> 1) & opponent
    x |= ((x & pre) >> 1) & opponent
    x |= ((x & pre) >> 1) & opponent
    x |= ((x & pre) >> 1) & opponent
    x |= ((x & pre) >> 1) & opponent
    x |= ((x & pre) >> 1) & opponent
    moves |= ((x & pre) >> 1) & empty

    # NE (+9), mask H file
    pre = 0x7F7F7F7F7F7F7F7F
    x = ((player & pre) << 9) & FULL_MASK & opponent
    x |= ((x & pre) << 9) & FULL_MASK & opponent
    x |= ((x & pre) << 9) & FULL_MASK & opponent
    x |= ((x & pre) << 9) & FULL_MASK & opponent
    x |= ((x & pre) << 9) & FULL_MASK & opponent
    x |= ((x & pre) << 9) & FULL_MASK & opponent
    moves |= ((x & pre) << 9) & FULL_MASK & empty

    # NW (+7), mask A file
    pre = 0xFEFEFEFEFEFEFEFE
    x = ((player & pre) << 7) & FULL_MASK & opponent
    x |= ((x & pre) << 7) & FULL_MASK & opponent
    x |= ((x & pre) << 7) & FULL_MASK & opponent
    x |= ((x & pre) << 7) & FULL_MASK & opponent
    x |= ((x & pre) << 7) & FULL_MASK & opponent
    x |= ((x & pre) << 7) & FULL_MASK & opponent
    moves |= ((x & pre) << 7) & FULL_MASK & empty

    # SE (-7), mask H file
    pre = 0x7F7F7F7F7F7F7F7F
    x = ((player & pre) >> 7) & opponent
    x |= ((x & pre) >> 7) & opponent
    x |= ((x & pre) >> 7) & opponent
    x |= ((x & pre) >> 7) & opponent
    x |= ((x & pre) >> 7) & opponent
    x |= ((x & pre) >> 7) & opponent
    moves |= ((x & pre) >> 7) & empty

    # SW (-9), mask A file
    pre = 0xFEFEFEFEFEFEFEFE
    x = ((player & pre) >> 9) & opponent
    x |= ((x & pre) >> 9) & opponent
    x |= ((x & pre) >> 9) & opponent
    x |= ((x & pre) >> 9) & opponent
    x |= ((x & pre) >> 9) & opponent
    x |= ((x & pre) >> 9) & opponent
    moves |= ((x & pre) >> 9) & empty

    return moves

def apply_move(player: int, opponent: int, move_bit: int) -> tuple[int, int]:
    """Applies a move and returns (new_player, new_opponent) bitboards."""
    flipped = 0

    # North
    m = (move_bit << 8) & FULL_MASK
    x = 0
    while m & opponent:
        x |= m
        m = (m << 8) & FULL_MASK
    if m & player:
        flipped |= x

    # South
    m = move_bit >> 8
    x = 0
    while m & opponent:
        x |= m
        m >>= 8
    if m & player:
        flipped |= x

    # East
    pre = 0x7F7F7F7F7F7F7F7F
    m = ((move_bit & pre) << 1) & FULL_MASK
    x = 0
    while m & opponent:
        x |= m
        m = ((m & pre) << 1) & FULL_MASK
    if m & player:
        flipped |= x

    # West
    pre = 0xFEFEFEFEFEFEFEFE
    m = ((move_bit & pre) >> 1)
    x = 0
    while m & opponent:
        x |= m
        m = ((m & pre) >> 1)
    if m & player:
        flipped |= x

    # NE
    pre = 0x7F7F7F7F7F7F7F7F
    m = ((move_bit & pre) << 9) & FULL_MASK
    x = 0
    while m & opponent:
        x |= m
        m = ((m & pre) << 9) & FULL_MASK
    if m & player:
        flipped |= x

    # NW
    pre = 0xFEFEFEFEFEFEFEFE
    m = ((move_bit & pre) << 7) & FULL_MASK
    x = 0
    while m & opponent:
        x |= m
        m = ((m & pre) << 7) & FULL_MASK
    if m & player:
        flipped |= x

    # SE
    pre = 0x7F7F7F7F7F7F7F7F
    m = ((move_bit & pre) >> 7)
    x = 0
    while m & opponent:
        x |= m
        m = ((m & pre) >> 7)
    if m & player:
        flipped |= x

    # SW
    pre = 0xFEFEFEFEFEFEFEFE
    m = ((move_bit & pre) >> 9)
    x = 0
    while m & opponent:
        x |= m
        m = ((m & pre) >> 9)
    if m & player:
        flipped |= x

    return player | move_bit | flipped, opponent ^ flipped

def get_move_list(player: int, opponent: int) -> list[int]:
    """Returns a list of single-bit moves from a bitboard of legal moves."""
    bb = get_moves(player, opponent)
    moves = []
    while bb:
        lsb = bb & -bb
        moves.append(lsb)
        bb ^= lsb
    return moves

def evaluate(player: int, opponent: int) -> int:
    """Heuristic evaluation from the perspective of `player`."""
    total = (player | opponent).bit_count()
    empty = 64 - total
    score = 0

    # Corners
    p_c = (player & CORNERS_MASK).bit_count()
    o_c = (opponent & CORNERS_MASK).bit_count()
    score += 100 * (p_c - o_c)

    # X and C squares (penalised when associated corner is empty)
    for corner in (0, 7, 56, 63):
        corner_bit = 1 << corner
        if not ((player | opponent) & corner_bit):
            x_bit = 1 << CORNER_X_MAP[corner]
            if player & x_bit:
                score -= 25
            if opponent & x_bit:
                score += 25
            for c in CORNER_C_MAP[corner]:
                c_bit = 1 << c
                if player & c_bit:
                    score -= 15
                if opponent & c_bit:
                    score += 15

    # Remaining edge squares
    p_e = (player & EDGE_OTHER_MASK).bit_count()
    o_e = (opponent & EDGE_OTHER_MASK).bit_count()
    score += 3 * (p_e - o_e)

    # Phase-dependent mobility and disc count
    if empty > 24:
        mob_weight, disc_weight = 6, 0
    elif empty > 12:
        mob_weight, disc_weight = 4, 1
    else:
        mob_weight, disc_weight = 0, 6

    if mob_weight:
        p_moves = get_moves(player, opponent).bit_count()
        o_moves = get_moves(opponent, player).bit_count()
        score += mob_weight * (p_moves - o_moves)
    if disc_weight:
        score += disc_weight * (player.bit_count() - opponent.bit_count())

    # Parity bonus in the endgame
    if empty <= 12:
        score += 8 if empty % 2 else -8

    return score

def negamax(player: int, opponent: int, depth: int, alpha: int, beta: int,
            start_time: float, time_limit: float) -> int:
    """Negamax with alpha-beta pruning."""
    if time.perf_counter() - start_time > time_limit:
        raise TimeoutError()
    if depth == 0:
        return evaluate(player, opponent)

    moves = get_move_list(player, opponent)
    if not moves:
        # pass move: if opponent also has no move, game ends
        if not get_moves(opponent, player):
            diff = player.bit_count() - opponent.bit_count()
            if diff > 0:
                return 10000
            if diff < 0:
                return -10000
            return 0
        return -negamax(opponent, player, depth, -beta, -alpha, start_time, time_limit)

    # Move ordering by static square weights
    moves.sort(key=lambda m: MOVE_WEIGHTS[(m.bit_length() - 1)], reverse=True)
    best = -999999
    for move in moves:
        new_p, new_o = apply_move(player, opponent, move)
        score = -negamax(new_o, new_p, depth - 1, -beta, -alpha, start_time, time_limit)
        if score > best:
            best = score
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break
    return best

def bit_to_algebraic(move_bit: int) -> str:
    """Converts a single-bit move to algebraic notation, e.g. 'd3'."""
    idx = move_bit.bit_length() - 1
    row = idx // 8
    col = idx % 8
    return chr(ord('a') + col) + str(row + 1)

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    # Convert numpy arrays to bitboards (bit 0 = a1, bit 63 = h8)
    player_bb = 0
    opp_bb = 0
    for r in range(8):
        for c in range(8):
            if you[r, c]:
                player_bb |= 1 << (r * 8 + c)
            if opponent[r, c]:
                opp_bb |= 1 << (r * 8 + c)

    moves = get_move_list(player_bb, opp_bb)
    if not moves:
        return "pass"

    start_time = time.perf_counter()
    time_limit = 0.95
    best_move = moves[0]

    # Iterative deepening
    for depth in range(1, 20):
        if time.perf_counter() - start_time > time_limit:
            break
        try:
            current_best = None
            alpha = -999999
            beta = 999999

            # Put the best move from the previous iteration first
            moves_sorted = sorted(moves, key=lambda m: MOVE_WEIGHTS[(m.bit_length() - 1)], reverse=True)
            if depth > 1 and best_move in moves_sorted:
                moves_sorted.remove(best_move)
                moves_sorted.insert(0, best_move)

            for move in moves_sorted:
                new_p, new_o = apply_move(player_bb, opp_bb, move)
                score = -negamax(new_o, new_p, depth - 1, -beta, -alpha, start_time, time_limit)
                if score > alpha:
                    alpha = score
                    current_best = move
            if current_best is not None:
                best_move = current_best
        except TimeoutError:
            break

    return bit_to_algebraic(best_move)
