
def policy(state: list[list[object]], role: str) -> str:
    # Build a representation of the board
    board = {}
    empty_cells = []
    
    for fact in state:
        if fact[0] == "cell":
            r, c, val = fact[1], fact[2], fact[3]
            board[(r, c)] = val
            if val == 'b':
                empty_cells.append((r, c))
    
    # Identify opponent role
    opponent = 'o' if role == 'x' else 'x'
    
    # Winning and Blocking logic
    lines = [
        [('1','1'), ('1','2'), ('1','3')],
        [('2','1'), ('2','2'), ('2','3')],
        [('3','1'), ('3','2'), ('3','3')],
        [('1','1'), ('2','1'), ('3','1')],
        [('1','2'), ('2','2'), ('3','2')],
        [('1','3'), ('2','3'), ('3','3')],
        [('1','1'), ('2','2'), ('3','3')],
        [('1','3'), ('2','2'), ('3','1')]
    ]
    
    def find_move(target_role):
        for line in lines:
            vals = [board[pos] for pos in line]
            if vals.count(target_role) == 2 and vals.count('b') == 1:
                return line[vals.index('b')]
        return None

    # 1. Try to win
    move = find_move(role)
    if move:
        return f"mark({move[0]},{move[1]})"
    
    # 2. Try to block
    move = find_move(opponent)
    if move:
        return f"mark({move[0]},{move[1]})"
    
    # 3. Take center
    if ('2', '2') in empty_cells:
        return "mark(2,2)"
    
    # 4. Default to first empty cell
    if empty_cells:
        move = empty_cells[0]
        return f"mark({move[0]},{move[1]})"
    
    return ""
