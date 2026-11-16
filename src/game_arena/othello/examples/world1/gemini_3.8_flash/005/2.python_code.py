
import time
import numpy as np

# Bitboard masks
NOT_A = 0xFEFEFEFEFEFEFEFE
NOT_H = 0x7F7F7F7F7F7F7F7F
CORNER_MASK = 0x8100000000000081

# Positional square weights
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

CORNERS_SET = {0, 7, 56, 63}
X_SQUARES = {9: 0, 14: 7, 49: 56, 54: 63}
C_SQUARES = {1: 0, 8: 0, 6: 7, 15: 7, 48: 56, 57: 56, 55: 63, 62: 63}

EXACT = 0
LOWERBOUND = 1
UPPERBOUND = 2
MAX_TT_SIZE = 250000


def get_moves(P: int, O: int) -> int:
    """Generates a bitmask of all legal moves for player P against opponent O."""
    empty = ~(P | O) & 0xFFFFFFFFFFFFFFFF
    moves = 0

    # East (<< 1)
    mO = O & NOT_H
    w = (P & NOT_H) << 1 & mO
    w |= (w << 1) & mO
    w |= (w << 1) & mO
    w |= (w << 1) & mO
    w |= (w << 1) & mO
    w |= (w << 1) & mO
    moves |= (w << 1) & empty

    # West (>> 1)
    mO = O & NOT_A
    w = (P & NOT_A) >> 1 & mO
    w |= (w >> 1) & mO
    w |= (w >> 1) & mO
    w |= (w >> 1) & mO
    w |= (w >> 1) & mO
    w |= (w >> 1) & mO
    moves |= (w >> 1) & empty

    # South (<< 8)
    w = (P << 8) & O
    w |= (w << 8) & O
    w |= (w << 8) & O
    w |= (w << 8) & O
    w |= (w << 8) & O
    w |= (w << 8) & O
    moves |= (w << 8) & empty

    # North (>> 8)
    w = (P >> 8) & O
    w |= (w >> 8) & O
    w |= (w >> 8) & O
    w |= (w >> 8) & O
    w |= (w >> 8) & O
    w |= (w >> 8) & O
    moves |= (w >> 8) & empty

    # South-East (<< 9)
    mO = O & NOT_H
    w = (P & NOT_H) << 9 & mO
    w |= (w << 9) & mO
    w |= (w << 9) & mO
    w |= (w << 9) & mO
    w |= (w << 9) & mO
    w |= (w << 9) & mO
    moves |= (w << 9) & empty

    # South-West (<< 7)
    mO = O & NOT_A
    w = (P & NOT_A) << 7 & mO
    w |= (w << 7) & mO
    w |= (w << 7) & mO
    w |= (w << 7) & mO
    w |= (w << 7) & mO
    w |= (w << 7) & mO
    moves |= (w << 7) & empty

    # North-East (>> 7)
    mO = O & NOT_H
    w = (P & NOT_H) >> 7 & mO
    w |= (w >> 7) & mO
    w |= (w >> 7) & mO
    w |= (w >> 7) & mO
    w |= (w >> 7) & mO
    w |= (w >> 7) & mO
    moves |= (w >> 7) & empty

    # North-West (>> 9)
    mO = O & NOT_A
    w = (P & NOT_A) >> 9 & mO
    w |= (w >> 9) & mO
    w |= (w >> 9) & mO
    w |= (w >> 9) & mO
    w |= (w >> 9) & mO
    w |= (w >> 9) & mO
    moves |= (w >> 9) & empty

    return moves & 0xFFFFFFFFFFFFFFFF


