
import numpy as np
import random

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Smart Dots and Boxes policy:
    1. Capture boxes if possible
    2. Avoid creating 3-sided boxes for opponent
    3. Make safe moves when no captures available
    """
    
    # Check for capture opportunities (boxes with exactly 3 edges filled)
    for row in range(4):
        for col in range(4):
            # Skip already captured boxes
            if capture[row, col] != 0:
                continue
                
            # Count edges around this box
            edges = 0
            if horizontal[row, col] != 0:  # top edge
                edges += 1
            if horizontal[row+1, col] != 0:  # bottom edge
                edges += 1
            if vertical[row, col] != 0:  # left edge
                edges += 1
            if vertical[row, col+1] != 0:  # right edge
                edges += 1
                
            # If 3 edges are filled, we can capture this box
            if edges == 3:
                # Find which edge is missing and return it
                if horizontal[row, col] == 0:  # top edge missing
                    return f"{row},{col},H"
                if horizontal[row+1, col] == 0:  # bottom edge missing
                    return f"{row+1},{col},H"
                if vertical[row, col] == 0:  # left edge missing
                    return f"{row},{col},V"
                if vertical[row, col+1] == 0:  # right edge missing
                    return f"{row},{col+1},V"
    
    # No immediate captures, look for safe moves that don't create vulnerable positions
    safe_moves = []
    avoid_moves = []
    
    # Check horizontal edges
    for row in range(5):
        for col in range(4):
            if horizontal[row, col] == 0:  # Edge is available
                move_str = f"{row},{col},H"
                # Check if this move would create a vulnerable box
                creates_vulnerable = False
                
                # Top box (if exists)
                if row > 0 and row <= 4:
                    if is_vulnerable_box(row-1, col, horizontal, vertical, capture):
                        creates_vulnerable = True
                
                # Bottom box (if exists)
                if row < 4:
                    if is_vulnerable_box(row, col, horizontal, vertical, capture):
                        creates_vulnerable = True
                
                if creates_vulnerable:
                    avoid_moves.append(move_str)
                else:
                    safe_moves.append(move_str)
    
    # Check vertical edges
    for row in range(4):
        for col in range(5):
            if vertical[row, col] == 0:  # Edge is available
                move_str = f"{row},{col},V"
                # Check if this move would create a vulnerable box
                creates_vulnerable = False
                
                # Left box (if exists)
                if col > 0 and col <= 4:
                    if is_vulnerable_box(row, col-1, horizontal, vertical, capture):
                        creates_vulnerable = True
                
                # Right box (if exists)
                if col < 4:
                    if is_vulnerable_box(row, col, horizontal, vertical, capture):
                        creates_vulnerable = True
                
                if creates_vulnerable:
                    avoid_moves.append(move_str)
                else:
                    safe_moves.append(move_str)
    
    # Prefer safe moves over moves that create vulnerabilities
    if safe_moves:
        return random.choice(safe_moves)
    elif avoid_moves:
        return random.choice(avoid_moves)
    
    # Fallback: return any legal move
    for row in range(5):
        for col in range(4):
            if horizontal[row, col] == 0:
                return f"{row},{col},H"
    for row in range(4):
        for col in range(5):
            if vertical[row, col] == 0:
                return f"{row},{col},V"
    
    # Should never reach here in a valid game state
    return "0,0,H"

def is_vulnerable_box(row, col, horizontal, vertical, capture):
    """
    Check if placing an edge would create a box with exactly 3 edges filled.
    This would give the opponent an easy capture on their next turn.
    """
    # Skip if box is already captured
    if capture[row, col] != 0:
        return False
    
    # Count existing edges around the box
    edges = 0
    if horizontal[row, col] != 0:  # top edge
        edges += 1
    if horizontal[row+1, col] != 0:  # bottom edge
        edges += 1
    if vertical[row, col] != 0:  # left edge
        edges += 1
    if vertical[row, col+1] != 0:  # right edge
        edges += 1
    
    # If the box already has 2 or 3 edges, adding one more would make it vulnerable
    return edges >= 2
