
def policy(board: list[list[int]]) -> tuple[int, int]:
    empty_cells = [(r, c) for r in range(3) for c in range(3) if board[r][c] == 0]
    
    # Check for player's winning move
    for r, c in empty_cells:
        row_sum = sum(board[r]) + 1
        if row_sum == 3:
            return (r, c)
        col_sum = sum(board[row][c] for row in range(3)) + 1
        if col_sum == 3:
            return (r, c)
        if r == c:
            diag1_sum = sum(board[i][i] for i in range(3)) + 1
            if diag1_sum == 3:
                return (r, c)
        if r + c == 2:
            diag2_sum = sum(board[i][2-i] for i in range(3)) + 1
            if diag2_sum == 3:
                return (r, c)
    
    # Check for opponent's winning move to block
    for r, c in empty_cells:
        row_sum = sum(board[r]) - 1
        if row_sum == -3:
            return (r, c)
        col_sum = sum(board[row][c] for row in range(3)) - 1
        if col_sum == -3:
            return (r, c)
        if r == c:
            diag1_sum = sum(board[i][i] for i in range(3)) - 1
            if diag1_sum == -3:
                return (r, c)
        if r + c == 2:
            diag2_sum = sum(board[i][2-i] for i in range(3)) - 1
            if diag2_sum == -3:
                return (r, c)
    
    # Default move: center, then corners, then edges
    if board[1][1] == 0:
        return (1, 1)
    corners = [(0,0), (0,2), (2,0), (2,2)]
    for r, c in corners:
        if board[r][c] == 0:
            return (r, c)
    edges = [(0,1), (1,0), (1,2), (2,1)]
    for r, c in edges:
        if board[r][c] == 0:
            return (r, c)
    
    return empty_cells[0]  # Fallback if no other logic applies (shouldn't reach here)
