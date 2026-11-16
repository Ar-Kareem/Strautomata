
import numpy as np
import time

# ============================================================================
# Bitboard constants and helpers
# ============================================================================
# Board layout: bit index = r * 8 + c, where r=0..7 (row 1..8), c=0..7 (a..h)
FULL_MASK = 0xFFFFFFFFFFFFFFFF
A_FILE   = 0x0101010101010101
H_FILE   = 0x8080808080808080

MASK_EAST = FULL_MASK & ~H_FILE
MASK_WEST = FULL_MASK & ~A_FILE

def east(bb):   return ((bb & MASK_EAST) << 1) & FULL_MASK
def west(bb):   return (bb & MASK_WEST) >> 1
def north(bb):  return (bb << 8) & FULL_MASK
def south(bb):  return bb >> 8
def ne(bb):     return ((bb & MASK_EAST) << 9) & FULL_MASK
def nw(bb):     return ((bb & MASK_WEST) << 7) & FULL_MASK
def se(bb):     return ((bb & MASK_EAST) >> 7)
def sw(bb):     return ((bb & MASK_WEST) >> 9)

DIRECTION_FUNCS = [east, west, north, south, ne, nw, se, sw]

# ============================================================================
# Static evaluation weights (classic Othello matrix, row-major)
# ============================================================================
WEIGHT_ARR = [
    100, -20, 10,  5,  5, 10, -20, 100,
    -20, -50, -2, -2, -2, -2, -50, -20,
    10,  -2, -1, -1, -1, -1,  -2,  10,
     5,  -2, -1,  0,  0, -1,  -2,   5,
     5,  -2, -1,  0,  0, -1,  -2,   5,
    10,  -2, -1, -1, -1, -1,  -2,  10,
    -20, -50, -2, -2, -2, -2, -50, -20,
    100, -20, 10,  5,  5, 10, -20, 100
]

# ============================================================================
# Move generation and execution
# ============================================================================
def legal_moves(me, opp):
    """Return bitmask of all legal moves for player 'me'."""
    empty = ~(me | opp) & FULL_MASK
    legal = 0
    for dir_f in DIRECTION_FUNCS:
        propagated = 0
        temp = dir_f(me) & opp
        while temp:
            propagated |= temp
            temp = dir_f(temp) & opp
        legal |= dir_f(propagated) & empty
    return legal

def make_move(me, opp, pos):
    """Place disc at 'pos' (single-bit mask) for player 'me', return (new_me, new_opp)."""
    flips = 0
    for dir_f in DIRECTION_FUNCS:
        line = 0
        temp = dir_f(pos) & opp
        while temp:
            line |= temp
            temp = dir_f(temp) & opp
        if dir_f(line) & (me | pos):
            flips |= line
    return me | pos | flips, opp ^ flips

# ============================================================================
# Evaluation
# ============================================================================
def eval_state(us, them, empty_count):
    """Heuristic evaluation from 'us' perspective (positive = good for us)."""
    if empty_count <= 14:
        # Endgame: pure piece difference
        return us.bit_count() - them.bit_count()
    score = 0
    # Weighted squares for our pieces
    bb = us
    while bb:
        lsb = bb & -bb
        score += WEIGHT_ARR[lsb.bit_length() - 1]
        bb ^= lsb
    # Subract weighted squares for opponent
    bb = them
    while bb:
        lsb = bb & -bb
        score -= WEIGHT_ARR[lsb.bit_length() - 1]
        bb ^= lsb
    return score

# ============================================================================
# Alpha-beta search with iterative deepening
# ============================================================================
class TimeoutError(Exception):
    """Raised when the time budget is exceeded."""
    pass

def list_bits(bb):
    res = []
    while bb:
        lsb = bb & -bb
        res.append(lsb)
        bb ^= lsb
    return res

