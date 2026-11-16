
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert to list of lists if needed (defensive)
    # board is 4x4 with 0=empty, 1=me, -1=opponent
    
    # All possible lines where you can get 3 in a row in 4x4 grid
    lines = []
    
    # Rows - each row can have two 3-in-a-row possibilities
    for r in range(4):
        lines.append([(r, 0), (r, 1), (r, 2)])
        lines.append([(r, 1), (r, 2), (r, 3)])
    
    # Columns - each column can have two 3-in-a-row possibilities  
    for c in range(4):
        lines.append([(0, c), (1, c), (2, c)])
        lines.append([(1, c), (2, c), (3, c)])
    
    # Diagonals
    # Main diagonal directions
    lines.append([(0, 0), (1, 1), (2, 2)])
    lines.append([(1, 1), (2, 2), (3, 3)])
    lines.append([(0, 1), (1, 2), (2, 3)])
    lines.append([(1, 0), (2, 1), (3, 2)])
    
    # Anti-diagonal directions
    lines.append([(0, 3), (1, 2), (2, 1)])
    lines.append([(1, 2), (2, 1), (3, 0)])
    lines.append([(0, 2), (1, 1), (2, 0)])
    lines.append([(1, 3), (2, 2), (3, 1)])
    
    # Priority 1: Check for immediate win
    for line in lines:
        values = [board[r][c] for r, c in line]
        if values.count(1) == 2 and values.count(0) == 1:
            # Find the empty spot and take it
            for r, c in line:
                if board[r][c] == 0:
                    return (r, c)
    
    # Priority 2: Block opponent's immediate win
    for line in lines:
        values = [board[r][c] for r, c in line]
        if values.count(-1) == 2 and values.count(0) == 1:
            # Find the empty spot and block it
            for r, c in line:
                if board[r][c] == 0:
                    return (r, c)
    
    # Priority 3: Strategic positions - center is better
    # In 4x4, center positions are (1,1), (1,2), (2,1), (2,2)
    center_positions = [(1, 1), (1, 2), (2, 1), (2, 2)]
    empty_centers = [(r, c) for r, c in center_positions if board[r][c] == 0]
    if empty_centers:
        # Prefer positions that are part of more potential lines
        # Just pick the first one for now
        return empty_centers[0]
    
    # Priority 4: Look for moves that create multiple threats (forks)
    # For each empty spot, see how many lines it completes with 2 of our marks
    best_move = None
    max_threats = 0
    
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                # Count how many lines this move would complete with 2 of our marks
                threats = 0
                for line in lines:
                    if (r, c) in line:
                        values = [board[pos[0]][pos[1]] for pos in line]
                        # If this line has exactly 2 of our marks and 1 empty (this spot)
                        if values.count(1) == 2 and values.count(0) == 1:
                            threats += 1
                
                if threats > max_threats:
                    max_threats = threats
                    best_move = (r, c)
    
    if best_move:
        return best_move
    
    # Priority 5: Fallback - first available spot
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                return (r, c)
    
    # Should not happen in a valid game
    return (0, 0)
