
def policy(state: list[list[object]], role: str) -> str:
    # 1. Parse the board
    board = {}
    empty_cells = []
    for fact in state:
        if fact[0] == "cell":
            r, c, val = int(fact[1]), int(fact[2]), fact[3]
            board[(r, c)] = val
            if val == 'b':
                empty_cells.append((r, c))

    opponent = 'o' if role == 'x' else 'x'

    def check_win(current_board, player):
        for i in range(1, 4):
            # Rows and Columns
            if all(current_board.get((i, j)) == player for j in range(1, 4)): return True
            if all(current_board.get((j, i)) == player for j in range(1, 4)): return True
        # Diagonals
        if all(current_board.get((i, i)) == player for i in range(1, 4)): return True
        if all(current_board.get((i, 4 - i)) == player for i in range(1, 4)): return True
        return False

    # 2. Heuristic: Try to win immediately
    for cell in empty_cells:
        board[cell] = role
        if check_win(board, role):
            return f"mark({cell[0]},{cell[1]})"
        board[cell] = 'b'

    # 3. Heuristic: Block opponent win
    for cell in empty_cells:
        board[cell] = opponent
        if check_win(board, opponent):
            return f"mark({cell[0]},{cell[1]})"
        board[cell] = 'b'

    # 4. Default: Pick the first available cell (legal move)
    if empty_cells:
        move = empty_cells[0]
        return f"mark({move[0]},{move[1]})"
    
    return ""
