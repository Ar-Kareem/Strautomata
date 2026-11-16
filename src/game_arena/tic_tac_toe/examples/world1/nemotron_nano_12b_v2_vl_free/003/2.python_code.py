
def policy(board: list[list[int]]) -> tuple[int, int]:
    def check_win(temp, player):
        # Check rows
        if any(all(cell == player for cell in row) for row in temp):
            return True
        # Check columns
        if any(all(temp[row][col] == player for row in range(3)) for col in range(3)):
            return True
        # Check main diagonal
        if all(temp[i][i] == player for i in range(3)):
            return True
        # Check anti-diagonal
        if all(temp[i][2 - i] == player for i in range(3)):
            return True
        return False

    # Step 1: Check for a winning move
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                temp = [row.copy() for row in board]
                temp[i][j] = 1
                if check_win(temp, 1):
                    return (i, j)
    
    # Step 2: Check for opponent's winning move to block
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                temp = [row.copy() for row in board]
                temp[i][j] = -1
                if check_win(temp, -1):
                    return (i, j)
    
    # Step 3: Choose best strategic move
    if board[1][1] == 0:
        return (1, 1)
    
    # Check corners in order
    for (i, j) in [(0,0), (0,2), (2,0), (2,2)]:
        if board[i][j] == 0:
            return (i, j)
    
    # Check edges
    for (i, j) in [(0,1), (1,0), (1,2), (2,1)]:
        if board[i][j] == 0:
            return (i, j)
    
    # Fallback (theoretical, should not happen)
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                return (i, j)
    return (0, 0)  # This line is a fallback and unlikely to execute
