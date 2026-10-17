
import numpy as np
from typing import Tuple, List

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Determine the best move for 4x4 Tic Tac Toe using minimax with alpha-beta pruning.
    """
    board = np.array(board)
    
    def check_winner(board):
        # Check rows, columns, and diagonals for a win
        for i in range(4):
            if abs(np.sum(board[i, :])) == 4:
                return np.sum(board[i, :]) // 4
            if abs(np.sum(board[:, i])) == 4:
                return np.sum(board[:, i]) // 4
                
        # Check main diagonal
        if abs(np.sum(np.diag(board))) == 4:
            return np.sum(np.diag(board)) // 4
            
        # Check anti-diagonal
        if abs(np.sum(np.diag(np.fliplr(board)))) == 4:
            return np.sum(np.diag(np.fliplr(board))) // 4
            
        return 0
    
    def is_terminal(board):
        # Check if game is over (win or draw)
        if check_winner(board) != 0:
            return True
        # Check for draw (no empty cells)
        if np.all(board != 0):
            return True
        return False
    
    def get_score(board):
        winner = check_winner(board)
        if winner == 1:  # AI wins
            return 10
        elif winner == -1:  # Opponent wins
            return -10
        elif np.all(board != 0):  # Draw
            return 0
        else:  # Game continues
            # Simple heuristic for non-terminal states
            score = 0
            # Evaluate potential winning lines
            lines = []
            # Rows
            for i in range(4):
                lines.append(board[i, :])
            # Columns
            for j in range(4):
                lines.append(board[:, j])
            # Diagonals
            lines.append(np.diag(board))
            lines.append(np.diag(np.fliplr(board)))
            
            for line in lines:
                if 1 in line and -1 in line:
                    continue  # Mixed line, no potential
                elif 1 in line:
                    score += line.tolist().count(1)  # More X's is good
                elif -1 in line:
                    score -= line.tolist().count(-1)  # More O's is bad
                    
            return score
    
    def minimax(board, depth, alpha, beta, maximizing_player):
        if is_terminal(board) or depth == 0:
            return get_score(board)
            
        legal_moves = [(i, j) for i in range(4) for j in range(4) if board[i, j] == 0]
        
        if maximizing_player:
            max_eval = float('-inf')
            for move in legal_moves:
                board[move] = 1
                eval_score = minimax(board, depth - 1, alpha, beta, False)
                board[move] = 0
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Beta cutoff
            return max_eval
        else:
            min_eval = float('inf')
            for move in legal_moves:
                board[move] = -1
                eval_score = minimax(board, depth - 1, alpha, beta, True)
                board[move] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Alpha cutoff
            return min_eval
    
    # Get all valid moves
    empty_cells = [(i, j) for i in range(4) for j in range(4) if board[i, j] == 0]
    
    if not empty_cells:
        return (0, 0)  # No moves available (should not happen in normal play)
    
    # If this is the first move, take center position
    if len(empty_cells) == 16:
        return (1, 1)
    
    # Use minimax to find the best move
    best_score = float('-inf')
    best_move = empty_cells[0]
    
    # Adjust depth based on number of empty cells
    empty_count = len(empty_cells)
    if empty_count >= 10:
        depth = 5
    elif empty_count >= 6:
        depth = 7
    else:
        depth = 9
    
    for move in empty_cells:
        board[move] = 1  # Place AI's mark
        score = minimax(board, depth, float('-inf'), float('inf'), False)
        board[move] = 0  # Undo move
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
