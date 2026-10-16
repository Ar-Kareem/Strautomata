
def policy(state, role):
    """
    Policy for parallelknightthrough game.
    Prioritizes winning moves, captures, and advancing toward goal.
    """
    
    # Parse state
    cells = {}
    played = set()
    
    for prop in state:
        if len(prop) < 2:
            continue
        if prop[0] == "cell" and len(prop) >= 5:
            board, col, row, color = prop[1], prop[2], prop[3], prop[4]
            cells[(board, col, int(row))] = color
        elif prop[0] == "played" and len(prop) >= 2:
            played.add(prop[1])
    
    boards = ['a', 'b', 'c']
    
    # Knight moves (forward only)
    if role == "white":
        knight_moves = [(1, 2), (-1, 2), (2, 1), (-2, 1)]
        goal_board = 'a'
        goal_row = 8
        enemy = "black"
    else:
        knight_moves = [(1, -2), (-1, -2), (2, -1), (-2, -1)]
        goal_board = 'c'
        goal_row = 1
        enemy = "white"
    
    # Generate legal moves on boards not yet played
    legal_moves = []
    for board in boards:
        if board in played:
            continue
        for (b, col, row), color in cells.items():
            if b != board or color != role:
                continue
            col_idx = ord(col) - ord('a')
            for dc, dr in knight_moves:
                new_col_idx = col_idx + dc
                new_row = row + dr
                if 0 <= new_col_idx < 3 and 1 <= new_row <= 8:
                    new_col = chr(ord('a') + new_col_idx)
                    dest = (board, new_col, new_row)
                    if dest not in cells or cells[dest] != role:
                        legal_moves.append((board, col, row, new_col, new_row))
    
    if not legal_moves:
        return "tick"
    
    def score(move):
        board, fc, fr, tc, tr = move
        s = 0
        dest = (board, tc, tr)
        
        # Winning move - highest priority
        if board == goal_board and tr == goal_row:
            return 10000
        
        # Capture bonus
        if dest in cells and cells[dest] == enemy:
            s += 100
            # Extra bonus for capturing on enemy's goal board
            if role == "white" and board == 'c':
                s += 50 + (tr - 1) * 10  # Higher for pieces closer to winning
            elif role == "black" and board == 'a':
                s += 50 + (8 - tr) * 10
        
        # Goal board bonus
        if board == goal_board:
            s += 50
        
        # Advance bonus
        if role == "white":
            s += (tr - fr) * 10
            s += tr * 2
        else:
            s += (fr - tr) * 10
            s += (9 - tr) * 2
        
        return s
    
    legal_moves.sort(key=score, reverse=True)
    best = legal_moves[0]
    return f"move({best[0]},{best[1]},{best[2]},{best[3]},{best[4]})"
