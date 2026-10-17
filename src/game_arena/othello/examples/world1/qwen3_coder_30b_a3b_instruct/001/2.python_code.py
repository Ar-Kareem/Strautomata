
import numpy as np
import copy
from typing import Tuple, List

# Predefined corner and edge weights for positional evaluation
POSITION_WEIGHT = np.array([
    [100, -20, 10, 5, 5, 10, -20, 100],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [ 10,  -2,  1,  2,  2,  1,  -2,  10],
    [  5,  -2,  2,  1,  1,  2,  -2,   5],
    [  5,  -2,  2,  1,  1,  2,  -2,   5],
    [ 10,  -2,  1,  2,  2,  1,  -2,  10],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [100, -20, 10, 5, 5, 10, -20, 100]
])

def get_legal_moves(board: np.ndarray, player: np.ndarray, opponent: np.ndarray) -> List[str]:
    """Get all legal moves for current player"""
    moves = []
    for r in range(8):
        for c in range(8):
            if player[r][c] == 0 and opponent[r][c] == 0 and is_legal_move(player, opponent, r, c):
                # Convert to algebraic notation
                moves.append(chr(ord('a') + c) + str(8 - r))
    return moves

def is_legal_move(player: np.ndarray, opponent: np.ndarray, r: int, c: int) -> bool:
    """Check if placing at (r,c) is a legal move"""
    if player[r][c] == 1 or opponent[r][c] == 1:
        return False
    
    # Check in all 8 directions
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    for dr, dc in directions:
        if check_direction(player, opponent, r, c, dr, dc):
            return True
    return False

def check_direction(player: np.ndarray, opponent: np.ndarray, r: int, c: int, dr: int, dc: int) -> bool:
    """Check if placing at (r,c) flips opponent discs in given direction"""
    r += dr
    c += dc
    found_opponent = False
    
    while 0 <= r < 8 and 0 <= c < 8:
        if opponent[r][c] == 1:
            found_opponent = True
        elif player[r][c] == 1:
            return found_opponent
        else:
            break
        r += dr
        c += dc
    return False

def get_flipped_discs(player: np.ndarray, opponent: np.ndarray, r: int, c: int) -> List[Tuple[int, int]]:
    """Get list of opponent discs that would be flipped if placing at (r,c)"""
    flipped = []
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    
    for dr, dc in directions:
        temp_flipped = []
        r1, c1 = r + dr, c + dc
        
        while 0 <= r1 < 8 and 0 <= c1 < 8:
            if opponent[r1][c1] == 1:
                temp_flipped.append((r1, c1))
            elif player[r1][c1] == 1:
                flipped.extend(temp_flipped)
                break
            else:
                break
            r1 += dr
            c1 += dc
    
    return flipped

def make_move(player: np.ndarray, opponent: np.ndarray, r: int, c: int) -> Tuple[np.ndarray, np.ndarray]:
    """Make a move and return new boards"""
    new_player = copy.deepcopy(player)
    new_opponent = copy.deepcopy(opponent)
    
    new_player[r][c] = 1
    flipped_discs = get_flipped_discs(new_player, new_opponent, r, c)
    
    for fr, fc in flipped_discs:
        new_opponent[fr][fc] = 0
        new_player[fr][fc] = 1
    
    return new_player, new_opponent

def evaluate_position(player: np.ndarray, opponent: np.ndarray) -> int:
    """Evaluate current board position"""
    # Count discs
    player_discs = np.sum(player)
    opponent_discs = np.sum(opponent)
    
    # Positional advantage
    pos_value = 0
    for r in range(8):
        for c in range(8):
            if player[r][c] == 1:
                pos_value += POSITION_WEIGHT[r][c]
            elif opponent[r][c] == 1:
                pos_value -= POSITION_WEIGHT[r][c]
    
    # Mobility 
    player_moves = len(get_legal_moves(player, player, opponent))
    opponent_moves = len(get_legal_moves(opponent, opponent, player))
    
    mobility_value = 0
    if player_moves + opponent_moves > 0:
        mobility_value = 10 * (player_moves - opponent_moves) / (player_moves + opponent_moves)
    
    # Stability: corners and edges worth more
    stability = 0
    corners = [(0,0), (0,7), (7,0), (7,7)]
    for r, c in corners:
        if player[r][c] == 1:
            stability += 100
        elif opponent[r][c] == 1:
            stability -= 100
    
    # Combine all factors
    return (player_discs - opponent_discs) * 10 + pos_value + mobility_value + stability

def minimax(player: np.ndarray, opponent: np.ndarray, depth: int, alpha: float, beta: float, maximizing: bool) -> int:
    """Minimax with alpha-beta pruning"""
    if depth == 0:
        return evaluate_position(player, opponent)
    
    legal_moves = get_legal_moves(player, player, opponent)
    
    if not legal_moves:
        # If no move, pass turn
        if maximizing:
            return minimax(opponent, player, depth - 1, alpha, beta, False)
        else:
            return minimax(player, opponent, depth - 1, alpha, beta, True)
    
    if maximizing:
        max_eval = float('-inf')
        for move in legal_moves:
            c = ord(move[0]) - ord('a')
            r = 8 - int(move[1])
            new_player, new_opponent = make_move(player, opponent, r, c)
            eval_score = minimax(new_opponent, new_player, depth - 1, alpha, beta, False)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break  # Alpha-beta pruning
        return max_eval
    else:
        min_eval = float('inf')
        for move in legal_moves:
            c = ord(move[0]) - ord('a')
            r = 8 - int(move[1])
            new_player, new_opponent = make_move(player, opponent, r, c)
            eval_score = minimax(new_opponent, new_player, depth - 1, alpha, beta, True)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break  # Alpha-beta pruning
        return min_eval

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """Main policy function"""
    legal_moves = get_legal_moves(you, you, opponent)
    
    if not legal_moves:
        return "pass"
    
    # Try a deeper search for better moves
    best_move = None
    best_value = float('-inf')
    
    for move in legal_moves:
        c = ord(move[0]) - ord('a')
        r = 8 - int(move[1])
        new_player, new_opponent = make_move(you, opponent, r, c)
        value = minimax(new_opponent, new_player, 5, float('-inf'), float('inf'), False)
        
        if value > best_value:
            best_value = value
            best_move = move
    
    return best_move if best_move else legal_moves[0]
