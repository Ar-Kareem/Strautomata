
import numpy as np
from typing import List, Tuple

def policy(board: List[List[int]]) -> int:
    # Convert to numpy array for easier manipulation
    grid = np.array(board, dtype=np.int8)
    
    # Define player and opponent
    player = 1  # Current player
    opponent = -1

    # Get valid moves (non-full columns)
    def get_valid_moves(board):
        return [col for col in range(7) if board[0][col] == 0]
    
    # Check if a move is valid
    def is_valid_move(board, col):
        return board[0][col] == 0

    # Drop a piece in the specified column
    def make_move(board, col, player):
        new_board = board.copy()
        for row in range(5, -1, -1):
            if new_board[row][col] == 0:
                new_board[row][col] = player
                return new_board, row, col
        return None  # shouldn't happen if valid
    
    # Check if the move results in a win
    def check_win(board, row, col, player):
        # Check horizontal
        count = 0
        for c in range(max(0, col-3), min(7, col+4)):
            if board[row][c] == player:
                count += 1
                if count == 4:
                    return True
            else:
                count = 0
        
        # Check vertical
        count = 0
        for r in range(max(0, row-3), min(6, row+4)):
            if board[r][col] == player:
                count += 1
                if count == 4:
                    return True
            else:
                count = 0
        
        # Check diagonal /
        count = 0
        for i in range(-3, 4):
            r, c = row - i, col + i
            if 0 <= r < 6 and 0 <= c < 7:
                if board[r][c] == player:
                    count += 1
                    if count == 4:
                        return True
                else:
                    count = 0
        
        # Check diagonal \
        count = 0
        for i in range(-3, 4):
            r, c = row + i, col + i
            if 0 <= r < 6 and 0 <= c < 7:
                if board[r][c] == player:
                    count += 1
                    if count == 4:
                        return True
                else:
                    count = 0
        return False

    # Heuristic evaluation function
    def evaluate_board(board, player):
        score = 0
        opponent = -player

        # Center control bonus
        center_col = board[:, 3]
        center_count = np.sum(center_col == player)
        score += center_count * 3

        # Check all 4-length windows for potential
        def score_window(window, player):
            score = 0
            opp = -player
            if np.sum(window == player) == 4:
                score += 1000
            elif np.sum(window == player) == 3 and np.sum(window == 0) == 1:
                score += 50
            elif np.sum(window == player) == 2 and np.sum(window == 0) == 2:
                score += 10
            if np.sum(window == opp) == 3 and np.sum(window == 0) == 1:
                score -= 40  # Block opponent's threat
            return score

        # Horizontal
        for r in range(6):
            for c in range(4):
                window = board[r, c:c+4]
                score += score_window(window, player)
        
        # Vertical
        for c in range(7):
            for r in range(3):
                window = board[r:r+4, c]
                score += score_window(window, player)
        
        # Diagonal / 
        for r in range(3, 6):
            for c in range(4):
                window = [board[r-i][c+i] for i in range(4)]
                score += score_window(np.array(window), player)
        
        # Diagonal \
        for r in range(3):
            for c in range(4):
                window = [board[r+i][c+i] for i in range(4)]
                score += score_window(np.array(window), player)

        return score

    # Minimax with alpha-beta pruning
    def minimax(board, depth, alpha, beta, maximizing_player, player):
        valid_moves = get_valid_moves(board)
        if depth == 0 or len(valid_moves) == 0:
            return evaluate_board(board, player), None
        
        # Check for terminal win
        # We need to know the last move? But we don't track... so check all?
        # Instead, we'll check after making move in recursion base

        if maximizing_player:
            max_eval = -float('inf')
            best_col = valid_moves[0]
            for col in valid_moves:
                if not is_valid_move(board, col):
                    continue
                new_board, row, col_idx = make_move(board, col, player)
                if check_win(new_board, row, col, player):
                    eval_score = 10000 - depth  # Prefer quicker wins
                else:
                    eval_score, _ = minimax(new_board, depth - 1, alpha, beta, False, -player)
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_col = col
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval, best_col
        else:
            min_eval = float('inf')
            best_col = valid_moves[0]
            for col in valid_moves:
                if not is_valid_move(board, col):
                    continue
                new_board, row, col_idx = make_move(board, col, opponent)
                if check_win(new_board, row, col, opponent):
                    eval_score = -10000 + depth  # Opponent wins
                else:
                    eval_score, _ = minimax(new_board, depth - 1, alpha, beta, True, -player)
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_col = col
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_col

    # Determine search depth based on game stage
    # Count filled cells to estimate game phase
    filled = np.sum(grid != 0)
    if filled < 10:
        depth = 6
    elif filled < 20:
        depth = 5
    elif filled < 30:
        depth = 4
    else:
        depth = 3

    # First, check for immediate win
    valid_moves = get_valid_moves(grid)
    for col in valid_moves:
        new_board, row, col_idx = make_move(grid, col, player)
        if check_win(new_board, row, col, player):
            return col

    # Then, check for opponent win and block
    for col in valid_moves:
        new_board, row, col_idx = make_move(grid, col, opponent)
        if check_win(new_board, row, col, opponent):
            return col

    # Otherwise, use minimax
    _, best_col = minimax(grid, depth, -float('inf'), float('inf'), True, player)
    return best_col
