
import numpy as np
from typing import Tuple, List

def policy(you, opponent) -> str:
    # Convert inputs to numpy arrays
    you_board = np.array(you)
    opp_board = np.array(opponent)
    
    # Get all possible moves
    possible_moves = get_possible_moves(you_board, opp_board)
    
    # Try to win immediately
    for move in possible_moves:
        row, col, quad, dir = parse_move(move)
        if would_win(you_board, opp_board, row, col, quad, dir):
            return move
    
    # Try to prevent opponent from winning
    for move in possible_moves:
        row, col, quad, dir = parse_move(move)
        if would_lose(you_board, opp_board, row, col, quad, dir):
            return move
    
    # Use minimax to find best move
    best_move = minimax(you_board, opp_board, depth=2, alpha=-np.inf, beta=np.inf, maximizing=True)
    
    return best_move

def parse_move(move_str: str) -> Tuple[int, int, int, str]:
    parts = move_str.split(',')
    return int(parts[0]), int(parts[1]), int(parts[2]), parts[3]

def get_possible_moves(you_board: np.ndarray, opp_board: np.ndarray) -> List[str]:
    moves = []
    for r in range(6):
        for c in range(6):
            if you_board[r, c] == 0 and opp_board[r, c] == 0:
                for quad in range(4):
                    for dir in ['L', 'R']:
                        moves.append(f"{r+1},{c+1},{quad},{dir}")
    return moves

def would_win(you_board: np.ndarray, opp_board: np.ndarray, row: int, col: int, quad: int, dir: str) -> bool:
    # Simulate the move
    new_you, new_opp = apply_move(you_board, opp_board, row, col, quad, dir)
    
    # Check if we have a 5-in-a-row
    return has_five_in_a_row(new_you)

def would_lose(you_board: np.ndarray, opp_board: np.ndarray, row: int, col: int, quad: int, dir: str) -> bool:
    # Simulate the move
    new_you, new_opp = apply_move(you_board, opp_board, row, col, quad, dir)
    
    # Check if opponent has a 5-in-a-row
    return has_five_in_a_row(new_opp)

def has_five_in_a_row(board: np.ndarray) -> bool:
    # Check horizontal
    for r in range(6):
        for c in range(2):
            if all(board[r, c+i] == 1 for i in range(5)):
                return True
    
    # Check vertical
    for c in range(6):
        for r in range(2):
            if all(board[r+i, c] == 1 for i in range(5)):
                return True
    
    # Check diagonal (top-left to bottom-right)
    for r in range(2):
        for c in range(2):
            if all(board[r+i, c+i] == 1 for i in range(5)):
                return True
    
    # Check diagonal (bottom-left to top-right)
    for r in range(5, 0, -1):
        for c in range(2):
            if all(board[r-i, c+i] == 1 for i in range(5)):
                return True
    
    return False

def apply_move(you_board: np.ndarray, opp_board: np.ndarray, row: int, col: int, quad: int, dir: str) -> Tuple[np.ndarray, np.ndarray]:
    # Create copies
    new_you = you_board.copy()
    new_opp = opp_board.copy()
    
    # Place the marble
    new_you[row-1, col-1] = 1
    
    # Rotate the quadrant
    if quad == 0:
        quadrant = new_you[0:3, 0:3], new_opp[0:3, 0:3]
    elif quad == 1:
        quadrant = new_you[0:3, 3:6], new_opp[0:3, 3:6]
    elif quad == 2:
        quadrant = new_you[3:6, 0:3], new_opp[3:6, 0:3]
    else:  # quad == 3
        quadrant = new_you[3:6, 3:6], new_opp[3:6, 3:6]
    
    # Rotate
    if dir == 'L':
        rotated_you = np.rot90(quadrant[0], k=1)
        rotated_opp = np.rot90(quadrant[1], k=1)
    else:  # dir == 'R'
        rotated_you = np.rot90(quadrant[0], k=3)
        rotated_opp = np.rot90(quadrant[1], k=3)
    
    # Update the board
    if quad == 0:
        new_you[0:3, 0:3] = rotated_you
        new_opp[0:3, 0:3] = rotated_opp
    elif quad == 1:
        new_you[0:3, 3:6] = rotated_you
        new_opp[0:3, 3:6] = rotated_opp
    elif quad == 2:
        new_you[3:6, 0:3] = rotated_you
        new_opp[3:6, 0:3] = rotated_opp
    else:  # quad == 3
        new_you[3:6, 3:6] = rotated_you
        new_opp[3:6, 3:6] = rotated_opp
    
    return new_you, new_opp

