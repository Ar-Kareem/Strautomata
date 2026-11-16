
import random
from copy import deepcopy

# ----------------------------------------------------------------------
# Global parameters
# ----------------------------------------------------------------------
MAX_DEPTH = 5          # search depth (ply)
ROLE_SCORE_WEIGHT = 10   # weight for material difference
POSITION_WEIGHT = 0.5    # weight for advanced pieces
MOBILITY_WEIGHT = 0.1    # weight for move count difference

# ----------------------------------------------------------------------
# State parsing
# ----------------------------------------------------------------------
def parse_state(state):
    """
    Convert the list of Stanford propositions into a usable representation.
    Returns:
        board   : dict {(r,c): 'red'|'black'|'blank'}
        scores  : dict {'red': int, 'black': int}
        step    : int
        control : str (the player to move)
    """
    board = {(r, c): 'blank' for r in range(1, 5) for c in range(1, 5)}
    scores = {'red': 0, 'black': 0}
    step = 0
    control = None

    for prop in state:
        if prop[0] == 'cell':
            r = int(prop[1])
            c = int(prop[2])
            colour = prop[3]
            board[(r, c)] = colour
        elif prop[0] == 'score':
            role = prop[1]
            scores[role] = int(prop[2])
        elif prop[0] == 'step':
            step = int(prop[1])
        elif prop[0] == 'control':
            control = prop[1]

    return board, scores, step, control

# ----------------------------------------------------------------------
# Move generation
# ----------------------------------------------------------------------
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]   # orthogonal directions

def generate_moves(board, role):
    """
    Return a list of possible moves for `role`.
    Each move is a tuple:
        ('move', (r1,c1,r2,c2))               – simple move
        ('jump', (r1,c1,rm,cm,r2,c2))         – jump (capture)
    """
    opponent = 'black' if role == 'red' else 'red'
    moves = []

    for (r, c), colour in board.items():
        if colour != role:
            continue

        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if not (1 <= nr <= 4 and 1 <= nc <= 4):
                continue

            if board[(nr, nc)] == 'blank':
                # simple step
                moves.append(('move', (r, c, nr, nc)))
            elif board[(nr, nc)] == role:
                # possible jump over own piece
                jr, jc = nr + dr, nc + dc
                if not (1 <= jr <= 4 and 1 <= jc <= 4):
                    continue
                if board[(jr, jc)] == opponent:
                    moves.append(('jump', (r, c, nr, nc, jr, jc)))

    return moves

def apply_move(board, move, role):
    """Return a new board after performing `move`."""
    new_board = dict(board)

    if move[0] == 'move':
        r1, c1, r2, c2 = move[1]
        new_board[(r1, c1)] = 'blank'
        new_board[(r2, c2)] = role
    else:  # jump
        r1, c1, rm, cm, r2, c2 = move[1]
        # start becomes empty
        new_board[(r1, c1)] = 'blank'
        # landing square takes the moving piece (capture)
        new_board[(r2, c2)] = role
        # middle piece stays unchanged

    return new_board

# ----------------------------------------------------------------------
# Evaluation heuristic
# ----------------------------------------------------------------------
def evaluate(board, role):
    """
    Simple evaluation for `role`.  Positive values favour `role`.
    """
    opponent = 'black' if role == 'red' else 'red'

    # material
    my_pieces = sum(1 for v in board.values() if v == role)
    opp_pieces = sum(1 for v in board.values() if v == opponent)
    material = ROLE_SCORE_WEIGHT * (my_pieces - opp_pieces)

    # positional advantage: pieces on opponent's home rows
    if role == 'red':
        # opponent rows are 1 and 2
        my_adv = sum(POSITION_WEIGHT for r in range(1, 3) for c in range(1, 5) if board[(r, c)] == role)
        # opponent pieces on our side (rows 3,4) are slightly bad for us
        opp_adv = sum(POSITION_WEIGHT for r in range(3, 5) for c in range(1, 5) if board[(r, c)] == opponent)
    else:
        # opponent rows are 3 and 4
        my_adv = sum(POSITION_WEIGHT for r in range(3, 5) for c in range(1, 5) if board[(r, c)] == role)
        opp_adv = sum(POSITION_WEIGHT for r in range(1, 3) for c in range(1, 5) if board[(r, c)] == opponent)

    # mobility
    my_moves = len(generate_moves(board, role))
    opp_moves = len(generate_moves(board, opponent))
    mobility = MOBILITY_WEIGHT * (my_moves - opp_moves)

    return material + (my_adv - opp_adv) + mobility

# ----------------------------------------------------------------------
# Minimax with α‑β pruning
# ----------------------------------------------------------------------
def minimax(board, step, depth, alpha, beta, maximizing, role):
    """
    Recursive α‑β search.
    `role` is the player we are ultimately trying to maximise for.
    `maximizing` indicates whether the current node is for `role` (True) or opponent (False).
    """
    opponent = 'black' if role == 'red' else 'red'

    # Terminal conditions
    if depth == 0 or step >= 30:
        return evaluate(board, role)

    current = role if maximizing else opponent
    moves = generate_moves(board, current)

    # If no legal moves, we treat it as a pass (the turn simply changes)
    if not moves:
        # board unchanged, step increases, player switches
        return minimax(board, step + 1, depth - 1, alpha, beta, not maximizing, role)

    # Order moves: captures first (jump > move) to improve pruning
    moves_sorted = sorted(moves, key=lambda m: 0 if m[0] == 'jump' else 1)

    if maximizing:
        value = -float('inf')
        for move in moves_sorted:
            new_board = apply_move(board, move, current)
            value = max(value,
                        minimax(new_board, step + 1, depth - 1, alpha, beta, False, role))
            if value > alpha:
                alpha = value
            if beta <= alpha:
                break
        return value
    else:
        value = float('inf')
        for move in moves_sorted:
            new_board = apply_move(board, move, current)
            value = min(value,
                        minimax(new_board, step + 1, depth - 1, alpha, beta, True, role))
            if value < beta:
                beta = value
            if beta <= alpha:
                break
        return value

# ----------------------------------------------------------------------
# Main policy entry point
# ----------------------------------------------------------------------
def policy(state, role):
    """
    Called by the game master.  Returns a legal move string for `role`.
    """
    board, _, step, _ = parse_state(state)

    # All legal moves for the player
    moves = generate_moves(board, role)

    # If no moves, we must pass
    if not moves:
        return "kerchunk"

    # Depth‑limited α‑β search
    best_value = -float('inf')
    best_moves = []

    # Order moves: captures first
    ordered = sorted(moves, key=lambda m: 0 if m[0] == 'jump' else 1)

    for move in ordered:
        new_board = apply_move(board, move, role)
        val = minimax(new_board, step + 1, MAX_DEPTH - 1,
                       -float('inf'), float('inf'), False, role)
        if val > best_value:
            best_value = val
            best_moves = [move]
        elif val == best_value:
            best_moves.append(move)

    # Pick uniformly at random among the best moves
    chosen = random.choice(best_moves)

    # Format the move string
    if chosen[0] == 'move':
        r1, c1, r2, c2 = chosen[1]
        return f"move({r1},{c1},{r2},{c2})"
    else:  # jump
        r1, c1, rm, cm, r2, c2 = chosen[1]
        return f"jump({r1},{c1},{rm},{cm},{r2},{c2})"
