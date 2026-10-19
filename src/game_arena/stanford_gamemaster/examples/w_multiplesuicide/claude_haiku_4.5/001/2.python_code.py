
def policy(state: list[list[object]], role: str) -> str:
    # Parse the state to find current board configuration
    board_state = {}
    for prop in state:
        if prop[0] == "cell":
            board_id = int(prop[1])
            row = int(prop[2])
            col = int(prop[3])
            value = prop[4]
            if board_id not in board_state:
                board_state[board_id] = {}
            board_state[board_id][(row, col)] = value
    
    # Only care about middle board (board 2)
    middle_board = board_state.get(2, {})
    
    def has_three_in_row(board, player):
        """Check if a player has three in a row on the board"""
        # Check rows
        for row in [1, 2, 3]:
            if all(board.get((row, col), 'b') == player for col in [1, 2, 3]):
                return True
        # Check columns
        for col in [1, 2, 3]:
            if all(board.get((row, col), 'b') == player for row in [1, 2, 3]):
                return True
        # Check diagonals
        if all(board.get((i, i), 'b') == player for i in [1, 2, 3]):
            return True
        if all(board.get((i, 4-i), 'b') == player for i in [1, 2, 3]):
            return True
        return False
    
    def would_create_three(board, row, col, player):
        """Check if placing at (row, col) would create three in a row"""
        test_board = dict(board)
        test_board[(row, col)] = player
        return has_three_in_row(test_board, player)
    
    # Collect all empty cells on middle board
    empty_middle = [(r, c) for r in [1, 2, 3] for c in [1, 2, 3] 
                     if middle_board.get((r, c), 'b') == 'b']
    
    # Priority 1: Avoid creating three-in-a-row for ourselves
    safe_moves = []
    for r, c in empty_middle:
        if not would_create_three(middle_board, r, c, role):
            safe_moves.append((r, c))
    
    # If we have safe moves on middle board, prefer center and strategic positions
    if safe_moves:
        # Prefer center, then edges, then corners
        center = [(2, 2)]
        edges = [(1, 2), (2, 1), (2, 3), (3, 2)]
        corners = [(1, 1), (1, 3), (3, 1), (3, 3)]
        
        for priority_cells in [center, edges, corners]:
            for r, c in priority_cells:
                if (r, c) in safe_moves:
                    return f"mark(2,{r},{c})"
    
    # If no safe moves on middle board, try other boards
    all_boards = [1, 3, 2]  # Try boards 1, 3 first, then 2 as last resort
    for board_id in all_boards:
        board = board_state.get(board_id, {})
        empty_cells = [(r, c) for r in [1, 2, 3] for c in [1, 2, 3] 
                       if board.get((r, c), 'b') == 'b']
        
        # Find safe moves on this board
        for r, c in empty_cells:
            if not would_create_three(board, r, c, role):
                return f"mark({board_id},{r},{c})"
    
    # Fallback: return any legal move (shouldn't reach here)
    for board_id in [1, 2, 3]:
        board = board_state.get(board_id, {})
        for r in [1, 2, 3]:
            for c in [1, 2, 3]:
                if board.get((r, c), 'b') == 'b':
                    return f"mark({board_id},{r},{c})"
    
    return "mark(1,1,1)"
