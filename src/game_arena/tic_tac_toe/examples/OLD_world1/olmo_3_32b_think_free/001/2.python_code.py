
def policy(board: list[list[int]]) -> tuple[int, int]:
    def check_win(b, player):
        # Check rows
        for row in b:
            if row[0] == row[1] == row[2] == player:
                return True
        # Check columns
        for col in range(3):
            if b[0][col] == b[1][col] == b[2][col] == player:
                return True
        # Check diagonals
        if b[0][0] == b[1][1] == b[2][2] == player:
            return True
        if b[0][2] == b[1][1] == b[2][0] == player:
            return True
        return False

    # Step 1: Check for winning moves
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                temp = [row.copy() for row in board]
                temp[i][j] = 1
                if check_win(temp, 1):
                    return (i, j)
    
    # Step 2: Check for opponent's winning moves and block
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                temp = [row.copy() for row in board]
                temp[i][j] = -1
                if check_win(temp, -1):
                    return (i, j)
    
    # Step 3: Choose best move in priority order
    for move in [(1,1), (0,0), (0,2), (2,0), (2,2), (0,1), (1,0), (1,2), (2,1)]:
        i, j = move
        if board[i][j] == 0:
            return (i, j)
    
    # Fallback (shouldn't happen if game is active)
    return (0, 0)
