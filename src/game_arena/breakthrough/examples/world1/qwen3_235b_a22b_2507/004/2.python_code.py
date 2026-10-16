
import random
from typing import List, Tuple

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    # Define movement direction based on color
    if color == 'w':
        direction = 1  # White moves up (increasing row)
        opponent_home_row = 7
    else:  # color == 'b'
        direction = -1  # Black moves down (decreasing row)
        opponent_home_row = 0

    # Convert opp list to set for fast lookup
    opp_set = set(opp)
    me_set = set(me)

    best_score = -float('inf')
    best_move = None

    # Precompute center preference to slightly favor central columns
    center_cols = {3, 4}

    for piece in me:
        r, c = piece

        # Try forward move (straight)
        new_r = r + direction
        if 0 <= new_r <= 7:
            # Straight forward
            if (new_r, c) not in me_set and (new_r, c) not in opp_set:
                if new_r == opponent_home_row:
                    return (r, c), (new_r, c)  # Immediate win
                score = 10  # Base move value
                score += new_r if color == 'w' else (7 - new_r)  # Promote progress
                if c in center_cols:
                    score += 1  # Center bonus
                if score > best_score:
                    best_score = score
                    best_move = (r, c), (new_r, c)

            # Diagonal captures (left and right)
            for dc in [-1, 1]:
                nc = c + dc
                if not (0 <= nc <= 7):
                    continue
                if (new_r, nc) in opp_set:  # Can capture
                    if new_r == opponent_home_row:
                        return (r, c), (new_r, nc)  # Immediate win via capture
                    score = 20  # Capture bonus
                    # Bonus for capturing pieces that are deeper in our direction
                    capture_depth = new_r if color == 'w' else (7 - new_r)
                    score += capture_depth
                    if c in center_cols:
                        score += 1
                    if score > best_score:
                        best_score = score
                        best_move = (r, c), (new_r, nc)

    # If no move found above, something is wrong, but fallback to random legal move
    if best_move is None:
        # Should not happen, but for safety
        for piece in me:
            r, c = piece
            new_r = r + direction
            if 0 <= new_r <= 7:
                if (new_r, c) not in me_set and (new_r, c) not in opp_set:
                    return (r, c), (new_r, c)
                for dc in [-1, 1]:
                    nc = c + dc
                    if 0 <= nc <= 7 and (new_r, nc) in opp_set:
                        return (r, c), (new_r, nc)
        # Last resort: return first piece's current position (should not occur)
        return (me[0], me[0])

    return best_move
