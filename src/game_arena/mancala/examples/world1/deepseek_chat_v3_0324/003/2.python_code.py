
import numpy as np

def policy(you: list[int], opponent: list[int]) -> int:
    # Check for moves that give an extra turn (land last in store)
    for i in range(5, -1, -1):
        if you[i] == 0:
            continue
        if (you[i] + i) % 13 == 6:  # Lands exactly in store
            return i
    
    # Check for capture opportunities
    best_capture = -1
    best_capture_gain = -1
    for i in range(5, -1, -1):
        if you[i] == 0:
            continue
        total_seeds = you[i]
        last_pos = (i + total_seeds) % 12  # Position in 0-11 (excluding stores)
        
        # If lands in empty house on our side and opposite has seeds
        if last_pos < 6 and you[last_pos] == 0 and (i + total_seeds) < 12 and opponent[5 - last_pos] > 0:
            capture_gain = 1 + opponent[5 - last_pos]
            if capture_gain > best_capture_gain:
                best_capture_gain = capture_gain
                best_capture = i
    
    if best_capture != -1:
        return best_capture
    
    # Default strategy: choose rightmost non-empty house
    for i in range(5, -1, -1):
        if you[i] > 0:
            return i
    
    # Should never reach here per problem statement
    return 0
