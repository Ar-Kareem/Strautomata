
import numpy as np

def policy(you: list[int], opponent: list[int]) -> int:
    # First check for moves that give an extra turn
    for i in range(5, -1, -1):
        if you[i] == 0:
            continue
        if (you[i] + i) % 13 == 6:  # Lands in store
            return i
    
    # Then check for the best capture opportunity
    best_capture = -1
    best_move = -1
    for i in range(5, -1, -1):
        if you[i] == 0:
            continue
        total_seeds = you[i]
        last_pos = (i + total_seeds) % 13
        # Check if lands in empty house on our side
        if 0 <= last_pos < 6:
            if you[last_pos] == 0 and (i + total_seeds) < 13:
                opposite = opponent[5 - last_pos]
                if opposite > 0:
                    capture = 1 + opposite
                    if capture > best_capture:
                        best_capture = capture
                        best_move = i
    
    if best_move != -1:
        return best_move
    
    # Fallback: choose rightmost non-empty house
    for i in range(5, -1, -1):
        if you[i] > 0:
            return i
    
    # Should never reach here per problem statement
    return 0
