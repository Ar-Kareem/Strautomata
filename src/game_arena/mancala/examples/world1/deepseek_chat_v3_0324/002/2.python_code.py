
import numpy as np

def policy(you: list[int], opponent: list[int]) -> int:
    # First check for moves that give extra turns (land in store)
    for i in range(5, -1, -1):
        if you[i] == 0:
            continue
        seeds = you[i]
        if (seeds + i) % 13 == 6:  # Will land in store
            return i
            
    # Then check for capture opportunities
    for i in range(5, -1, -1):
        if you[i] == 0:
            continue
        seeds = you[i]
        landing_pos = (i + seeds) % 13
        if landing_pos < 6:  # Lands on our side
            if you[landing_pos] == 0 and opponent[5 - landing_pos] > 0:
                return i
                
    # Default: choose rightmost non-empty house
    for i in range(5, -1, -1):
        if you[i] > 0:
            return i
            
    # Should never reach here per problem statement
    return 0
