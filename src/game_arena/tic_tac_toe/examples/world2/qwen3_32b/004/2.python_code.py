
def policy(board: list[list[int]]) -> tuple[int, int]:
    def is_winning(r, c, player):
        # Check row
        row_win = True
        for col in range(4):
            if board[r][col] != player and col != c:
                row_win = False
                break
        if row_win:
            return True

        # Check column
        col_win = True
        for row in range(4):
            if board[row][c] != player and row != r:
                col_win = False
                break
        if col_win:
            return True

        # Check main diagonal
        if r == c:
            diag_win = True
            for i in range(4):
                if board[i][i] != player and i != r:
                    diag_win = False
                    break
            if diag_win:
                return True

        # Check anti-diagonal
        if r + c == 3:
            diag_win = True
            for i in range(4):
                j = 3 - i
                if i == r and j == c:
                    continue
                if board[i][j] != player:
                    diag_win = False
                    break
            if diag_win:
                return True

        return False

    # Check for own winning move
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0 and is_winning(r, c, 1):
                return (r, c)

    # Check for opponent's winning move
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0 and is_winning(r, c, -1):
                return (r, c)

    # No immediate win or block; choose move based on priority
    possible_moves = [(r, c) for r in range(4) for c in range(4) if board[r][c] == 0]

    def move_priority(move):
        r, c = move
        # Priority 0: center cells
        if (r in [1, 2]) and (c in [1, 2]):
            return 0
        # Priority 1: corners
        if (r, c) in [(0, 0), (0, 3), (3, 0), (3, 3)]:
            return 1
        # Priority 2: edge centers
        if (r in [0, 3] and c in [1, 2]) or (c in [0, 3] and r in [1, 2]):
            return 2
        # Priority 3: others
        return 3

    possible_moves.sort(key=move_priority)
    return possible_moves[0]
