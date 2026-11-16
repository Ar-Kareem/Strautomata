
import numpy as np
import time

# Positional weights for evaluation
WEIGHTS = np.array([
    [120, -20, 20,  5,  5, 20, -20, 120],
    [-20, -40, -5, -5, -5, -5, -40, -20],
    [ 20,  -5, 15,  3,  3, 15,  -5,  20],
    [  5,  -5,  3,  3,  3,  3,  -5,   5],
    [  5,  -5,  3,  3,  3,  3,  -5,   5],
    [ 20,  -5, 15,  3,  3, 15,  -5,  20],
    [-20, -40, -5, -5, -5, -5, -40, -20],
    [120, -20, 20,  5,  5, 20, -20, 120]
])

DIRECTIONS = [(-1,-1), (-1,0), (-1,1),
              (0,-1),          (0,1),
              (1,-1),  (1,0), (1,1)]

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    start_time = time.time()
    max_depth = 4  # Initial search depth
    remaining_moves = 64 - (np.sum(you) + np.sum(opponent))
    
    # Increase depth in endgame
    if remaining_moves < 12:
        max_depth = 6
    
    legal_moves = get_legal_moves(you, opponent)
    if not legal_moves:
        return "pass"
    
    # Order moves by importance (corners first)
    legal_moves = sorted(legal_moves, key=lambda move: -WEIGHTS[move[0]][move[1]])
    
    best_move = None
    best_score = -float('inf')
    
    # Iterative deepening with time management
    for move in legal_moves:
        if time.time() - start_time > 0.8:  # Reserve time for final decision
            break
            
        new_you, new_opp = make_move(you, opponent, move)
        score = -alpha_beta(new_opp, new_you, max_depth-1, -float('inf'), float('inf'), False)
        
        if score > best_score:
            best_score = score
            best_move = move
    
    if best_move is None:  # Time ran out, pick first legal move
        best_move = legal_moves[0]
    
    return f"{chr(best_move[1]+97)}{best_move[0]+1}"

def alpha_beta(you, opponent, depth, alpha, beta, maximizing_player):
    if depth == 0:
        return evaluate_position(you, opponent)
    
    legal_moves = get_legal_moves(you, opponent)
    
    if not legal_moves:
        if not get_legal_moves(opponent, you):  # Game over
            return np.sum(you) - np.sum(opponent)
        return -alpha_beta(opponent, you, depth-1, -beta, -alpha, not maximizing_player)
    
    if maximizing_player:
        value = -float('inf')
        for move in legal_moves:
            new_you, new_opp = make_move(you, opponent, move)
            value = max(value, -alpha_beta(new_opp, new_you, depth-1, -beta, -alpha, False))
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    else:
        value = float('inf')
        for move in legal_moves:
            new_you, new_opp = make_move(you, opponent, move)
            value = min(value, -alpha_beta(new_opp, new_you, depth-1, -beta, -alpha, True))
            beta = min(beta, value)
            if beta <= alpha:
                break
        return value

def evaluate_position(you, opponent):
    # Material count with weights
    score = np.sum(you * WEIGHTS) - np.sum(opponent * WEIGHTS)
    
    # Mobility
    your_moves = len(get_legal_moves(you, opponent))
    opp_moves = len(get_legal_moves(opponent, you))
    if your_moves + opp_moves != 0:
        score += 10 * (your_moves - opp_moves) / (your_moves + opp_moves)
    
    # Corner control
    corners = [(0,0), (0,7), (7,0), (7,7)]
    your_corners = sum(you[c] for c in corners)
    opp_corners = sum(opponent[c] for c in corners)
    score += 50 * (your_corners - opp_corners)
    
    return score

def get_legal_moves(you, opponent):
    legal_moves = []
    for r in range(8):
        for c in range(8):
            if you[r][c] == 0 and opponent[r][c] == 0:
                for dr, dc in DIRECTIONS:
                    if check_direction(you, opponent, r, c, dr, dc):
                        legal_moves.append((r, c))
                        break
    return legal_moves

def check_direction(you, opponent, r, c, dr, dc):
    nr, nc = r + dr, c + dc
    if nr < 0 or nr >= 8 or nc < 0 or nc >= 8 or opponent[nr][nc] != 1:
        return False
    
    while True:
        nr += dr
        nc += dc
        if nr < 0 or nr >= 8 or nc < 0 or nc >= 8:
            return False
        if you[nr][nc] == 1:
            return True
        if opponent[nr][nc] == 0:
            return False

def make_move(you, opponent, move):
    r, c = move
    new_you = you.copy()
    new_opp = opponent.copy()
    new_you[r][c] = 1
    
    for dr, dc in DIRECTIONS:
        nr, nc = r + dr, c + dc
        to_flip = []
        while 0 <= nr < 8 and 0 <= nc < 8 and new_opp[nr][nc] == 1:
            to_flip.append((nr, nc))
            nr += dr
            nc += dc
            if 0 <= nr < 8 and 0 <= nc < 8 and new_you[nr][nc] == 1:
                for flip_r, flip_c in to_flip:
                    new_you[flip_r][flip_c] = 1
                    new_opp[flip_r][flip_c] = 0
                break
    
    return new_you, new_opp
