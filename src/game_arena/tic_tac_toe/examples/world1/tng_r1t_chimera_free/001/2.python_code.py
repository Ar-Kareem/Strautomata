
def policy(board: list[list[int]]) -> tuple[int, int]:
    def is_win(b, player, i, j):
        # Simulate placing the player's mark at (i,j) and check for a win
        temp = [row.copy() for row in b]
        temp[i][j] = player
        # Check row
        if sum(temp[i]) == player * 3:
            return True
        # Check column
        if sum(temp[r][j] for r in range(3)) == player * 3:
            return True
        # Check main diagonal
        if i == j and sum(temp[k][k] for k in range(3)) == player * 3:
            return True
        # Check anti-diagonal
        if i + j == 2 and sum(temp[k][2 - k] for k in range(3)) == player * 3:
            return True
        return False
    
    # Collect all empty cells
    empty = [(i, j) for i in range(3) for j in range(3) if board[i][j] == 0]
    
    # Check for immediate win
    for i, j in empty:
        if is_win(board, 1, i, j):
            return (i, j)
    
    # Check for opponent's immediate win and block
    for i, j in empty:
        if is_win(board, -1, i, j):
            return (i, j)
    
    # Prefer center, then corners, then edges
    preferred_order = [(1, 1), (0, 0), (0, 2), (2, 0), (2, 2),
                       (0, 1), (1, 0), (1, 2), (2, 1)]
    
    for move in preferred_order:
        if board[move[0]][move[1]] == 0:
            return move
    
    # Fallback (shouldn't be reached in a valid game state)
    return empty[0]
