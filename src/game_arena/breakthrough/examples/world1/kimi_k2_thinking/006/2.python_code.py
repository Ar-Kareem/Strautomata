
import random
from typing import List, Tuple

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """
    Breakthrough policy optimized for arena competition.
    Strategy: Advance pieces aggressively while avoiding immediate losses,
    with capture priority and safety checks.
    """
    me_set = set(me)
    opp_set = set(opp)
    direction = 1 if color == 'w' else -1
    opponent_home_row = 7 if color == 'w' else 0
    
    # --- Move Generation ---
    # Sort pieces by advancement to prioritize forward-most pieces
    sorted_pieces = sorted(me_set, key=lambda p: (p[0] if color == 'w' else -p[0]), reverse=True)
    
    moves = []
    for piece in sorted_pieces:
        r, c = piece
        nr = r + direction
        
        if not (0 <= nr < 8):
            continue
        
        # Straight forward move
        straight_pos = (nr, c)
        if straight_pos not in me_set and straight_pos not in opp_set:
            moves.append((piece, straight_pos))
        
        # Diagonal moves (left/right)
        for dc in (-1, 1):
            nc = c + dc
            if 0 <= nc < 8:
                diag_pos = (nr, nc)
                if diag_pos not in me_set:  # Can move to empty or capture
                    moves.append((piece, diag_pos))
    
    # --- Immediate Win Check ---
    for move in moves:
        if move[1][0] == opponent_home_row:
            return move
    
    if not moves:
        # Fallback: return any move that doesn't immediately lose
        for piece in sorted_pieces:
            r, c = piece
            nr = r + direction
            if 0 <= nr < 8:
                # Try straight first
                if (nr, c) not in me_set:
                    return (piece, (nr, c))
                # Then try diagonals
                for dc in (-1, 1):
                    nc = c + dc
                    if 0 <= nc < 8 and (nr, nc) not in me_set:
                        return (piece, (nr, nc))
        # Last resort (shouldn't happen)
        return (sorted_pieces[0], sorted_pieces[0])
    
    # --- Move Evaluation ---
    best_move = moves[0]
    best_score = float('-inf')
    
    for move in moves:
        score = 0.0
        to_r, to_c = move[1]
        from_r, from_c = move[0]
        
        # 1. Capture bonus
        if move[1] in opp_set:
            score += 1000.0
        
        # 2. Advancement score
        if color == 'w':
            advancement = to_r
        else:
            advancement = 7 - to_r
        score += advancement * 15.0  # Prefer moving forward
        
        # 3. Safety check: avoid moves that can be immediately recaptured
        opp_dir = -direction
        threatened = False
        for dc in (-1, 1):
            opp_r = to_r + opp_dir
            opp_c = to_c + dc
            if 0 <= opp_r < 8 and 0 <= opp_c < 8:
                if (opp_r, opp_c) in opp_set:
                    threatened = True
                    score -= 250.0  # Heavy penalty for threatened squares
                    break
        
        # 4. Bonus for safe advancement
        if not threatened:
            score += 75.0
        
        # 5. Prefer straight moves (maintain formation)
        if from_c == to_c:
            score += 10.0
        
        # 6. Small randomness for tie-breaking
        score += random.random()
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
