
def policy(board: list[list[int]]) -> tuple[int, int]:
    def check_win(b, player):
        # Check rows
        for row in b:
            if all(cell == player for cell in row):
                return True
        # Check columns
        for col in range(4):
            if all(b[row][col] == player for row in range(4)):
                return True
        # Check main diagonal
        if all(b[i][i] == player for i in range(4)):
            return True
        # Check other diagonal
        if all(b[i][3-i] == player for i in range(4)):
            return True
        return False

    # Check for our win
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                temp = [row[:] for row in board]
                temp[r][c] = 1
                if check_win(temp, 1):
                    return (r, c)

    # Check for opponent's win to block
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                temp = [row[:] for row in board]
                temp[r][c] = -1
                if check_win(temp, -1):
                    return (r, c)

    # Priority move selection if no urgent win/block
    priority_order = [
        (1,1), (1,2), (2,1), (2,2),     # Center
        (0,0), (0,3), (3,0), (3,3),     # Corners
        (0,1), (0,2),                   # Top edges
        (1,0), (1,3),                   # Left/Right edges
        (2,0), (2,3), (3,1), (3,2)      # Bottom edges
    ]
    for r, c in priority_order:
        if board[r][c] == 0:
            return (r, c)

    # Fallback: pick first available cell
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                return (r, c)
