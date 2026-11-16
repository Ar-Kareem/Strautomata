
import random
import math

# Constants representing the board
EMPTY = 0
ME = 1
OPPONENT = -1
SIZE = 4
WIN_LENGTH = 4

# Precompute all possible lines (rows, columns, diagonals) for efficient evaluation
LINES = []
# Rows
for r in range(SIZE):
    LINES.append([(r, c) for c in range(SIZE)])
# Columns
for c in range(SIZE):
    LINES.append([(r, c) for r in range(SIZE)])
# Diagonals
LINES.append([(i, i) for i in range(SIZE)])
LINES.append([(i, SIZE - 1 - i) for i in range(SIZE)])

# Static move ordering: Center > Corners > Edges
# This improves Alpha-Beta pruning efficiency
CENTER_MOVES = [(1, 1), (1, 2), (2, 1), (2, 2)]
CORNER_MOVES = [(0, 0), (0, 3), (3, 0), (3, 3)]
EDGE_MOVES = [
    (0, 1), (0, 2),
    (1, 0), (1, 3),
    (2, 0), (2, 3),
    (3, 1), (3, 2)
]
ORDERED_MOVES = CENTER_MOVES + CORNER_MOVES + EDGE_MOVES

def get_valid_moves(board):
    """Returns a list of valid moves (r, c) ordered by strategic importance."""
    valid = []
    # Check moves in the precomputed strategic order
    for r, c in ORDERED_MOVES:
        if board[r][c] == EMPTY:
            valid.append((r, c))
    
    # If the precomputed list didn't cover everything (shouldn't happen for 4x4), 
    # fallback to scanning (though for 4x4 the ordered list covers all 16 cells).
    if not valid:
        for r in range(SIZE):
            for c in range(SIZE):
                if board[r][c] == EMPTY:
                    valid.append((r, c))
    return valid

def check_win(board, player):
    """Checks if the given player has formed a line of WIN_LENGTH."""
    for line in LINES:
        if all(board[r][c] == player for r, c in line):
            return True
    return False

def evaluate_board(board):
    """
    Heuristic evaluation of the board state.
    Returns a score positive for ME, negative for OPPONENT.
    """
    score = 0
    
    # Weights for having N pieces in a line
    weights = {0: 0, 1: 1, 2: 10, 3: 100, 4: 10000}
    
    for line in LINES:
        count_me = 0
        count_opp = 0
        empty_exists = False
        
        for r, c in line:
            cell = board[r][c]
            if cell == ME:
                count_me += 1
            elif cell == OPPONENT:
                count_opp += 1
            else:
                empty_exists = True
        
        # If the line is mixed (blocked by both), it contributes nothing
        if count_me > 0 and count_opp > 0:
            continue
            
        # If the line is pure (or empty), score it
        if count_me > 0:
            score += weights[count_me]
        elif count_opp > 0:
            score -= weights[count_opp]
            
    return score

def minimax(board, depth, alpha, beta, maximizing_player):
    """
    Minimax algorithm with Alpha-Beta pruning.
    """
    # Terminal states
    if check_win(board, ME):
        return 100000 + depth  # Prefer winning sooner
    if check_win(board, OPPONENT):
        return -100000 - depth # Prefer losing later
    valid_moves = get_valid_moves(board)
    if not valid_moves:
        return 0 # Draw

    # Depth limit cutoff
    if depth == 0:
        return evaluate_board(board)

    if maximizing_player:
        max_eval = -math.inf
        for r, c in valid_moves:
            board[r][c] = ME
            eval_score = minimax(board, depth - 1, alpha, beta, False)
            board[r][c] = EMPTY # Undo move
            
            if eval_score > max_eval:
                max_eval = eval_score
            
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break # Beta cutoff
        return max_eval
    else:
        min_eval = math.inf
        for r, c in valid_moves:
            board[r][c] = OPPONENT
            eval_score = minimax(board, depth - 1, alpha, beta, True)
            board[r][c] = EMPTY # Undo move
            
            if eval_score < min_eval:
                min_eval = eval_score
                
            beta = min(beta, eval_score)
            if beta <= alpha:
                break # Alpha cutoff
        return min_eval

def policy(board):
    """
    Main policy function. Returns the next move as a tuple (row, col).
    """
    valid_moves = get_valid_moves(board)
    if not valid_moves:
        # Should not happen in a running game, but safety check
        return (0, 0)

    # 1. Check for immediate win
    for r, c in valid_moves:
        board[r][c] = ME
        if check_win(board, ME):
            board[r][c] = EMPTY
            return (r, c)
        board[r][c] = EMPTY

    # 2. Check for immediate block (opponent about to win)
    for r, c in valid_moves:
        board[r][c] = OPPONENT
        if check_win(board, OPPONENT):
            board[r][c] = EMPTY
            return (r, c)
        board[r][c] = EMPTY

    # 3. Run Minimax search
    # Dynamic depth: increase depth if board is sparsely populated to ensure speed,
    # but if few moves are left, increase depth to solve endgame.
    empty_count = len(valid_moves)
    
    if empty_count > 12:
        search_depth = 4
    elif empty_count > 8:
        search_depth = 5
    else:
        # Solve endgame
        search_depth = 10 

    best_score = -math.inf
    best_move = None
    
    # Shuffle moves slightly at the start to add variety if scores are equal,
    # but prioritize our strategic order.
    # We stick to the strategic order primarily.
    
    alpha = -math.inf
    beta = math.inf

    for r, c in valid_moves:
        board[r][c] = ME
        score = minimax(board, search_depth - 1, alpha, beta, False)
        board[r][c] = EMPTY
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
        
        alpha = max(alpha, score)
        # Optional: if alpha is extremely high (win found), break early
        if score > 50000:
            break

    if best_move is not None:
        return best_move
    
    # Fallback (should not be reached)
    return valid_moves[0]
