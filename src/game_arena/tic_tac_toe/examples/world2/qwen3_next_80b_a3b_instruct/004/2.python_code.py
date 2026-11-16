
import numpy as np
from functools import lru_cache

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert to numpy array for easier manipulation
    board_np = np.array(board, dtype=int)
    
    # Get list of empty positions
    empty_cells = [(i, j) for i in range(4) for j in range(4) if board_np[i, j] == 0]
    if not empty_cells:
        return (0, 0)  # Shouldn't happen in valid game, but safety

    # Check for immediate win
    for move in empty_cells:
        if check_wins(board_np, move, 1):
            return move

    # Check for immediate block
    for move in empty_cells:
        if check_wins(board_np, move, -1):
            return move

    # Use minimax with alpha-beta pruning
    # Since board is small (4x4), we can go deeper
    best_move = None
    best_score = float('-inf')
    alpha = float('-inf')
    beta = float('inf')
    
    # Prioritize center moves first for better pruning
    sorted_moves = sorted(empty_cells, key=center_priority, reverse=True)
    
    for move in sorted_moves:
        # Make move
        board_np[move[0], move[1]] = 1
        score = minimax(board_np, 1, alpha, beta, depth=5)
        board_np[move[0], move[1]] = 0  # Undo move
        
        if score > best_score:
            best_score = score
            best_move = move
        alpha = max(alpha, best_score)
        
        # Prune if possible
        if alpha >= beta:
            break

    # Fallback: if no move found (shouldn't happen), pick first empty
    if best_move is None:
        return empty_cells[0]
    
    return best_move

def center_priority(cell):
    i, j = cell
    # Center cells are (1,1), (1,2), (2,1), (2,2) — highest priority
    center_score = 0
    if i in [1, 2] and j in [1, 2]:
        center_score = 4
    elif i in [0, 3] and j in [0, 3]:  # Corners
        center_score = 3
    elif i in [0, 3] or j in [0, 3]:  # Edges
        center_score = 1
    else:  # Center
        center_score = 4
    return center_score

@lru_cache(maxsize=100000)
def minimax(board_tuple, player, alpha, beta, depth):
    # Convert tuple back to numpy array for processing
    board = np.array(board_tuple, dtype=int)
    
    # Check terminal states
    if has_won(board, 1):
        return 1000
    if has_won(board, -1):
        return -1000
    if depth == 0 or not np.any(board == 0):
        return evaluate_board(board)
    
    empty_cells = [(i, j) for i in range(4) for j in range(4) if board[i, j] == 0]
    if not empty_cells:
        return evaluate_board(board)
    
    if player == 1:  # Maximizer
        max_eval = float('-inf')
        for move in empty_cells:
            board[move[0], move[1]] = 1
            eval_score = minimax(tuple(map(tuple, board)), -1, alpha, beta, depth - 1)
            board[move[0], move[1]] = 0
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:  # Minimizer (opponent)
        min_eval = float('inf')
        for move in empty_cells:
            board[move[0], move[1]] = -1
            eval_score = minimax(tuple(map(tuple, board)), 1, alpha, beta, depth - 1)
            board[move[0], move[1]] = 0
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

def evaluate_board(board):
    """Heuristic evaluation based on potential winning lines."""
    score = 0
    
    # Count potential winning lines for each player
    player_1_lines = count_potential_lines(board, 1)
    player_2_lines = count_potential_lines(board, -1)
    
    # Heuristic: prioritize having more potential lines
    score += player_1_lines * 10
    score -= player_2_lines * 10
    
    # Add center control bonus
    center_cells = [(1,1), (1,2), (2,1), (2,2)]
    for ci, cj in center_cells:
        if board[ci, cj] == 1:
            score += 3
        elif board[ci, cj] == -1:
            score -= 3
    
    # Add corner control bonus
    corner_cells = [(0,0), (0,3), (3,0), (3,3)]
    for ci, cj in corner_cells:
        if board[ci, cj] == 1:
            score += 2
        elif board[ci, cj] == -1:
            score -= 2
    
    return score

def count_potential_lines(board, player):
    """Count the number of potential winning lines for the player (not yet blocked)"""
    count = 0
    
    # Check rows
    for i in range(4):
        row = board[i, :]
        if np.sum(row == player) == 3 and np.sum(row == 0) == 1:
            count += 1
        if np.sum(row == player) == 2 and np.sum(row == 0) == 2:
            # At least 2 in a row, 2 open
            count += 1
    
    # Check columns
    for j in range(4):
        col = board[:, j]
        if np.sum(col == player) == 3 and np.sum(col == 0) == 1:
            count += 1
        if np.sum(col == player) == 2 and np.sum(col == 0) == 2:
            count += 1
    
    # Check diagonals
    diag1 = [board[i, i] for i in range(4)]
    diag2 = [board[i, 3-i] for i in range(4)]
    
    if np.sum(diag1 == player) == 3 and np.sum(diag1 == 0) == 1:
        count += 1
    if np.sum(diag1 == player) == 2 and np.sum(diag1 == 0) == 2:
        count += 1
        
    if np.sum(diag2 == player) == 3 and np.sum(diag2 == 0) == 1:
        count += 1
    if np.sum(diag2 == player) == 2 and np.sum(diag2 == 0) == 2:
        count += 1
    
    # Check other 3-cell diagonals (in 4x4, there are more than 2)
    # Diagonals of length 3:
    for start_i in range(2):
        for start_j in range(2):
            # Diagonal down-right
            diag = [board[start_i + k, start_j + k] for k in range(3)]
            if np.sum(np.array(diag) == player) == 3 and np.sum(np.array(diag) == 0) == 0:
                pass # already win, not potential
            elif np.sum(np.array(diag) == player) == 2 and np.sum(np.array(diag) == 0) == 1:
                count += 1
                
            # Diagonal down-left
            diag = [board[start_i + k, start_j + 2 - k] for k in range(3)]
            if np.sum(np.array(diag) == player) == 2 and np.sum(np.array(diag) == 0) == 1:
                count += 1
    
    # Also check if player has a double threat (2 open lines with 2 in each)
    # This is complex, but the heuristic above is sufficient for good play
    
    return count

def has_won(board, player):
    """Check if player has won on the 4x4 board"""
    # Check rows
    for i in range(4):
        if np.all(board[i, :] == player):
            return True
    
    # Check columns
    for j in range(4):
        if np.all(board[:, j] == player):
            return True
    
    # Check main diagonal
    if np.all([board[i, i] == player for i in range(4)]):
        return True
    
    # Check anti-diagonal
    if np.all([board[i, 3-i] == player for i in range(4)]):
        return True
    
    # Check all 3x1 diagonals (we need to check every possible 3-in-a-row)
    # Horizontal 3-in-a-row: 2 possible in each row
    for i in range(4):
        for j in range(2):
            if np.all(board[i, j:j+3] == player):
                return True
    # Vertical 3-in-a-row: 2 possible in each column
    for j in range(4):
        for i in range(2):
            if np.all(board[i:i+3, j] == player):
                return True

    # Diagonal 3-in-a-row: top-left to bottom-right
    for i in range(2):
        for j in range(2):
            if np.all([board[i+k, j+k] == player for k in range(3)]):
                return True
    
    # Diagonal 3-in-a-row: top-right to bottom-left
    for i in range(2):
        for j in range(2):
            if np.all([board[i+k, j+2-k] == player for k in range(3)]):
                return True
    
    return False

def check_wins(board, move, player):
    """Check if placing player at move results in win"""
    r, c = move
    board[r, c] = player
    win = has_won(board, player)
    board[r, c] = 0  # Undo
    return win
