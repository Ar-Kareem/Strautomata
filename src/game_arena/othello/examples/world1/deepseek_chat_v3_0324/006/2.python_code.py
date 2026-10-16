
import numpy as np
from collections import defaultdict

# Precomputed positional weights
POSITION_WEIGHTS = np.array([
    [100, -20, 10, 5, 5, 10, -20, 100],
    [-20, -30, -5, -5, -5, -5, -30, -20],
    [10, -5, 2, 2, 2, 2, -5, 10],
    [5, -5, 2, 0, 0, 2, -5, 5],
    [5, -5, 2, 0, 0, 2, -5, 5],
    [10, -5, 2, 2, 2, 2, -5, 10],
    [-20, -30, -5, -5, -5, -5, -30, -20],
    [100, -20, 10, 5, 5, 10, -20, 100]
])

DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1),
              (0, -1),          (0, 1),
              (1, -1),  (1, 0), (1, 1)]

def is_valid_move(board, opponent, r, c):
    if board[r][c] != 0 or opponent[r][c] != 0:
        return False
    
    for dr, dc in DIRECTIONS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 8 and 0 <= nc < 8 and opponent[nr][nc] == 1:
            while 0 <= nr < 8 and 0 <= nc < 8 and opponent[nr][nc] == 1:
                nr += dr
                nc += dc
            if 0 <= nr < 8 and 0 <= nc < 8 and board[nr][nc] == 1:
                return True
    return False

def get_valid_moves(board, opponent):
    moves = []
    for r in range(8):
        for c in range(8):
            if is_valid_move(board, opponent, r, c):
                moves.append((r, c))
    return moves

def make_move(board, opponent, r, c):
    new_board = board.copy()
    new_opponent = opponent.copy()
    new_board[r][c] = 1
    flipped = 0
    
    for dr, dc in DIRECTIONS:
        to_flip = []
        nr, nc = r + dr, c + dc
        while 0 <= nr < 8 and 0 <= nc < 8 and new_opponent[nr][nc] == 1:
            to_flip.append((nr, nc))
            nr += dr
            nc += dc
        if 0 <= nr < 8 and 0 <= nc < 8 and new_board[nr][nc] == 1 and to_flip:
            flipped += len(to_flip)
            for flip_r, flip_c in to_flip:
                new_board[flip_r][flip_c] = 1
                new_opponent[flip_r][flip_c] = 0
    
    return new_board, new_opponent, flipped

def evaluate_position(board, opponent, move=None):
    # Material count
    my_discs = np.sum(board)
    opp_discs = np.sum(opponent)
    
    # Positional advantage
    my_pos = np.sum(board * POSITION_WEIGHTS)
    opp_pos = np.sum(opponent * POSITION_WEIGHTS)
    
    # Mobility
    my_moves = len(get_valid_moves(board, opponent))
    opp_moves = len(get_valid_moves(opponent, board))
    
    # Corner control
    corners = [(0,0), (0,7), (7,0), (7,7)]
    my_corners = sum(board[c] for c in corners)
    opp_corners = sum(opponent[c] for c in corners)
    
    # Edge control
    edges = [(0,c) for c in range(8)] + [(7,c) for c in range(8)] + \
            [(r,0) for r in range(8)] + [(r,7) for r in range(8)]
    my_edges = sum(board[r][c] for (r,c) in edges)
    opp_edges = sum(opponent[r][c] for (r,c) in edges)
    
    # Game phase (0-1) where 0 is early game
    total_discs = my_discs + opp_discs
    game_phase = min(total_discs / 64, 1.0)
    
    # Weighted evaluation
    evaluation = 0
    evaluation += 10 * (my_discs - opp_discs) * game_phase  # More important late game
    evaluation += 20 * (my_pos - opp_pos)
    evaluation += 15 * (my_moves - opp_moves) * (1 - game_phase)  # More important early
    evaluation += 100 * (my_corners - opp_corners)
    evaluation += 5 * (my_edges - opp_edges)
    
    return evaluation

def minimax(board, opponent, depth, alpha, beta, maximizing_player):
    if depth == 0:
        return evaluate_position(board, opponent)
    
    valid_moves = get_valid_moves(board, opponent)
    
    if not valid_moves:
        # Pass if no moves
        if len(get_valid_moves(opponent, board)) == 0:
            # Game over
            my_discs = np.sum(board)
            opp_discs = np.sum(opponent)
            return (my_discs - opp_discs) * 1000
        else:
            # Opponent's turn
            return -minimax(opponent, board, depth-1, -beta, -alpha, not maximizing_player)
    
    if maximizing_player:
        max_eval = -float('inf')
        for r, c in valid_moves:
            new_board, new_opponent, _ = make_move(board, opponent, r, c)
            eval = minimax(new_board, new_opponent, depth-1, alpha, beta, False)
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for r, c in valid_moves:
            new_board, new_opponent, _ = make_move(board, opponent, r, c)
            eval = minimax(new_board, new_opponent, depth-1, alpha, beta, True)
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    valid_moves = get_valid_moves(you, opponent)
    if not valid_moves:
        return "pass"
    
    # Early game: prioritize corners
    total_discs = np.sum(you) + np.sum(opponent)
    if total_discs < 20:
        corners = [(0,0), (0,7), (7,0), (7,7)]
        for r, c in corners:
            if (r, c) in valid_moves:
                return f"{chr(ord('a') + c)}{r + 1}"
    
    best_move = None
    best_score = -float('inf')
    
    # Limit depth based on remaining moves
    depth = 3 if len(valid_moves) <= 10 else 2
    
    for r, c in valid_moves:
        new_board, new_opponent, flipped = make_move(you, opponent, r, c)
        
        # Immediate corner capture is always best
        if (r, c) in [(0,0), (0,7), (7,0), (7,7)]:
            return f"{chr(ord('a') + c)}{r + 1}"
        
        # Evaluate with minimax
        score = minimax(new_board, new_opponent, depth, -float('inf'), float('inf'), False)
        
        # Bonus for flipping many discs
        score += flipped * 2
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    if best_move:
        r, c = best_move
        return f"{chr(ord('a') + c)}{r + 1}"
    
    # Fallback: first valid move (shouldn't happen)
    r, c = valid_moves[0]
    return f"{chr(ord('a') + c)}{r + 1}"
