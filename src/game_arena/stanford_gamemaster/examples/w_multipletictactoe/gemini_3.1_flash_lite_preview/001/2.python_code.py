
def policy(state, role):
    # Parse the state: Find grid cells
    # We are looking for moves "mark(b1, b2, r, c)"
    # A cell is ["cell", b1, b2, r, c, val]
    
    cells = {}
    for fact in state:
        if fact[0] == "cell":
            # fact: ["cell", b1, b2, r, c, val]
            cells[(int(fact[1]), int(fact[2]), int(fact[3]), int(fact[4]))] = fact[5]
            
    def get_board_lines(b1, b2):
        lines = []
        # Rows
        for r in range(1, 4):
            lines.append(((b1, b2, r, 1), (b1, b2, r, 2), (b1, b2, r, 3)))
        # Cols
        for c in range(1, 4):
            lines.append(((b1, b2, 1, c), (b1, b2, 2, c), (b1, b2, 3, c)))
        # Diagonals
        lines.append(((b1, b2, 1, 1), (b1, b2, 2, 2), (b1, b2, 3, 3)))
        lines.append(((b1, b2, 1, 3), (b1, b2, 2, 2), (b1, b2, 3, 1)))
        return lines

    def find_winning_move(b1, b2, player):
        for line in get_board_lines(b1, b2):
            values = [cells.get(pos) for pos in line]
            if values.count(player) == 2 and values.count('b') == 1:
                return [pos for pos in line if cells.get(pos) == 'b'][0]
        return None

    # Priority 1: Check winning/blocking move on middle board (2, 2)
    win_move = find_winning_move(2, 2, role)
    if win_move:
        return f"mark({win_move[0]}, {win_move[1]}, {win_move[2]}, {win_move[3]})"
    
    opp = 'o' if role == 'x' else 'x'
    block_move = find_winning_move(2, 2, opp)
    if block_move:
        return f"mark({block_move[0]}, {block_move[1]}, {block_move[2]}, {block_move[3]})"

    # Priority 2: Any legal move on board (2, 2)
    for r in range(1, 4):
        for c in range(1, 4):
            if cells.get((2, 2, r, c)) == 'b':
                return f"mark(2, 2, {r}, {c})"

    # Priority 3: Fallback - any legal move
    for pos, val in cells.items():
        if val == 'b':
            return f"mark({pos[0]}, {pos[1]}, {pos[2]}, {pos[3]})"
            
    return ""
