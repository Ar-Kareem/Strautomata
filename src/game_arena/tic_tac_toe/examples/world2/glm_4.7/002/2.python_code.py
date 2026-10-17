
import math
from functools import lru_cache

# Define winning lines for a 4x4 board (4 rows, 4 cols, 2 diags)
LINES = []
# Rows
LINES += [[(r, c) for c in range(4)] for r in range(4)]
# Cols
LINES += [[(r, c) for r in range(4)] for c in range(4)]
# Diagonals
LINES.append([(i, i) for i in range(4)])
LINES.append([(i, 3 - i) for i in range(4)])

# Precompute move priorities: Center > Corners > Edges
# Center: (1,1), (1,2), (2,1), (2,2)
# Corners: (0,0), (0,3), (3,0), (3,3)
# Edges: Everything else
MOVE_PRIORITY = {
    (1, 1): 3, (1, 2): 3, (2, 1): 3, (2, 2): 3, # Center
    (0, 0): 2, (0, 3): 2, (3, 0): 2, (3, 3): 2, # Corners
    (0, 1): 1, (0, 2): 1, (1, 0): 1, (1, 3): 1,
    (2, 0): 1, (2, 3): 1, (3, 1): 1, (3, 2): 1  # Edges
}

def check_win(board_tuple, player):
    """Check if the given player has won."""
    for line in LINES:
        if all(board_tuple[r][c] == player for r, c in line):
            return True
    return False

def evaluate(board_tuple):
    """
    Heuristic evaluation of the board.
    Returns a score where positive is good for Player 1, negative for Player -1.
    """
    score = 0
    # Check lines
    for line in LINES:
        p1_count = 0
        p2_count = 0
        empty_count = 0
        
        for r, c in line:
            val = board_tuple[r][c]
            if val == 1:
                p1_count += 1
            elif val == -1:
                p2_count += 1
            else:
                empty_count += 1
        
        # Evaluate Player 1 (AI) potential
        if p1_count > 0 and p2_count == 0:
            score += 10 ** p1_count # 1->10, 2->100, 3->1000
        
        # Evaluate Player -1 (Opponent) potential (negative for AI)
        if p2_count > 0 and p1_count == 0:
            score -= 10 ** p2_count

    return score

@lru_cache(maxsize=None)
def minimax(board_tuple, depth, alpha, beta, maximizing_player):
    """
    Minimax algorithm with Alpha-Beta pruning.
    """
    # Check terminal states
    if check_win(board_tuple, 1):
        return 100000 + depth # Prefer winning sooner
    if check_win(board_tuple, -1):
        return -100000 - depth # Prefer losing later
    
    # Flatten to count empty cells efficiently
    # Since board_tuple is a tuple of tuples, we iterate to find 0s
    empty_spots = 0
    for r in range(4):
        for c in range(4):
            if board_tuple[r][c] == 0:
                empty_spots += 1
                
    if empty_spots == 0:
        return 0 # Draw

    if depth == 0:
        return evaluate(board_tuple)

    if maximizing_player:
        max_eval = -math.inf
        # Generate moves sorted by priority to improve pruning
        moves = []
        for r in range(4):
            for c in range(4):
                if board_tuple[r][c] == 0:
                    moves.append((r, c))
        
        # Sort moves: Center -> Corner -> Edge
        moves.sort(key=lambda m: MOVE_PRIORITY.get(m, 0), reverse=True)

        for r, c in moves:
            # Make move
            new_board_list = [list(row) for row in board_tuple]
            new_board_list[r][c] = 1
            new_board = tuple(tuple(row) for row in new_board_list)
            
            eval_score = minimax(new_board, depth - 1, alpha, beta, False)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = math.inf
        moves = []
        for r in range(4):
            for c in range(4):
                if board_tuple[r][c] == 0:
                    moves.append((r, c))
        
        # Sort moves
        moves.sort(key=lambda m: MOVE_PRIORITY.get(m, 0), reverse=True)

        for r, c in moves:
            # Make move
            new_board_list = [list(row) for row in board_tuple]
            new_board_list[r][c] = -1
            new_board = tuple(tuple(row) for row in new_board_list)
            
            eval_score = minimax(new_board, depth - 1, alpha, beta, True)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Returns the best move for the AI (Player 1).
    """
    board_tuple = tuple(tuple(row) for row in board)
    
    # Dynamic depth calculation
    # Count empty squares
    empty_count = sum(1 for r in range(4) for c in range(4) if board[r][c] == 0)
    
    if empty_count > 12:
        depth_limit = 3
    elif empty_count > 8:
        depth_limit = 4
    elif empty_count > 5:
        depth_limit = 5
    else:
        depth_limit = 10 # Deep search in endgame

    best_move = None
    best_val = -math.inf
    
    # Generate moves and sort by priority
    moves = []
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                moves.append((r, c))
    
    if not moves:
        return (0, 0) # Should not happen if game isn't drawn

    moves.sort(key=lambda m: MOVE_PRIORITY.get(m, 0), reverse=True)

    alpha = -math.inf
    beta = math.inf
    
    # First level of search (Policy loop)
    for r, c in moves:
        # Create new board state
        new_board_list = [list(row) for row in board_tuple]
        new_board_list[r][c] = 1
        new_board = tuple(tuple(row) for row in new_board_list)
        
        val = minimax(new_board, depth_limit - 1, alpha, beta, False)
        
        if val > best_val:
            best_val = val
            best_move = (r, c)
        
        alpha = max(alpha, val)

    return best_move
