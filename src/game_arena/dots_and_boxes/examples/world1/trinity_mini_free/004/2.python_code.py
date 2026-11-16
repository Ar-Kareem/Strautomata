
import numpy as np

def check_completed_boxes(h, v, i, j, dir):
    """Check if drawing edge (i,j,dir) completes any boxes."""
    completed = 0
    boxes = []
    if dir == 'H':
        if 1 <= i < 4:
            boxes.append((i-1, j))
            boxes.append((i, j))
    else:  # 'V'
        if 1 <= j < 4:
            boxes.append((i, j-1))
            boxes.append((i, j))
    for (r, c) in boxes:
        if h[r][c] != 0 and h[r+1][c] != 0 and v[r][c] != 0 and v[r][c+1] != 0:
            completed += 1
    return completed

def check_three_sided_boxes(h, v, i, j, dir):
    """Check if drawing edge (i,j,dir) creates any boxes with three sides."""
    three = 0
    boxes = []
    if dir == 'H':
        if 1 <= i < 4:
            boxes.append((i-1, j))
            boxes.append((i, j))
    else:  # 'V'
        if 1 <= j < 4:
            boxes.append((i, j-1))
            boxes.append((i, j))
    for (r, c) in boxes:
        edges = [h[r][c], h[r+1][c], v[r][c], v[r][c+1]]
        count = sum(1 for e in edges if e != 0)
        if count == 3 and any(e == 0 for e in edges):
            three += 1
    return three

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Create copies to avoid modifying original state
    h = np.copy(horizontal)
    v = np.copy(vertical)
    c = np.copy(capture)
    
    moves = []  # Store (i, j, dir, completed_boxes, three_sided_boxes)
    
    # Check all horizontal edges
    for i in range(5):
        for j in range(5):
            if h[i][j] == 0:
                completed = check_completed_boxes(h, v, i, j, 'H')
                three = check_three_sided_boxes(h, v, i, j, 'H')
                moves.append((i, j, 'H', completed, three))
    
    # Check all vertical edges
    for i in range(5):
        for j in range(5):
            if v[i][j] == 0:
                completed = check_completed_boxes(h, v, i, j, 'V')
                three = check_three_sided_boxes(h, v, i, j, 'V')
                moves.append((i, j, 'V', completed, three))
    
    # Prioritize capture moves
    capture_moves = [m for m in moves if m[3] > 0]
    if capture_moves:
        return f"{capture_moves[0][0]},{capture_moves[0][1]},{capture_moves[0][2]}"
    
    # Select safe moves (no three-sided boxes)
    safe_moves = [m for m in moves if m[4] == 0]
    if safe_moves:
        return f"{safe_moves[0][0]},{safe_moves[0][1]},{safe_moves[0][2]}"
    
    # Choose move with fewest three-sided boxes if all moves are unsafe
    moves.sort(key=lambda x: x[4])
    return f"{moves[0][0]},{moves[0][1]},{moves[0][2]}"
