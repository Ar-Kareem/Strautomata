
def policy(state: list[list[object]], role: str) -> str:
    # Parse the board
    board = {}
    for prop in state:
        if prop[0] == "cell":
            row, col, value = int(prop[1]), int(prop[2]), prop[3]
            board[(row, col)] = value
    
    # Ensure all cells are represented
    for i in range(1, 4):
        for j in range(1, 4):
            if (i, j) not in board:
                board[(i, j)] = "b"
    
    # Determine opponent role
    opponent = "o" if role == "x" else "x"
    
    # Get legal moves (empty cells)
    legal_moves = [(i, j) for i in range(1, 4) for j in range(1, 4) if board[(i, j)] == "b"]
    
    def check_three_in_row(test_board, test_role):
        """Check if test_role has three in a row"""
        lines = [
            [(1,1), (1,2), (1,3)],
            [(2,1), (2,2), (2,3)],
            [(3,1), (3,2), (3,3)],
            [(1,1), (2,1), (3,1)],
            [(1,2), (2,2), (3,2)],
            [(1,3), (2,3), (3,3)],
            [(1,1), (2,2), (3,3)],
            [(1,3), (2,2), (3,1)],
        ]
        for line in lines:
            if all(test_board.get(pos) == test_role for pos in line):
                return True
        return False
    
    def would_lose(pos):
        """Check if placing our mark at pos would create three in a row for us"""
        test_board = board.copy()
        test_board[pos] = role
        return check_three_in_row(test_board, role)
    
    def would_opponent_win_next(pos):
        """Check if opponent would win if we don't block this position"""
        test_board = board.copy()
        test_board[pos] = opponent
        return check_three_in_row(test_board, opponent)
    
    # First priority: find moves that don't lose
    safe_moves = [move for move in legal_moves if not would_lose(move)]
    
    if not safe_moves:
        # If all moves lose, just pick any legal move
        return f"mark({legal_moves[0][0]},{legal_moves[0][1]})"
    
    # Second priority: block opponent from winning
    blocking_moves = [move for move in safe_moves if would_opponent_win_next(move)]
    
    if blocking_moves:
        # Prefer blocking moves that also don't set up dangerous positions
        return f"mark({blocking_moves[0][0]},{blocking_moves[0][1]})"
    
    # Third priority: choose strategically from safe moves
    # Prefer center, then edges, then corners
    priority_order = [(2, 2), (1, 2), (2, 1), (2, 3), (3, 2), (1, 1), (1, 3), (3, 1), (3, 3)]
    
    for pos in priority_order:
        if pos in safe_moves:
            return f"mark({pos[0]},{pos[1]})"
    
    # Fallback: return any safe move
    return f"mark({safe_moves[0][0]},{safe_moves[0][1]})"
