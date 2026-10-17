
import time
import numpy as np

# Bitboard constants
MASK_NOT_A = 0xfefefefefefefefe
MASK_NOT_H = 0x7f7f7f7f7f7f7f7f
MASK_NOT_AB = 0xfcfcfcfcfcfcfcfc
MASK_NOT_GH = 0x3f3f3f3f3f3f3f3f
FULL_MASK = 0xffffffffffffffff

# Positional square weights (64-element table)
WEIGHTS = [
    120, -25,  20,   5,   5,  20, -25, 120,
    -25, -45,  -5,  -5,  -5,  -5, -45, -25,
     20,  -5,  15,   3,   3,  15,  -5,  20,
      5,  -5,   3,   3,   3,   3,  -5,   5,
      5,  -5,   3,   3,   3,   3,  -5,   5,
     20,  -5,  15,   3,   3,  15,  -5,  20,
    -25, -45,  -5,  -5,  -5,  -5, -45, -25,
    120, -25,  20,   5,   5,  20, -25, 120
]

CORNERS = [0, 7, 56, 63]
X_SQUARES = {
    0: 9,
    7: 14,
    56: 49,
    63: 54
}

def popcount(b: int) -> int:
    return bin(b).count('1')

def get_moves(P: int, O: int) -> int:
    """Generate all legal moves for player P given opponent O as a bitboard."""
    empty = ~(P | O) & FULL_MASK
    legal = 0

    # East (+1)
    mask = O & MASK_NOT_H
    t = (P << 1) & mask
    t |= (t << 1) & mask
    t |= (t << 1) & mask
    t |= (t << 1) & mask
    t |= (t << 1) & mask
    t |= (t << 1) & mask
    legal |= (t << 1) & MASK_NOT_A & empty

    # West (-1)
    mask = O & MASK_NOT_A
    t = (P >> 1) & mask
    t |= (t >> 1) & mask
    t |= (t >> 1) & mask
    t |= (t >> 1) & mask
    t |= (t >> 1) & mask
    t |= (t >> 1) & mask
    legal |= (t >> 1) & MASK_NOT_H & empty

    # South (+8)
    mask = O
    t = (P << 8) & mask
    t |= (t << 8) & mask
    t |= (t << 8) & mask
    t |= (t << 8) & mask
    t |= (t << 8) & mask
    t |= (t << 8) & mask
    legal |= (t << 8) & empty

    # North (-8)
    mask = O
    t = (P >> 8) & mask
    t |= (t >> 8) & mask
    t |= (t >> 8) & mask
    t |= (t >> 8) & mask
    t |= (t >> 8) & mask
    t |= (t >> 8) & mask
    legal |= (t >> 8) & empty

    # South-East (+9)
    mask = O & MASK_NOT_H
    t = (P << 9) & mask
    t |= (t << 9) & mask
    t |= (t << 9) & mask
    t |= (t << 9) & mask
    t |= (t << 9) & mask
    t |= (t << 9) & mask
    legal |= (t << 9) & MASK_NOT_A & empty

    # South-West (+7)
    mask = O & MASK_NOT_A
    t = (P << 7) & mask
    t |= (t << 7) & mask
    t |= (t << 7) & mask
    t |= (t << 7) & mask
    t |= (t << 7) & mask
    t |= (t << 7) & mask
    legal |= (t << 7) & MASK_NOT_H & empty

    # North-East (-7)
    mask = O & MASK_NOT_H
    t = (P >> 7) & mask
    t |= (t >> 7) & mask
    t |= (t >> 7) & mask
    t |= (t >> 7) & mask
    t |= (t >> 7) & mask
    t |= (t >> 7) & mask
    legal |= (t >> 7) & MASK_NOT_A & empty

    # North-West (-9)
    mask = O & MASK_NOT_A
    t = (P >> 9) & mask
    t |= (t >> 9) & mask
    t |= (t >> 9) & mask
    t |= (t >> 9) & mask
    t |= (t >> 9) & mask
    t |= (t >> 9) & mask
    legal |= (t >> 9) & MASK_NOT_H & empty

    return legal & FULL_MASK

def make_move(P: int, O: int, move_sq: int):
    """Execute move on square move_sq (0-63). Returns (new_P, new_O)."""
    move_bit = 1 << move_sq
    flipped = 0

    shifts = [
        (1, MASK_NOT_H, MASK_NOT_A, True),    # East
        (-1, MASK_NOT_A, MASK_NOT_H, False),  # West
        (8, FULL_MASK, FULL_MASK, True),      # South
        (-8, FULL_MASK, FULL_MASK, False),    # North
        (9, MASK_NOT_H, MASK_NOT_A, True),    # South-East
        (7, MASK_NOT_A, MASK_NOT_H, True),    # South-West
        (-7, MASK_NOT_H, MASK_NOT_A, False),  # North-East
        (-9, MASK_NOT_A, MASK_NOT_H, False)   # North-West
    ]

    for shift, mask_step, _, is_left in shifts:
        cur_flipped = 0
        cur = (move_bit << shift) if is_left else (move_bit >> shift)
        while cur and (cur & O & mask_step):
            cur_flipped |= cur
            cur = (cur << shift) if is_left else (cur >> shift)
        if cur & P:
            flipped |= cur_flipped

    new_P = P | move_bit | flipped
    new_O = O & ~flipped
    return new_P, new_O

