
import numpy as np
from typing import Tuple, List, Optional

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    """Minimax-based policy for 3D Tic Tac Toe with alpha-beta pruning."""
    
    # Convert to numpy array for easier manipulation
    board_array = np.array(board)
    
    # Helper function to check if a move is valid
    def is_valid_move(i: int, j: int, k: int) -> bool:
        return board_array[i, j, k] == 0
    
    # Helper function to make a move
    def make_move(i: int, j: int, k: int, player: int):
        board_array[i, j, k] = player
    
    # Helper function to undo a move
    def undo_move(i: int, j: int, k: int):
        board_array[i, j, k] = 0
    
    # Helper function to check for a win
    def check_win(player: int) -> bool:
        # Check all possible winning lines
        for i in range(3):
            for j in range(3):
                # Check rows in k direction
                if all(board_array[i, j, k] == player for k in range(3)):
                    return True
                # Check columns in j direction
                if all(board_array[i, j, k] == player for j in range(3)):
                    return True
                # Check columns in i direction
                if all(board_array[i, j, k] == player for i in range(3)):
                    return True
        
        # Check face diagonals
        for i in range(3):
            # Check diagonals on each i-face
            if all(board_array[i, j, j] == player for j in range(3)):
                return True
            if all(board_array[i, j, 2-j] == player for j in range(3)):
                return True
        
        for j in range(3):
            # Check diagonals on each j-face
            if all(board_array[i, j, i] == player for i in range(3)):
                return True
            if all(board_array[2-i, j, i] == player for i in range(3)):
                return True
        
        for k in range(3):
            # Check diagonals on each k-face
            if all(board_array[i, i, k] == player for i in range(3)):
                return True
            if all(board_array[2-i, i, k] == player for i in range(3)):
                return True
        
        # Check 3D diagonals
        if all(board_array[i, i, i] == player for i in range(3)):
            return True
        if all(board_array[i, i, 2-i] == player for i in range(3)):
            return True
        if all(board_array[i, 2-i, i] == player for i in range(3)):
            return True
        if all(board_array[2-i, 2-i, i] == player for i in range(3)):
            return True
        
        return False
    
    # Helper function to get all valid moves
    def get_valid_moves() -> List[Tuple[int, int, int]]:
        moves = []
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    if is_valid_move(i, j, k):
                        moves.append((i, j, k))
        return moves
    
    # Helper function to evaluate the board
    def evaluate() -> int:
        if check_win(1):  # AI wins
            return 1000
        elif check_win(-1):  # Opponent wins
            return -1000
        else:
            return 0
    
    # Helper function to check if the game is over
    def is_game_over() -> bool:
        return check_win(1) or check_win(-1) or len(get_valid_moves()) == 0
    
    # Minimax algorithm with alpha-beta pruning
    def minimax(depth: int, alpha: float, beta: float, is_maximizing: bool) -> int:
        # Terminal conditions
        score = evaluate()
        if score != 0:
            return score
        if is_game_over():
            return 0
        
        # Depth limit for performance
        if depth >= 4:
            return 0
        
        if is_maximizing:
            max_eval = float('-inf')
            for move in get_valid_moves():
                make_move(move[0], move[1], move[2], 1)
                eval_score = minimax(depth + 1, alpha, beta, False)
                undo_move(move[0], move[1], move[2])
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in get_valid_moves():
                make_move(move[0], move[1], move[2], -1)
                eval_score = minimax(depth + 1, alpha, beta, True)
                undo_move(move[0], move[1], move[2])
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    # Find the best move
    def find_best_move() -> Optional[Tuple[int, int, int]]:
        valid_moves = get_valid_moves()
        if not valid_moves:
            return None
        
        best_score = float('-inf')
        best_move = valid_moves[0]  # Default to first valid move
        
        for move in valid_moves:
            make_move(move[0], move[1], move[2], 1)
            move_score = minimax(0, float('-inf'), float('inf'), False)
            undo_move(move[0], move[1], move[2])
            
            if move_score > best_score:
                best_score = move_score
                best_move = move
        
        return best_move
    
    # First, check if we can win in one move
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if is_valid_move(i, j, k):
                    make_move(i, j, k, 1)
                    if check_win(1):
                        undo_move(i, j, k)
                        return (i, j, k)
                    undo_move(i, j, k)
    
    # Then, check if opponent can win in one move and block them
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if is_valid_move(i, j, k):
                    make_move(i, j, k, -1)
                    if check_win(-1):
                        undo_move(i, j, k)
                        return (i, j, k)
                    undo_move(i, j, k)
    
    # If no immediate win/block, use minimax to find the best move
    best_move = find_best_move()
    if best_move:
        return best_move
    
    # Fallback: return the first valid move
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if is_valid_move(i, j, k):
                    return (i, j, k)
    
    # This should never happen if the game is valid
    return (0, 0, 0)
