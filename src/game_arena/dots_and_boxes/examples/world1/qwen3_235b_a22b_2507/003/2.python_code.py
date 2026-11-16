
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Get legal moves
    legal_moves = []
    
    # Horizontal edges: 5 rows, 4 columns (each row has 4 horizontal edges)
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] == 0:
                legal_moves.append((r, c, 'H'))
    
    # Vertical edges: 4 rows, 5 columns (each row has 5 vertical edges)
    for r in range(4):
        for c in range(5):
            if vertical[r, c] == 0:
                legal_moves.append((r, c, 'V'))
    
    # If no legal moves, return any (should not happen)
    if not legal_moves:
        return "0,0,H"
    
    # Score each move
    best_score = -float('inf')
    best_move = legal_moves[0]
    
    for move in legal_moves:
        score = evaluate_move(move, horizontal.copy(), vertical.copy(), capture.copy())
        if score > best_score:
            best_score = score
            best_move = move
    
    return f"{best_move[0]},{best_move[1]},{best_move[2]}"

def evaluate_move(move, horiz, vert, cap):
    r, c, d = move
    score = 0
    
    # Simulate drawing the edge
    if d == 'H':
        horiz[r, c] = 1
    else:
        vert[r, c] = 1
    
    # Check how many boxes are completed
    boxes_completed = 0
    four_corners = []  # list of (box_r, box_c) that become enclosed
    
    # For each of the up to two boxes that could be completed
    if d == 'H':
        # Horizontal edge at (r,c): affects box above (r-1,c) and below (r,c)
        if r > 0:  # box above
            br, bc = r-1, c
            if br < 4 and bc < 4 and cap[br, bc] == 0:
                top = horiz[br, bc]
                bottom = horiz[br+1, bc]
                left = vert[br, bc]
                right = vert[br, bc+1]
                if top != 0 and bottom != 0 and left != 0 and right != 0:
                    boxes_completed += 1
                    four_corners.append((br, bc))
        if r < 4:  # box below
            br, bc = r, c
            if br < 4 and bc < 4 and cap[br, bc] == 0:
                top = horiz[br, bc]
                bottom = horiz[br+1, bc]
                left = vert[br, bc]
                right = vert[br, bc+1]
                if top != 0 and bottom != 0 and left != 0 and right != 0:
                    boxes_completed += 1
                    four_corners.append((br, bc))
    else:  # d == 'V'
        # Vertical edge at (r,c): affects box to the left (r,c-1) and right (r,c)
        if c > 0:  # left box
            br, bc = r, c-1
            if br < 4 and bc < 4 and cap[br, bc] == 0:
                top = horiz[br, bc]
                bottom = horiz[br+1, bc]
                left = vert[br, bc]
                right = vert[br, bc+1]
                if top != 0 and bottom != 0 and left != 0 and right != 0:
                    boxes_completed += 1
                    four_corners.append((br, bc))
        if c < 4:  # right box
            br, bc = r, c
            if br < 4 and bc < 4 and cap[br, bc] == 0:
                top = horiz[br, bc]
                bottom = horiz[br+1, bc]
                left = vert[br, bc]
                right = vert[br, bc+1]
                if top != 0 and bottom != 0 and left != 0 and right != 0:
                    boxes_completed += 1
                    four_corners.append((br, bc))
    
    # Immediate reward for completing boxes
    if boxes_completed > 0:
        score += 100 * boxes_completed
        # Bonus for double-box move
        if boxes_completed >= 2:
            score += 50
        # If we complete boxes, we get another turn, so less risk
        # But still need to avoid setting up opponent
    else:
        # No box completed — opponent's turn. Avoid moves that create 3-edge boxes
        # Simulate and count how many boxes are now one edge away from completion
        danger_count = 0
        for br in range(4):
            for bc in range(4):
                if cap[br, bc] != 0:
                    continue
                top = horiz[br, bc]
                bottom = horiz[br+1, bc]
                left = vert[br, bc]
                right = vert[br, bc+1]
                sides = sum(1 for x in [top, bottom, left, right] if x != 0)
                if sides == 3:
                    danger_count += 1
        
        # Each danger counts as a potential free box for opponent
        score -= 100 * danger_count
    
    # Additional heuristic: prefer center moves slightly over edge
    # This avoids isolated edge openings
    if d == 'H':
        pos_score = 0.1 * (abs(r - 2) + abs(c - 1.5))  # normalize to 4x4 outer grid
        score -= pos_score  # less on edge is better, but not dominant
    else:
        pos_score = 0.1 * (abs(r - 1.5) + abs(c - 2))
        score -= pos_score
    
    # Avoid symmetry breaking early; prefer lower index if tied? (already happens via iteration)
    
    return score
