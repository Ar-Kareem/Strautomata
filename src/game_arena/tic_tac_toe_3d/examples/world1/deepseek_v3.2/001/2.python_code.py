
import numpy as np
from typing import List, Tuple

# Precompute all winning lines in a 3x3x3 cube
def generate_winning_lines() -> List[List[Tuple[int, int, int]]]:
    lines = []
    # Lines in each layer (9 lines per layer, 3 layers = 27)
    for z in range(3):
        # Rows in layer z
        for y in range(3):
            lines.append([(x, y, z) for x in range(3)])
        # Columns in layer z
        for x in range(3):
            lines.append([(x, y, z) for y in range(3)])
        # Diagonals in layer z
        lines.append([(i, i, z) for i in range(3)])  # main diagonal
        lines.append([(i, 2-i, z) for i in range(3)])  # anti-diagonal
    
    # Vertical lines through layers (9 lines)
    for x in range(3):
        for y in range(3):
            lines.append([(x, y, z) for z in range(3)])
    
    # Space diagonals (4 lines through the cube)
    lines.append([(i, i, i) for i in range(3)])  # main space diagonal
    lines.append([(i, i, 2-i) for i in range(3)])  # space diagonal
    lines.append([(i, 2-i, i) for i in range(3)])  # space diagonal  
    lines.append([(i, 2-i, 2-i) for i in range(3)])  # space diagonal
    
    return lines

WINNING_LINES = generate_winning_lines()

def evaluate_board(board: List[List[List[int]]], player: int) -> int:
    """Evaluate board from perspective of given player (1 = me, -1 = opponent)"""
    score = 0
    
    for line in WINNING_LINES:
        values = [board[z][y][x] for (x, y, z) in line]
        my_count = values.count(player)
        opp_count = values.count(-player)
        empty_count = values.count(0)
        
        if my_count == 3:
            return 10000  # Winning move
        if opp_count == 3:
            return -10000  # Opponent winning
        
        if opp_count == 0:
            # Line not blocked by opponent
            if my_count == 2 and empty_count == 1:
                score += 100
            elif my_count == 1 and empty_count == 2:
                score += 10
        if my_count == 0:
            # Line not containing my pieces
            if opp_count == 2 and empty_count == 1:
                score -= 100
            elif opp_count == 1 and empty_count == 2:
                score -= 10
    
    # Bonus for center control
    if board[1][1][1] == player:
        score += 20
    elif board[1][1][1] == -player:
        score -= 20
    
    return score

def get_possible_moves(board: List[List[List[int]]]) -> List[Tuple[int, int, int]]:
    """Return list of empty cell coordinates"""
    moves = []
    for z in range(3):
        for y in range(3):
            for x in range(3):
                if board[z][y][x] == 0:
                    moves.append((x, y, z))
    return moves

def minimax(board: List[List[List[int]]], depth: int, alpha: float, beta: float, 
            maximizing_player: bool, player: int) -> Tuple[float, Tuple[int, int, int]]:
    """Minimax with alpha-beta pruning. Returns (score, best_move)"""
    possible_moves = get_possible_moves(board)
    
    # Terminal conditions
    if depth == 0 or not possible_moves:
        return evaluate_board(board, player), None
    
    # Check for immediate wins/losses
    for (x, y, z) in possible_moves:
        # Test if this move gives player a win
        board[z][y][x] = player
        if evaluate_board(board, player) >= 10000:
            board[z][y][x] = 0
            return (10000 if maximizing_player else -10000), (x, y, z)
        board[z][y][x] = -player
        if evaluate_board(board, player) <= -10000:
            board[z][y][x] = 0
            return (-10000 if maximizing_player else 10000), (x, y, z)
        board[z][y][x] = 0
    
    best_move = possible_moves[0]
    
    if maximizing_player:
        max_eval = float('-inf')
        for (x, y, z) in possible_moves:
            board[z][y][x] = player
            eval_score, _ = minimax(board, depth-1, alpha, beta, False, player)
            board[z][y][x] = 0
            
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = (x, y, z)
            
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for (x, y, z) in possible_moves:
            board[z][y][x] = -player
            eval_score, _ = minimax(board, depth-1, alpha, beta, True, player)
            board[z][y][x] = 0
            
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = (x, y, z)
            
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        
        return min_eval, best_move

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Convert to mutable list
    board_copy = [[list(row) for row in layer] for layer in board]
    
    # First, check if there's an immediate winning move
    possible_moves = get_possible_moves(board_copy)
    for (x, y, z) in possible_moves:
        board_copy[z][y][x] = 1
        if evaluate_board(board_copy, 1) >= 10000:
            return (x, y, z)
        board_copy[z][y][x] = 0
    
    # Check if opponent has immediate winning move and block it
    for (x, y, z) in possible_moves:
        board_copy[z][y][x] = -1
        if evaluate_board(board_copy, 1) <= -10000:
            return (x, y, z)
        board_copy[z][y][x] = 0
    
    # Use minimax with depth 3 (adjustable based on performance)
    # On first move, choose center for optimal play
    if len(possible_moves) == 27:
        return (1, 1, 1)
    
    _, best_move = minimax(board_copy, depth=3, alpha=float('-inf'), 
                          beta=float('inf'), maximizing_player=True, player=1)
    
    return best_move