def make_flips(P: int, O: int, move_bit: int) -> int:
    """Returns a bitmask of all opponent discs flipped by placing a disc at move_bit."""
    flips = 0

    # East
    mO = O & NOT_H
    w = (move_bit & NOT_H) << 1 & mO
    w |= (w << 1) & mO
    w |= (w << 1) & mO
    w |= (w << 1) & mO
    w |= (w << 1) & mO
    w |= (w << 1) & mO
    if (w << 1) & P:
        flips |= w

    # West
    mO = O & NOT_A
    w = (move_bit & NOT_A) >> 1 & mO
    w |= (w >> 1) & mO
    w |= (w >> 1) & mO
    w |= (w >> 1) & mO
    w |= (w >> 1) & mO
    w |= (w >> 1) & mO
    if (w >> 1) & P:
        flips |= w

    # South
    w = (move_bit << 8) & O
    w |= (w << 8) & O
    w |= (w << 8) & O
    w |= (w << 8) & O
    w |= (w << 8) & O
    w |= (w << 8) & O
    if (w << 8) & P:
        flips |= w

    # North
    w = (move_bit >> 8) & O
    w |= (w >> 8) & O
    w |= (w >> 8) & O
    w |= (w >> 8) & O
    w |= (w >> 8) & O
    w |= (w >> 8) & O
    if (w >> 8) & P:
        flips |= w

    # South-East
    mO = O & NOT_H
    w = (move_bit & NOT_H) << 9 & mO
    w |= (w << 9) & mO
    w |= (w << 9) & mO
    w |= (w << 9) & mO
    w |= (w << 9) & mO
    w |= (w << 9) & mO
    if (w << 9) & P:
        flips |= w

    # South-West
    mO = O & NOT_A
    w = (move_bit & NOT_A) << 7 & mO
    w |= (w << 7) & mO
    w |= (w << 7) & mO
    w |= (w << 7) & mO
    w |= (w << 7) & mO
    w |= (w << 7) & mO
    if (w << 7) & P:
        flips |= w

    # North-East
    mO = O & NOT_H
    w = (move_bit & NOT_H) >> 7 & mO
    w |= (w >> 7) & mO
    w |= (w >> 7) & mO
    w |= (w >> 7) & mO
    w |= (w >> 7) & mO
    w |= (w >> 7) & mO
    if (w >> 7) & P:
        flips |= w

    # North-West
    mO = O & NOT_A
    w = (move_bit & NOT_A) >> 9 & mO
    w |= (w >> 9) & mO
    w |= (w >> 9) & mO
    w |= (w >> 9) & mO
    w |= (w >> 9) & mO
    w |= (w >> 9) & mO
    if (w >> 9) & P:
        flips |= w

    return flips


def evaluate(P: int, O: int, my_moves: int, opp_moves: int, empty_count: int) -> int:
    """Static evaluation function combining mobility, corners, stability, and position weights."""
    my_cnt = bin(P).count('1')
    opp_cnt = bin(O).count('1')

    if empty_count <= 0:
        return (my_cnt - opp_cnt) * 10000

    # Corner scores
    c_p = bin(P & CORNER_MASK).count('1')
    c_o = bin(O & CORNER_MASK).count('1')
    corner_score = (c_p - c_o) * 250

    # Danger squares penalty if corner is unoccupied
    danger_score = 0
    if not ((P | O) & 1):
        if P & (1 << 9): danger_score -= 80
        elif O & (1 << 9): danger_score += 80
        if P & 0x0102: danger_score -= 30
        elif O & 0x0102: danger_score += 30

    if not ((P | O) & (1 << 7)):
        if P & (1 << 14): danger_score -= 80
        elif O & (1 << 14): danger_score += 80
        if P & 0x8040: danger_score -= 30
        elif O & 0x8040: danger_score += 30

    if not ((P | O) & (1 << 56)):
        if P & (1 << 49): danger_score -= 80
        elif O & (1 << 49): danger_score += 80
        if P & ((1 << 48) | (1 << 57)): danger_score -= 30
        elif O & ((1 << 48) | (1 << 57)): danger_score += 30

    if not ((P | O) & (1 << 63)):
        if P & (1 << 54): danger_score -= 80
        elif O & (1 << 54): danger_score += 80
        if P & ((1 << 55) | (1 << 62)): danger_score -= 30
        elif O & ((1 << 55) | (1 << 62)): danger_score += 30

    # Mobility score
    my_m = bin(my_moves).count('1')
    opp_m = bin(opp_moves).count('1')
    if my_m + opp_m > 0:
        mobility_score = int(100 * (my_m - opp_m) / (my_m + opp_m))
    else:
        mobility_score = 0

    # Positional weights
    pos_score = 0
    temp_P = P
    while temp_P:
        lsb = temp_P & -temp_P
        pos_score += SQUARE_WEIGHTS[lsb.bit_length() - 1]
        temp_P ^= lsb
    temp_O = O
    while temp_O:
        lsb = temp_O & -temp_O
        pos_score -= SQUARE_WEIGHTS[lsb.bit_length() - 1]
        temp_O ^= lsb

    # Disc parity transition towards endgame
    if empty_count < 16:
        disc_score = (16 - empty_count) * (my_cnt - opp_cnt) * 6
    else:
        disc_score = 0

    return pos_score + corner_score + danger_score + mobility_score * 8 + disc_score


def move_score(sq: int, P: int, O: int, tt_move: int = None) -> int:
    """Move ordering heuristic score."""
    if sq == tt_move:
        return 1000000
    if sq in CORNERS_SET:
        return 100000
    if sq in X_SQUARES and not ((P | O) & (1 << X_SQUARES[sq])):
        return -50000
    if sq in C_SQUARES and not ((P | O) & (1 << C_SQUARES[sq])):
        return -20000
    return SQUARE_WEIGHTS[sq]


