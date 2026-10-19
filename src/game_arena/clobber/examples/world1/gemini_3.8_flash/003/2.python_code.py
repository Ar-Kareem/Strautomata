
import time
import numpy as np

# Board dimensions
ROWS = 5
COLS = 6
NUM_CELLS = ROWS * COLS

# Precompute neighbor moves for all cells
# Moves: 'U', 'R', 'D', 'L'
DIRECTIONS = [
    ('U', -1, 0, -COLS),
    ('R', 0, 1, 1),
    ('D', 1, 0, COLS),
    ('L', 0, -1, -1),
]

MOVES_TABLE = [[] for _ in range(NUM_CELLS)]
for r in range(ROWS):
    for c in range(COLS):
        idx = r * COLS + c
        for dir_name, dr, dc, d_idx in DIRECTIONS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                n_idx = nr * COLS + nc
                MOVES_TABLE[idx].append((dir_name, r, c, idx, n_idx))


def get_legal_moves(my_bits: int, opp_bits: int):
    """Generate all legal moves for current player as list of (move_str, from_idx, to_idx)."""
    moves = []
    # Iterate through bits of my_bits
    temp = my_bits
    while temp:
        # Extract lowest set bit index
        lsb = temp & -temp
        idx = (lsb.bit_length()) - 1
        temp ^= lsb
        for dir_name, r, c, from_idx, to_idx in MOVES_TABLE[idx]:
            if opp_bits & (1 << to_idx):
                moves.append((f"{r},{c},{dir_name}", from_idx, to_idx))
    return moves


def count_legal_moves(my_bits: int, opp_bits: int) -> int:
    """Fast count of legal moves without allocating strings."""
    count = 0
    temp = my_bits
    while temp:
        lsb = temp & -temp
        idx = (lsb.bit_length()) - 1
        temp ^= lsb
        for _, _, _, _, to_idx in MOVES_TABLE[idx]:
            if opp_bits & (1 << to_idx):
                count += 1
    return count


def evaluate_state(my_bits: int, opp_bits: int) -> int:
    """Heuristic evaluation from the perspective of the player to move."""
    my_moves = count_legal_moves(my_bits, opp_bits)
    opp_moves = count_legal_moves(opp_bits, my_bits)

    if my_moves == 0:
        return -90000
    if opp_moves == 0:
        return 90000

    # Mobility is the dominant factor in Clobber
    score = (my_moves - opp_moves) * 100

    # Count of pieces that can make at least one capture
    my_active_pieces = 0
    temp = my_bits
    while temp:
        lsb = temp & -temp
        idx = (lsb.bit_length()) - 1
        temp ^= lsb
        can_move = False
        for _, _, _, _, to_idx in MOVES_TABLE[idx]:
            if opp_bits & (1 << to_idx):
                can_move = True
                break
        if can_move:
            my_active_pieces += 1

    opp_active_pieces = 0
    temp = opp_bits
    while temp:
        lsb = temp & -temp
        idx = (lsb.bit_length()) - 1
        temp ^= lsb
        can_move = False
        for _, _, _, _, to_idx in MOVES_TABLE[idx]:
            if my_bits & (1 << to_idx):
                can_move = True
                break
        if can_move:
            opp_active_pieces += 1

    score += (my_active_pieces - opp_active_pieces) * 40
    return score


class TimeoutException(Exception):
    pass


def negamax(my_bits: int, opp_bits: int, depth: int, alpha: int, beta: int, 
            deadline: float, tt: dict) -> tuple[int, str]:
    """Negamax search with alpha-beta pruning and transposition table."""
    if time.time() >= deadline:
        raise TimeoutException()

    tt_entry = tt.get((my_bits, opp_bits))
    best_move_str = None

    if tt_entry is not None:
        tt_depth, tt_val, tt_flag, tt_best = tt_entry
        if tt_depth >= depth:
            if tt_flag == 'EXACT':
                return tt_val, tt_best
            elif tt_flag == 'LOWERBOUND' and tt_val > alpha:
                alpha = tt_val
            elif tt_flag == 'UPPERBOUND' and tt_val < beta:
                beta = tt_val
            if alpha >= beta:
                return tt_val, tt_best
        best_move_str = tt_best

    moves = get_legal_moves(my_bits, opp_bits)
    if not moves:
        # Current player has no moves: loss
        return -100000 - depth, None

    if depth <= 0:
        val = evaluate_state(my_bits, opp_bits)
        return val, moves[0][0]

    # Move ordering: best move from TT first
    if best_move_str is not None:
        moves.sort(key=lambda m: 0 if m[0] == best_move_str else 1)

    best_val = -float('inf')
    chosen_move = moves[0][0]
    orig_alpha = alpha

    for move_str, from_idx, to_idx in moves:
        # Apply move:
        # Piece moves from from_idx to to_idx.
        # Opponent loses piece at to_idx.
        new_my_bits = (my_bits ^ (1 << from_idx)) | (1 << to_idx)
        new_opp_bits = opp_bits ^ (1 << to_idx)

        val, _ = negamax(new_opp_bits, new_my_bits, depth - 1, -beta, -alpha, deadline, tt)
        val = -val

        if val > best_val:
            best_val = val
            chosen_move = move_str

        if best_val > alpha:
            alpha = best_val

        if alpha >= beta:
            break

    # Transposition table store
    if best_val <= orig_alpha:
        flag = 'UPPERBOUND'
    elif best_val >= beta:
        flag = 'LOWERBOUND'
    else:
        flag = 'EXACT'

    tt[(my_bits, opp_bits)] = (depth, best_val, flag, chosen_move)
    return best_val, chosen_move


def policy(you: list[int], opponent: list[int]) -> str:
    """
    Computes the best next move for Clobber on a 5x6 board.
    Guaranteed to return a legal move string formatted as 'row,col,dir'.
    """
    start_time = time.time()
    deadline = start_time + 0.70  # Leave safety margin for execution

    # Parse board to bitboards
    you_arr = np.asarray(you, dtype=np.int32).reshape(ROWS, COLS)
    opp_arr = np.asarray(opponent, dtype=np.int32).reshape(ROWS, COLS)

    my_bits = 0
    opp_bits = 0
    for r in range(ROWS):
        for c in range(COLS):
            idx = r * COLS + c
            if you_arr[r, c] == 1:
                my_bits |= (1 << idx)
            elif opp_arr[r, c] == 1:
                opp_bits |= (1 << idx)

    legal_moves = get_legal_moves(my_bits, opp_bits)
    if not legal_moves:
        # Fallback if no moves are available
        return "0,0,U"

    best_overall_move = legal_moves[0][0]
    tt = {}

    # Iterative deepening
    for depth in range(1, 35):
        try:
            score, move = negamax(my_bits, opp_bits, depth, -150000, 150000, deadline, tt)
            if move is not None:
                best_overall_move = move
            # If a guaranteed win is found, no need to search further
            if score >= 90000:
                break
        except TimeoutException:
            break

    return best_overall_move
