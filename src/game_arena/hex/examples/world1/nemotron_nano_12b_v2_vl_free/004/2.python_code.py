
def policy(me, opp, color):
    me_set = set(me)
    opp_set = set(opp)
    empty = []
    for i in range(11):
        for j in range(11):
            if (i, j) not in me_set and (i, j) not in opp_set:
                empty.append((i, j))
    
    if not empty:
        return (0, 0)  # Handle unexpected case, though it should not occur
    
    def is_adjacent(a, b):
        dx = a[0] - b[0]
        dy = a[1] - b[1]
        return (dx == 0 and abs(dy) == 1) or (dy == 0 and abs(dx) == 1) or (abs(dx) == 1 and abs(dy) == 1)
    
    adjacent_cells = []
    for cell in empty:
        for m_cell in me:
            if is_adjacent(cell, m_cell):
                adjacent_cells.append(cell)
                break
    
    candidates = adjacent_cells if adjacent_cells else empty
    
    best_move = None
    best_score = -float('inf')
    
    for cell in candidates:
        cell_x, cell_y = cell
        adj_own = 0
        adj_opp = 0
        
        # Check all 6 neighbors
        neighbors = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if abs(dx) + abs(dy) != 1 or (dx in (0, 1) and dy in (0, 1)):
                    continue
                neighbor = (cell_x + dx, cell_y + dy)
                if 0 <= neighbor[0] < 11 and 0 <= neighbor[1] < 11:
                    if neighbor in me_set:
                        adj_own += 1
                    elif neighbor in opp_set:
                        adj_opp += 1
        
        # Heuristic score calculation
        score = adj_own * 10
        if color == 'b':
            row_priority = cell_x * 2 + (10 - abs(cell_x - 5)) * 0.5
            score += row_priority
        else:
            col_priority = cell_y * 2 + (10 - abs(cell_y - 5)) * 0.5
            score += col_priority
        
        # Penalize distance from center
        dist_penalty = (cell_x - 5)**2 + (cell_y - 5)**2
        score -= dist_penalty * 0.1
        
        # Penalize cells adjacent to opponent's stones
        if color == 'b':
            score -= adj_opp * 2
        else:
            score -= adj_opp * 2
        
        if score > best_score:
            best_move = cell
            best_score = score
    
    return best_move
