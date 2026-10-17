
import numpy as np
from typing import Tuple, List, Optional
import copy

# Board size constants
BOARD_SIZE = 6
QUAD_SIZE = 3
ROWS, COLS = BOARD_SIZE, BOARD_SIZE
QUADS = 4

# Directions for checking lines (horizontal, vertical, diagonal)
DIRECTIONS = [
    (0, 1),   # horizontal
    (1, 0),   # vertical
    (1, 1),   # diagonal down-right
    (1, -1)   # diagonal down-left
]

def get_quadrant_cells(quad: int) -> List[Tuple[int, int]]:
    """Get all cells in a quadrant."""
    if quad == 0:  # top-left
        return [(r, c) for r in range(3) for c in range(3)]
    elif quad == 1:  # top-right
        return [(r, c) for r in range(3) for c in range(3, 6)]
    elif quad == 2:  # bottom-left
        return [(r, c) for r in range(3, 6) for c in range(3)]
    elif quad == 3:  # bottom-right
        return [(r, c) for r in range(3, 6) for c in range(3, 6)]
    else:
        raise ValueError(f"Invalid quadrant: {quad}")

def rotate_quadrant(board: np.ndarray, quad: int, direction: str) -> np.ndarray:
    """Rotate a quadrant 90 degrees."""
    new_board = board.copy()
    
    # Get cells in the quadrant
    cells = get_quadrant_cells(quad)
    
    # Extract quadrant values
    quad_vals = np.zeros((QUAD_SIZE, QUAD_SIZE))
    for r, c in cells:
        quad_vals[r % QUAD_SIZE, c % QUAD_SIZE] = board[r, c]
    
    # Rotate
    if direction == 'L':  # 90 degrees anticlockwise
        rotated = np.rot90(quad_vals, k=1)
    elif direction == 'R':  # 90 degrees clockwise
        rotated = np.rot90(quad_vals, k=3)
    else:
        raise ValueError(f"Invalid direction: {direction}")
    
    # Place back
    for r, c in cells:
        new_board[r, c] = rotated[r % QUAD_SIZE, c % QUAD_SIZE]
    
    return new_board

def check_win(board: np.ndarray) -> bool:
    """Check if the player has 5 in a row."""
    for r in range(ROWS):
        for c in range(COLS):
            if board[r, c] == 0:
                continue
            
            for dr, dc in DIRECTIONS:
                count = 1
                nr, nc = r + dr, c + dc
                
                while 0 <= nr < ROWS and 0 <= nc < COLS and board[nr, nc] == 1:
                    count += 1
                    nr, nc = nr + dr, nc + dc
                
                if count >= 5:
                    return True
    
    return False

def get_empty_cells(you: np.ndarray, opponent: np.ndarray) -> List[Tuple[int, int]]:
    """Get all empty cells."""
    empty = []
    for r in range(ROWS):
        for c in range(COLS):
            if you[r, c] == 0 and opponent[r, c] == 0:
                empty.append((r, c))
    return empty

def evaluate_position(you: np.ndarray, opponent: np.ndarray) -> int:
    """Evaluate position heuristic."""
    score = 0
    
    # Check for wins
    if check_win(you):
        return 10000
    if check_win(opponent):
        return -10000
    
    # Count potential lines
    for r in range(ROWS):
        for c in range(COLS):
            # Your pieces
            if you[r, c] == 1:
                for dr, dc in DIRECTIONS:
                    # Count consecutive pieces in this direction
                    count = 1
                    nr, nc = r + dr, c + dc
                    while 0 <= nr < ROWS and 0 <= nc < COLS and you[nr, nc] == 1:
                        count += 1
                        nr, nc = nr + dr, nc + dc
                    
                    if count >= 4:
                        score += count * 100
                    elif count == 3:
                        score += 50
                    else:
                        score += count * 10
            
            # Opponent pieces
            elif opponent[r, c] == 1:
                for dr, dc in DIRECTIONS:
                    count = 1
                    nr, nc = r + dr, c + dc
                    while 0 <= nr < ROWS and 0 <= nc < COLS and opponent[nr, nc] == 1:
                        count += 1
                        nr, nc = nr + dr, nc + dc
                    
                    if count >= 4:
                        score -= count * 100
                    elif count == 3:
                        score -= 50
                    else:
                        score -= count * 10
    
    return score

