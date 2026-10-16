
import numpy as np
import math
from typing import List, Tuple, Optional

# Direction vectors: 8 directions (row, col)
DIRECTIONS = [(-1,-1), (-1,0), (-1,1),
              (0,-1),           (0,1),
              (1,-1),  (1,0),   (1,1)]

# Corner and edge bonuses
CORNER_WEIGHT = 100
C_EDGE_WEIGHT = 50  # Adjacent to corner — usually bad if you take these
X_SQUARE_WEIGHT = 30  # X-squares: diagonal to corners — weak access to corner

# Positional weights matrix
WEIGHTS = np.array([
    [CORNER_WEIGHT, -X_SQUARE_WEIGHT, C_EDGE_WEIGHT,  C_EDGE_WEIGHT,  C_EDGE_WEIGHT, C_EDGE_WEIGHT, -X_SQUARE_WEIGHT, CORNER_WEIGHT],
    [-X_SQUARE_WEIGHT, -C_EDGE_WEIGHT,  1,              1,              1,           1,             -C_EDGE_WEIGHT,  -X_SQUARE_WEIGHT],
    [C_EDGE_WEIGHT,    1,              5,              5,              5,           5,             1,              C_EDGE_WEIGHT],
    [C_EDGE_WEIGHT,    1,              5,              5,              5,           5,             1,              C_EDGE_WEIGHT],
    [C_EDGE_WEIGHT,    1,              5,              5,              5,           5,             1,              C_EDGE_WEIGHT],
    [C_EDGE_WEIGHT,    1,              5,              5,              5,           5,             1,              C_EDGE_WEIGHT],
    [-X_SQUARE_WEIGHT, -C_EDGE_WEIGHT,  1,              1,              1,           1,             -C_EDGE_WEIGHT,  -X_SQUARE_WEIGHT],
    [CORNER_WEIGHT, -X_SQUARE_WEIGHT, C_EDGE_WEIGHT,  C_EDGE_WEIGHT,  C_EDGE_WEIGHT, C_EDGE_WEIGHT, -X_SQUARE_WEIGHT, CORNER_WEIGHT]
])

def is_on_board(r: int, c: int) -> bool:
    return 0 <= r < 8 and 0 <= c < 8

def get_flip_dirs(you: np.ndarray, opponent: np.ndarray, r: int, c: int) -> List[Tuple[int,int]]:
    """
    Returns the list of directions in which placing a disc at (r,c) would flip opponent discs.
    """
    flip_dirs = []
    for dr, dc in DIRECTIONS:
        nr, nc = r + dr, c + dc
        to_flip = []
        while is_on_board(nr, nc) and opponent[nr][nc] == 1:
            to_flip.append((nr, nc))
            nr += dr
            nc += dc
        if (is_on_board(nr, nc) and len(to_flip) > 0 and you[nr][nc] == 1):
            flip_dirs.append((dr, dc))
    return flip_dirs

def is_legal_move(you: np.ndarray, opponent: np.ndarray, r: int, c: int) -> bool:
    if you[r][c] == 1 or opponent[r][c] == 1:
        return False
    return len(get_flip_dirs(you, opponent, r, c)) > 0

def get_legal_moves(you: np.ndarray, opponent: np.ndarray) -> List[Tuple[int, int]]:
    moves = []
    for r in range(8):
        for c in range(8):
            if is_legal_move(you, opponent, r, c):
                moves.append((r, c))
    return moves

def make_move(you: np.ndarray, opponent: np.ndarray, r: int, c: int):
    """
    Returns a new you/opponent board pair after placing a disc at (r,c).
    """
    new_you = you.copy()
    new_opponent = opponent.copy()

    new_you[r][c] = 1
    for dr, dc in get_flip_dirs(you, opponent, r, c):
        nr, nc = r + dr, c + dc
        while new_opponent[nr][nc] == 1:
            new_opponent[nr][nc] = 0
            new_you[nr][nc] = 1
            nr += dr
            nc += dc

    return new_you, new_opponent

def evaluate(you: np.ndarray, opponent: np.ndarray) -> float:
    """
    Evaluate the board state from `you`'s perspective.
    """
    total = 0.0
    for r in range(8):
        for c in range(8):
            if you[r][c] == 1:
                total += WEIGHTS[r][c]
            elif opponent[r][c] == 1:
                total -= WEIGHTS[r][c]

    # Bonus for mobility (number of legal moves)
    my_moves = len(get_legal_moves(you, opponent))
    opp_moves = len(get_legal_moves(opponent, you))
    if my_moves + opp_moves > 0:
        total += 10 * (my_moves - opp_moves) / (my_moves + opp_moves)

    # Disc count bonus in late game
    total_discs = np.sum(you) + np.sum(opponent)
    if total_discs > 50:
        total += 2 * (np.sum(you) - np.sum(opponent))

    return total

def minimax(you: np.ndarray, opponent: np.ndarray, depth: int, alpha: float, beta: float, 
            maximizing: bool, orig_depth: int) -> float:
    if depth == 0:
        return evaluate(you, opponent)

    moves = get_legal_moves(you, opponent)
    if len(moves) == 0:
        # If no moves, opponent takes turn
        opp_moves = get_legal_moves(opponent, you)
        if len(opp_moves) == 0:
            return 1000 if np.sum(you) > np.sum(opponent) else -1000
        return minimax(opponent, you, depth-1, -beta, -alpha, not maximizing, orig_depth)

    # Move ordering: sort by evaluation after making the move (greedy)
    move_scores = []
    for r, c in moves:
        new_you, new_opp = make_move(you, opponent, r, c)
        score = evaluate(new_you, new_opp)
        move_scores.append((score, r, c))
    
    # Sort moves: descending if maximizing, ascending otherwise
    move_scores.sort(reverse=maximizing)

    if maximizing:
        max_eval = -math.inf
        for _, r, c in move_scores:
            new_you, new_opp = make_move(you, opponent, r, c)
            eval_score = minimax(new_opp, new_you, depth-1, alpha, beta, False, orig_depth)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break  # Beta cutoff
        return max_eval
    else:
        min_eval = math.inf
        for _, r, c in move_scores:
            new_you, new_opp = make_move(you, opponent, r, c)
            eval_score = minimax(new_opp, new_you, depth-1, alpha, beta, True, orig_depth)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break  # Alpha cutoff
        return min_eval

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    legal_moves = get_legal_moves(you, opponent)
    
    if not legal_moves:
        return "pass"
    
    total_discs = np.sum(you) + np.sum(opponent)
    
    # Adjust depth based on game phase
    if total_discs < 15:
        depth = 4
    elif total_discs < 45:
        depth = 6
    else:
        depth = 3  # Late game: faster to handle time, and evaluation is stronger
    
    # Try to sort moves by greedy evaluation first
    best_move = legal_moves[0]
    best_value = -math.inf

    # Move ordering based on immediate gain + position weight
    move_evals = []
    for r, c in legal_moves:
        score = WEIGHTS[r][c]
        flips = len(get_flip_dirs(you, opponent, r, c))
        move_evals.append((-(score + 2 * flips), r, c))  # negative for sorting by descending eval
    
    move_evals.sort()
    
    for _, r, c in move_evals:
        new_you, new_opponent = make_move(you, opponent, r, c)
        value = minimax(new_opponent, new_you, depth, -math.inf, math.inf, False, depth)
        
        if value > best_value:
            best_value = value
            best_move = (r, c)
    
    # Convert (r,c) to move string: r=0 -> '1', c=0 -> 'a'
    row_str = str(best_move[0] + 1)
    col_str = chr(ord('a') + best_move[1])
    return col_str + row_str
