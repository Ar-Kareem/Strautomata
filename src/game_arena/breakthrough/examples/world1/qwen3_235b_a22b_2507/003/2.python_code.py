
import numpy as np
from typing import List, Tuple

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    # Convert lists to sets for faster lookup
    me_set = set(me)
    opp_set = set(opp)
    
    # Determine direction of movement
    if color == 'w':
        direction = 1  # White moves up (row increases)
        home_row = 7   # White wins when reaching top (row 7)
    else:  # color == 'b'
        direction = -1  # Black moves down (row decreases)
        home_row = 0    # Black wins when reaching bottom (row 0)
    
    # Generate all legal moves
    moves = []
    
    for r, c in me:
        # Forward move (straight)
        nr = r + direction
        if 0 <= nr < 8:
            if (nr, c) not in me_set and (nr, c) not in opp_set:
                moves.append(((r, c), (nr, c)))
            # Diagonal left capture
            if c > 0:
                nc = c - 1
                if (nr, nc) in opp_set:
                    moves.append(((r, c), (nr, nc)))
            # Diagonal right capture
            if c < 7:
                nc = c + 1
                if (nr, nc) in opp_set:
                    moves.append(((r, c), (nr, nc)))
    
    # Immediate win: if any move reaches the opponent's home row, pick it
    for move in moves:
        (fr, fc), (tr, tc) = move
        if tr == home_row:
            return move
    
    # If there are captures, we prefer them unless risky
    capture_moves = [m for m in moves if m[1] in opp_set]
    if len(opp) <= 1:  # Next capture wins
        if capture_moves:
            return capture_moves[0]
    
    # Score each move
    scored_moves = []
    for move in moves:
        (fr, fc), (tr, tc) = move
        score = 0
        
        # Reward for moving forward: maximize progress toward opponent's back row
        if color == 'w':
            progress = tr  # closer to 7 is better
        else:
            progress = 7 - tr  # closer to 0 is better
        score += progress * 10
        
        # Big bonus for capture
        if (tr, tc) in opp_set:
            score += 50
        
        # Bonus for being in center columns (better mobility)
        if 2 <= tc <= 5:
            score += 5
        
        # Avoid moving into a square that exposes the piece to capture next turn
        # i.e., check if after this move, opponent could capture *this* piece next turn
        vulnerable = False
        opp_dir = -direction  # opponent's movement direction
        # Simulate opponent pieces possibly capturing the piece at (tr, tc)
        for orow, ocol in opp:
            # Opponent would move in opp_dir
            nr1 = orow + opp_dir
            # Check if opponent at (orow, ocol) can capture (tr, tc) diagonally
            if (nr1 == tr and 
                ((ocol + 1 == tc and ocol < 7) or (ocol - 1 == tc and ocol > 0))):
                vulnerable = True
                break
        
        if not vulnerable:
            score += 10
        
        scored_moves.append((score, move))
    
    # Sort by score descending
    scored_moves.sort(key=lambda x: x[0], reverse=True)
    
    # Return the best move
    if scored_moves:
        return scored_moves[0][1]
    
    # Fallback: return first legal move (should not happen)
    return moves[0] if moves else ((0, 0), (0, 0))
