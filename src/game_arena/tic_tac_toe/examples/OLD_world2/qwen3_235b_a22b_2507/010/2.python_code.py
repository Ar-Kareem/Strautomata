
import numpy as np
from typing import Tuple, List, Optional

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Minimax-based policy for 4x4 Tic Tac Toe with alpha-beta pruning.
    Returns the best move (row, col) for player 1 (us) against player -1 (opponent).
    """
    board_array = np.array(board)
    
    def check_winner(board: np.ndarray) -> int:
        """Check if there's a winner. Returns 1, -1, 0 (no winner), or 2 (draw)."""
        # Check rows, columns, and diagonals for 4 in a row
        for player in [1, -1]:
            # Check rows
            for i in range(4):
                if np.all(board[i, :i+4] == player) if i <= 0 else False:
                    for j in range(1):
                        if np.all(board[i, j:j+4] == player):
                            return player
            
            # This approach is cleaner:
            # Check rows
            for i in range(4):
                for j in range(1):
                    if np.all(board[i, j:j+4] == player):
                        return player
            
            # Check columns
            for j in range(4):
                for i in range(1):
                    if np.all(board[i:i+4, j] == player):
                        return player
            
            # Check diagonals (top-left to bottom-right)
            for i in range(1):
                for j in range(1):
                    if np.all(np.diag(board[i:i+4, j:j+4]) == player):
                        return player
            
            # Check diagonals (top-right to bottom-left)
            for i in range(1):
                for j in range(3, 4):
                    if np.all(np.diag(np.fliplr(board[i:i+4, j-3:j+1])) == player):
                        return player
        
        # Check if board is full (draw)
        if 0 not in board:
            return 2  # Draw
        
        return 0  # Game continues
    
    def get_winner(board: np.ndarray) -> int:
        """Simplified winner check for 4x4 board."""
        # Check rows
        for i in range(4):
            for j in range(1):  # Only one possible sequence of 4 in a row of 4
                if board[i, j] != 0 and board[i, j] == board[i, j+1] == board[i, j+2] == board[i, j+3]:
                    return board[i, j]
        
        # Check columns
        for j in range(4):
            for i in range(1):
                if board[i, j] != 0 and board[i, j] == board[i+1, j] == board[i+2, j] == board[i+3, j]:
                    return board[i, j]
        
        # Check main diagonal
        if board[0,0] != 0 and board[0,0] == board[1,1] == board[2,2] == board[3,3]:
            return board[0,0]
        
        # Check other diagonal
        if board[0,3] != 0 and board[0,3] == board[1,2] == board[2,1] == board[3,0]:
            return board[0,3]
        
        # Check for draw
        if 0 not in board:
            return 2
        
        return 0
    
    def get_valid_moves(board: np.ndarray) -> List[Tuple[int, int]]:
        """Get all empty positions on the board."""
        moves = []
        for i in range(4):
            for j in range(4):
                if board[i, j] == 0:
                    moves.append((i, j))
        return moves
    
    def evaluate(board: np.ndarray, depth: int) -> int:
        """Heuristic evaluation of board position."""
        winner = get_winner(board)
        if winner == 1:  # We win
            return 10000 - depth  # Prefer quicker wins
        elif winner == -1:  # Opponent wins
            return -10000 + depth  # Prefer slower losses
        elif winner == 2:  # Draw
            return 0
        
        # Simple heuristic: count potential winning lines
        score = 0
        
        # Count our marks in potential winning lines
        for i in range(4):
            row = board[i, :]
            if -1 not in row:  # No opponent marks in this row
                score += np.sum(row == 1)
        
        for j in range(4):
            col = board[:, j]
            if -1 not in col:
                score += np.sum(col == 1)
        
        # Diagonals
        diag1 = np.diag(board)
        if -1 not in diag1:
            score += np.sum(diag1 == 1)
        
        diag2 = np.diag(np.fliplr(board))
        if -1 not in diag2:
            score += np.sum(diag2 == 1)
        
        # Subtract opponent's potential
        for i in range(4):
            row = board[i, :]
            if 1 not in row:
                score -= np.sum(row == -1)
        
        for j in range(4):
            col = board[:, j]
            if 1 not in col:
                score -= np.sum(col == -1)
        
        diag1 = np.diag(board)
        if 1 not in diag1:
            score -= np.sum(diag1 == -1)
        
        diag2 = np.diag(np.fliplr(board))
        if 1 not in diag2:
            score -= np.sum(diag2 == -1)
        
        return score
    
    def minimax(board: np.ndarray, depth: int, alpha: float, beta: float, 
                is_maximizing: bool, max_depth: int = 6) -> Tuple[int, Optional[Tuple[int, int]]]:
        """Minimax with alpha-beta pruning."""
        winner = get_winner(board)
        if winner != 0:  # Game over
            if winner == 1:
                return 10000 - depth, None
            elif winner == -1:
                return -10000 + depth, None
            else:  # Draw
                return 0, None
        
        if depth >= max_depth:
            return evaluate(board, depth), None
        
        valid_moves = get_valid_moves(board)
        if not valid_moves:
            return 0, None
        
        best_move = valid_moves[0]  # Default
        
        if is_maximizing:
            max_eval = float('-inf')
            for move in valid_moves:
                # Make move
                board[move[0], move[1]] = 1
                eval_score, _ = minimax(board, depth + 1, alpha, beta, False, max_depth)
                # Undo move
                board[move[0], move[1]] = 0
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Beta cutoff
            
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for move in valid_moves:
                # Make move
                board[move[0], move[1]] = -1
                eval_score, _ = minimax(board, depth + 1, alpha, beta, True, max_depth)
                # Undo move
                board[move[0], move[1]] = 0
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Alpha cutoff
            
            return min_eval, best_move
    
    # Get all valid moves
    valid_moves = get_valid_moves(board_array)
    
    # If only one move left, take it
    if len(valid_moves) == 1:
        return valid_moves[0]
    
    # Look for immediate win
    for move in valid_moves:
        board_array[move[0], move[1]] = 1
        if get_winner(board_array) == 1:
            board_array[move[0], move[1]] = 0
            return move
        board_array[move[0], move[1]] = 0
    
    # Block immediate opponent win
    for move in valid_moves:
        board_array[move[0], move[1]] = -1
        if get_winner(board_array) == -1:
            board_array[move[0], move[1]] = 0
            return move
        board_array[move[0], move[1]] = 0
    
    # Use minimax to find best move
    # Adjust depth based on number of empty squares
    empty_count = len(valid_moves)
    if empty_count >= 10:
        max_depth = 4
    elif empty_count >= 6:
        max_depth = 5
    else:
        max_depth = 6
    
    _, best_move = minimax(board_array.copy(), 0, float('-inf'), float('inf'), True, max_depth)
    
    return best_move if best_move is not None else valid_moves[0]
