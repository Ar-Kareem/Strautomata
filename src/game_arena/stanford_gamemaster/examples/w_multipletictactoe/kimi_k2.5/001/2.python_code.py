
def policy(state: list[list[object]], role: str) -> str:
    # Helper functions for tic-tac-toe logic
    def is_win(board, player, move):
        """Check if placing player at move results in 3 in a row."""
        temp = dict(board)
        temp[move] = player
        lines = [
            [("1","1"),("1","2"),("1","3")], [("2","1"),("2","2"),("2","3")], [("3","1"),("3","2"),("3","3")],
            [("1","1"),("2","1"),("3","1")], [("1","2"),("2","2"),("3","2")], [("1","3"),("2","3"),("3","3")],
            [("1","1"),("2","2"),("3","3")], [("1","3"),("2","2"),("3","1")]
        ]
        for line in lines:
            if all(temp.get(cell) == player for cell in line):
                return True
        return False
    
    def is_fork(board, player, move):
        """Check if placing player at move creates a fork (two winning threats)."""
        temp = dict(board)
        temp[move] = player
        lines = [
            [("1","1"),("1","2"),("1","3")], [("2","1"),("2","2"),("2","3")], [("3","1"),("3","2"),("3","3")],
            [("1","1"),("2","1"),("3","1")], [("1","2"),("2","2"),("3","2")], [("1","3"),("2","3"),("3","3")],
            [("1","1"),("2","2"),("3","3")], [("1","3"),("2","2"),("3","1")]
        ]
        threats = 0
        for line in lines:
            my_marks = sum(1 for cell in line if temp.get(cell) == player)
            empty = sum(1 for cell in line if cell not in temp)
            if my_marks == 2 and empty == 1:
                threats += 1
        return threats >= 2
    
    # Parse state
    middle_board = {}  # (x,y) -> content for board (2,2)
    side_empty = []    # list of (bx,by,cx,cy) for non-middle boards
    
    for prop in state:
        if prop[0] == "cell":
            _, bx, by, cx, cy, content = prop
            if bx == "2" and by == "2":
                if content != "b":
                    middle_board[(cx, cy)] = content
            else:
                if content == "b":
                    side_empty.append((bx, by, cx, cy))
    
    opponent = "o" if role == "x" else "x"
    
    # Find empty cells on middle board
    middle_empty = []
    for x in ["1", "2", "3"]:
        for y in ["1", "2", "3"]:
            if (x, y) not in middle_board:
                middle_empty.append((x, y))
    
    # 1. Check for immediate win on middle board
    for move in middle_empty:
        if is_win(middle_board, role, move):
            return f"mark(2,2,{move[0]},{move[1]})"
    
    # 2. Check for block (opponent win)
    for move in middle_empty:
        if is_win(middle_board, opponent, move):
            return f"mark(2,2,{move[0]},{move[1]})"
    
    # 3. Check for fork creation
    for move in middle_empty:
        if is_fork(middle_board, role, move):
            return f"mark(2,2,{move[0]},{move[1]})"
    
    # 4. Play on side board to keep control
    if side_empty:
        # Pick first available side move
        move = side_empty[0]
        return f"mark({move[0]},{move[1]},{move[2]},{move[3]})"
    
    # 5. Fallback: play any empty on middle board (should be rare)
    if middle_empty:
        move = middle_empty[0]
        return f"mark(2,2,{move[0]},{move[1]})"
    
    # Emergency fallback (should never reach here in legal game)
    return "mark(1,1,1,1)"
