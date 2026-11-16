
def get_neighbors(r, c):
    """Get valid neighbors of cell (r, c) on 11x11 hex board"""
    neighbors = []
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 11 and 0 <= nc < 11:
            neighbors.append((nr, nc))
    return neighbors

def check_win(stones, color):
    """Check if stones connect the required sides for the given color"""
    if not stones:
        return False
    
    stones_set = set(stones)
    visited = set()
    queue = []
    
    if color == 'b':  # Black: connect top (row 0) to bottom (row 10)
        for c in range(11):
            if (0, c) in stones_set:
                queue.append((0, c))
                visited.add((0, c))
        
        while queue:
            r, c = queue.pop(0)
            if r == 10:  # Reached bottom
                return True
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) in stones_set and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    queue.append((nr, nc))
    else:  # White: connect left (col 0) to right (col 10)
        for r in range(11):
            if (r, 0) in stones_set:
                queue.append((r, 0))
                visited.add((r, 0))
        
        while queue:
            r, c = queue.pop(0)
            if c == 10:  # Reached right side
                return True
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) in stones_set and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    queue.append((nr, nc))
    
    return False

def find_bridge_moves(my_stones, opp_stones):
    """Find all moves that complete a bridge pattern"""
    moves = []
    my_set = set(my_stones)
    opp_set = set(opp_stones)
    
    # Bridge orientation 1: (r,c) and (r+1,c+1)
    for r in range(10):
        for c in range(10):
            if (r, c) in my_set and (r+1, c+1) in my_set:
                if (r+1, c) not in my_set and (r+1, c) not in opp_set:
                    moves.append((r+1, c))
                if (r, c+1) not in my_set and (r, c+1) not in opp_set:
                    moves.append((r, c+1))
    
    # Bridge orientation 2: (r+1,c) and (r,c+1)
    for r in range(10):
        for c in range(10):
            if (r+1, c) in my_set and (r, c+1) in my_set:
                if (r, c) not in my_set and (r, c) not in opp_set:
                    moves.append((r, c))
                if (r+1, c+1) not in my_set and (r+1, c+1) not in opp_set:
                    moves.append((r+1, c+1))
    
    return list(set(moves))  # Remove duplicates

def evaluate_cell(r, c, color, me_set, opp_set):
    """Heuristic evaluation of a cell for the given player"""
    score = 0
    
    # Base score: distance to opposite side
    if color == 'b':  # Black: reach bottom
        score = 10 - r
        if r == 0:  # Top edge bonus
            score += 15
    else:  # White: reach right side
        score = 10 - c
        if c == 0:  # Left edge bonus
            score += 15
    
    # Connectivity bonus
    connections = 0
    for nr, nc in get_neighbors(r, c):
        if (nr, nc) in me_set:
            connections += 1
        elif (nr, nc) in opp_set:
            score += 0.5  # Blocking bonus
    
    # Multiple connections are valuable
    if connections >= 2:
        score += connections * 3
    elif connections == 1:
        score += 2
    
    # Center control bonus (approximate hex distance)
    dist = max(abs(r - 5), abs(c - 5))
    score += max(0, 5 - dist)
    
    # Tie-breaker
    score += (r + c) * 0.001
    
    return score

def policy(me, opp, color):
    """
    Main policy function for Hex on 11x11 board.
    Returns a legal move tuple (row, col).
    """
    me_set = set(me)
    opp_set = set(opp)
    
    # 1. Check for immediate winning move
    for r in range(11):
        for c in range(11):
            if (r, c) not in me_set and (r, c) not in opp_set:
                if check_win(me_set | {(r, c)}, color):
                    return (r, c)
    
    # 2. Block opponent's immediate winning move
    opp_color = 'w' if color == 'b' else 'b'
    for r in range(11):
        for c in range(11):
            if (r, c) not in me_set and (r, c) not in opp_set:
                if check_win(opp_set | {(r, c)}, opp_color):
                    return (r, c)
    
    # 3. Early game: claim center
    if len(me) + len(opp) < 4:
        center_positions = [
            (5, 5), (5, 4), (5, 6), (4, 5), (6, 5),
            (4, 4), (6, 6), (4, 6), (6, 4)
        ]
        for r, c in center_positions:
            if (r, c) not in me_set and (r, c) not in opp_set:
                return (r, c)
    
    # 4. Complete our bridge patterns
    bridge_moves = find_bridge_moves(me_set, opp_set)
    if bridge_moves:
        # Prioritize by proximity to goal
        if color == 'b':
            bridge_moves.sort(key=lambda m: m[0], reverse=True)
        else:
            bridge_moves.sort(key=lambda m: m[1], reverse=True)
        return bridge_moves[0]
    
    # 5. Block opponent's bridge patterns
    opp_bridge_moves = find_bridge_moves(opp_set, me_set)
    if opp_bridge_moves:
        if color == 'b':
            opp_bridge_moves.sort(key=lambda m: m[0], reverse=True)
        else:
            opp_bridge_moves.sort(key=lambda m: m[1], reverse=True)
        return opp_bridge_moves[0]
    
    # 6. Strategically evaluate all moves
    best_move = None
    best_score = float('-inf')
    
    for r in range(11):
        for c in range(11):
            if (r, c) not in me_set and (r, c) not in opp_set:
                score = evaluate_cell(r, c, color, me_set, opp_set)
                
                # Extra bonus for multi-path moves
                path_count = sum(1 for nr, nc in get_neighbors(r, c) if (nr, nc) in me_set)
                if path_count >= 2:
                    score += 4
                
                if score > best_score:
                    best_score = score
                    best_move = (r, c)
    
    return best_move if best_move is not None else (0, 0)