def alphabeta(P: int, O: int, depth: int, alpha: int, beta: int, passed: bool,
              start_time: float, time_limit: float, TT: dict, node_counter: list) -> int:
    """Minimax search with alpha-beta pruning and transposition table."""
    node_counter[0] += 1
    if node_counter[0] & 511 == 0:
        if time.time() - start_time > time_limit:
            raise TimeoutError()

    empty_mask = ~(P | O) & 0xFFFFFFFFFFFFFFFF
    if empty_mask == 0:
        my_c = bin(P).count('1')
        opp_c = bin(O).count('1')
        return (my_c - opp_c) * 10000

    tt_entry = TT.get((P, O))
    tt_move = None
    if tt_entry is not None:
        tt_depth, tt_flag, tt_val, tt_move = tt_entry
        if tt_depth >= depth:
            if tt_flag == EXACT:
                return tt_val
            elif tt_flag == LOWERBOUND and tt_val > alpha:
                alpha = tt_val
            elif tt_flag == UPPERBOUND and tt_val < beta:
                beta = tt_val
            if alpha >= beta:
                return tt_val

    my_moves = get_moves(P, O)

    if my_moves == 0:
        if passed:
            my_c = bin(P).count('1')
            opp_c = bin(O).count('1')
            if my_c > opp_c:
                return 100000 + (my_c - opp_c) * 100
            elif my_c < opp_c:
                return -100000 + (my_c - opp_c) * 100
            else:
                return 0
        return -alphabeta(O, P, depth - 1, -beta, -alpha, True, start_time, time_limit, TT, node_counter)

    if depth <= 0:
        opp_moves = get_moves(O, P)
        empty_count = bin(empty_mask).count('1')
        return evaluate(P, O, my_moves, opp_moves, empty_count)

    moves_list = []
    temp = my_moves
    while temp:
        lsb = temp & -temp
        moves_list.append(lsb.bit_length() - 1)
        temp ^= lsb

    moves_list.sort(key=lambda s: move_score(s, P, O, tt_move), reverse=True)

    best_val = -float('inf')
    best_m = moves_list[0]
    orig_alpha = alpha

    for sq in moves_list:
        m_bit = 1 << sq
        flips = make_flips(P, O, m_bit)
        next_P = O ^ flips
        next_O = P ^ m_bit ^ flips

        val = -alphabeta(next_P, next_O, depth - 1, -beta, -alpha, False, start_time, time_limit, TT, node_counter)

        if val > best_val:
            best_val = val
            best_m = sq
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    if len(TT) < MAX_TT_SIZE:
        if best_val <= orig_alpha:
            flag = UPPERBOUND
        elif best_val >= beta:
            flag = LOWERBOUND
        else:
            flag = EXACT
        TT[(P, O)] = (depth, flag, best_val, best_m)

    return best_val


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Computes the best legal move for the current player in algebraic notation.
    Returns "pass" if no legal moves exist.
    """
    start_time = time.time()
    time_budget = 0.82  # Safely within 1.0 second constraint

    # Convert 8x8 numpy arrays to 64-bit integer bitboards
    P = 0
    O = 0
    for r in range(8):
        for c in range(8):
            if you[r, c]:
                P |= 1 << (r * 8 + c)
            elif opponent[r, c]:
                O |= 1 << (r * 8 + c)

    my_moves = get_moves(P, O)
    if my_moves == 0:
        return "pass"

    moves_list = []
    temp = my_moves
    while temp:
        lsb = temp & -temp
        moves_list.append(lsb.bit_length() - 1)
        temp ^= lsb

    # Immediate return if only one legal move
    if len(moves_list) == 1:
        sq = moves_list[0]
        return chr(ord('a') + (sq % 8)) + str((sq // 8) + 1)

    empty_count = bin(~(P | O) & 0xFFFFFFFFFFFFFFFF).count('1')
    best_move = moves_list[0]
    TT = {}
    node_counter = [0]

    max_depth = 64 if empty_count <= 12 else 12

    # Iterative deepening
    for depth in range(1, max_depth + 1):
        try:
            alpha = -float('inf')
            beta = float('inf')
            current_best_val = -float('inf')
            current_best_move = None

            moves_list.sort(key=lambda s: (s == best_move, move_score(s, P, O)), reverse=True)

            for sq in moves_list:
                if time.time() - start_time > time_budget:
                    raise TimeoutError()

                m_bit = 1 << sq
                flips = make_flips(P, O, m_bit)
                next_P = O ^ flips
                next_O = P ^ m_bit ^ flips

                val = -alphabeta(next_P, next_O, depth - 1, -beta, -alpha, False,
                                 start_time, time_budget, TT, node_counter)

                if val > current_best_val:
                    current_best_val = val
                    current_best_move = sq
                if val > alpha:
                    alpha = val

            if current_best_move is not None:
                best_move = current_best_move

            # If full game tree solved to the end
            if empty_count <= 12 and depth >= empty_count:
                break

        except TimeoutError:
            break

    # Convert square index to algebraic notation
    r = best_move // 8
    c = best_move % 8
    return chr(ord('a') + c) + str(r + 1)