def is_terminal(you: np.ndarray, opponent: np.ndarray) -> bool:
    """Check if game is over."""
    return check_win(you) or check_win(opponent)

def minimax(you: np.ndarray, opponent: np.ndarray, depth: int, alpha: int, beta: int, maximizing: bool) -> int:
    """Minimax with alpha-beta pruning."""
    if depth == 0 or is_terminal(you, opponent):
        return evaluate_position(you, opponent)
    
    empty_cells = get_empty_cells(you, opponent)
    
    if maximizing:
        max_eval = -float('inf')
        for r, c in empty_cells:
            # Place piece
            new_you = you.copy()
            new_you[r, c] = 1
            
            # Try all rotations
            for quad in range(QUADS):
                for direction in ['L', 'R']:
                    # Rotate
                    new_you_rot = rotate_quadrant(new_you, quad, direction)
                    new_opp_rot = rotate_quadrant(opponent, quad, direction)
                    
                    eval = minimax(new_you_rot, new_opp_rot, depth - 1, alpha, beta, False)
                    max_eval = max(max_eval, eval)
                    alpha = max(alpha, eval)
                    
                    if beta <= alpha:
                        break
                if beta <= alpha:
                    break
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for r, c in empty_cells:
            # Place piece for opponent
            new_opp = opponent.copy()
            new_opp[r, c] = 1
            
            # Try all rotations
            for quad in range(QUADS):
                for direction in ['L', 'R']:
                    new_you_rot = rotate_quadrant(you, quad, direction)
                    new_opp_rot = rotate_quadrant(new_opp, quad, direction)
                    
                    eval = minimax(new_you_rot, new_opp_rot, depth - 1, alpha, beta, True)
                    min_eval = min(min_eval, eval)
                    beta = min(beta, eval)
                    
                    if beta <= alpha:
                        break
                if beta <= alpha:
                    break
            if beta <= alpha:
                break
        return min_eval

def policy(you, opponent) -> str:
    """Main policy function."""
    # Convert to numpy arrays
    you_np = np.array(you)
    opponent_np = np.array(opponent)
    
    empty_cells = get_empty_cells(you_np, opponent_np)
    
    if not empty_cells:
        # This should not happen as per problem constraints
        return "1,1,0,L"
    
    # Opening book for first few moves
    if len(empty_cells) >= 30:
        # Prefer center positions in opening
        center_cells = [(2, 2), (2, 3), (3, 2), (3, 3)]
        for r, c in center_cells:
            if 0 <= r < ROWS and 0 <= c < COLS and you_np[r, c] == 0 and opponent_np[r, c] == 0:
                return f"{r+1},{c+1},0,L"
    
    # Minimax search
    best_score = -float('inf')
    best_move = None
    
    # Try all possible moves
    for r, c in empty_cells:
        for quad in range(QUADS):
            for direction in ['L', 'R']:
                # Make move
                new_you = you_np.copy()
                new_you[r, c] = 1
                
                # Rotate
                new_you_rot = rotate_quadrant(new_you, quad, direction)
                new_opp_rot = rotate_quadrant(opponent_np, quad, direction)
                
                # Evaluate
                score = minimax(new_you_rot, new_opp_rot, 2, -float('inf'), float('inf'), False)
                
                if score > best_score:
                    best_score = score
                    best_move = (r, c, quad, direction)
    
    if best_move is None:
        # Fallback to first available move
        r, c = empty_cells[0]
        return f"{r+1},{c+1},0,L"
    
    r, c, quad, direction = best_move
    return f"{r+1},{c+1},{quad},{direction}"
