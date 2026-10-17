
def policy(state: list[list[object]], role: str) -> str:
    # Build the board representation
    board = {}
    for fact in state:
        if fact[0] == "cell":
            r, c, val = int(fact[1]), int(fact[2]), fact[3]
            board[(r, c)] = val

    empty_cells = [pos for pos, val in board.items() if val == "b"]
    
    opponent = "o" if role == "x" else "x"
    
    # Helper to check for a winning move
    def get_winning_move(player):
        for r, c in empty_cells:
            # Simulate move
            board[(r, c)] = player
            # Check rows, cols, diagonals
            for i in range(1, 4):
                if all(board.get((i, j)) == player for j in range(1, 4)): return f"mark({i},{c})"
                if all(board.get((j, i)) == player for j in range(1, 4)): return f"mark({r},{i})"
            if all(board.get((i, i)) == player for i in range(1, 4)): return f"mark({r},{c})"
            if all(board.get((i, 4 - i)) == player for i in range(1, 4)): return f"mark({r},{c})"
            # Backtrack
            board[(r, c)] = "b"
        return None

    # 1. Try to win
    win = get_winning_move(role)
    if win: return win
    
    # 2. Try to block opponent
    block = get_winning_move(opponent)
    if block: return block
    
    # 3. Take center if available
    if (2, 2) in empty_cells:
        return "mark(2,2)"
        
    # 4. Default to the first available legal move
    if empty_cells:
        r, c = empty_cells[0]
        return f"mark({r},{c})"
    
    return ""
