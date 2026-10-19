
import numpy as np

DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

# Positional weights emphasizing corners and penalizing danger squares
WEIGHTS = np.array([
    [120, -20,  20,   5,   5,  20, -20, 120],
    [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
    [ 20,  -5,  15,   3,   3,  15,  -5,  20],
    [  5,  -5,   3,   3,   3,   3,  -5,   5],
    [  5,  -5,   3,   3,   3,   3,  -5,   5],
    [ 20,  -5,  15,   3,   3,  15,  -5,  20],
    [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
    [120, -20,  20,   5,   5,  20, -20, 120]
], dtype=np.int32)

def get_moves(you: np.ndarray, opp: np.ndarray):
    """Return list of legal moves (r, c) for player 'you'."""
    empty = 1 - you - opp
    moves = []
    for r in range(8):
        for c in range(8):
            if empty[r, c]:
                valid = False
                for dr, dc in DIRECTIONS:
                    nr, nc = r + dr, c + dc
                    # Check if adjacent has opponent
                    if 0 <= nr < 8 and 0 <= nc < 8 and opp[nr, nc]:
                        # Continue in direction
                        while 0 <= nr < 8 and 0 <= nc < 8 and opp[nr, nc]:
                            nr += dr
                            nc += dc
                        # Check if ended at own disc
                        if 0 <= nr < 8 and 0 <= nc < 8 and you[nr, nc]:
                            valid = True
                            break
                if valid:
                    moves.append((r, c))
    return moves

def make_move(you: np.ndarray, opp: np.ndarray, r: int, c: int):
    """Apply move (r,c) for 'you' and return new board states."""
    new_you = you.copy()
    new_opp = opp.copy()
    new_you[r, c] = 1
    
    for dr, dc in DIRECTIONS:
        nr, nc = r + dr, c + dc
        to_flip = []
        # Collect opponent discs
        while 0 <= nr < 8 and 0 <= nc < 8 and opp[nr, nc]:
            to_flip.append((nr, nc))
            nr += dr
            nc += dc
        # If line ends with own disc, flip collected
        if to_flip and 0 <= nr < 8 and 0 <= nc < 8 and you[nr, nc]:
            for rr, cc in to_flip:
                new_you[rr, cc] = 1
                new_opp[rr, cc] = 0
    return new_you, new_opp

def evaluate(you: np.ndarray, opp: np.ndarray):
    """Static evaluation from perspective of 'you'."""
    return int(np.sum(WEIGHTS * (you - opp)))

def alphabeta(you: np.ndarray, opp: np.ndarray, depth: int, alpha: int, beta: int):
    """Negamax alpha-beta search."""
    if depth == 0:
        return evaluate(you, opp)
    
    moves = get_moves(you, opp)
    
    if not moves:
        # Pass turn to opponent
        if get_moves(opp, you):
            return -alphabeta(opp, you, depth - 1, -beta, -alpha)
        else:
            # Game over
            diff = int(np.sum(you) - np.sum(opp))
            if diff > 0:
                return 100000 + diff
            elif diff < 0:
                return -100000 + diff
            else:
                return 0
    
    # Move ordering: corners first
    corners = {(0,0), (0,7), (7,0), (7,7)}
    moves.sort(key=lambda m: m not in corners)
    
    for r, c in moves:
        ny, no = make_move(you, opp, r, c)
        val = -alphabeta(no, ny, depth - 1, -beta, -alpha)
        if val >= beta:
            return beta
        if val > alpha:
            alpha = val
    return alpha

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """Main policy function."""
    moves = get_moves(you, opponent)
    
    if not moves:
        return "pass"
    
    # Determine search depth based on game phase
    total_discs = int(np.sum(you) + np.sum(opponent))
    empty_sq = 64 - total_discs
    
    if empty_sq > 50:
        depth = 4
    elif empty_sq > 20:
        depth = 5
    elif empty_sq > 12:
        depth = 6
    else:
        depth = 64  # Solve endgame
    
    # Move ordering for root
    corners = {(0,0), (0,7), (7,0), (7,7)}
    moves.sort(key=lambda m: m not in corners)
    
    best_move = moves[0]
    best_score = -1000000
    
    for r, c in moves:
        ny, no = make_move(you, opponent, r, c)
        score = -alphabeta(no, ny, depth - 1, -1000000, 1000000)
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    files = "abcdefgh"
    ranks = "12345678"
    return files[best_move[1]] + ranks[best_move[0]]
