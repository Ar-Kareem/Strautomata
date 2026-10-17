
import numpy as np
from typing import Tuple, List

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    """
    Implements a 3D Tic Tac Toe AI using minimax with alpha-beta pruning.
    
    Args:
        board: 3x3x3 list of lists representing the game state
               0 = empty, 1 = AI player, -1 = opponent
    
    Returns:
        Tuple (x, y, z) representing the chosen move coordinates
    """
    
    # Convert to numpy array for easier manipulation
    board_np = np.array(board)
    
    # Check if we can win immediately
    win_move = check_immediate_win(board_np, 1)
    if win_move:
        return win_move
    
    # Check if we need to block opponent from winning
    block_move = check_immediate_win(board_np, -1)
    if block_move:
        return block_move
    
    # Use minimax to find the best move
    _, move = minimax(board_np, depth=4, alpha=-float('inf'), beta=float('inf'), 
                      maximizing_player=True, player=1)
    
    # If minimax didn't return a valid move, pick the first available
    if move is None:
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    if board_np[i, j, k] == 0:
                        return (i, j, k)
    
    return move

def check_immediate_win(board: np.ndarray, player: int) -> None:
    """
    Check if the given player can win in one move.
    """
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i, j, k] == 0:
                    # Try placing the player's piece here
                    board[i, j, k] = player
                    if check_winner(board) == player:
                        board[i, j, k] = 0  # Reset the board
                        return (i, j, k)
                    board[i, j, k] = 0  # Reset the board
    return None

def check_winner(board: np.ndarray) -> int:
    """
    Check if there's a winner on the board.
    Returns: 1 if AI wins, -1 if opponent wins, 0 if no winner.
    """
    # Check all possible lines (rows, columns, diagonals in 3D)
    
    # Check rows in each layer (x-y planes)
    for z in range(3):
        for x in range(3):
            if board[x, 0, z] == board[x, 1, z] == board[x, 2, z] != 0:
                return board[x, 0, z]
        for y in range(3):
            if board[0, y, z] == board[1, y, z] == board[2, y, z] != 0:
                return board[0, y, z]
        # Check diagonals in each layer
        if board[0, 0, z] == board[1, 1, z] == board[2, 2, z] != 0:
            return board[0, 0, z]
        if board[0, 2, z] == board[1, 1, z] == board[2, 0, z] != 0:
            return board[0, 2, z]
    
    # Check columns through layers (z-axis)
    for x in range(3):
        for y in range(3):
            if board[x, y, 0] == board[x, y, 1] == board[x, y, 2] != 0:
                return board[x, y, 0]
    
    # Check vertical diagonals
    # Diagonals that go through all layers
    if board[0, 0, 0] == board[1, 1, 1] == board[2, 2, 2] != 0:
        return board[0, 0, 0]
    if board[0, 2, 0] == board[1, 1, 1] == board[2, 0, 2] != 0:
        return board[0, 2, 0]
    if board[2, 0, 0] == board[1, 1, 1] == board[0, 2, 2] != 0:
        return board[2, 0, 0]
    if board[2, 2, 0] == board[1, 1, 1] == board[0, 0, 2] != 0:
        return board[2, 2, 0]
        
    # Additional diagonals
    for i in range(3):
        # X-axis constant diagonals through layers
        if board[i, 0, 0] == board[i, 1, 1] == board[i, 2, 2] != 0:
            return board[i, 0, 0]
        if board[i, 0, 2] == board[i, 1, 1] == board[i, 2, 0] != 0:
            return board[i, 0, 2]
        # Y-axis constant diagonals through layers
        if board[0, i, 0] == board[1, i, 1] == board[2, i, 2] != 0:
            return board[0, i, 0]
        if board[0, i, 2] == board[1, i, 1] == board[2, i, 0] != 0:
            return board[0, i, 2]
            
    return 0  # No winner

def is_board_full(board: np.ndarray) -> bool:
    """Check if the board is full."""
    return not np.any(board == 0)

def evaluate_board(board: np.ndarray, player: int) -> int:
    """
    Heuristic evaluation function for the board position.
    """
    winner = check_winner(board)
    if winner == player:
        return 100
    elif winner == -player:
        return -100
    else:
        # Simple heuristic: count potential lines
        score = 0
        
        # Check all possible lines and score them
        lines = get_all_lines()
        for line in lines:
            line_values = [board[x, y, z] for x, y, z in line]
            player_count = line_values.count(player)
            opponent_count = line_values.count(-player)
            empty_count = line_values.count(0)
            
            # If the line is winnable
            if player_count > 0 and opponent_count == 0:
                score += player_count ** 2
            if opponent_count > 0 and player_count == 0:
                score -= opponent_count ** 2
                
        return score

def get_all_lines():
    """Get all possible lines in a 3x3x3 board."""
    lines = []
    
    # Rows in each layer
    for z in range(3):
        for x in range(3):
            lines.append([(x, y, z) for y in range(3)])
        for y in range(3):
            lines.append([(x, y, z) for x in range(3)])
        # Diagonals in each layer
        lines.append([(i, i, z) for i in range(3)])
        lines.append([(i, 2-i, z) for i in range(3)])
    
    # Columns through layers
    for x in range(3):
        for y in range(3):
            lines.append([(x, y, z) for z in range(3)])
    
    # Diagonals through layers
    lines.append([(i, i, i) for i in range(3)])
    lines.append([(i, 2-i, i) for i in range(3)])
    lines.append([(2-i, i, i) for i in range(3)])
    lines.append([(2-i, 2-i, i) for i in range(3)])
    
    # More diagonals
    for i in range(3):
        lines.append([(i, j, j) for j in range(3)])
        lines.append([(i, 2-j, j) for j in range(3)])
        lines.append([(j, i, j) for j in range(3)])
        lines.append([(j, i, 2-j) for j in range(3)])
        
    return lines

def minimax(board: np.ndarray, depth: int, alpha: float, beta: float, 
           maximizing_player: bool, player: int) -> None:
    """
    Minimax algorithm with alpha-beta pruning.
    """
    winner = check_winner(board)
    
    # Terminal conditions
    if winner == player:
        return 1000 + depth, None
    elif winner == -player:
        return -1000 - depth, None
    elif is_board_full(board) or depth == 0:
        return evaluate_board(board, player), None
    
    best_move = None
    
    if maximizing_player:
        max_eval = -float('inf')
        # Get all possible moves
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    if board[i, j, k] == 0:
                        board[i, j, k] = player
                        eval_score, _ = minimax(board, depth - 1, alpha, beta, False, player)
                        board[i, j, k] = 0
                        
                        if eval_score > max_eval:
                            max_eval = eval_score
                            best_move = (i, j, k)
                            
                        alpha = max(alpha, eval_score)
                        if beta <= alpha:
                            break
                if beta <= alpha:
                    break
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        # Get all possible moves
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    if board[i, j, k] == 0:
                        board[i, j, k] = -player
                        eval_score, _ = minimax(board, depth - 1, alpha, beta, True, player)
                        board[i, j, k] = 0
                        
                        if eval_score < min_eval:
                            min_eval = eval_score
                            best_move = (i, j, k)
                            
                        beta = min(beta, eval_score)
                        if beta <= alpha:
                            break
                if beta <= alpha:
                    break
            if beta <= alpha:
                break
        return min_eval, best_move
