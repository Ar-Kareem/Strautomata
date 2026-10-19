
import sys
sys.setrecursionlimit(10000)

# Directions: up, right, down, left
DIRS = [(-1, 0), (0, 1), (1, 0), (0, -1)]
DIRCHAR = ['U', 'R', 'D', 'L']

# ------------------------------------------------------------
# Convert the board (given as list of lists or flat list) to bit‑boards
def board_to_masks(you, opponent):
    you_mask = 0
    opp_mask = 0
    # flat list of length 30 ?
    if len(you) == 30:
        for i, v in enumerate(you):
            if v == 1:
                you_mask |= 1 << i
        for i, v in enumerate(opponent):
            if v == 1:
                opp_mask |= 1 << i
    else:
        # 2‑D list / numpy array
        for r in range(5):
            for c in range(6):
                if you[r][c] == 1:
                    you_mask |= 1 << (r * 6 + c)
                if opponent[r][c] == 1:
                    opp_mask |= 1 << (r * 6 + c)
    return you_mask, opp_mask

# ------------------------------------------------------------
# Generate all legal captures for the player described by my_mask
def generate_moves(my_mask, opp_mask):
    moves = []
    m = my_mask
    while m:
        low = m & -m                     # isolate lowest set bit
        idx = low.bit_length() - 1       # its index 0‑29
        row, col = divmod(idx, 6)
        for dr, dc in DIRS:
            nr, nc = row + dr, col + dc
            if 0 <= nr < 5 and 0 <= nc < 6:
                nidx = nr * 6 + nc
                if (opp_mask >> nidx) & 1:
                    moves.append((idx, nidx))
        m &= m - 1                        # clear lowest bit
    return moves

# ------------------------------------------------------------
# Apply a move (start->dest) for the side described by my_mask
def apply_move(my_mask, opp_mask, move):
    start, dest = move
    new_my = my_mask
    new_my &= ~(1 << start)      # leave the start square
    new_my |= (1 << dest)        # occupy the destination
    new_opp = opp_mask & ~(1 << dest)   # remove captured piece
    return new_my, new_opp

# Apply a move for the opponent (the same function, swapped roles)
def apply_move_opp(opp_mask, my_mask, move):
    start, dest = move
    new_opp = opp_mask
    new_opp &= ~(1 << start)
    new_opp |= (1 << dest)
    new_my = my_mask & ~(1 << dest)
    return new_opp, new_my

# ------------------------------------------------------------
def piece_count(mask):
    return mask.bit_count()

def mobility(my_mask, opp_mask):
    return len(generate_moves(my_mask, opp_mask))

# Static evaluation of a board from the perspective of "you"
def evaluate(you_mask, opp_mask):
    # Immediate win / loss
    if mobility(opp_mask, you_mask) == 0:          # opponent cannot move
        return 10000 + (piece_count(you_mask) - piece_count(opp_mask))
    if mobility(you_mask, opp_mask) == 0:          # we cannot move
        return -10000 - (piece_count(opp_mask) - piece_count(you_mask))

    piece_diff = piece_count(you_mask) - piece_count(opp_mask)
    move_diff = mobility(you_mask, opp_mask) - mobility(opp_mask, you_mask)
    return piece_diff * 100 + move_diff

# ------------------------------------------------------------
# Minimax with alpha‑beta pruning
def minimax(you_mask, opp_mask, depth, alpha, beta, is_your_turn):
    if depth == 0:
        return evaluate(you_mask, opp_mask)

    if is_your_turn:
        moves = generate_moves(you_mask, opp_mask)
        if not moves:
            return -10000                     # loss
        best = -10**9
        for move in moves:
            new_you, new_opp = apply_move(you_mask, opp_mask, move)
            score = minimax(new_you, new_opp, depth-1, alpha, beta, False)
            if score > best:
                best = score
            if best > alpha:
                alpha = best
            if beta <= alpha:
                break
        return best
    else:
        moves = generate_moves(opp_mask, you_mask)
        if not moves:
            return 10000                       # win for us
        best = 10**9
        for move in moves:
            new_opp, new_you = apply_move_opp(opp_mask, you_mask, move)
            score = minimax(new_you, new_opp, depth-1, alpha, beta, True)
            if score < best:
                best = score
            if best < beta:
                beta = best
            if beta <= alpha:
                break
        return best

# ------------------------------------------------------------
# Choose the best move for the current position
def choose_move(you_mask, opp_mask, depth):
    moves = generate_moves(you_mask, opp_mask)
    if not moves:
        return None

    # 1) Immediate winning move?
    for move in moves:
        new_you, new_opp = apply_move(you_mask, opp_mask, move)
        if mobility(new_opp, new_you) == 0:   # opponent has no moves left
            return move

    # 2) Order moves by static evaluation for better pruning
    move_evals = []
    for move in moves:
        new_you, new_opp = apply_move(you_mask, opp_mask, move)
        ev = evaluate(new_you, new_opp)
        move_evals.append((ev, move))
    move_evals.sort(key=lambda x: x[0], reverse=True)

    best_move = None
    best_score = -10**9
    alpha = -10**9
    beta = 10**9

    for ev, move in move_evals:
        new_you, new_opp = apply_move(you_mask, opp_mask, move)
        score = minimax(new_you, new_opp, depth-1, alpha, beta, False)
        if score > best_score:
            best_score = score
            best_move = move
            if best_score > alpha:
                alpha = best_score
    return best_move

# ------------------------------------------------------------
def move_to_string(move):
    start, dest = move
    row, col = divmod(start, 6)
    delta = dest - start
    if delta == -6:
        dirc = 'U'
    elif delta == 1:
        dirc = 'R'
    elif delta == 6:
        dirc = 'D'
    elif delta == -1:
        dirc = 'L'
    else:
        dirc = '?'          # should never happen
    return f"{row},{col},{dirc}"

# ------------------------------------------------------------
def policy(you, opponent):
    """
    Main entry point required by the arena.
    you, opponent – 5x6 (or flat 30) arrays of 0/1.
    Returns a legal move in the format 'row,col,dir'.
    """
    you_mask, opp_mask = board_to_masks(you, opponent)
    # Depth 4 gives a strong player while staying well inside the time limit.
    depth = 4
    move = choose_move(you_mask, opp_mask, depth)
    if move is None:
        # Should not happen if we have a legal move.
        return ""
    return move_to_string(move)
