
import numpy as np
import random

def policy(horizontal, vertical, capture):
    # First check for any immediate captures
    for row in range(4):
        for col in range(4):
            # Check horizontal edges that would complete a box
            if horizontal[row, col] == 0 and horizontal[row+1, col] == 0:
                sides = 0
                if vertical[row, col] != 0: sides += 1
                if vertical[row, col+1] != 0: sides += 1
                if horizontal[row, col] == 0: sides += 1
                if horizontal[row+1, col] == 0: sides += 1
                if sides == 3:
                    if vertical[row, col] == 0:
                        return f"{row},{col},V"
                    if vertical[row, col+1] == 0:
                        return f"{row},{col+1},V"
                    if horizontal[row, col] == 0:
                        return f"{row},{col},H"
                    if horizontal[row+1, col] == 0:
                        return f"{row+1},{col},H"
            
            # Check vertical edges that would complete a box
            if vertical[row, col] == 0 and vertical[row, col+1] == 0:
                sides = 0
                if horizontal[row, col] != 0: sides += 1
                if horizontal[row, col+1] != 0: sides += 1
                if vertical[row, col] == 0: sides += 1
                if vertical[row, col+1] == 0: sides += 1
                if sides == 3:
                    if horizontal[row, col] == 0:
                        return f"{row},{col},H"
                    if horizontal[row, col+1] == 0:
                        return f"{row},{col+1},H"
                    if vertical[row, col] == 0:
                        return f"{row},{col},V"
                    if vertical[row, col+1] == 0:
                        return f"{row},{col+1},V"
    
    # Then look for safe moves that don't create 3-side boxes
    safe_moves = []
    for row in range(5):
        for col in range(5):
            # Check horizontal edges
            if row < 5 and col < 4 and horizontal[row, col] == 0:
                safe = True
                # Check if this move would create a 3-side box above
                if row > 0:
                    box_above = (vertical[row-1, col] != 0) + (vertical[row-1, col+1] != 0) + (horizontal[row-1, col] != 0)
                    if box_above == 2 and horizontal[row, col] == 0:
                        safe = False
                # Check if this move would create a 3-side box below
                if row < 4:
                    box_below = (vertical[row, col] != 0) + (vertical[row, col+1] != 0) + (horizontal[row+1, col] != 0)
                    if box_below == 2 and horizontal[row, col] == 0:
                        safe = False
                if safe:
                    safe_moves.append(f"{row},{col},H")
            
            # Check vertical edges
            if row < 4 and col < 5 and vertical[row, col] == 0:
                safe = True
                # Check if this move would create a 3-side box to the left
                if col > 0:
                    box_left = (horizontal[row, col-1] != 0) + (horizontal[row+1, col-1] != 0) + (vertical[row, col-1] != 0)
                    if box_left == 2 and vertical[row, col] == 0:
                        safe = False
                # Check if this move would create a 3-side box to the right
                if col < 4:
                    box_right = (horizontal[row, col] != 0) + (horizontal[row+1, col] != 0) + (vertical[row, col+1] != 0)
                    if box_right == 2 and vertical[row, col] == 0:
                        safe = False
                if safe:
                    safe_moves.append(f"{row},{col},V")
    
    if safe_moves:
        return random.choice(safe_moves)
    
    # If no safe moves, find any legal move
    all_moves = []
    for row in range(5):
        for col in range(4):
            if horizontal[row, col] == 0:
                all_moves.append(f"{row},{col},H")
    for row in range(4):
        for col in range(5):
            if vertical[row, col] == 0:
                all_moves.append(f"{row},{col},V")
    
    if all_moves:
        return random.choice(all_moves)
    
    # Should never reach here as game would be over
    return "0,0,H"
