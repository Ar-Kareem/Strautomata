
def policy(board: list[list[int]]) -> tuple[int, int]:
    def can_win(board, i, j, player):
        # Check row
        if sum(board[i]) == player * 3:
            return True
        # Check column
        if sum(board[row][j] for row in range(4)) == player * 3:
            return True
        # Check main diagonal
        if i == j:
            diag_sum = sum(board[k][k] for k in range(4))
            if diag_sum == player * 3:
                return True
        # Check anti-diagonal
        if i + j == 3:
            anti_diag_sum = sum(board[k][3 - k] for k in range(4))
            if anti_diag_sum == player * 3:
                return True
        return False

    # Check for winning move
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                if can_win(board, i, j, 1):
                    return (i, j)
    
    # Check for blocking opponent's win
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                if can_win(board, i, j, -1):
                    return (i, j)
    
    # Prioritize center cells
    centers = [(1, 1), (1, 2), (2, 1), (2, 2)]
    for c in centers:
        if board[c[0]][c[1]] == 0:
            return c
    
    # Choose any corner
    corners = [(0, 0), (0, 3), (3, 0), (3, 3)]
    for c in corners:
        if board[c[0]][c[1]] == 0:
            return c
    
    # Choose first available cell
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                return (i, j)
    
    # If no moves are possible (shouldn't happen)
    return (0, 0)
