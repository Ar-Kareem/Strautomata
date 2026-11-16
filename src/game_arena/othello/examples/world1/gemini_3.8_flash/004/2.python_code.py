
import time
import numpy as np

# Bitboard masks and constants
MASK64 = 0xFFFFFFFFFFFFFFFF
NOT_A = 0xFEFEFEFEFEFEFEFE
NOT_H = 0x7F7F7F7F7F7F7F7F
NOT_AB = 0xFCFCFCFCFCFCFCFC
NOT_GH = 0x3F3F3F3F3F3F3F3F

# 8 directions: (shift, is_left_shift, mask)
DIRECTIONS = [
    (1, True, NOT_H),       # East
    (1, False, NOT_A),      # West
    (8, True, MASK64),      # South
    (8, False, MASK64),     # North
    (9, True, NOT_H),       # South-East
    (7, True, NOT_A),       # South-West
    (7, False, NOT_H),      # North-East
    (9, False, NOT_A),      # North-West
]

# Positional weights for 8x8 board (sq = r * 8 + c)
SQUARE_WEIGHTS = [
    120, -20,  20,   5,   5,  20, -20, 120,
    -20, -40,  -5,  -5,  -5,  -5, -40, -20,
     20,  -5,  15,   3,   3,  15,  -5,  20,
      5,  -5,   3,   3,   3,   3,  -5,   5,
      5,  -5,   3,   3,   3,   3,  -5,   5,
     20,  -5,  15,   3,   3,  15,  -5,  20,
    -20, -40,  -5,  -5,  -5,  -5, -40, -20,
    120, -20,  20,   5,   5,  20, -20, 120
]

CORNERS = [0, 7, 56, 63]
X_SQUARES = {
    0: 9,
    7: 14,
    56: 49,
    63: 54
}
C_SQUARES = {
    0: [1, 8],
    7: [6, 15],
    56: [48, 57],
    63: [55, 62]
}


def get_moves_bitboard(P: int, O: int) -> int:
    empty = (~(P | O)) & MASK64
    legal = 0
    for shift, is_left, mask in DIRECTIONS:
        if is_left:
            w = ((P << shift) & mask) & O
            w |= ((w << shift) & mask) & O
            w |= ((w << shift) & mask) & O
            w |= ((w << shift) & mask) & O
            w |= ((w << shift) & mask) & O
            w |= ((w << shift) & mask) & O
            legal |= (w << shift) & mask & empty
        else:
            w = ((P >> shift) & mask) & O
            w |= ((w >> shift) & mask) & O
            w |= ((w >> shift) & mask) & O
            w |= ((w >> shift) & mask) & O
            w |= ((w >> shift) & mask) & O
            w |= ((w >> shift) & mask) & O
            legal |= (w >> shift) & mask & empty
    return legal


def get_flips(P: int, O: int, move_sq: int) -> int:
    move_bb = 1 << move_sq
    flips = 0
    for shift, is_left, mask in DIRECTIONS:
        if is_left:
            w = (move_bb << shift) & mask & O
            w |= (w << shift) & mask & O
            w |= (w << shift) & mask & O
            w |= (w << shift) & mask & O
            w |= (w << shift) & mask & O
            w |= (w << shift) & mask & O
            if (w << shift) & mask & P:
                flips |= w
        else:
            w = (move_bb >> shift) & mask & O
            w |= (w >> shift) & mask & O
            w |= (w >> shift) & mask & O
            w |= (w >> shift) & mask & O
            w |= (w >> shift) & mask & O
            w |= (w >> shift) & mask & O
            if (w >> shift) & mask & P:
                flips |= w
    return flips


def popcount(x: int) -> int:
    return bin(x).count('1')


def evaluate(P: int, O: int, num_empty: int) -> int:
    p_cnt = popcount(P)
    o_cnt = popcount(O)

    # In endgame, final disc count dominates
    if num_empty <= 4:
        return (p_cnt - o_cnt) * 1000

    # Disc difference
    disc_diff = p_cnt - o_cnt

    # Positional evaluation
    pos_score = 0
    p_temp = P
    while p_temp:
        lsb = p_temp & -p_temp
        sq = (lsb.bit_length() - 1)
        pos_score += SQUARE_WEIGHTS[sq]
        p_temp ^= lsb

    o_temp = O
    while o_temp:
        lsb = o_temp & -o_temp
        sq = (lsb.bit_length() - 1)
        pos_score -= SQUARE_WEIGHTS[sq]
        o_temp ^= lsb

    # Corner dynamic adjustments
    for corner, x_sq in X_SQUARES.items():
        if not ((P | O) & (1 << corner)):
            # Corner is empty, X-square is very dangerous
            if P & (1 << x_sq):
                pos_score -= 50
            if O & (1 << x_sq):
                pos_score += 50
            for c_sq in C_SQUARES[corner]:
                if P & (1 << c_sq):
                    pos_score -= 20
                if O & (1 << c_sq):
                    pos_score += 20

    # Mobility
    p_moves = popcount(get_moves_bitboard(P, O))
    o_moves = popcount(get_moves_bitboard(O, P))
    mobility_score = 0
    if p_moves + o_moves > 0:
        mobility_score = int(100 * (p_moves - o_moves) / (p_moves + o_moves))

    # Weight blending by game phase
    game_progress = (64 - num_empty) / 64.0
    if game_progress < 0.65:
        return pos_score * 10 + mobility_score * 35 - disc_diff * 5
    else:
        return pos_score * 6 + mobility_score * 20 + disc_diff * 15


