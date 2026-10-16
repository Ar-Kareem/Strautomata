
def policy(board: list[list[int]]) -> tuple[int, int]:
    def is_win(b, player):
        # Check rows
        for row in b:
            if all(cell == player for cell in row):
                return True
        # Check columns
        for col in range(3):
            if all(b[row][col] == player for row in range(3)):
                return True
        # Check diagonals
        if all(b[i][i] == player for i in range(3)):
            return True
        if all(b[i][2 - i] == player for i in range(3)):
            return True
        return False
    
    # Check for winning move for player 1
    for row in range(3):
        for col in range(3):
            if board[row][col] == 0:
                new_board = [r.copy() for r in board]
                new_board[row][col] = 1
                if is_win(new_board, 1):
                    return (row, col)
    
    # Check for opponent's winning move to block
    for row in range(3):
        for col in range(3):
            if board[row][col] == 0:
                new_board = [r.copy() for r in board]
                new_board[row][col] = -1
                if is_win(new_board, -1):
                    return (row, col)
    
    # Choose center if available
    if board[1][1] == 0:
        return (1, 1)
    
    # Check corners in order
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    for r, c in corners:
        if board[r][c] == 0:
            return (r, c)
    
    # Check edges in order
    edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
    for r, c in edges:
        if board[r][c] == 0:
            return (r, c)
    
    # Fallback return (should not be reached with valid input)
    return (0, 0)
