
import time
import numpy as np

# Bitboard constants and masks
MASK64 = 0xFFFFFFFFFFFFFFFF
NOT_A_FILE = 0xFEFEFEFEFEFEFEFE
NOT_H_FILE = 0x7F7F7F7F7F7F7F7F

# Directions: (shift, is_left_shift, mask)
DIRECTIONS = [
    (1, True, NOT_A_FILE),    # East (right, +1 col)
    (1, False, NOT_H_FILE),   # West (left, -1 col)
    (8, True, MASK64),        # South (+1 row)
    (8, False, MASK64),       # North (-1 row)
    (9, True, NOT_A_FILE),    # South-East
    (7, True, NOT_H_FILE),    # South-West
    (7, False, NOT_A_FILE),   # North-East
    (9, False, NOT_H_FILE),   # North-West
]

# Static evaluation square weights
WEIGHTS = [
    100, -20,  10,   5,   5,  10, -20, 100,
    -20, -40,  -2,  -2,  -2,  -2, -40, -20,
     10,  -2,   1,   1,   1,   1,  -2,  10,
      5,  -2,   1,   0,   0,   1,  -2,   5,
      5,  -2,   1,   0,   0,   1,  -2,   5,
     10,  -2,   1,   1,   1,   1,  -2,  10,
    -20, -40,  -2,  -2,  -2,  -2, -40, -20,
    100, -20,  10,   5,   5,  10, -20, 100
]

CORNER_MASKS = [
    (0, [1, 8, 9]),
    (7, [6, 14, 15]),
    (56, [48, 49, 57]),
    (63, [54, 55, 62])
]


def count_bits(n: int) -> int:
    return bin(n).count("1")


def get_moves(p: int, o: int) -> int:
    """Generate bitboard of legal moves for player p against opponent o."""
    empty = ~(p | o) & MASK64
    legal = 0
    for shift, is_left, mask in DIRECTIONS:
        if is_left:
            w = ((p << shift) & MASK64) & o & mask
            for _ in range(5):
                w |= ((w << shift) & MASK64) & o & mask
            legal |= ((w << shift) & MASK64) & empty & mask
        else:
            w = (p >> shift) & o & mask
            for _ in range(5):
                w |= (w >> shift) & o & mask
            legal |= (w >> shift) & empty & mask
    return legal & MASK64


def make_move(p: int, o: int, move_idx: int) -> tuple[int, int]:
    """Execute move at move_idx (0..63) for player p against opponent o. Return (new_p, new_o)."""
    move_bb = 1 << move_idx
    flipped = 0
    for shift, is_left, mask in DIRECTIONS:
        cur_flipped = 0
        if is_left:
            cur = ((move_bb << shift) & MASK64) & mask
            while cur and (cur & o):
                cur_flipped |= cur
                cur = ((cur << shift) & MASK64) & mask
            if cur & p:
                flipped |= cur_flipped
        else:
            cur = (move_bb >> shift) & mask
            while cur and (cur & o):
                cur_flipped |= cur
                cur = (cur >> shift) & mask
            if cur & p:
                flipped |= cur_flipped
    new_p = p | move_bb | flipped
    new_o = o & ~flipped
    return new_p, new_o


def bit_to_pos(idx: int) -> str:
    r = idx // 8
    c = idx % 8
    return chr(ord('a') + c) + str(r + 1)


def evaluate(p: int, o: int, empty_count: int) -> int:
    """Heuristic evaluation from the perspective of player p."""
    p_disc_count = count_bits(p)
    o_disc_count = count_bits(o)

    # Endgame disc dominance
    if empty_count == 0:
        return (p_disc_count - o_disc_count) * 1000

    # Positional square weights
    pos_score = 0
    p_temp, o_temp = p, o
    for i in range(64):
        if (p_temp >> i) & 1:
            pos_score += WEIGHTS[i]
        elif (o_temp >> i) & 1:
            pos_score -= WEIGHTS[i]

    # Mitigate corner hazards if corners are occupied
    for corner_idx, adj_indices in CORNER_MASKS:
        corner_bit = 1 << corner_idx
        if p & corner_bit:
            for adj in adj_indices:
                if (p >> adj) & 1:
                    pos_score += 25
        elif o & corner_bit:
            for adj in adj_indices:
                if (o >> adj) & 1:
                    pos_score -= 25

    # Mobility: Difference in legal moves
    p_moves = count_bits(get_moves(p, o))
    o_moves = count_bits(get_moves(o, p))
    mob_score = 0
    if p_moves + o_moves > 0:
        mob_score = int(100.0 * (p_moves - o_moves) / (p_moves + o_moves))

    # Corner occupancy
    corners = (0x8100000000000081)
    p_corners = count_bits(p & corners)
    o_corners = count_bits(o & corners)
    corner_score = (p_corners - o_corners) * 150

    return pos_score + 10 * mob_score + corner_score


def get_move_list(legal_bb: int) -> list[int]:
    moves = []
    while legal_bb:
        lsb = legal_bb & -legal_bb
        moves.append(lsb.bit_length() - 1)
        legal_bb ^= lsb
    # Prioritize corners and high-value cells
    moves.sort(key=lambda idx: WEIGHTS[idx], reverse=True)
    return moves


def alpha_beta(p: int, o: int, depth: int, alpha: int, beta: int, passed: bool, deadline: float) -> int:
    if time.time() > deadline:
        raise TimeoutError()

    empty_count = 64 - count_bits(p | o)
    if depth == 0 or empty_count == 0:
        return evaluate(p, o, empty_count)

    legal_bb = get_moves(p, o)
    if not legal_bb:
        if passed:
            # Both players passed -> terminal state
            return (count_bits(p) - count_bits(o)) * 1000
        # Pass turn to opponent
        return -alpha_beta(o, p, depth - 1, -beta, -alpha, True, deadline)

    moves = get_move_list(legal_bb)
    for m in moves:
        np_p, np_o = make_move(p, o, m)
        val = -alpha_beta(np_o, np_p, depth - 1, -beta, -alpha, False, deadline)
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break
    return alpha


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    # Convert 8x8 numpy arrays to 64-bit bitboards
    p = 0
    o = 0
    for r in range(8):
        for c in range(8):
            bit = 1 << (r * 8 + c)
            if you[r, c] == 1:
                p |= bit
            elif opponent[r, c] == 1:
                o |= bit

    legal_bb = get_moves(p, o)
    if not legal_bb:
        return "pass"

    moves = get_move_list(legal_bb)
    if len(moves) == 1:
        return bit_to_pos(moves[0])

    empty_count = 64 - count_bits(p | o)
    start_time = time.time()
    deadline = start_time + 0.85  # Conservative budget under 1.0s

    best_move = moves[0]

    # Iterative deepening search
    max_depth = empty_count if empty_count <= 12 else 8
    for depth in range(1, max_depth + 1):
        try:
            current_best_move = moves[0]
            alpha = -1000000000
            beta = 1000000000

            for m in moves:
                np_p, np_o = make_move(p, o, m)
                score = -alpha_beta(np_o, np_p, depth - 1, -beta, -alpha, False, deadline)
                if score > alpha:
                    alpha = score
                    current_best_move = m

            best_move = current_best_move
            # Reorder moves putting the best move first for subsequent depths
            moves.remove(best_move)
            moves.insert(0, best_move)

        except TimeoutError:
            break

    return bit_to_pos(best_move)
