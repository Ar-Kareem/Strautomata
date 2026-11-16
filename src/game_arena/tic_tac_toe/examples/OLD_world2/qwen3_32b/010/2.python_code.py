
def policy(board):
    def is_winning_move(r, c, player):
        # Check if placing the player at (r,c) completes a winning line
        # Row check
        row_win = True
        for i in range(4):
            if board[r][i] != player and i != c:
                row_win = False
                break
        if row_win:
            return True

        # Column check
        col_win = True
        for i in range(4):
            if board[i][c] != player and i != r:
                col_win = False
                break
        if col_win:
            return True

        # Main diagonal check (r == c)
        if r == c:
            diag1_win = True
            for i in range(4):
                if board[i][i] != player and i != r:
                    diag1_win = False
                    break
            if diag1_win:
                return True

        # Anti-diagonal check (r + c == 3)
        if r + c == 3:
            diag2_win = True
            for i in range(4):
                j = 3 - i
                if not (i == r and j == c) and board[i][j] != player:
                    diag2_win = False
                    break
            if diag2_win:
                return True

        return False

    # 1. Check for an immediate win
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0 and is_winning_move(r, c, 1):
                return (r, c)

    # 2. Check if the opponent can win in the next move and block it
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0 and is_winning_move(r, c, -1):
                return (r, c)

    # 3. Fallback: select center, then corners, then edges in fixed order
    for (r, c) in [(1, 1), (1, 2), (2, 1), (2, 2)]:
        if board[r][c] == 0:
            return (r, c)

    for (r, c) in [(0, 0), (0, 3), (3, 0), (3, 3)]:
        if board[r][c] == 0:
            return (r, c)

    for (r, c) in [(0, 1), (0, 2), (1, 0), (1, 3), (2, 0), (2, 3), (3, 1), (3, 2)]:
        if board[r][c] == 0:
            return (r, c)

    # Fallback to the top-left corner if all else fails
    return (0, 0)
