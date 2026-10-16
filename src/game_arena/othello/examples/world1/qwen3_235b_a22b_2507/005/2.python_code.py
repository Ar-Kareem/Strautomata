
import numpy as np
from typing import List, Tuple
import copy

# Predefined direction vectors (row, col): 8 directions
DIRECTIONS = [(-1,-1), (-1,0), (-1,1),
              (0,-1),           (0,1),
              (1,-1),  (1,0),   (1,1)]

# Heuristic board weights: corners and edges prioritized
WEIGHTS = np.array([
    [500, -150, 50, 30, 30, 50, -150, 500],
    [-150, -250, 10, 10, 10, 10, -250, -150],
    [50, 10, 20, 15, 15, 20, 10, 50],
    [30, 10, 15, 10, 10, 15, 10, 30],
    [30, 10, 15, 10, 10, 15, 10, 30],
    [50, 10, 20, 15, 15, 20, 10, 50],
    [-150, -250, 10, 10, 10, 10, -250, -150],
    [500, -150, 50, 30, 30, 50, -150, 500]
])

def get_legal_moves(you: np.ndarray, opponent: np.ndarray) -> List[Tuple[int, int]]:
    """Return list of legal moves as (r, c) tuples."""
    moves = []
    for r in range(8):
        for c in range(8):
            if you[r][c] == 0 and opponent[r][c] == 0:
                if is_valid_move(you, opponent, r, c):
                    moves.append((r, c))
    return moves

def is_valid_move(you: np.ndarray, opponent: np.ndarray, r: int, c: int) -> bool:
    """Check if placing at (r,c) flips at least one opponent disc."""
    for dr, dc in DIRECTIONS:
        if will_flip_in_direction(you, opponent, r, c, dr, dc):
            return True
    return False

def will_flip_in_direction(you: np.ndarray, opponent: np.ndarray, r: int, c: int, dr: int, dc: int) -> bool:
    """Check if move (r,c) flips opponent discs in direction (dr,dc)."""
    nr, nc = r + dr, c + dc
    if not (0 <= nr < 8 and 0 <= nc < 8):
        return False
    if opponent[nr][nc] == 0:
        return False
    # Traverse in direction
    while 0 <= nr < 8 and 0 <= nc < 8:
        if opponent[nr][nc] == 1:
            nr += dr
            nc += dc
        elif you[nr][nc] == 1:
            return (nr - dr, nc - dc) != (r + dr, c + dc)  # flipped at least one
        else:  # empty
            return False
    return False

def make_move(you: np.ndarray, opponent: np.ndarray, r: int, c: int):
    """Apply move (r,c) to both boards (modifies in place)."""
    to_flip = []
    for dr, dc in DIRECTIONS:
        nr, nc = r + dr, c + dc
        flips = []
        while 0 <= nr < 8 and 0 <= nc < 8 and opponent[nr][nc] == 1:
            flips.append((nr, nc))
            nr += dr
            nc += dc
        if 0 <= nr < 8 and 0 <= nc < 8 and you[nr][nc] == 1 and flips:
            to_flip.extend(flips)
    # Flip discs
    for fr, fc in to_flip:
        opponent[fr][fc] = 0
        you[fr][fc] = 1
    # Place new disc
    you[r][c] = 1

def evaluate(you: np.ndarray, opponent: np.ndarray) -> float:
    """Heuristic evaluation of the board state."""
    total_discs = np.sum(you) + np.sum(opponent)
    
    if total_discs > 50:  # Late game: prioritize disc count
        return float(np.sum(you) - np.sum(opponent))
    
    # Positional weight score
    pos_score = np.sum(you * WEIGHTS) - np.sum(opponent * WEIGHTS)
    
    # Mobility: count legal moves available
    my_moves = len(get_legal_moves(you, opponent))
    opp_moves = len(get_legal_moves(opponent, you))  # swap roles
    if my_moves + opp_moves == 0:
        mobility = 0
    else:
        mobility = 100 * (my_moves - opp_moves) / (my_moves + opp_moves)
    
    # Disc count is less important early, but still a factor
    disc_count = np.sum(you) - np.sum(opponent)
    
    # Combine factors
    score = pos_score + 2 * mobility + 0.1 * disc_count
    return score

def minimax(you: np.ndarray, opponent: np.ndarray, depth: int, alpha: float, beta: float, maximizing: bool) -> float:
    """Alpha-beta pruning minimax for evaluation."""
    if depth == 0:
        return evaluate(you, opponent)
    
    moves = get_legal_moves(you, opponent)
    if not moves:
        # If no moves, pass and let opponent play
        if not get_legal_moves(opponent, you):
            # Game over
            return evaluate(you, opponent)
        else:
            return -minimax(opponent, you, depth - 1, -beta, -alpha, not maximizing)
    
    if maximizing:
        max_eval = -np.inf
        for r, c in moves:
            # Copy boards
            you_copy = you.copy()
            opp_copy = opponent.copy()
            make_move(you_copy, opp_copy, r, c)
            eval_score = -minimax(opp_copy, you_copy, depth - 1, -beta, -alpha, False)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = np.inf
        for r, c in moves:
            you_copy = you.copy()
            opp_copy = opponent.copy()
            make_move(you_copy, opp_copy, r, c)
            eval_score = -minimax(opp_copy, you_copy, depth - 1, -beta, -alpha, True)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """Main policy function: select best move using minimax with depth control."""
    moves = get_legal_moves(you, opponent)
    if not moves:
        return "pass"
    
    total_discs = np.sum(you) + np.sum(opponent)
    # Adjust search depth based on game phase
    if total_discs < 10:
        depth = 2  # Early game: positional
    elif total_discs < 50:
        depth = 2  # Mid game: balance
    else:
        depth = 3  # Late game: deeper search
    
    if len(moves) == 1:
        r, c = moves[0]
        return f"{chr(97 + c)}{r + 1}"
    
    # Evaluate all moves with minimax
    best_score = -np.inf
    best_move = moves[0]
    
    for r, c in moves:
        you_copy = you.copy()
        opp_copy = opponent.copy()
        make_move(you_copy, opp_copy, r, c)
        score = -minimax(opp_copy, you_copy, depth - 1, -np.inf, np.inf, False)
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    r, c = best_move
    return f"{chr(97 + c)}{r + 1}"
