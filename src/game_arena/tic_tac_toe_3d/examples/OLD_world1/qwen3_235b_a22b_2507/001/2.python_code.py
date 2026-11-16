
import numpy as np
from typing import List, Tuple, Iterable

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    """
    Returns the next move for 3x3x3 3D Tic Tac Toe using minimax with alpha-beta pruning.
    """
    board_array = np.array(board)
    n = 3
    
    # Convert board to numpy array for easier manipulation
    def is_valid_move(x, y, z):
        return 0 <= x < n and 0 <= y < n and 0 <= z < n and board_array[x, y, z] == 0
    
    def get_possible_moves():
        moves = []
        for x in range(n):
            for y in range(n):
                for z in range(n):
                    if board_array[x, y, z] == 0:
                        moves.append((x, y, z))
        return moves
    
    def check_winner():
        # Check all possible winning lines in 3D
        for player in [1, -1]:
            # Check rows (fixed y, z, varying x)
            for y in range(n):
                for z in range(n):
                    if all(board_array[x, y, z] == player for x in range(n)):
                        return player
            
            # Check columns (fixed x, z, varying y)
            for x in range(n):
                for z in range(n):
                    if all(board_array[x, y, z] == player for y in range(n)):
                        return player
            
            # Check depths (fixed x, y, varying z)
            for x in range(n):
                for y in range(n):
                    if all(board_array[x, y, z] == player for z in range(n)):
                        return player
            
            # Check face diagonals
            # Front face diagonals
            for z in range(n):
                if all(board_array[i, i, z] == player for i in range(n)):
                    return player
                if all(board_array[i, n-1-i, z] == player for i in range(n)):
                    return player
            
            # Side face diagonals  
            for x in range(n):
                if all(board_array[x, i, i] == player for i in range(n)):
                    return player
                if all(board_array[x, i, n-1-i] == player for i in range(n)):
                    return player
            
            # Top face diagonals
            for y in range(n):
                if all(board_array[i, y, i] == player for i in range(n)):
                    return player
                if all(board_array[i, y, n-1-i] == player for i in range(n)):
                    return player
            
            # Check space diagonals (through the cube)
            if all(board_array[i, i, i] == player for i in range(n)):
                return player
            if all(board_array[i, i, n-1-i] == player for i in range(n)):
                return player
            if all(board_array[i, n-1-i, i] == player for i in range(n)):
                return player
            if all(board_array[n-1-i, i, i] == player for i in range(n)):
                return player
        
        return 0  # No winner yet
    
    def evaluate():
        winner = check_winner()
        if winner == 1:  # AI wins
            return 1000
        elif winner == -1:  # Opponent wins
            return -1000
        else:
            # Count potential winning lines for each player
            score = 0
            # Check all possible lines
            lines = []
            
            # Add all possible lines
            for i in range(n):
                for j in range(n):
                    # Rows
                    lines.append([(k, i, j) for k in range(n)])
                    # Columns
                    lines.append([(i, k, j) for k in range(n)])
                    # Depths
                    lines.append([(i, j, k) for k in range(n)])
            
            # Add diagonals
            # Face diagonals
            for i in range(n):
                lines.append([(j, j, i) for j in range(n)])
                lines.append([(j, n-1-j, i) for j in range(n)])
                lines.append([(i, j, j) for j in range(n)])
                lines.append([(i, j, n-1-j) for j in range(n)])
                lines.append([(j, i, j) for j in range(n)])
                lines.append([(j, i, n-1-j) for j in range(n)])
            
            # Space diagonals
            lines.append([(i, i, i) for i in range(n)])
            lines.append([(i, i, n-1-i) for i in range(n)])
            lines.append([(i, n-1-i, i) for i in range(n)])
            lines.append([(n-1-i, i, i) for i in range(n)])
            
            for line in lines:
                player_count = 0
                opponent_count = 0
                empty_count = 0
                
                for x, y, z in line:
                    if board_array[x, y, z] == 1:
                        player_count += 1
                    elif board_array[x, y, z] == -1:
                        opponent_count += 1
                    else:
                        empty_count += 1
                
                # If line is not blocked, evaluate its potential
                if player_count > 0 and opponent_count == 0:
                    # Unblocked line for AI
                    if player_count == 2:
                        score += 100  # Very valuable - one move from winning
                    else:
                        score += player_count * 10
                elif opponent_count > 0 and player_count == 0:
                    # Unblocked line for opponent
                    if opponent_count == 2:
                        score -= 100  # Must block this
                    else:
                        score -= opponent_count * 10
            
            return score
    
    def minimax(depth: int, alpha: float, beta: float, is_maximizing: bool) -> float:
        # Check for terminal states
        winner = check_winner()
        if winner == 1:
            return 1000 - depth  # Prefer earlier wins
        elif winner == -1:
            return -1000 + depth  # Prefer later losses
        elif depth == 0 or len(get_possible_moves()) == 0:
            return evaluate()
        
        moves = get_possible_moves()
        
        if is_maximizing:
            max_eval = float('-inf')
            for move in moves:
                x, y, z = move
                board_array[x, y, z] = 1  # AI's move
                eval_score = minimax(depth - 1, alpha, beta, False)
                board_array[x, y, z] = 0  # Undo move
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Beta cutoff
            return max_eval
        else:
            min_eval = float('inf')
            for move in moves:
                x, y, z = move
                board_array[x, y, z] = -1  # Opponent's move
                eval_score = minimax(depth - 1, alpha, beta, True)
                board_array[x, y, z] = 0  # Undo move
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Alpha cutoff
            return min_eval
    
    # Find the best move
    moves = get_possible_moves()
    
    # If it's the first move, take the center
    if len(moves) == 27:
        return (1, 1, 1)
    
    # If we're in a late game, search deeper
    depth = 3 if len(moves) > 10 else 4
    
    best_move = moves[0]
    best_value = float('-inf')
    
    # Use iterative deepening for better move ordering
    for move in moves:
        x, y, z = move
        board_array[x, y, z] = 1  # Try AI's move
        move_value = minimax(depth - 1, float('-inf'), float('inf'), False)
        board_array[x, y, z] = 0  # Undo move
        
        if move_value > best_value:
            best_value = move_value
            best_move = move
    
    return best_move
