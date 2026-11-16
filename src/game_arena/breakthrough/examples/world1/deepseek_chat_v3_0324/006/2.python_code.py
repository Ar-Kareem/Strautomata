
import math
from collections import defaultdict

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    # Determine movement direction based on color
    direction = 1 if color == 'w' else -1
    
    # Convert positions to sets for faster lookup
    my_pieces = set(me)
    opp_pieces = set(opp)
    
    # Check for immediate winning moves first
    target_row = 7 if color == 'w' else 0
    for (r, c) in my_pieces:
        if r == target_row - direction:
            # Can we move to home row?
            forward_pos = (r + direction, c)
            if forward_pos not in my_pieces and forward_pos not in opp_pieces:
                return ((r, c), forward_pos)
    
    # Evaluate all possible moves with scores
    moves = []
    
    for (r, c) in my_pieces:
        # Forward move
        forward_pos = (r + direction, c)
        if forward_pos not in my_pieces and forward_pos not in opp_pieces:
            # Score based on advancement and centrality
            score = (r + direction if color == 'w' else 7 - (r + direction)) * 10
            score += (3.5 - abs(c - 3.5))  # Bonus for center columns
            moves.append((score, ((r, c), forward_pos)))
        
        # Diagonal captures
        for dc in [-1, 1]:
            capture_pos = (r + direction, c + dc)
            if capture_pos in opp_pieces:
                # Evaluate capture safety and position
                score = 50  # Base capture bonus
                score += (r + direction if color == 'w' else 7 - (r + direction)) * 10
                score += (3.5 - abs((c + dc) - 3.5))  # Centrality bonus
                
                # Check if capture leaves us vulnerable
                back_pos = (r, c + dc)
                if back_pos in opp_pieces:
                    opp_capture_pos = (r - direction, c)
                    if opp_capture_pos not in my_pieces and opp_capture_pos not in opp_pieces:
                        score -= 30  # Penalty for vulnerable capture
                
                moves.append((score, ((r, c), capture_pos)))
    
    # If we have moves, return the highest scoring one
    if moves:
        moves.sort(key=lambda x: -x[0])
        return moves[0][1]
    
    # Fallback - should never happen if game isn't over
    # Just return first legal move found (shouldn't reach here in valid game)
    for (r, c) in my_pieces:
        forward_pos = (r + direction, c)
        if forward_pos not in my_pieces and forward_pos not in opp_pieces:
            return ((r, c), forward_pos)
        for dc in [-1, 1]:
            capture_pos = (r + direction, c + dc)
            if capture_pos in opp_pieces:
                return ((r, c), capture_pos)
    
    # Shouldn't reach here if game isn't over
    return (me[0], (me[0][0] + direction, me[0][1]))
