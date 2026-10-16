
import math

# Precompute all winning lines for a 4x4 board: rows, columns, and two diagonals.
LINES = []
# Rows
for r in range(4):
    LINES.append([(r, c) for c in range(4)])
# Columns
for c in range(4):
    LINES.append([(r, c) for r in range(4)])
# Main diagonal
LINES.append([(i, i) for i in range(4)])
# Anti-diagonal
LINES.append([(i, 3 - i) for i in range(4)])

def get_empty_cells(board):
    """Return list of (row, col) for empty cells."""
    empty = []
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                empty.append((r, c))
    return empty

def check_winner(board):
    """Return 1 if we win, -1 if opponent wins, 0 otherwise."""
    for line in LINES:
        values = [board[r][c] for (r, c) in line]
        if all(v == 1 for v in values):
            return 1
        if all(v == -1 for v in values):
            return -1
    return 0

def is_terminal(board):
    """Return True if the game is over."""
    if check_winner(board) != 0:
        return True
    if not get_empty_cells(board):
        return True
    return False

def evaluate(board):
    """Heuristic evaluation of the board."""
    score = 0
    # Evaluate lines
    for line in LINES:
        our = 0
        opp = 0
        for (r, c) in line:
            if board[r][c] == 1:
                our += 1
            elif board[r][c] == -1:
                opp += 1
        if our > 0 and opp == 0:
            # Only our pieces in this line
            if our == 3:
                score += 10000
            elif our == 2:
                score += 100
            elif our == 1:
                score += 1
        elif opp > 0 and our == 0:
            # Only opponent pieces
            if opp == 3:
                score -= 10000
            elif opp == 2:
                score -= 100
            elif opp == 1:
                score -= 1
        # If both have pieces, line is blocked, no score.

    # Center bonus (the four central squares)
    center = [(1, 1), (1, 2), (2, 1), (2, 2)]
    for (r, c) in center:
        if board[r][c] == 1:
            score += 2
        elif board[r][c] == -1:
            score -= 2

    # Corner bonus
    corners = [(0, 0), (0, 3), (3, 0), (3, 3)]
    for (r, c) in corners:
        if board[r][c] == 1:
            score += 1
        elif board[r][c] == -1:
            score -= 1

    return score

def minimax(board, depth, alpha, beta, maximizing):
    """Minimax with alpha-beta pruning."""
    if depth == 0 or is_terminal(board):
        # Terminal state evaluation
        winner = check_winner(board)
        if winner == 1:
            return 100000 - depth  # Prefer faster wins
        elif winner == -1:
            return -100000 + depth  # Prefer slower losses
        elif not get_empty_cells(board):
            return 0  # Draw
        else:
            return evaluate(board)

    empty_cells = get_empty_cells(board)
    if maximizing:
        # Our turn (maximizing player)
        value = -math.inf
        for (r, c) in empty_cells:
            board[r][c] = 1
            value = max(value, minimax(board, depth - 1, alpha, beta, False))
            board[r][c] = 0
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    else:
        # Opponent's turn (minimizing player)
        value = math.inf
        for (r, c) in empty_cells:
            board[r][c] = -1
            value = min(value, minimax(board, depth - 1, alpha, beta, True))
            board[r][c] = 0
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value

def policy(board):
    """Return the best move (row, col) for the current board."""
    # First, check if there is an immediate winning move for us.
    empty_cells = get_empty_cells(board)
    for (r, c) in empty_cells:
        board[r][c] = 1
        if check_winner(board) == 1:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    # Second, check if opponent has an immediate winning move and block it.
    for (r, c) in empty_cells:
        board[r][c] = -1
        if check_winner(board) == -1:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    # Determine search depth based on number of empty cells.
    empty_count = len(empty_cells)
    if empty_count <= 6:
        depth = empty_count
    else:
        depth = 5  # Reasonable depth for speed

    # Use minimax to find the best move.
    best_move = None
    best_value = -math.inf
    for (r, c) in empty_cells:
        board[r][c] = 1
        move_value = minimax(board, depth - 1, -math.inf, math.inf, False)
        board[r][c] = 0
        if move_value > best_value:
            best_value = move_value
            best_move = (r, c)

    # Fallback: if no move chosen (should not happen), return first empty cell.
    if best_move is None and empty_cells:
        best_move = empty_cells[0]
    return best_move
