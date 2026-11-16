
def policy(board: list[list[int]]) -> tuple[int, int]:
    import random
    
    # 1. Identify confirmed marks (1) and unknowns (0)
    my_marks = set()
    unknowns = set()
    for r in range(3):
        for c in range(3):
            if board[r][c] == 1:
                my_marks.add((r, c))
            else:
                unknowns.add((r, c))
    
    # 2. Check for my own winning move (I have 2 marks in a line, 3rd is free)
    lines = [
        [(0,0), (0,1), (0,2)], [(1,0), (1,1), (1,2)], [(2,0), (2,1), (2,2)], # Rows
        [(0,0), (1,0), (2,0)], [(0,1), (1,1), (2,1)], [(0,2), (1,2), (2,2)], # Cols
        [(0,0), (1,1), (2,2)], [(0,2), (1,1), (2,0)]  # Diagonals
    ]
    
    for line in lines:
        line_set = set(line)
        intersection = line_set.intersection(my_marks)
        if len(intersection) == 2:
            # I have 2 in this line. The 3rd must be the move.
            target = list(line_set - intersection)[0]
            if target in unknowns:
                return target # WINNING MOVE
    
    # 3. Check for opponent's potential winning moves (Block)
    # We infer opponent marks by looking at cells that are NOT mine.
    # If a line has 2 cells that are NOT mine (either confirmed opponent or unknown),
    # and the 3rd is also NOT mine, we are in danger.
    # Actually, simpler heuristic: If a line has 2 cells not in my_marks, 
    # and the 3rd is unknown, it might be the opponent's winning move.
    # We should block the 3rd unknown cell.
    
    for line in lines:
        not_my_cells = [c for c in line if c not in my_marks]
        if len(not_my_cells) == 2:
            # Potential opponent threat if the remaining cell is unknown
            remaining = list(set(line) - set(not_my_cells))
            if remaining:
                target = remaining[0]
                if target in unknowns:
                    return target # BLOCKING MOVE
    
    # 4. Strategic Moves
    
    # Center preference
    if (1, 1) in unknowns:
        return (1, 1)
        
    # Corner preference
    corners = [(0,0), (0,2), (2,0), (2,2)]
    available_corners = [c for c in corners if c in unknowns]
    if available_corners:
        return random.choice(available_corners)
        
    # Side preference
    sides = [(0,1), (1,0), (1,2), (2,1)]
    available_sides = [c for c in sides if c in unknowns]
    if available_sides:
        return random.choice(available_sides)
        
    # Fallback (should not happen if board is full)
    return random.choice(list(unknowns))
