
import numpy as np
from typing import List, Tuple

# Constants for the board size
ROWS, COLS = 8, 8

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    # Create board representation
    board = np.zeros((ROWS, COLS), dtype=int)
    
    # Place pieces on board: 1 for me, -1 for opponent, 0 for empty
    for r, c in me:
        board[r, c] = 1 if color == 'w' else -1
    for r, c in opp:
        board[r, c] = -1 if color == 'w' else 1

    # Determine direction of movement
    direction = -1 if color == 'w' else 1  # white moves up (row+1), black moves down (row-1)
    
    # Find potential moves
    moves = []
    for r, c in me:
        # Forward move
        nr = r + direction
        if 0 <= nr < ROWS and board[nr, c] == 0:
            moves.append(((r, c), (nr, c)))
            # Check if this move wins
            if nr == (0 if color == 'w' else 7):
                return ((r, c), (nr, c))
        
        # Diagonal captures
        for dc in [-1, 1]:
            nc = c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                if board[nr, nc] == (-1 if color == 'w' else 1):
                    moves.append(((r, c), (nr, nc)))
                    # Check if this move wins
                    if nr == (0 if color == 'w' else 7):
                        return ((r, c), (nr, nc))

    # If no immediate winning moves, prioritize moves
    if not moves:
        # Fallback: should not happen in valid state
        return ((0, 0), (0, 0))

    # Simple evaluation function
    best_move = None
    best_score = -float('inf')
    
    for move in moves:
        score = evaluate_move(board, move, color, direction)
        if score > best_score:
            best_score = score
            best_move = move

    return best_move

def evaluate_move(board: np.ndarray, move: Tuple[Tuple[int, int], Tuple[int, int]], 
                  color: str, direction: int) -> float:
    from_pos, to_pos = move
    from_r, from_c = from_pos
    to_r, to_c = to_pos
    
    score = 0.0
    
    # Prefer advancing pieces (closer to opponent's home row is better)
    progress = abs(to_r - (7 if color == 'w' else 0))
    score += (7 - progress) * 10
    
    # Prefer captures
    if board[to_r, to_c] != 0:
        score += 50
    
    # Prefer central columns
    score += (4 - abs(to_c - 3.5)) * 2
    
    # Prefer moving pieces that are further back
    score += (7 - abs(from_r - (0 if color == 'w' else 7))) * 0.5
    
    return score
