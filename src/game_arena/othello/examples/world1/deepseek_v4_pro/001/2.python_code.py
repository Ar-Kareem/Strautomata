
import numpy as np
from typing import Tuple, List, Optional

# Pre-computed direction vectors
DIRECTIONS = np.array([[-1, -1], [-1, 0], [-1, 1],
                        [0, -1],           [0, 1],
                        [1, -1],  [1, 0],  [1, 1]])

# Corner positions
CORNERS = [(0, 0), (0, 7), (7, 0), (7, 7)]

# Corner-adjacent squares (bad to play early)
CORNER_ADJACENT = {
    (0, 0): [(0, 1), (1, 0), (1, 1)],
    (0, 7): [(0, 6), (1, 6), (1, 7)],
    (7, 0): [(6, 0), (6, 1), (7, 1)],
    (7, 7): [(6, 6), (6, 7), (7, 6)]
}

# Edge positions (excluding corners)
EDGES = [(0, j) for j in range(1, 7)] + \
        [(7, j) for j in range(1, 7)] + \
        [(i, 0) for i in range(1, 7)] + \
        [(i, 7) for i in range(1, 7)]

# Weight matrix for positional evaluation
POSITION_WEIGHTS = np.array([
    [100, -20,  10,   5,   5,  10, -20, 100],
    [-20, -50,  -2,  -2,  -2,  -2, -50, -20],
    [ 10,  -2,  -1,  -1,  -1,  -1,  -2,  10],
    [  5,  -2,  -1,  -1,  -1,  -1,  -2,   5],
    [  5,  -2,  -1,  -1,  -1,  -1,  -2,   5],
    [ 10,  -2,  -1,  -1,  -1,  -1,  -2,  10],
    [-20, -50,  -2,  -2,  -2,  -2, -50, -20],
    [100, -20,  10,   5,   5,  10, -20, 100]
], dtype=np.float64)


def get_legal_moves(you: np.ndarray, opponent: np.ndarray) -> List[Tuple[int, int]]:
    """Return list of all legal moves as (row, col) tuples."""
    empty = (you == 0) & (opponent == 0)
    legal = []
    
    # Check each empty cell
    for r, c in zip(*np.where(empty)):
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < 8 and 0 <= nc < 8):
                continue
            if opponent[nr, nc] == 0:
                continue
            
            # Follow the line
            nr, nc = nr + dr, nc + dc
            while 0 <= nr < 8 and 0 <= nc < 8:
                if you[nr, nc] == 1:
                    legal.append((r, c))
                    break
                elif opponent[nr, nc] == 0:
                    break
                nr, nc = nr + dr, nc + dc
            else:
                continue
            
            # Break out of direction loop if move already found
            if (r, c) in legal:
                break
    
    return list(set(legal))


def apply_move(you: np.ndarray, opponent: np.ndarray, move: Tuple[int, int]) -> Tuple[np.ndarray, np.ndarray]:
    """Apply a move and return new board states. Assumes move is legal."""
    r, c = move
    new_you = you.copy()
    new_opponent = opponent.copy()
    new_you[r, c] = 1
    
    for dr, dc in DIRECTIONS:
        to_flip = []
        nr, nc = r + dr, c + dc
        
        while 0 <= nr < 8 and 0 <= nc < 8 and new_opponent[nr, nc] == 1:
            to_flip.append((nr, nc))
            nr, nc = nr + dr, nc + dc
        
        if 0 <= nr < 8 and 0 <= nc < 8 and new_you[nr, nc] == 1:
            for fr, fc in to_flip:
                new_you[fr, fc] = 1
                new_opponent[fr, fc] = 0
    
    return new_you, new_opponent