def alphabeta(us, them, depth, alpha, beta, maximixing, empty_count, start_time, time_limit):
    if time.time() - start_time > time_limit:
        raise TimeoutError()
    if depth == 0 or empty_count == 0:
        return eval_state(us, them, empty_count)

    if maximixing:
        legal = legal_moves(us, them)
        if legal == 0:
            opp_legal = legal_moves(them, us)
            if opp_legal == 0:
                diff = us.bit_count() - them.bit_count()
                return diff * 10000
            # Pass turn
            return alphabeta(us, them, depth - 1, alpha, beta, False, empty_count, start_time, time_limit)

        move_list = list_bits(legal)
        # Sort moves by quick static evaluation of resulting position
        move_evals = []
        for mv in move_list:
            new_us, new_them = make_move(us, them, mv)
            move_evals.append((eval_state(new_us, new_them, empty_count - 1), mv))
        move_evals.sort(reverse=True)

        val = -float('inf')
        for _, mv in move_evals:
            new_us, new_them = make_move(us, them, mv)
            child = alphabeta(new_us, new_them, depth - 1, alpha, beta, False, empty_count - 1, start_time, time_limit)
            if child > val:
                val = child
            if val > alpha:
                alpha = val
            if alpha >= beta:
                break
        return val
    else:
        legal = legal_moves(them, us)
        if legal == 0:
            opp_legal = legal_moves(us, them)
            if opp_legal == 0:
                diff = us.bit_count() - them.bit_count()
                return diff * 10000
            return alphabeta(us, them, depth - 1, alpha, beta, True, empty_count, start_time, time_limit)

        move_list = list_bits(legal)
        move_evals = []
        for mv in move_list:
            new_them, new_us = make_move(them, us, mv)
            move_evals.append((eval_state(new_us, new_them, empty_count - 1), mv))
        move_evals.sort()  # ascending: good for opponent = bad for us

        val = float('inf')
        for _, mv in move_evals:
            new_them, new_us = make_move(them, us, mv)
            child = alphabeta(new_us, new_them, depth - 1, alpha, beta, True, empty_count - 1, start_time, time_limit)
            if child < val:
                val = child
            if val < beta:
                beta = val
            if alpha >= beta:
                break
        return val

def get_best_move(us, them, empty_count, time_limit=0.95):
    start = time.time()
    legal = legal_moves(us, them)
    if legal == 0:
        return None

    move_list = list_bits(legal)
    move_evals = []
    for mv in move_list:
        new_us, new_them = make_move(us, them, mv)
        move_evals.append((eval_state(new_us, new_them, empty_count - 1), mv))
    move_evals.sort(reverse=True)
    best_move = move_evals[0][1]  # fallback

    depth = 1
    try:
        while True:
            # Run one iteration of alpha-beta to depth 'depth'
            alpha = -float('inf')
            beta = float('inf')
            best_val = -float('inf')
            for sc, mv in move_evals:
                new_us, new_them = make_move(us, them, mv)
                val = alphabeta(new_us, new_them, depth - 1, alpha, beta, False,
                                empty_count - 1, start, time_limit)
                if val > best_val:
                    best_val = val
                    best_move = mv
                if val > alpha:
                    alpha = val
            depth += 1
    except TimeoutError:
        pass
    return best_move

def bit_to_str(bit):
    idx = bit.bit_length() - 1
    r = idx // 8
    c = idx % 8
    return f"{chr(ord('a') + c)}{r + 1}"

# ============================================================================
# Main policy API
# ============================================================================
def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    # Convert numpy arrays to bitboards
    us = 0
    them = 0
    for r in range(8):
        for c in range(8):
            if you[r, c]:
                us |= 1 << (r * 8 + c)
            if opponent[r, c]:
                them |= 1 << (r * 8 + c)

    empty = ~(us | them) & FULL_MASK
    empty_count = empty.bit_count()
    legal = legal_moves(us, them)

    if legal == 0:
        return "pass"

    # If only one legal move, play it instantly
    if legal.bit_count() == 1:
        return bit_to_str(legal)

    best_bit = get_best_move(us, them, empty_count)
    if best_bit is None:
        # fallback to first legal move (should not happen)
        legal = legal_moves(us, them)
        best_bit = list_bits(legal)[0]

    return bit_to_str(best_bit)