class SearchTimeout(Exception):
    pass


class Engine:
    def __init__(self, time_limit: float = 0.85):
        self.time_limit = time_limit
        self.start_time = 0.0
        self.tt = {}

    def alpha_beta(self, P: int, O: int, depth: int, alpha: int, beta: int, passed: bool, num_empty: int) -> int:
        if (num_empty & 7) == 0 and time.perf_counter() - self.start_time > self.time_limit:
            raise SearchTimeout()

        if depth == 0 or num_empty == 0:
            return evaluate(P, O, num_empty)

        moves_bb = get_moves_bitboard(P, O)
        if moves_bb == 0:
            if passed:
                p_cnt = popcount(P)
                o_cnt = popcount(O)
                if p_cnt > o_cnt:
                    return 50000 + (p_cnt - o_cnt)
                elif p_cnt < o_cnt:
                    return -50000 + (p_cnt - o_cnt)
                return 0
            # Pass move
            return -self.alpha_beta(O, P, depth - 1, -beta, -alpha, True, num_empty)

        # Transposition table probe
        tt_entry = self.tt.get((P, O))
        best_move_sq = None
        if tt_entry is not None:
            tt_depth, tt_val, tt_flag, tt_best = tt_entry
            if tt_depth >= depth:
                if tt_flag == 0:  # EXACT
                    return tt_val
                elif tt_flag == 1 and tt_val <= alpha:  # UPPER
                    return alpha
                elif tt_flag == 2 and tt_val >= beta:  # LOWER
                    return beta
            best_move_sq = tt_best

        # Extract and order moves
        moves = []
        temp = moves_bb
        while temp:
            lsb = temp & -temp
            sq = lsb.bit_length() - 1
            weight = SQUARE_WEIGHTS[sq]
            if sq == best_move_sq:
                weight += 1000
            moves.append((weight, sq))
            temp ^= lsb

        moves.sort(reverse=True, key=lambda x: x[0])

        best_score = -1000000
        best_sq = moves[0][1]
        orig_alpha = alpha

        for _, sq in moves:
            flips = get_flips(P, O, sq)
            new_P = (P | (1 << sq) | flips)
            new_O = (O ^ flips)
            val = -self.alpha_beta(new_O, new_P, depth - 1, -beta, -alpha, False, num_empty - 1)

            if val > best_score:
                best_score = val
                best_sq = sq

            alpha = max(alpha, val)
            if alpha >= beta:
                break

        # Store in TT
        if best_score <= orig_alpha:
            flag = 1  # UPPER
        elif best_score >= beta:
            flag = 2  # LOWER
        else:
            flag = 0  # EXACT
        self.tt[(P, O)] = (depth, best_score, flag, best_sq)

        return best_score

    def find_best_move(self, P: int, O: int) -> int:
        legal_bb = get_moves_bitboard(P, O)
        if legal_bb == 0:
            return -1

        num_empty = 64 - popcount(P | O)
        moves = []
        temp = legal_bb
        while temp:
            lsb = temp & -temp
            sq = lsb.bit_length() - 1
            moves.append((SQUARE_WEIGHTS[sq], sq))
            temp ^= lsb

        moves.sort(reverse=True, key=lambda x: x[0])
        best_move = moves[0][1]

        self.start_time = time.perf_counter()
        max_depth = 64 if num_empty <= 12 else 16

        for depth in range(1, max_depth + 1):
            cur_best_move = best_move
            alpha = -1000000
            beta = 1000000
            depth_best_score = -1000000

            try:
                for _, sq in moves:
                    flips = get_flips(P, O, sq)
                    new_P = (P | (1 << sq) | flips)
                    new_O = (O ^ flips)
                    val = -self.alpha_beta(new_O, new_P, depth - 1, -beta, -alpha, False, num_empty - 1)
                    if val > depth_best_score:
                        depth_best_score = val
                        cur_best_move = sq
                    alpha = max(alpha, val)

                best_move = cur_best_move
                # Re-sort moves to prioritize current best
                moves.sort(key=lambda x: 10000 if x[1] == best_move else x[0], reverse=True)

                if depth_best_score >= 40000 or depth_best_score <= -40000:
                    break
            except SearchTimeout:
                break

            if num_empty <= 12 and depth >= num_empty:
                break

        return best_move


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    # Convert numpy 8x8 arrays to bitboards
    P = 0
    O = 0
    for r in range(8):
        for c in range(8):
            sq = r * 8 + c
            if you[r, c] == 1:
                P |= (1 << sq)
            elif opponent[r, c] == 1:
                O |= (1 << sq)

    engine = Engine(time_limit=0.88)
    best_sq = engine.find_best_move(P, O)

    if best_sq == -1:
        return "pass"

    r = best_sq // 8
    c = best_sq % 8
    col_str = chr(ord('a') + c)
    row_str = str(r + 1)
    return col_str + row_str
