
import math
from functools import lru_cache

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Determines the next move for the 4x4 Tic Tac Toe game.
    Player 1 is the AI, Player -1 is the opponent.
    """
    
    # Helper to check win on a list of lists (used for fast immediate checks)
    def check_win_list(b, player):
        # Rows
        for r in range(4):
            if all(cell == player for cell in b[r]):
                return True
        # Cols
        for c in range(4):
            if all(b[r][c] == player for r in range(4)):
                return True
        # Diagonals
        if all(b[i][i] == player for i in range(4)):
            return True
        if all(b[i][3-i] == player for i in range(4)):
            return True
        return False

    # 1. Check for immediate win
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                board[r][c] = 1
                if check_win_list(board, 1):
                    board[r][c] = 0
                    return (r, c)
                board[r][c] = 0

    # 2. Check for immediate block (opponent about to win)
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                board[r][c] = -1
                if check_win_list(board, -1):
                    board[r][c] = 0
                    return (r, c)
                board[r][c] = 0

    # 3. Minimax with Alpha-Beta Pruning
    # Convert board to tuple for hashing (caching)
    board_tuple = tuple(tuple(row) for row in board)
    
    DEPTH_LIMIT = 6
    best_score = -math.inf
    best_move = None
    
    # Get valid moves
    valid_moves = [(r, c) for r in range(4) for c in range(4) if board[r][c] == 0]
    
    # Move ordering to improve pruning: Center > Corners > Edges
    def sort_key(move):
        r, c = move
        if 1 <= r <= 2 and 1 <= c <= 2: return 0
        if (r == 0 or r == 3) and (c == 0 or c == 3): return 1
        return 2
    
    valid_moves.sort(key=sort_key)
    
    for r, c in valid_moves:
        # Create new state for recursion
        new_board = [list(row) for row in board]
        new_board[r][c] = 1
        new_board_tuple = tuple(tuple(row) for row in new_board)
        
        # Depth DEPTH_LIMIT - 1 because we made one move
        score = minimax(new_board_tuple, DEPTH_LIMIT - 1, -math.inf, math.inf, False)
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
            
    return best_move

@lru_cache(maxsize=None)
def minimax(board_tuple, depth, alpha, beta, is_maximizing):
    """
    Recursive minimax with alpha-beta pruning.
    board_tuple is a tuple of tuples representing the 4x4 grid.
    """
    
    # Terminal State Checks
    # Check Win for Player 1 (AI)
    if check_win_tuple(board_tuple, 1):
        return 100000
    # Check Win for Player -1 (Opponent)
    if check_win_tuple(board_tuple, -1):
        return -100000
        
    # Check Draw or Depth Limit
    if depth == 0:
        return evaluate(board_tuple)
        
    # Check if board is full (Draw)
    is_full = True
    for r in range(4):
        for c in range(4):
            if board_tuple[r][c] == 0:
                is_full = False
                break
        if not is_full: break
    
    if is_full:
        return 0

    if is_maximizing:
        max_eval = -math.inf
        for r in range(4):
            for c in range(4):
                if board_tuple[r][c] == 0:
                    # Make move for Player 1
                    new_board = [list(row) for row in board_tuple]
                    new_board[r][c] = 1
                    new_board_tuple = tuple(tuple(row) for row in new_board)
                    
                    eval_score = minimax(new_board_tuple, depth - 1, alpha, beta, False)
                    max_eval = max(max_eval, eval_score)
                    alpha = max(alpha, eval_score)
                    if beta <= alpha:
                        break
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = math.inf
        for r in range(4):
            for c in range(4):
                if board_tuple[r][c] == 0:
                    # Make move for Player -1
                    new_board = [list(row) for row in board_tuple]
                    new_board[r][c] = -1
                    new_board_tuple = tuple(tuple(row) for row in new_board)
                    
                    eval_score = minimax(new_board_tuple, depth - 1, alpha, beta, True)
                    min_eval = min(min_eval, eval_score)
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        break
            if beta <= alpha:
                break
        return min_eval

def check_win_tuple(board_tuple, player):
    """Checks if a player has won on a tuple-based board."""
    # Rows
    for r in range(4):
        if board_tuple[r] == (player, player, player, player):
            return True
    # Cols
    for c in range(4):
        col = tuple(board_tuple[r][c] for r in range(4))
        if col == (player, player, player, player):
            return True
    # Diagonals
    diag1 = tuple(board_tuple[i][i] for i in range(4))
    if diag1 == (player, player, player, player):
        return True
    diag2 = tuple(board_tuple[i][3-i] for i in range(4))
    if diag2 == (player, player, player, player):
        return True
    return False

def evaluate(board_tuple):
    """
    Heuristic evaluation function.
    Returns a score based on potential lines.
    """
    score = 0
    
    lines = []
    # Rows
    for r in range(4):
        lines.append(board_tuple[r])
    # Cols
    for c in range(4):
        lines.append(tuple(board_tuple[r][c] for r in range(4)))
    # Diagonals
    lines.append(tuple(board_tuple[i][i] for i in range(4)))
    lines.append(tuple(board_tuple[i][3-i] for i in range(4)))
    
    for line in lines:
        p1_count = line.count(1)
        p2_count = line.count(-1)
        
        # If line is blocked by both, it's worthless
        if p1_count > 0 and p2_count > 0:
            continue
            
        if p1_count == 3:
            score += 1000
        elif p1_count == 2:
            score += 100
        elif p1_count == 1:
            score += 10
            
        if p2_count == 3:
            score -= 1000
        elif p2_count == 2:
            score -= 100
        elif p2_count == 1:
            score -= 10
            
    return score
