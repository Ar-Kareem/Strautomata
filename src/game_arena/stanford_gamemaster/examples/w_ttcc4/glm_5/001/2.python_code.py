
def policy(state, role):
    # Parse board state
    board = {}
    for fact in state:
        if fact[0] == 'cell':
            x, y, piece = int(fact[1]), int(fact[2]), fact[3]
            board[(x, y)] = piece
    
    my_color = role
    opp_color = 'black' if role == 'white' else 'white'
    
    # Available drop positions (columns 1-7, stack from row 3 to 5)
    drop_cols = {}
    for col in range(1, 8):
        row = 3
        while (col, row) in board and 'disk' in board[(col, row)]:
            row += 1
        if row <= 5:
            drop_cols[col] = row
    
    # Center 3x3 winning lines (columns 3-5, rows 3-5)
    lines = [
        [(3,3), (4,3), (5,3)],
        [(3,4), (4,4), (5,4)],
        [(3,5), (4,5), (5,5)],
        [(3,3), (3,4), (3,5)],
        [(4,3), (4,4), (4,5)],
        [(5,3), (5,4), (5,5)],
        [(3,3), (4,4), (5,5)],
        [(3,5), (4,4), (5,3)],
    ]
    
    # Check for winning drop
    for col, row in drop_cols.items():
        pos = (col, row)
        sim_board = dict(board)
        sim_board[pos] = my_color + 'disk'
        for line in lines:
            if pos in line:
                count = sum(1 for p in line if sim_board.get(p, '').startswith(my_color))
                if count >= 3:
                    return f'drop({col})'
    
    # Check for blocking drop
    for line in lines:
        opp_count = sum(1 for p in line if board.get(p, '').startswith(opp_color))
        my_count = sum(1 for p in line if board.get(p, '').startswith(my_color))
        if opp_count >= 2 and my_count == 0:
            empty_pos = [p for p in line if p not in board]
            if len(empty_pos) == 1:
                col, row = empty_pos[0]
                if col in drop_cols and drop_cols[col] == row:
                    return f'drop({col})'
    
    # Strategic center drops
    for col in [4, 3, 5]:
        if col in drop_cols:
            return f'drop({col})'
    
    # Any available drop
    if drop_cols:
        return f'drop({list(drop_cols.keys())[0]})'
    
    # Generate piece moves
    moves = []
    for (x, y), piece in board.items():
        if not piece.startswith(my_color):
            continue
        piece_type = piece[len(my_color):]
        
        if piece_type == 'knight':
            for dx, dy in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
                nx, ny = x + dx, y + dy
                if 1 <= nx <= 7 and 1 <= ny <= 7:
                    dest = board.get((nx, ny))
                    if dest is None or not dest.startswith(my_color):
                        moves.append(f'knightmove({x},{y},{nx},{ny})')
        
        elif piece_type == 'checker':
            for dx, dy in [(-1,-1),(-1,1),(1,-1),(1,1)]:
                nx, ny = x + dx, y + dy
                if 1 <= nx <= 7 and 1 <= ny <= 7:
                    dest = board.get((nx, ny))
                    if dest is None or not dest.startswith(my_color):
                        moves.append(f'checkermove({x},{y},{nx},{ny})')
        
        elif piece_type == 'pawn':
            dy = 1 if my_color == 'white' else -1
            ny = y + dy
            if 1 <= ny <= 7:
                if (x, ny) not in board:
                    moves.append(f'pawnmove({x},{y},{x},{ny})')
                for dx in [-1, 1]:
                    nx = x + dx
                    if 1 <= nx <= 7:
                        dest = board.get((nx, ny))
                        if dest and dest.startswith(opp_color):
                            moves.append(f'pawnmove({x},{y},{nx},{ny})')
    
    if moves:
        # Prioritize captures
        for move in moves:
            parts = move.split('(')[1].split(')')[0].split(',')
            if len(parts) == 4:
                nx, ny = int(parts[2]), int(parts[3])
                if (nx, ny) in board and board[(nx, ny)].startswith(opp_color):
                    return move
        return moves[0]
    
    return 'noop'
