
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Dots and Boxes AI for a 4x4 grid of boxes.
    Grid of boxes is 4x4, meaning horizontal is 5x4 (effectively) and vertical is 4x5.
    The input arrays are 5x5.
    """
    
    def get_box_sides(r, c):
        # A box at (r, c) is defined by edges:
        # horizontal[r, c], horizontal[r+1, c], vertical[r, c], vertical[r, c+1]
        count = 0
        edges = []
        if horizontal[r, c] == 0: edges.append((r, c, 'H'))
        else: count += 1
        if horizontal[r+1, c] == 0: edges.append((r+1, c, 'H'))
        else: count += 1
        if vertical[r, c] == 0: edges.append((r, c, 'V'))
        else: count += 1
        if vertical[r, c+1] == 0: edges.append((r, c+1, 'V'))
        else: count += 1
        return count, edges

    winning_moves = []
    safe_moves = []
    unsafe_moves = []

    # 1. Classify all possible legal moves
    # Check all horizontal edges (5 rows, 4 columns for a 4x4 box grid)
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] == 0:
                move = f"{r},{c},H"
                creates_capture = False
                makes_third_side = False
                
                # Check box above
                if r > 0:
                    cnt, _ = get_box_sides(r-1, c)
                    if cnt == 3: creates_capture = True
                    if cnt == 2: makes_third_side = True
                # Check box below
                if r < 4:
                    cnt, _ = get_box_sides(r, c)
                    if cnt == 3: creates_capture = True
                    if cnt == 2: makes_third_side = True
                
                if creates_capture:
                    winning_moves.append(move)
                elif not makes_third_side:
                    safe_moves.append(move)
                else:
                    unsafe_moves.append(move)

    # Check all vertical edges (4 rows, 5 columns for a 4x4 box grid)
    for r in range(4):
        for c in range(5):
            if vertical[r, c] == 0:
                move = f"{r},{c},V"
                creates_capture = False
                makes_third_side = False
                
                # Check box left
                if c > 0:
                    cnt, _ = get_box_sides(r, c-1)
                    if cnt == 3: creates_capture = True
                    if cnt == 2: makes_third_side = True
                # Check box right
                if c < 4:
                    cnt, _ = get_box_sides(r, c)
                    if cnt == 3: creates_capture = True
                    if cnt == 2: makes_third_side = True
                
                if creates_capture:
                    winning_moves.append(move)
                elif not makes_third_side:
                    safe_moves.append(move)
                else:
                    unsafe_moves.append(move)

    # Priority 1: Take a box if available
    if winning_moves:
        return winning_moves[0]
    
    # Priority 2: Play a safe move (doesn't give opponent a box)
    if safe_moves:
        # Heuristic: try to pick edges that aren't on the perimeter if possible
        return safe_moves[0]
    
    # Priority 3: If no safe moves, pick an unsafe move
    if unsafe_moves:
        return unsafe_moves[0]

    # Fallback to any legal move (should not be reached if logic is correct)
    for r in range(5):
        for c in range(5):
            if horizontal[r, c] == 0: return f"{r},{c},H"
            if vertical[r, c] == 0: return f"{r},{c},V"

    return "0,0,H"
