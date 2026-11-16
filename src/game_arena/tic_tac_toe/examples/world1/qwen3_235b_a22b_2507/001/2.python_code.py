
import numpy as np
from typing import Tuple, List

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Returns the optimal move using minimax algorithm with alpha-beta pruning.
    """
    
    def check_winner(board):
        """Returns 1 if player 1 wins, -1 if player -1 wins, 0 otherwise."""
        # Convert to numpy array for easier manipulation
        b = np.array(board)
        
        # Check rows, columns, and diagonals
        for i in range(3):
            if abs(sum(b[i, :])) == 3:  # Row
                return b[i, 0]
            if abs(sum(b[:, i])) == 3:  # Column
                return b[0, i]
        
        if abs(sum([b[i, i] for i in range(3)])) == 3:  # Main diagonal
            return b[0, 0]
        if abs(sum([b[i, 2-i] for i in range(3)])) == 3:  # Anti-diagonal
            return b[0, 2]
            
        return 0  # No winner yet
    
    def is_game_over(board):
        """Check if the game is over (win or draw)."""
        if check_winner(board) != 0:
            return True
        
        # Check for empty cells
        for row in board:
            if 0 in row:
                return False
        return True
    
    def get_valid_moves(board):
        """Return list of valid moves as (row, col) tuples."""
        moves = []
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    moves.append((i, j))
        return moves
    
    def minimax(board, depth, alpha, beta, is_maximizing):
        """
        Minimax algorithm with alpha-beta pruning.
        Returns the best score for the current position.
        """
        winner = check_winner(board)
        if winner == 1:  # I win
            return 10 - depth
        elif winner == -1:  # Opponent wins
            return depth - 10
        elif is_game_over(board):  # Draw
            return 0
        
        if is_maximizing:
            max_eval = float('-inf')
            for move in get_valid_moves(board):
                # Make the move
                board[move[0]][move[1]] = 1
                eval_score = minimax(board, depth + 1, alpha, beta, False)
                # Undo the move
                board[move[0]][move[1]] = 0
                
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Alpha-beta pruning
            return max_eval
        else:
            min_eval = float('inf')
            for move in get_valid_moves(board):
                # Make the move
                board[move[0]][move[1]] = -1
                eval_score = minimax(board, depth + 1, alpha, beta, True)
                # Undo the move
                board[move[0]][move[1]] = 0
                
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Alpha-beta pruning
            return min_eval
    
    # Get all valid moves and evaluate each one
    valid_moves = get_valid_moves(board)
    
    if not valid_moves:
        return (0, 0)  # Should never happen in a real game
    
    # If it's the first move, take center if available, otherwise take a corner
    if len(valid_moves) == 9:
        return (1, 1)  # Take center
    
    best_move = valid_moves[0]
    best_value = float('-inf')
    
    # Try each move and pick the one with the highest minimax score
    for move in valid_moves:
        # Make the move
        board[move[0]][move[1]] = 1
        move_value = minimax(board, 0, float('-inf'), float('inf'), False)
        # Undo the move
        board[move[0]][move[1]] = 0
        
        if move_value > best_value:
            best_value = move_value
            best_move = move
    
    return best_move
