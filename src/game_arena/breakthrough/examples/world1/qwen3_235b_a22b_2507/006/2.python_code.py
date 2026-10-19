
import numpy as np
from typing import List, Tuple

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    # Create a set for fast lookup
    my_pieces = set(me)
    opp_pieces = set(opp)
    
    # Define direction
    direction = -1 if color == 'b' else 1  # black moves down (row decreases), white moves up (row increases)
    home_row = 7 if color == 'b' else 0
    enemy_home_row = 0 if color == 'b' else 7
    
    # All legal moves
    moves = []

    for r, c in me:
        # One forward
        nr = r + direction
        if 0 <= nr < 8:
            # Straight forward move
            if (nr, c) not in my_pieces and (nr, c) not in opp_pieces:
                moves.append(((r, c), (nr, c)))
            
            # Diagonally left (capture or move)
            if c > 0:
                nrc = (nr, c - 1)
                if nrc in opp_pieces:
                    moves.append(((r, c), nrc))
                elif nrc not in my_pieces:
                    moves.append(((r, c), nrc))
            
            # Diagonally right
            if c < 7:
                nrc = (nr, c + 1)
                if nrc in opp_pieces:
                    moves.append(((r, c), nrc))
                elif nrc not in my_pieces:
                    moves.append(((r, c), nrc))
    
    # If no moves, should not happen in Breakthrough without capture, but let's be safe
    if not moves:
        # Fallback: return any piece moving? But per rules there's always a move unless blocked
        # But in Breakthrough, you can always capture or advance unless fully blocked — so this is a failsafe
        return ((me[0][0], me[0][1]), (me[0][0], me[0][1]))  # Not legal, but avoid crash

    # Score each move
    best_score = -float('inf')
    best_move = moves[0]

    for move in moves:
        (fr, fc), (tr, tc) = move
        score = 0.0
        
        # Immediate win: reaching enemy's home row
        if tr == enemy_home_row:
            score += 1000
        
        # Capture bonus
        if (tr, tc) in opp_pieces:
            score += 10
        
        # Progress toward enemy home row
        forward_progress = abs(tr - home_row)  # For black: want tr to decrease; for white: increase
        normalized_progress = (forward_progress - (0 if color == 'b' else 0)) / 7.0
        if color == 'b':
            # Black: lower row number is better
            score += (7 - tr) * 0.5
        else:
            # White: higher row number is better
            score += tr * 0.5
        
        # Piece that is one step from promotion gets higher priority
        if tr == (enemy_home_row + direction):
            score += 0.3

        # Prevent unnecessary side moves unless for capture
        if abs(tc - fc) > 0 and (tr, tc) not in opp_pieces:
            score -= 0.1  # Slight penalty for non-capture diagonal unless it advances

        # Prefer moving pieces that are behind (spread advancement)
        # Encourage advancing lagging pieces slightly
        if color == 'b':
            if fr > 4:  # pieces that are already forward
                score += 0.05
        else:
            if fr < 3:
                score += 0.05

        # Capture threat: if opponent has piece near our home, block or capture
        # Not heavily modeled here but capture is already prioritized

        if score > best_score:
            best_score = score
            best_move = move

    return best_move
