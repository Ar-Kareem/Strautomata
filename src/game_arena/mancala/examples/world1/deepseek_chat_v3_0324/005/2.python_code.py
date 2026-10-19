
import numpy as np

def policy(you: list[int], opponent: list[int]) -> int:
    # First priority: moves that give extra turns
    for i in range(5, -1, -1):
        if you[i] == 0:
            continue
        if (you[i] + i) % 13 == 6:  # Lands in store
            return i
    
    # Second priority: capture moves
    for i in range(5, -1, -1):
        if you[i] == 0:
            continue
        total_seeds = you[i]
        last_pos = (i + total_seeds) % 12
        if last_pos < 6:  # Lands in our side
            if you[last_pos] == 0 and opponent[5 - last_pos] > 0:
                return i
    
    # Default: rightmost non-empty house
    for i in range(5, -1, -1):
        if you[i] > 0:
            return i
    
    # Should never reach here per problem statement
    return 0
