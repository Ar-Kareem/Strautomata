
import numpy as np
from typing import List, Tuple

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    """
    Determines the next move for 3x3x3 3D Tic Tac Toe using a minimax algorithm with alpha-beta pruning.
    """
    # Convert to numpy array for easier manipulation
    board_array = np.array(board)
    n = board_array.shape[0]
    
    def check_winner(board_state):
        """Check if there's a winner on the current board."""
        # Check all possible lines (rows, columns, depths, diagonals)
        for i in range(n):
            for j in range(n):
                # Check lines along depth (fixed x,y)
                if abs(sum(board_state[i][j][k] for k in range(n))) == n:
                    return board_state[i][j][0] if board_state[i][j][0] != 0 else 0
                
                # Check lines along columns (fixed x,z)
                if abs(sum(board_state[i][k][j] for k in range(n))) == n:
                    return board_state[i][0][j] if board_state[i][0][j] != 0 else 0
                
                # Check lines along rows (fixed y,z)
                if abs(sum(board_state[k][i][j] for k in range(n))) == n:
                    return board_state[0][i][j] if board_state[0][i][j] != 0 else 0
        
        # Check all diagonals in each dimension
        # Main diagonal (0,0,0) -> (1,1,1) -> (2,2,2)
        if abs(sum(board_state[i][i][i] for i in range(n))) == n:
            return board_state[0][0][0] if board_state[0][0][0] != 0 else 0
            
        # Diagonal (0,0,2) -> (1,1,1) -> (2,2,0)
        if abs(sum(board_state[i][i][n-1-i] for i in range(n))) == n:
            return board_state[0][0][n-1] if board_state[0][0][n-1] != 0 else 0
            
        # Diagonal (0,2,0) -> (1,1,1) -> (2,0,2)
        if abs(sum(board_state[i][n-1-i][i] for i in range(n))) == n:
            return board_state[0][n-1][0] if board_state[0][n-1][0] != 0 else 0
            
        # Diagonal (0,2,2) -> (1,1,1) -> (2,0,0)
        if abs(sum(board_state[i][n-1-i][n-1-i] for i in range(n))) == n:
            return board_state[0][n-1][n-1] if board_state[0][n-1][n-1] != 0 else 0
        
        # Check face diagonals
        for k in range(n):  # For each layer
            # Check diagonals in xy plane
            if abs(sum(board_state[i][i][k] for i in range(n))) == n:
                return board_state[0][0][k] if board_state[0][0][k] != 0 else 0
            if abs(sum(board_state[i][n-1-i][k] for i in range(n))) == n:
                return board_state[0][n-1][k] if board_state[0][n-1][k] != 0 else 0
                
            # Check diagonals in xz plane
            if abs(sum(board_state[i][k][i] for i in range(n))) == n:
                return board_state[0][k][0] if board_state[0][k][0] != 0 else 0
            if abs(sum(board_state[i][k][n-1-i] for i in range(n))) == n:
                return board_state[0][k][n-1] if board_state[0][k][n-1] != 0 else 0
                
            # Check diagonals in yz plane
            if abs(sum(board_state[k][i][i] for i in range(n))) == n:
                return board_state[k][0][0] if board_state[k][0][0] != 0 else 0
            if abs(sum(board_state[k][i][n-1-i] for i in range(n))) == n:
                return board_state[k][0][n-1] if board_state[k][0][n-1] != 0 else 0
        
        return 0  # No winner yet
    
    def minimax(board_state, depth, alpha, beta, maximizing_player):
        """Minimax algorithm with alpha-beta pruning."""
        winner = check_winner(board_state)
        
        # Return evaluation scores
        if winner == 1:  # AI wins
            return 10 - depth
        elif winner == -1:  # Opponent wins
            return depth - 10
        elif np.all(board_state != 0):  # Board is full (draw)
            return 0
        
        if depth == 6:  # Depth limit for performance
            return 0
        
        if maximizing_player:
            max_eval = float('-inf')
            for i in range(n):
                for j in range(n):
                    for k in range(n):
                        if board_state[i][j][k] == 0:
                            board_state[i][j][k] = 1  # Place AI's mark
                            eval_score = minimax(board_state, depth + 1, alpha, beta, False)
                            board_state[i][j][k] = 0  # Undo move
                            max_eval = max(max_eval, eval_score)
                            alpha = max(alpha, eval_score)
                            if beta <= alpha:
                                break  # Alpha-beta pruning
            return max_eval
        else:
            min_eval = float('inf')
            for i in range(n):
                for j in range(n):
                    for k in range(n):
                        if board_state[i][j][k] == 0:
                            board_state[i][j][k] = -1  # Place opponent's mark
                            eval_score = minimax(board_state, depth + 1, alpha, beta, True)
                            board_state[i][j][k] = 0  # Undo move
                            min_eval = min(min_eval, eval_score)
                            beta = min(beta, eval_score)
                            if beta <= alpha:
                                break  # Alpha-beta pruning
            return min_eval
    
    # First, check if there's an immediate winning move
    for i in range(n):
        for j in range(n):
            for k in range(n):
                if board_array[i][j][k] == 0:
                    board_array[i][j][k] = 1
                    if check_winner(board_array) == 1:
                        board_array[i][j][k] = 0
                        return (i, j, k)
                    board_array[i][j][k] = 0
    
    # Check if opponent has a winning move and block it
    for i in range(n):
        for j in range(n):
            for k in range(n):
                if board_array[i][j][k] == 0:
                    board_array[i][j][k] = -1
                    if check_winner(board_array) == -1:
                        board_array[i][j][k] = 0
                        return (i, j, k)
                    board_array[i][j][k] = 0
    
    # If center is available, take it
    if board_array[1][1][1] == 0:
        return (1, 1, 1)
    
    # Otherwise, use minimax to determine the best move
    best_score = float('-inf')
    best_move = None
    
    for i in range(n):
        for j in range(n):
            for k in range(n):
                if board_array[i][j][k] == 0:
                    board_array[i][j][k] = 1  # Place AI's mark
                    score = minimax(board_array, 0, float('-inf'), float('inf'), False)
                    board_array[i][j][k] = 0  # Undo move
                    
                    if score > best_score:
                        best_score = score
                        best_move = (i, j, k)
    
    # If no move was found (should not happen in normal gameplay), pick the first empty cell
    if best_move is None:
        for i in range(n):
            for j in range(n):
                for k in range(n):
                    if board_array[i][j][k] == 0:
                        return (i, j, k)
    
    return best_move