def evaluate_board(you_board: np.ndarray, opp_board: np.ndarray) -> float:
    # Count potential 5-in-a-row lines for each player
    you_score = count_lines(you_board)
    opp_score = count_lines(opp_board)
    
    return you_score - opp_score

def count_lines(board: np.ndarray) -> int:
    score = 0
    
    # Check horizontal
    for r in range(6):
        for c in range(2):
            line = board[r, c:c+5]
            if np.sum(line) > 0 and np.sum(line) == np.sum(board[r, c:c+5]):
                score += np.sum(line) ** 2
    
    # Check vertical
    for c in range(6):
        for r in range(2):
            line = board[r:r+5, c]
            if np.sum(line) > 0 and np.sum(line) == np.sum(board[r:r+5, c]):
                score += np.sum(line) ** 2
    
    # Check diagonal (top-left to bottom-right)
    for r in range(2):
        for c in range(2):
            line = [board[r+i, c+i] for i in range(5)]
            if sum(line) > 0 and sum(line) == sum([board[r+i, c+i] for i in range(5)]):
                score += sum(line) ** 2
    
    # Check diagonal (bottom-left to top-right)
    for r in range(5, 0, -1):
        for c in range(2):
            line = [board[r-i, c+i] for i in range(5)]
            if sum(line) > 0 and sum(line) == sum([board[r-i, c+i] for i in range(5)]):
                score += sum(line) ** 2
    
    return score

def minimax(you_board: np.ndarray, opp_board: np.ndarray, depth: int, alpha: float, beta: float, maximizing: bool) -> str:
    if depth == 0:
        return None
    
    possible_moves = get_possible_moves(you_board, opp_board)
    
    if maximizing:
        max_eval = -np.inf
        best_move = possible_moves[0]
        
        for move in possible_moves:
            row, col, quad, dir = parse_move(move)
            new_you, new_opp = apply_move(you_board, opp_board, row, col, quad, dir)
            
            if has_five_in_a_row(new_you):
                return move
            
            if depth > 1:
                result = minimax(new_opp, new_you, depth-1, alpha, beta, False)
                if result is not None:
                    eval = -evaluate_board(new_opp, new_you)
                else:
                    eval = evaluate_board(new_you, new_opp)
            else:
                eval = evaluate_board(new_you, new_opp)
            
            if eval > max_eval:
                max_eval = eval
                best_move = move
            
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        
        return best_move
    else:
        min_eval = np.inf
        best_move = possible_moves[0]
        
        for move in possible_moves:
            row, col, quad, dir = parse_move(move)
            new_you, new_opp = apply_move(you_board, opp_board, row, col, quad, dir)
            
            if has_five_in_a_row(new_opp):
                return move
            
            if depth > 1:
                result = minimax(new_opp, new_you, depth-1, alpha, beta, True)
                if result is not None:
                    eval = evaluate_board(new_opp, new_you)
                else:
                    eval = -evaluate_board(new_you, new_opp)
            else:
                eval = -evaluate_board(new_you, new_opp)
            
            if eval < min_eval:
                min_eval = eval
                best_move = move
            
            beta = min(beta, eval)
            if beta <= alpha:
                break
        
        return best_move
