
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    legal_moves = []
    # Collect all possible legal moves (unoccupied edges)
    for r in range(5):
        for c in range(5):
            if horizontal[r, c] == 0:
                legal_moves.append((r, c, 'H'))
            if vertical[r, c] == 0:
                legal_moves.append((r, c, 'V'))
    
    if not legal_moves:
        return None  # This case should not occur as the game would have ended
    
    # Evaluate each move to compute captures and risk (opponent's possible captures)
    evaluated_moves = []
    for move in legal_moves:
        r, c, dir = move
        capture_count = 0
        bad_box_count = 0
        
        # Calculate captures from this move
        affected_boxes = set()
        if dir == 'H':
            if r < 4:
                affected_boxes.add((r, c))
            if r > 0:
                affected_boxes.add((r - 1, c))
        else:  # 'V'
            affected_boxes.add((r, c))
            if c > 0:
                affected_boxes.add((r, c - 1))
        
        for (br, bc) in affected_boxes:
            if capture[br, bc] != 0:
                continue  # Box already captured
            
            # Check all four edges of the box (br, bc)
            top = horizontal[br, bc] != 0
            bottom = horizontal[br + 1, bc] != 0
            left = vertical[br, bc] != 0
            right = vertical[br, bc + 1] != 0
            
            # Adjust edges based on the move
            if dir == 'H':
                if br == r and bc == c:
                    top = True
                elif (r - 1 == br) and (c == bc):
                    bottom = True
            
            elif dir == 'V':
                if br == r and bc == c:
                    left = True
                elif (br == r) and (c - 1 == bc):
                    right = True
            
            sum_edges = sum([top, bottom, left, right])
            if sum_edges == 4:
                capture_count += 1
        
        # Calculate the number of three-edge boxes the opponent could capture next
        three_edge_count = 0
        for i in range(4):
            for j in range(4):
                if capture[i, j] != 0:
                    continue
                edges_filled = [
                    horizontal[i, j] != 0,
                    horizontal[i + 1, j] != 0,
                    vertical[i, j] != 0,
                    vertical[i, j + 1] != 0
                ]
                sum_edges = sum(edges_filled)
                # Adjust edges for the current move
                if dir == 'H':
                    if (i == r and j == c) or (i == r - 1 and j == c):
                        # Account for the current move's edge
                        edges_filled[0] = True  # top of (r,c) is moved edge
                        edges_filled[1] = True  # bottom of (r-1,c) is moved edge
                elif dir == 'V':
                    if (i == r and j == c):
                        edges_filled[1] = True  # right edge of (r, c-1)
                        edges_filled[2] = True  # left edge of (r, c)
                    elif (i == r and j == c - 1):
                        edges_filled[0] = True  # right edge of (r, c-1)
                        edges_filled[2] = True  # left edge of (r, c)
                # Recalculate sum_edges after adjusting the relevant edges
                if dir == 'H':
                    sum_edges = sum([edges_filled[0], horizontal[i + 1, j] != 0, vertical[i, j] != 0, vertical[i, j + 1] != 0])
                elif dir == 'V':
                    sum_edges = sum([edges_filled[0], edges_filled[1], edges_filled[2], edges_filled[3]])
                if sum_edges == 3:
                    three_edge_count += 1
        
        evaluated_moves.append((capture_count, -bad, mv))
    
    # Initialize best move
    best_move = None
    max_captured = -1
    min_bad = float('inf')
    
    # Check for moves that capture boxes
    for mv in evaluated_moves:
        cap_count, risk, m = mv
        if cap_count > 0:
            if cap_count > max_captured or (cap_count == max_captured and risk < min_bad):
                max_captured = cap_count
                min_bad = risk
                best_move = m
    
    # Check for non-capturing moves with least risk
    if not best_move:
        for mv in evaluated_moves:
            _, risk, m = mv
            if risk < min_bad:
                best_move = m
                min_bad = risk
    
    # Format the best move
    r, c, direc = best_move
    return f"{r},{c},{direc}"
