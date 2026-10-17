
import random
import numpy as np
from collections import defaultdict

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    # Convert to sets for faster lookup
    me_set = set(me)
    opp_set = set(opp)
    occupied = me_set | opp_set
    
    # Get all empty cells
    empty_cells = []
    for i in range(11):
        for j in range(11):
            if (i, j) not in occupied:
                empty_cells.append((i, j))
    
    # If no empty cells, we should not be here
    if not empty_cells:
        return (0, 0)
    
    # Try to play near center for flexibility
    center = (5, 5)
    if center not in occupied:
        return center
    
    # Return a random empty cell if no better choice is found
    return random.choice(empty_cells)
