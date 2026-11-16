
import random
from typing import List, Tuple

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """
    Policy for Breakthrough game. Prioritizes advancing pieces towards opponent's home row
    while avoiding captures when possible.
    """
    # Determine movement direction
    direction = -1 if color == 'w' else 1  # white moves up (row+), black moves down (row-)
    
    # Convert lists to sets for faster lookup
    me_set = set(me)
    opp_set = set(opp)
    
    # Get all possible moves
    possible_moves = []
    
    for piece in me:
        row, col = piece
        
        # Check forward move (straight)
        forward_row = row + direction
        if 0 <= forward_row <= 7 and (forward_row, col) not in me_set and (forward_row, col) not in opp_set:
            possible_moves.append((piece, (forward_row, col)))
        
        # Check diagonal captures
        for dc in [-1, 1]:
            diag_col = col + dc
            if 0 <= diag_col <= 7:
                diag_row = row + direction
                if 0 <= diag_row <= 7 and (diag_row, diag_col) in opp_set:
                    possible_moves.append((piece, (diag_row, diag_col)))
    
    if not possible_moves:
        # No moves available, return a random one (shouldn't happen in valid game state)
        return possible_moves[0]
    
    # Evaluate each move and select the best one
    best_move = None
    best_score = float('-inf')
    
    for move in possible_moves:
        score = evaluate_move(move, me, opp, color, direction)
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move

def evaluate_move(move: Tuple[Tuple[int, int], Tuple[int, int]], me: List[Tuple[int, int]], 
                 opp: List[Tuple[int, int]], color: str, direction: int) -> float:
    """
    Evaluate a move based on several heuristics.
    """
    from_pos, to_pos = move
    from_row, from_col = from_pos
    to_row, to_col = to_pos
    
    score = 0.0
    
    # 1. Distance to opponent's home row (highest priority)
    # For white (color='w'), home row is 0, opponent's home row is 7
    # For black (color='b'), home row is 7, opponent's home row is 0
    if color == 'w':
        distance_to_win = 7 - to_row
    else:
        distance_to_win = to_row
    
    score += distance_to_win * 10.0
    
    # 2. Check if this move captures an opponent piece
    if to_pos in set(opp):
        score += 5.0  # Positive score for capturing
    
    # 3. Avoid moves that would put the piece in danger of capture next turn
    # Check if the piece would be captured on the next opponent turn
    threat_penalty = 0.0
    for dr in [-1, 1]:
        threat_row = to_row - direction  # Opponent moves in opposite direction
        threat_col = to_col + dr
        if 0 <= threat_row <= 7 and 0 <= threat_col <= 7:
            if (threat_row, threat_col) in set(opp):
                # This piece would be under threat
                threat_penalty += 2.0
    
    score -= threat_penalty
    
    # 4. Prefer moving pieces that are further back (haven't advanced much)
    if color == 'w':
        score += from_row * 0.1
    else:
        score += (7 - from_row) * 0.1
    
    # 5. Small random component to break ties
    score += random.uniform(0, 0.05)
    
    return score
