
import numpy as np

# ----------------------------------------------------------------------
# Global constants
# ----------------------------------------------------------------------
FULL_MASK = (1 << 64) - 1

# Directions as (row_delta, col_delta)
DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1),
              (-1, -1), (-1, 1), (1, -1), (1, 1)]

# Positional weights (flattened row‑major: row0 = rank 1, col0 = file a)
# Corners are +100, squares next to corners are negative, others are modest.
WEIGHT = [
    100, -20, 10,  5,  5, 10, -20, 100,
    -20, -50, -2, -2, -2, -2, -50, -20,
    10,  -2, -1, -1, -1, -1, -2,  10,
    5,   -2, -1, -1, -1, -1, -2,  5,
    5,   -2, -1, -1, -1, -1, -2,  5,
    10,  -2, -1, -1, -1, -1, -2, 10,
    -20, -50, -2, -2, -2, -2, -50, -20,
    100, -20, 10,  5,  5, 10, -20, 100
]

# ----------------------------------------------------------------------
# Bit‑board helpers
# ----------------------------------------------------------------------
def compute_flips(you_bb: int, opp_bb: int, pos: int) -> int:
    """
    Return a 64‑bit mask of opponent discs that would be flipped
    if a disc is placed at `pos` (0 … 63).
    """
    flips = 0
    r, c = divmod(pos, 8)

    for dr, dc in DIRECTIONS:
        nr, nc = r + dr, c + dc
        # off‑board ?
        if not (0 <= nr < 8 and 0 <= nc < 8):
            continue
        npos = nr * 8 + nc
        # immediate neighbour must be opponent disc
        if not ((opp_bb >> npos) & 1):
            continue

        # scan the whole line
        line = 0
        while 0 <= nr < 8 and 0 <= nc < 8:
            bit = 1 << (nr * 8 + nc)
            if (opp_bb >> (nr * 8 + nc)) & 1:
                line |= bit
                nr += dr
                nc += dc
                continue
            elif (you_bb >> (nr * 8 + nc)) & 1:
                flips |= line
                break
            else:               # empty square – no capture in this direction
                break
    return flips


def get_legal_moves(you_bb: int, opp_bb: int):
    """
    Return a list of positions (0‑63) that are legal moves for the player
    whose bits are `you_bb`.
    """
    empty = FULL_MASK & ~(you_bb | opp_bb)
    moves = []
    while empty:
        lsb = empty & -empty
        pos = lsb.bit_length() - 1
        if compute_flips(you_bb, opp_bb, pos):
            moves.append(pos)
        empty ^= lsb
    return moves


def evaluate(you_bb: int, opp_bb: int) -> int:
    """
    Simple static evaluation: weighted sum of your discs minus opponent's.
    """
    you_sum = 0
    bits = you_bb
    while bits:
        lsb = bits & -bits
        pos = lsb.bit_length() - 1
        you_sum += WEIGHT[pos]
        bits ^= lsb

    opp_sum = 0
    bits = opp_bb
    while bits:
        lsb = bits & -bits
        pos = lsb.bit_length() - 1
        opp_sum += WEIGHT[pos]
        bits ^= lsb

    return you_sum - opp_sum


# ----------------------------------------------------------------------
# Minimax with alpha‑beta pruning
# ----------------------------------------------------------------------
def alphabeta(you_bb: int, opp_bb: int,
              depth: int, alpha: int, beta: int,
              maximizing: bool) -> int:
    """Recursive alpha‑beta search."""
    if depth == 0:
        return evaluate(you_bb, opp_bb)

    # generate moves for the player to move
    if maximizing:
        moves = get_legal_moves(you_bb, opp_bb)
    else:
        moves = get_legal_moves(opp_bb, you_bb)

    # terminal – no moves for the player to move
    if not moves:
        # does the opponent have any moves?
        if maximizing:
            opp_moves = get_legal_moves(opp_bb, you_bb)
        else:
            opp_moves = get_legal_moves(you_bb, opp_bb)

        if not opp_moves:                      # game over
            diff = you_bb.bit_count() - opp_bb.bit_count()
            return 10000 * diff                 # huge score for win/loss
        else:
            # pass – evaluate the position with the opponent to move
            return alphabeta(opp_bb, you_bb, depth, alpha, beta, not maximizing)

    if maximizing:
        value = -10**9
        # order moves using static evaluation of the resulting board
        move_evals = []
        for m in moves:
            flips = compute_flips(you_bb, opp_bb, m)
            new_you = you_bb | (1 << m) | flips
            new_opp = opp_bb & ~flips
            val = evaluate(new_you, new_opp)
            move_evals.append((val, m, flips))
        move_evals.sort(reverse=True, key=lambda x: x[0])

        for _, m, flips in move_evals:
            new_you = you_bb | (1 << m) | flips
            new_opp = opp_bb & ~flips
            score = alphabeta(new_you, new_opp,
                              depth - 1, alpha, beta, False)
            if score > value:
                value = score
            if value >= beta:
                break
            if value > alpha:
                alpha = value
        return value
    else:
        value = 10**9
        move_evals = []
        for m in moves:
            flips = compute_flips(opp_bb, you_bb, m)
            new_opp = opp_bb | (1 << m) | flips
            new_you = you_bb & ~flips
            # evaluate from opponent's perspective
            val = evaluate(new_opp, new_you)
            move_evals.append((val, m, flips))
        move_evals.sort(key=lambda x: x[0])   # ascending for minimiser

        for _, m, flips in move_evals:
            new_opp = opp_bb | (1 << m) | flips
            new_you = you_bb & ~flips
            score = alphabeta(new_you, new_opp,
                              depth - 1, alpha, beta, True)
            if score < value:
                value = score
            if value <= alpha:
                break
            if value < beta:
                beta = value
        return value


# ----------------------------------------------------------------------
# Main policy function
# ----------------------------------------------------------------------
def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Return the next Othello move for the player whose discs are `you`.
    `you` and `opponent` are 8×8 numpy arrays (0/1).
    """

    # Convert the numpy arrays into bit‑boards (player = you, opponent = opp)
    you_bb = 0
    opp_bb = 0
    for r in range(8):
        for c in range(8):
            if you[r, c]:
                you_bb |= 1 << (r * 8 + c)
            if opponent[r, c]:
                opp_bb |= 1 << (r * 8 + c)

    # Legal moves for the current player
    moves = get_legal_moves(you_bb, opp_bb)
    if not moves:
        return "pass"

    # Choose search depth – 5 ply is a good compromise strength / speed
    depth = 5

    # Root move ordering: evaluate each move's immediate static value
    move_evals = []
    for m in moves:
        flips = compute_flips(you_bb, opp_bb, m)
        new_you = you_bb | (1 << m) | flips
        new_opp = opp_bb & ~flips
        val = evaluate(new_you, new_opp)
        move_evals.append((val, m, flips))
    move_evals.sort(reverse=True, key=lambda x: x[0])

    best_move = None
    best_value = -10**9
    alpha = -10**9
    beta = 10**9

    for _, m, flips in move_evals:
        new_you = you_bb | (1 << m) | flips
        new_opp = opp_bb & ~flips
        value = alphabeta(new_you, new_opp,
                          depth - 1, alpha, beta, False)
        if value > best_value:
            best_value = value
            best_move = m
        if best_value > alpha:
            alpha = best_value

    # Convert best_move to algebraic notation (e.g., 27 -> 'd4')
    col = best_move % 8
    row = best_move // 8
    move_str = chr(ord('a') + col) + str(row + 1)
    return move_str
