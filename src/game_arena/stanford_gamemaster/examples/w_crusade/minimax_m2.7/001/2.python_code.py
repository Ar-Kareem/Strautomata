
import random

# Knight move offsets
KNIGHT_MOVES = [(2, 1), (1, 2), (-1, 2), (-2, 1),
                (-2, -1), (-1, -2), (1, -2), (2, -1)]

# Coordinate helpers
def file_to_idx(f):
    return ord(f) - ord('a')

def idx_to_file(i):
    return chr(ord('a') + i)

def rank_to_idx(r):
    return int(r) - 1

def idx_to_rank(i):
    return str(i + 1)

# ----------------------------------------------------------------------
# State parsing
# ----------------------------------------------------------------------
def parse_state(state):
    """Convert the list of facts into a usable board dictionary."""
    board = {}               # (file, rank) -> color
    control = None
    step = 0
    capture_counts = {}
    for fact in state:
        if not fact:
            continue
        if fact[0] == 'cell':
            file, rank, color = fact[1], fact[2], fact[3]
            board[(file, rank)] = color
        elif fact[0] == 'control':
            control = fact[1]
        elif fact[0] == 'step':
            step = int(fact[1])
        elif fact[0] == 'capturecount':
            color = fact[1]
            capture_counts[color] = int(fact[2])
    return board, control, step, capture_counts

# ----------------------------------------------------------------------
# Move generation
# ----------------------------------------------------------------------
def generate_moves(board, color):
    """All legal knight moves for `color` given the current board."""
    moves = []
    for (f, r), col in board.items():
        if col != color:
            continue
        x = file_to_idx(f)
        y = rank_to_idx(r)
        for dx, dy in KNIGHT_MOVES:
            nx, ny = x + dx, y + dy
            if 0 <= nx < 8 and 0 <= ny < 8:
                nf = idx_to_file(nx)
                nr = idx_to_rank(ny)
                dest = (nf, nr)
                dest_col = board.get(dest)
                # Can move onto empty square or opponent piece (capture)
                if dest_col is None or dest_col != color:
                    moves.append(((f, r), dest))
    return moves

# ----------------------------------------------------------------------
# Board simulation
# ----------------------------------------------------------------------
def simulate_move(board, src, dst):
    """Return a new board after the move and the captured piece (if any)."""
    new_board = dict(board)
    captured = new_board.pop(dst, None)   # None if destination was empty
    new_board[dst] = new_board[src]       # move the piece
    del new_board[src]
    return new_board, captured

# ----------------------------------------------------------------------
# Move evaluation
# ----------------------------------------------------------------------
def evaluate_move(board, move, color):
    """Score a move; higher is better."""
    src, dst = move
    new_board, captured = simulate_move(board, src, dst)

    # Immediate gain: capturing an opponent piece
    immediate_gain = 1 if captured else 0

    opponent = 'black' if color == 'white' else 'white'

    # Future capture potential: opponent pieces reachable from the destination
    x, y = file_to_idx(dst[0]), rank_to_idx(dst[1])
    future_captures = 0
    for dx, dy in KNIGHT_MOVES:
        nx, ny = x + dx, y + dy
        if 0 <= nx < 8 and 0 <= ny < 8:
            nf = idx_to_file(nx)
            nr = idx_to_rank(ny)
            if new_board.get((nf, nr)) == opponent:
                future_captures += 1

    # Danger: can any opponent knight capture our piece on the destination?
    danger = 0
    for (f, r), col in new_board.items():
        if col != opponent:
            continue
        ox, oy = file_to_idx(f), rank_to_idx(r)
        for dx, dy in KNIGHT_MOVES:
            nx, ny = ox + dx, oy + dy
            if 0 <= nx < 8 and 0 <= ny < 8:
                nf = idx_to_file(nx)
                nr = idx_to_rank(ny)
                if (nf, nr) == dst:
                    danger += 1
                    break   # count each threatening opponent only once

    # Combine components
    score = immediate_gain * 1000 + future_captures * 10 - danger * 5
    return score

# ----------------------------------------------------------------------
# Main policy entry point
# ----------------------------------------------------------------------
def policy(state, role):
    """
    Return a legal move for `role` in the current `state`.
    The move is chosen by a greedy heuristic that prioritises captures,
    then future capture opportunities, while trying to avoid dangerous squares.
    """
    board, control, step, _ = parse_state(state)

    # Generate all legal moves for the requested role
    moves = generate_moves(board, role)
    if not moves:                     # Should never happen in a real game
        return "move(a,1,b,3)"

    # Score each move
    scored_moves = [(evaluate_move(board, m, role), m) for m in moves]

    # Randomise tie‑breaks
    random.shuffle(scored_moves)
    # Sort descending by score
    scored_moves.sort(key=lambda x: x[0], reverse=True)

    best_score, best_move = scored_moves[0]
    src, dst = best_move
    return f"move({src[0]},{src[1]},{dst[0]},{dst[1]})"
