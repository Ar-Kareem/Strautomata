
def policy(board):
    def get_row(c):
        for r in reversed(range(6)):
            if board[r][c] == 0:
                return r
        return None

    def check_win(b, r, c, player):
        # Check horizontal
        count = 1
        cc = c - 1
        while cc >= 0 and b[r][cc] == player:
            count += 1
            cc -= 1
        cc = c + 1
        while cc < 7 and b[r][cc] == player:
            count += 1
            cc += 1
        if count >= 4:
            return True

        # Check vertical
        count = 1
        rr = r - 1
        while rr >= 0 and b[rr][c] == player:
            count += 1
            rr -= 1
        if count >= 4:
            return True

        # Check diagonal: top-left to bottom-right
        count = 1
        rr, cc = r - 1, c - 1
        while rr >= 0 and cc >= 0 and b[rr][cc] == player:
            count += 1
            rr -= 1
            cc -= 1
        rr, cc = r + 1, c + 1
        while rr < 6 and cc < 7 and b[rr][cc] == player:
            count += 1
            rr += 1
            cc += 1
        if count >= 4:
            return True

        # Check diagonal: top-right to bottom-left
        count = 1
        rr, cc = r - 1, c + 1
        while rr >= 0 and cc < 7 and b[rr][cc] == player:
            count += 1
            rr -= 1
            cc += 1
        rr, cc = r + 1, c - 1
        while rr < 6 and cc >= 0 and b[rr][cc] == player:
            count += 1
            rr += 1
            cc -= 1
        if count >= 4:
            return True

        return False

    # Check for winning moves
    for c in range(7):
        row = get_row(c)
        if row is not None:
            temp_board = [r.copy() for r in board]
            temp_board[row][c] = 1
            if check_win(temp_board, row, c, 1):
                return c

    # Check for opponent's winning moves
    for c in range(7):
        row = get_row(c)
        if row is not None:
            temp_board = [r.copy() for r in board]
            temp_board[row][c] = -1
            if check_win(temp_board, row, c, -1):
                return c

    # Heuristic: prefer center columns
    for c in [3, 2, 4, 1, 5, 0, 6]:
        if get_row(c) is not None:
            return c

    return 0