def evaluate_board(you: np.ndarray, opponent: np.ndarray) -> float:
    """Heuristic evaluation function."""
    # Count pieces
    my_count = np.sum(you)
    opp_count = np.sum(opponent)
    total = my_count + opp_count
    
    # Game phase: early (< 20 pieces), mid (20-50), late (> 50)
    if total < 20:
        # Early game: focus on mobility and position
        my_moves = len(get_legal_moves(you, opponent))
        opp_moves = len(get_legal_moves(opponent, you))
        mobility_score = 10 * (my_moves - opp_moves) if (my_moves + opp_moves) > 0 else 0
        
        # Positional score
        pos_score = np.sum(POSITION_WEIGHTS * you) - np.sum(POSITION_WEIGHTS * opponent)
        
        return mobility_score + 0.5 * pos_score
    
    elif total < 50:
        # Mid game: balance mobility, corners, and pieces
        my_moves = len(get_legal_moves(you, opponent))
        opp_moves = len(get_legal_moves(opponent, you))
        mobility_score = 5 * (my_moves - opp_moves) if (my_moves + opp_moves) > 0 else 0
        
        # Corner ownership
        corner_score = 0
        for cr, cc in CORNERS:
            if you[cr, cc] == 1:
                corner_score += 25
            elif opponent[cr, cc] == 1:
                corner_score -= 25
        
        # Positional score
        pos_score = np.sum(POSITION_WEIGHTS * you) - np.sum(POSITION_WEIGHTS * opponent)
        
        # Disc count
        disc_diff = my_count - opp_count
        
        return mobility_score + 0.3 * corner_score + 0.3 * pos_score + 0.1 * disc_diff
    
    else:
        # End game: maximize disc count
        return my_count - opp_count


def minimax(you: np.ndarray, opponent: np.ndarray, depth: int, alpha: float, beta: float, 
            maximizing: bool) -> float:
    """Minimax with alpha-beta pruning."""
    if depth == 0:
        return evaluate_board(you, opponent)
    
    if maximizing:
        moves = get_legal_moves(you, opponent)
        if not moves:
            # Check if opponent also has no moves (game over)
            if not get_legal_moves(opponent, you):
                my_count = np.sum(you)
                opp_count = np.sum(opponent)
                if my_count > opp_count:
                    return 10000
                elif my_count < opp_count:
                    return -10000
                else:
                    return 0
            # Pass turn
            return minimax(opponent, you, depth - 1, alpha, beta, False)
        
        max_eval = -float('inf')
        for move in moves:
            new_you, new_opp = apply_move(you, opponent, move)
            eval_score = minimax(new_opp, new_you, depth - 1, alpha, beta, False)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        moves = get_legal_moves(you, opponent)
        if not moves:
            if not get_legal_moves(opponent, you):
                my_count = np.sum(you)
                opp_count = np.sum(opponent)
                if my_count > opp_count:
                    return 10000
                elif my_count < opp_count:
                    return -10000
                else:
                    return 0
            return minimax(opponent, you, depth - 1, alpha, beta, True)
        
        min_eval = float('inf')
        for move in moves:
            new_you, new_opp = apply_move(you, opponent, move)
            eval_score = minimax(new_opp, new_you, depth - 1, alpha, beta, True)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """Return the best move as a string in algebraic notation."""
    moves = get_legal_moves(you, opponent)
    
    if not moves:
        return "pass"
    
    # Determine search depth based on remaining empty squares
    empty_count = np.sum((you == 0) & (opponent == 0))
    if empty_count > 40:
        depth = 3
    elif empty_count > 30:
        depth = 4
    elif empty_count > 20:
        depth = 5
    elif empty_count > 12:
        depth = 6
    else:
        depth = 8  # Perfect play in endgame
    
    # Ensure we don't exceed time by capping depth
    depth = min(depth, 8)
    
    best_move = None
    best_score = -float('inf')
    
    for move in moves:
        new_you, new_opp = apply_move(you, opponent, move)
        score = minimax(new_opp, new_you, depth - 1, -float('inf'), float('inf'), False)
        
        if score > best_score:
            best_score = score
            best_move = move
    
    if best_move is None:
        best_move = moves[0]
    
    # Convert to algebraic notation
    r, c = best_move
    col_letter = chr(ord('a') + c)
    row_number = str(r + 1)
    return f"{col_letter}{row_number}"
