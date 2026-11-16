
import numpy as np

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    # Determine movement direction based on color
    direction = -1 if color == 'b' else 1
    home_row = 7 if color == 'b' else 0
    
    # Check for winning moves (reaching opponent's home row)
    for (r, c) in me:
        new_r = r + direction
        if 0 <= new_r <= 7 and (new_r, c) not in me and (new_r, c) not in opp:
            if new_r == home_row:
                return ((r, c), (new_r, c))
    
    # Check for capture moves
    for (r, c) in me:
        for dr in [-1, 1]:
            new_r = r + direction
            new_c = c + dr
            if 0 <= new_r <= 7 and 0 <= new_c <= 7:
                if (new_r, new_c) in opp:
                    return ((r, c), (new_r, new_c))
    
    # Check for safe straight moves
    for (r, c) in me:
        new_r = r + direction
        if 0 <= new_r <= 7 and (new_r, c) not in me and (new_r, c) not in opp:
            return ((r, c), (new_r, c))
    
    # Fallback: return any valid move if none found (should not happen)
    for (r, c) in me:
        for dr in [-1, 1]:
            new_r = r + direction
            new_c = c + dr
            if 0 <= new_r <= 7 and 0 <= new_c <= 7:
                if (new_r, new_c) not in me and (new_r, new_c) not in opp:
                    return ((r, c), (new_r, new_c))
    return ((me[0][0], me[0][1]), (me[0][0] + direction, me[0][1]))
