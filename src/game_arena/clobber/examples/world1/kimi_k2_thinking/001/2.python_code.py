
# Clobber policy for 5x6 board – minimax with alpha‑beta pruning.

# ----------------------------------------------------------------------
# Constants and helper functions
# ----------------------------------------------------------------------
ROWS = 5
COLS = 6
DIRECTIONS = {'U': (-1, 0), 'D': (1, 0), 'L': (0, -1), 'R': (0, 1)}
INF = 10 ** 9

def in_bounds(r, c):
    return 0 <= r < ROWS and 0 <= c < COLS

def copy_board(board):
    """Return a deep copy of a 2‑D list."""
    return [row[:] for row in board]

# ----------------------------------------------------------------------
# Move generation
# ----------------------------------------------------------------------
def legal_moves(you, opponent):
    """Return a list of all legal moves for the player that owns the 'you' board."""
    moves = []
    for r in range(ROWS):
        for c in range(COLS):
            if you[r][c] == 1:
                # Up
                if r > 0 and opponent[r - 1][c] == 1:
                    moves.append(f"{r},{c},U")
                # Down
                if r < ROWS - 1 and opponent[r + 1][c] == 1:
                    moves.append(f"{r},{c},D")
                # Left
                if c > 0 and opponent[r][c - 1] == 1:
                    moves.append(f"{r},{c},L")
                # Right
                if c < COLS - 1 and opponent[r][c + 1] == 1:
                    moves.append(f"{r},{c},R")
    return moves

def apply_move(you, opponent, move):
    """Apply a move for the player that owns the 'you' board and return the new boards."""
    r, c, d = move.split(',')
    r = int(r)
    c = int(c)
    dr, dc = DIRECTIONS[d]
    dest_r = r + dr
    dest_c = c + dc

    new_you = copy_board(you)
    new_opponent = copy_board(opponent)

    new_you[r][c] = 0
    new_you[dest_r][dest_c] = 1
    new_opponent[dest_r][dest_c] = 0

    return new_you, new_opponent

def apply_move_for_player(you, opponent, move, player):
    """Apply a move for the specified player ('you' or 'opponent')."""
    if player == 'you':
        return apply_move(you, opponent, move)
    else:
        # opponent moves – swap roles
        new_opponent, new_you = apply_move(opponent, you, move)
        return new_you, new_opponent

# ----------------------------------------------------------------------
# Heuristic evaluation
# ----------------------------------------------------------------------
def degree_of_piece(board, opponent_board, r, c):
    """Count how many adjacent squares contain an opponent piece."""
    count = 0
    if r > 0 and opponent_board[r - 1][c] == 1:
        count += 1
    if r < ROWS - 1 and opponent_board[r + 1][c] == 1:
        count += 1
    if c > 0 and opponent_board[r][c - 1] == 1:
        count += 1
    if c < COLS - 1 and opponent_board[r][c + 1] == 1:
        count += 1
    return count

def heuristic(you, opponent):
    """Evaluate a position from the perspective of the 'you' player."""
    # Piece count difference
    our_pieces = sum(cell for row in you for cell in row)
    opp_pieces = sum(cell for row in opponent for cell in row)
    piece_diff = our_pieces - opp_pieces

    # Mobility difference
    our_moves = len(legal_moves(you, opponent))
    opp_moves = len(legal_moves(opponent, you))
    mobility_diff = our_moves - opp_moves

    # Simple combined score (tuned empirically)
    return piece_diff + mobility_diff

# ----------------------------------------------------------------------
# Minimax with alpha‑beta
# ----------------------------------------------------------------------
def minimax(you, opponent, depth, alpha, beta, maximizing):
    """Return (best_score, best_move) for the current player."""
    if depth == 0:
        return heuristic(you, opponent), None

    if maximizing:
        moves = legal_moves(you, opponent)
        if not moves:
            return -INF, None  # losing position

        # Order moves by the heuristic value after the move (descending)
        scored = []
        for mv in moves:
            ny, no = apply_move(you, opponent, mv)
            scored.append((heuristic(ny, no), mv))
        scored.sort(key=lambda x: x[0], reverse=True)
        ordered_moves = [mv for _, mv in scored]

        best_score = -INF
        best_move = None
        for mv in ordered_moves:
            ny, no = apply_move(you, opponent, mv)
            score, _ = minimax(ny, no, depth - 1, alpha, beta, False)
            if score > best_score:
                best_score = score
                best_move = mv
            alpha = max(alpha, score)
            if beta <= alpha:
                break
        return best_score, best_move

    else:  # minimizing (opponent's turn)
        moves = legal_moves(opponent, you)
        if not moves:
            return INF, None  # opponent cannot move – we win

        # Order moves by heuristic after the move (ascending from our perspective)
        scored = []
        for mv in moves:
            # Apply opponent move, then evaluate from our side
            ny, no = apply_move_for_player(you, opponent, mv, 'opponent')
            scored.append((heuristic(ny, no), mv))
        scored.sort(key=lambda x: x[0])
        ordered_moves = [mv for _, mv in scored]

        best_score = INF
        best_move = None
        for mv in ordered_moves:
            ny, no = apply_move_for_player(you, opponent, mv, 'opponent')
            score, _ = minimax(ny, no, depth - 1, alpha, beta, True)
            if score < best_score:
                best_score = score
                best_move = mv
            beta = min(beta, score)
            if beta <= alpha:
                break
        return best_score, best_move

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def policy(you, opponent):
    """
    Return a legal move for the current player.
    `you` and `opponent` are 5×6 lists of 0/1 values.
    """
    moves = legal_moves(you, opponent)
    if not moves:
        # Should never be called when no moves exist, but keep legal.
        raise ValueError("No legal moves available")

    # Search depth 4 gives a good balance between strength and speed.
    _, best_move = minimax(you, opponent, depth=4, alpha=-INF, beta=INF, maximizing=True)

    # Fallback to the first move if the search fails to produce a move.
    if best_move is None:
        best_move = moves[0]

    return best_move