def evaluate(P: int, O: int, p_moves: int, o_moves: int) -> int:
    total_discs = popcount(P | O)
    p_count = popcount(P)
    o_count = popcount(O)

    # Endgame disc difference
    if total_discs >= 58:
        return (p_count - o_count) * 100

    p_mob = popcount(p_moves)
    o_mob = popcount(o_moves)

    # Mobility score
    if p_mob + o_mob > 0:
        mob_score = 100 * (p_mob - o_mob) / (p_mob + o_mob)
    else:
        mob_score = 0

    # Positional score with dynamic corner safety
    pos_score = 0
    for sq in range(64):
        bit = 1 << sq
        if P & bit:
            pos_score += WEIGHTS[sq]
        elif O & bit:
            pos_score -= WEIGHTS[sq]

    # Mitigate X-square penalties if the corresponding corner is occupied
    for corner, x_sq in X_SQUARES.items():
        corner_bit = 1 << corner
        x_bit = 1 << x_sq
        if (P | O) & corner_bit:
            if P & x_bit:
                pos_score += 35
            elif O & x_bit:
                pos_score -= 35

    parity_score = (p_count - o_count)
    return int(pos_score * 1.5 + mob_score * 10 + parity_score)

def negamax(P: int, O: int, depth: int, alpha: int, beta: int, deadline: float, tt: dict) -> int:
    if time.time() > deadline:
        raise TimeoutError()

    state_key = (P, O)
    tt_entry = tt.get(state_key)
    if tt_entry and tt_entry[0] >= depth:
        stored_depth, flag, value, _ = tt_entry
        if flag == 0:  # EXACT
            return value
        elif flag == 1 and value <= alpha:  # UPPERBOUND
            return value
        elif flag == 2 and value >= beta:  # LOWERBOUND
            return value

    p_moves = get_moves(P, O)
    o_moves = get_moves(O, P)

    # Terminal state
    if p_moves == 0 and o_moves == 0:
        p_count = popcount(P)
        o_count = popcount(O)
        if p_count > o_count:
            return 10000 + (p_count - o_count)
        elif p_count < o_count:
            return -10000 + (p_count - o_count)
        return 0

    if depth <= 0:
        return evaluate(P, O, p_moves, o_moves)

    # Pass turn if no moves
    if p_moves == 0:
        val = -negamax(O, P, depth - 1, -beta, -alpha, deadline, tt)
        return val

    # Order moves
    moves_list = []
    temp_moves = p_moves
    while temp_moves:
        lsb = temp_moves & -temp_moves
        sq = (lsb.bit_length() - 1)
        moves_list.append(sq)
        temp_moves &= temp_moves - 1

    best_sq = None
    if tt_entry and tt_entry[3] in moves_list:
        best_sq = tt_entry[3]
        moves_list.remove(best_sq)
        moves_list.insert(0, best_sq)
    else:
        moves_list.sort(key=lambda s: WEIGHTS[s], reverse=True)

    best_val = -1000000
    orig_alpha = alpha
    best_move_here = moves_list[0]

    for sq in moves_list:
        new_P, new_O = make_move(P, O, sq)
        val = -negamax(new_O, new_P, depth - 1, -beta, -alpha, deadline, tt)
        if val > best_val:
            best_val = val
            best_move_here = sq
        alpha = max(alpha, val)
        if alpha >= beta:
            break

    # Store in transposition table
    flag = 0
    if best_val <= orig_alpha:
        flag = 1  # UPPERBOUND
    elif best_val >= beta:
        flag = 2  # LOWERBOUND
    tt[state_key] = (depth, flag, best_val, best_move_here)

    return best_val

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Given 'you' and 'opponent' (8x8 numpy arrays with 0/1 integers),
    returns the chosen move in algebraic notation (e.g. 'c4') or 'pass'.
    """
    # Convert numpy boards to 64-bit integers
    P = 0
    O = 0
    for r in range(8):
        for c in range(8):
            sq = r * 8 + c
            if you[r, c] == 1:
                P |= (1 << sq)
            elif opponent[r, c] == 1:
                O |= (1 << sq)

    legal_bb = get_moves(P, O)
    if legal_bb == 0:
        return "pass"

    moves_list = []
    temp = legal_bb
    while temp:
        lsb = temp & -temp
        sq = lsb.bit_length() - 1
        moves_list.append(sq)
        temp &= temp - 1

    if len(moves_list) == 1:
        sq = moves_list[0]
        r, c = divmod(sq, 8)
        return f"{chr(ord('a') + c)}{r + 1}"

    # Start iterative deepening search
    start_time = time.time()
    deadline = start_time + 0.85  # Stay safely within 1.0 second constraint
    best_move = moves_list[0]
    tt = {}

    empty_count = 64 - popcount(P | O)
    max_depth = min(empty_count, 14)

    for depth in range(1, max_depth + 1):
        try:
            moves_list.sort(key=lambda s: WEIGHTS[s], reverse=True)
            if best_move in moves_list:
                moves_list.remove(best_move)
                moves_list.insert(0, best_move)

            current_best_val = -1000000
            current_best_move = best_move
            alpha = -1000000
            beta = 1000000

            for sq in moves_list:
                new_P, new_O = make_move(P, O, sq)
                val = -negamax(new_O, new_P, depth - 1, -beta, -alpha, deadline, tt)
                if val > current_best_val:
                    current_best_val = val
                    current_best_move = sq
                alpha = max(alpha, val)

            best_move = current_best_move

            # If win is already proven, stop search
            if current_best_val >= 9000 or current_best_val <= -9000:
                break
        except TimeoutError:
            break

    r, c = divmod(best_move, 8)
    return f"{chr(ord('a') + c)}{r + 1}"
