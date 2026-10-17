
import numpy as np

# Static evaluation weights for Othello 8x8 board
WEIGHTS = np.array([
    [100, -20, 10,  5,  5, 10, -20, 100],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [ 10,  -2, -1, -1, -1, -1,  -2,  10],
    [  5,  -2, -1, -1, -1, -1,  -2,   5],
    [  5,  -2, -1, -1, -1, -1,  -2,   5],
    [ 10,  -2, -1, -1, -1, -1,  -2,  10],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [100, -20, 10,  5,  5, 10, -20, 100]
])

DIRECTIONS = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]

def get_legal_moves(you: np.ndarray, opponent: np.ndarray):
    """Returns list of legal move (r, c) tuples."""
    moves = []
    for r in range(8):
        for c in range(8):
            if you[r][c] == 1 or opponent[r][c] == 1:
                continue
            if is_valid_move(you, opponent, r, c):
                moves.append((r, c))
    return moves

def is_valid_move(you: np.ndarray, opponent: np.ndarray, r: int, c: int) -> bool:
    """Check if placing at (r,c) flips at least one opponent disc."""
    for dr, dc in DIRECTIONS:
        if check_direction(you, opponent, r, c, dr, dc):
            return True
    return False

def check_direction(you: np.ndarray, opponent: np.ndarray, r: int, c: int, dr: int, dc: int) -> bool:
    """Check if this direction results in a flip."""
    nr, nc = r + dr, c + dc
    found_opponent = False
    while 0 <= nr < 8 and 0 <= nc < 8:
        if opponent[nr][nc] == 1:
            found_opponent = True
        elif you[nr][nc] == 1:
            return found_opponent
        else:
            break
        nr += dr
        nc += dc
    return False

def evaluate(you: np.ndarray, opponent: np.ndarray) -> float:
    """Evaluate board state from your perspective."""
    your_score = 0
    opp_score = 0
    for r in range(8):
        for c in range(8):
            if you[r][c] == 1:
                your_score += WEIGHTS[r][c]
            elif opponent[r][c] == 1:
                opp_score += WEIGHTS[r][c]
    return your_score - opp_score

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """Return the best move based on greedy evaluation."""
    legal_moves = get_legal_moves(you, opponent)
    
    if not legal_moves:
        return "pass"
    
    best_move = legal_moves[0]
    best_score = float('-inf')
    
    for r, c in legal_moves:
        # Simulate move
        new_you = you.copy()
        new_opponent = opponent.copy()
        
        # Apply flips
        new_you[r][c] = 1
        for dr, dc in DIRECTIONS:
            if check_direction(opponent, you, r, c, dr, dc):
                nr, nc = r + dr, c + dc
                while opponent[nr][nc] == 1:
                    new_opponent[nr][nc] = 0
                    new_you[nr][nc] = 1
                    nr += dr
                    nc += dc
        
        # Evaluate board
        score = evaluate(new_you, new_opponent)
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    # Convert (r, c) to algebraic notation
    col_letter = 'abcdefgh'[best_move[1]]
    row_digit = str(best_move[0] + 1)
    return col_letter + row_digit
