
import numpy as np

def policy(you: list[int], opponent: list[int]) -> int:
    # First check for moves that give extra turns
    best_move = None
    
    # Check each possible move to see if it lands last in store
    for i in [5,4,3,2,1,0]:
        if you[i] == 0:
            continue
            
        seeds = you[i]
        landing_pos = (i + seeds) % 13
        if landing_pos == 6:  # lands in our store
            return i
    
    # No immediate extra move, look for captures
    max_capture = -1
    capture_move = None
    
    for i in [5,4,3,2,1,0]:
        if you[i] == 0:
            continue
            
        seeds = you[i]
        landing_pos = (i + seeds) % 13
        
        # Check if lands in an empty house on our side
        if landing_pos < 6:
            if you[landing_pos] == 0 and opponent[5 - landing_pos] > 0:
                capture_amount = 1 + opponent[5 - landing_pos]
                if capture_amount > max_capture:
                    max_capture = capture_amount
                    capture_move = i
    
    if capture_move is not None:
        return capture_move
    
    # Default to highest numbered house with seeds (pushes more toward store)
    for i in [5,4,3,2,1,0]:
        if you[i] > 0:
            return i
    
    # Shouldn't reach here per problem statement
    return 0
