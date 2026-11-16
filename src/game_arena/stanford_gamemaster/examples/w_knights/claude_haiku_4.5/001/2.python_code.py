
def policy(state: list[list[object]], role: str) -> str:
    # Parse state
    pieces = {}  # (col, row) -> color
    scores = {}
    
    for fact in state:
        if fact[0] == "cell":
            col, row, color = fact[1], int(fact[2]), fact[3]
            pieces[(col, row)] = color
        elif fact[0] == "score":
            scores[fact[1]] = int(fact[2])
    
    # Column mapping
    col_to_num = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5}
    num_to_col = {v: k for k, v in col_to_num.items()}
    
    # Find all pieces for current role
    my_pieces = [(col, row) for (col, row), color in pieces.items() if color == role]
    
    # Determine direction (white moves up, black moves down)
    if role == "white":
        direction = 1
        victory_row = 6
    else:
        direction = -1
        victory_row = 1
    
    # Knight move offsets
    knight_moves = [
        (1, 2), (2, 1), (2, -1), (1, -2),
        (-1, -2), (-2, -1), (-2, 1), (-1, 2)
    ]
    
    # Generate all legal moves with scoring
    best_move = None
    best_score = -float('inf')
    
    for col, row in my_pieces:
        col_num = col_to_num[col]
        
        for dc, dr in knight_moves:
            new_col_num = col_num + dc
            new_row = row + dr
            
            # Check bounds
            if not (0 <= new_col_num <= 5 and 1 <= new_row <= 6):
                continue
            
            # Check direction (cannot move backward)
            if direction == 1 and dr <= 0:
                continue
            if direction == -1 and dr >= 0:
                continue
            
            new_col = num_to_col[new_col_num]
            
            # Score this move
            move_score = 0
            
            # Priority 1: Can reach victory row
            if new_row == victory_row:
                move_score = 1000
            # Priority 2: Can capture opponent piece
            elif (new_col, new_row) in pieces and pieces[(new_col, new_row)] != role:
                move_score = 100
            # Priority 3: Forward progress
            else:
                move_score = new_row * direction
            
            if move_score > best_score:
                best_score = move_score
                best_move = (col, row, new_col, new_row)
    
    # Fallback: if no move found, return any legal move
    if best_move is None:
        for col, row in my_pieces:
            col_num = col_to_num[col]
            for dc, dr in knight_moves:
                new_col_num = col_num + dc
                new_row = row + dr
                if (0 <= new_col_num <= 5 and 1 <= new_row <= 6):
                    if (direction == 1 and dr > 0) or (direction == -1 and dr < 0):
                        new_col = num_to_col[new_col_num]
                        best_move = (col, row, new_col, new_row)
                        break
            if best_move:
                break
    
    # Format move
    from_col, from_row, to_col, to_row = best_move
    return f"move({from_col},{from_row},{to_col},{to_row})"
