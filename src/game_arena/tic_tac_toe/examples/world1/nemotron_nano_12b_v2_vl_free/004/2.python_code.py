
def policy(board: list[list[int]]) -> tuple[int, int]:
    def is_winning_move(player, r, c):
        # Check row
        row_win = True
        for i in range(3):
            if i != c and board[r][i] != player:
                row_win = False
                break
        if row_win:
            return True
        # Check column
        col_win = True
        for i in range(3):
            if i != r and board[i][c] != player:
                col_win = False
                break
        if col_win:
            return True
        # Check diagonal (if applicable)
        if r == c:
            diag_win = True
            for i in range(3):
                if i != r and board[i][i] != player:
                    diag_win = False
                    break
            if diag_win:
                return True
        # Check anti-diagonal (if applicable)
        if r + c == 2:
            anti_win = True
            for i in range(3):
                j = 2 - i
                if (i, j) == (r, c):
                    continue
                if board[i][j] != player:
                    anti_win = False
                    break
            if anti_win:
                return True
        return False

    priority = [(1, 1), (0, 0), (0, 2), (2, 0), (2, 2), (0, 1), (1, 0), (1, 2), (2, 1)]
    for r, c in priority:
        if board[r][c] == 0:
            if is_winning_move(1, r, c):
                return (r, c)
    for r, c in priority:
        if board[r][c] == 0:
            if is_winning_move(-1, r, c):
                return (r, c)
    for r, c in priority:
        if board[r][c] == 0:
            return (r, c)
    return (0, 0)
