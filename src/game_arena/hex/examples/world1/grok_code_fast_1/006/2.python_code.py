
import math

def get_neighbors(r, c):
    # Hex neighbors: standard 6, based on grid rules (exclude (r-1,c-1) and (r+1,c+1))
    candidates = [
        (r, c-1), (r, c+1),
        (r-1, c), (r+1, c),
        (r-1, c+1), (r+1, c-1)
    ]
    return [(nr, nc) for nr, nc in candidates if 0 <= nr < 11 and 0 <= nc < 11]

def has_path(board, color):
    # board is a set of player positions
    if color == 'b':
        # Black: rows 0 to 10
        start_row, end_row = 0, 10
        starts = [(r, c) for r, c in board if r == start_row]
        targets = set((r, c) for r, c in board if r == end_row)
    elif color == 'w':
        # White: cols 0 to 10
        start_col, end_col = 0, 10
        starts = [(r, c) for r, c in board if c == start_col]
        targets = set((r, c) for r, c in board if c == end_col)
    
    if not starts or not targets:
        return False
    
    visited = set()
    queue = starts[:]
    while queue:
        curr = queue.pop(0)
        if curr in targets:
            return True
        if curr in visited:
            continue
        visited.add(curr)
        for nr, nc in get_neighbors(*curr):
            if (nr, nc) in board and (nr, nc) not in visited:
                queue.append((nr, nc))
    return False

def policy(me, opp, color):
    me_set = set(me)
    opp_set = set(opp)
    occupied = me_set | opp_set
    empty = [(r, c) for r in range(11) for c in range(11) if (r, c) not in occupied]
    
    if not empty:
        # Theoretically impossible, but safety
        return (0, 0)
    
    best_score = -math.inf
    best_move = empty[0]
    center_r, center_c = 5, 5
    
    for r, c in empty:
        my_neighbors = sum(1 for nr, nc in get_neighbors(r, c) if (nr, nc) in me_set)
        opp_neighbors = sum(1 for nr, nc in get_neighbors(r, c) if (nr, nc) in opp_set)
        dist = abs(r - center_r) + abs(c - center_c)
        score = 2 * my_neighbors - opp_neighbors - (dist / 5.0)
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    # Now check if we can win with this move
    test_me_plus = me_set | {best_move}
    if has_path(test_me_plus, color):
        return best_move
    
    # Alternatively, check for immediate opponent win and block, but simplified: assume greedy handles
    
    return best_move
