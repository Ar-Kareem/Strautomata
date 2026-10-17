
def policy(state: list[list[object]], role: str) -> str:
    # Represent the board as a 3x3 matrix
    board = {}
    for fact in state:
        if fact[0] == "cell":
            board[(int(fact[1]), int(fact[2]))] = fact[3]

    def check_loss(r, c, p, current_board):
        # Simulate move
        temp_board = current_board.copy()
        temp_board[(r, c)] = p
        
        # Win-check lines: rows, cols, diagonals
        lines = [
            [(1, 1), (1, 2), (1, 3)], [(2, 1), (2, 2), (2, 3)], [(3, 1), (3, 2), (3, 3)],
            [(1, 1), (2, 1), (3, 1)], [(1, 2), (2, 2), (3, 2)], [(1, 3), (2, 3), (3, 3)],
            [(1, 1), (2, 2), (3, 3)], [(1, 3), (2, 2), (3, 1)]
        ]
        
        for line in lines:
            if all(temp_board.get(pos) == p for pos in line):
                return True
        return False

    # Collect legal moves
    empty_cells = [pos for pos, val in board.items() if val == 'b']
    
    # 1. Try to find a move that doesn't lose
    safe_moves = []
    for (r, c) in empty_cells:
        if not check_loss(r, c, role, board):
            safe_moves.append((r, c))
    
    if safe_moves:
        move = safe_moves[0]
        return f"mark({move[0]},{move[1]})"
    
    # 2. If no safe moves, pick any remaining move
    if empty_cells:
        move = empty_cells[0]
        return f"mark({move[0]},{move[1]})"
    
    return ""
