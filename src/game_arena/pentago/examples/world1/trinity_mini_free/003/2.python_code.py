
def policy(you, opponent) -> str:
    # Helper function to check if a player has a 5-in-a-row
    def check_win(board, player):
        # Check horizontal lines
        for r in range(6):
            for c in range(2):
                if all(board[r][c + d] == player for d in range(5)):
                    return True
        # Check vertical lines
        for c in range(6):
            for r in range(2):
                if all(board[r + d][c] == player for d in range(5)):
                    return True
        # Check diagonal (top-left to bottom-right)
        for r in range(2):
            for c in range(2):
                if all(board[r + d][c + d] == player for d in range(5)):
                    return True
        # Check diagonal (top-right to bottom-left)
        for r in range(2):
            for c in range(4, 2, -1):
                if all(board[r + d][c - d] == player for d in range(5)):
                    return True
        return False

    # Find all empty cells (both you and opponent are 0)
    empty_cells = [(r, c) for r in range(6) for c in range(6) if you[r][c] == 0 and opponent[r][c] == 0]
    
    # Check for immediate wins (your move creates a 5-in-a-row)
    for r, c in empty_cells:
        # Simulate placing your marble
        board = [row[:] for row in you]
        board[r][c] = 1
        if check_win(board, 1):
            return f"{r + 1},{c + 1},0,L"  # Place at (r+1, c+1), rotate quad 0 left
    
    # Check for opponent threats (blocking their potential win)
    for r, c in empty_cells:
        # Simulate opponent placing a marble
        board = [row[:] for row in opponent]
        board[r][c] = 1
        if check_win(board, 0):
            # Block by placing your marble here
            board = [row[:] for row in you]
            board[r][c] = 1
            return f"{r + 1},{c + 1},0,L"
    
    # Prefer center cells (rows 3-4, columns 3-4) if available
    center_cells = [(r, c) for r in (2, 3) for c in (2, 3) if (r, c) in empty_cells]
    if center_cells:
        r, c = center_cells[0]
        return f"{r + 1},{c + 1},0,L"
    
    # Prefer corners if center is unavailable
    corners = [(0, 0), (0, 5), (5, 0), (5, 5)]
    for r, c in corners:
        if (r, c) in empty_cells:
            return f"{r + 1},{c + 1},0,L"
    
    # Fallback to any available cell
    r, c = empty_cells[0]
    return f"{r + 1},{c + 1},0,L"
