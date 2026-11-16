
import math
import random

# --- Constants and Pre-computation for a 3x3x3 Board ---

N = 3
ME = 1
OPPONENT = -1
EMPTY = 0

# Pre-compute all winning lines to check for victory efficiently.
# There are 49 such lines on a 3x3x3 board.
WINNING_LINES = []

# 1. Lines fully within one of the 3 XY planes (9 rows + 9 columns + 6 diagonals = 24 lines)
for z in range(N):
    # Rows on this plane
    for y in range(N):
        WINNING_LINES.append([(z, y, x) for x in range(N)])
    # Columns on this plane
    for x in range(N):
        WINNING_LINES.append([(z, y, x) for y in range(N)])
    # Diagonals on this plane
    WINNING_LINES.append([(z, i, i) for i in range(N)])
    WINNING_LINES.append([(z, i, N - 1 - i) for i in range(N)])

# 2. Vertical columns through the layers (9 lines)
for y in range(N):
    for x in range(N):
        WINNING_LINES.append([(z, y, x) for z in range(N)])
        
# 3. Diagonals that are not confined to a single XY plane (6+6+4 = 16 lines)
# Diagonals on XZ planes
for y in range(N):
    WINNING_LINES.append([(i, y, i) for i in range(N)])
    WINNING_LINES.append([(i, y, N - 1 - i) for i in range(N)])
# Diagonals on YZ planes
for x in range(N):
    WINNING_LINES.append([(i, i, x) for i in range(N)])
    WINNING_LINES.append([(i, N - 1 - i, x) for i in range(N)])

# 4. The 4 main space diagonals
WINNING_LINES.append([(i, i, i) for i in range(N)])
WINNING_LINES.append([(i, i, N - 1 - i) for i in range(N)])
WINNING_LINES.append([(i, N - 1 - i, i) for i in range(N)])
WINNING_LINES.append([(N - 1 - i, i, i) for i in range(N)])

# Remove duplicates that arise from different generation methods
unique_lines = []
for line in WINNING_LINES:
    sorted_line = tuple(sorted(line))
    if sorted_line not in unique_lines:
        unique_lines.append(sorted_line)
WINNING_LINES = [[tuple(p) for p in line] for line in unique_lines]


# --- Helper Functions ---

def _get_empty_cells(board: list[list[list[int]]]) -> list[tuple[int, int, int]]:
    """Returns a list of all empty cells (z, y, x)."""
    empty_cells = []
    for z in range(N):
        for y in range(N):
            for x in range(N):
                if board[z][y][x] == EMPTY:
                    empty_cells.append((z, y, x))
    return empty_cells

def _check_winner(board: list[list[list[int]]]) -> None:
    """Checks for a winner (1 or -1), a draw (0), or if the game is ongoing (None)."""
    for line in WINNING_LINES:
        p1, p2, p3 = line
        s = board[p1[0]][p1[1]][p1[2]] + board[p2[0]][p2[1]][p2[2]] + board[p3[0]][p3[1]][p3[2]]
        if s == 3 * ME:
            return ME
        if s == 3 * OPPONENT:
            return OPPONENT
    
    if not any(EMPTY in row for layer in board for row in layer):
        return 0  # Draw
    
    return None  # Game is ongoing

def _evaluate_board(board: list[list[list[int]]]) -> int:
    """Heuristic evaluation of a non-terminal board state."""
    score = 0
    for line in WINNING_LINES:
        my_pieces = 0
        opp_pieces = 0
        for z, y, x in line:
            if board[z][y][x] == ME:
                my_pieces += 1
            elif board[z][y][x] == OPPONENT:
                opp_pieces += 1
        
        # Score lines that are not blocked by the opponent
        if my_pieces > 0 and opp_pieces == 0:
            # Score exponentially for more pieces in a line (1, 4, 9)
            score += my_pieces * my_pieces
        # Penalize for opponent's potential lines
        elif opp_pieces > 0 and my_pieces == 0:
            score -= opp_pieces * opp_pieces
            
    return score

def _minimax(board: list[list[list[int]]], depth: int, is_maximizing: bool, alpha: float, beta: float, max_depth: int) -> int:
    """Minimax algorithm with alpha-beta pruning."""
    winner = _check_winner(board)
    if winner is not None:
        if winner == ME:
            return 10000 - depth  # Prioritize faster wins
        elif winner == OPPONENT:
            return -10000 + depth # Prioritize delaying losses
        else: # Draw
            return 0

    if depth == max_depth:
        return _evaluate_board(board)

    empty_cells = _get_empty_cells(board)
    
    if is_maximizing:
        max_eval = -math.inf
        for z, y, x in empty_cells:
            board[z][y][x] = ME
            evaluation = _minimax(board, depth + 1, False, alpha, beta, max_depth)
            board[z][y][x] = EMPTY
            max_eval = max(max_eval, evaluation)
            alpha = max(alpha, evaluation)
            if beta <= alpha:
                break
        return max_eval
    else: # Minimizing
        min_eval = math.inf
        for z, y, x in empty_cells:
            board[z][y][x] = OPPONENT
            evaluation = _minimax(board, depth + 1, True, alpha, beta, max_depth)
            board[z][y][x] = EMPTY
            min_eval = min(min_eval, evaluation)
            beta = min(beta, evaluation)
            if beta <= alpha:
                break
        return min_eval

# --- Main Policy Function ---

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Determines the next best move for a 3x3x3 Tic Tac Toe game.
    """
    empty_cells = _get_empty_cells(board)
    num_empty = len(empty_cells)

    # Heuristic 1: On the first move, take the center.
    if num_empty == N * N * N:
        return (N // 2, N // 2, N // 2)

    # Heuristic 2: If we can win in one move, take it.
    for z, y, x in empty_cells:
        board[z][y][x] = ME
        if _check_winner(board) == ME:
            board[z][y][x] = EMPTY
            return (z, y, x)
        board[z][y][x] = EMPTY

    # Heuristic 3: If the opponent can win in one move, block them.
    for z, y, x in empty_cells:
        board[z][y][x] = OPPONENT
        if _check_winner(board) == OPPONENT:
            board[z][y][x] = EMPTY
            return (z, y, x)
        board[z][y][x] = EMPTY

    # Determine search depth based on game phase for performance.
    if num_empty > 20:   # Early game
        max_depth = 2
    elif num_empty > 12: # Mid game
        max_depth = 3
    else:                # Late game (can afford deeper search)
        max_depth = 5

    # Run Minimax to find the best strategic move
    best_score = -math.inf
    best_move = None
    
    # Shuffle moves to introduce variability in equally scored situations
    shuffled_moves = random.sample(empty_cells, len(empty_cells))

    for z, y, x in shuffled_moves:
        board[z][y][x] = ME
        # Call minimax for the opponent's turn (minimizing player)
        score = _minimax(board, 0, False, -math.inf, math.inf, max_depth)
        board[z][y][x] = EMPTY # Undo move
        
        if score > best_score:
            best_score = score
            best_move = (z, y, x)

    # Fallback: if no move was chosen (should not happen in a normal game)
    if best_move is None:
        return empty_cells[0]

    return best_move
