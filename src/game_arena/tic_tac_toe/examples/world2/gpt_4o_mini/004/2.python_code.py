
def policy(board: list[list[int]]) -> tuple[int, int]:
    def check_win(condition):
        return (condition.count(1) == 4)

    def check_block(condition):
        return (condition.count(-1) == 4)

    # Check rows for winning/blocking move
    for i in range(4):
        if board[i].count(1) == 3 and board[i].count(0) == 1:
            return i, board[i].index(0)
        if board[i].count(-1) == 3 and board[i].count(0) == 1:
            return i, board[i].index(0)

    # Check columns for winning/blocking move
    for j in range(4):
        col = [board[i][j] for i in range(4)]
        if col.count(1) == 3 and col.count(0) == 1:
            return col.index(0), j
        if col.count(-1) == 3 and col.count(0) == 1:
            return col.index(0), j

    # Check diagonals for winning/blocking move
    diag1 = [board[i][i] for i in range(4)]
    diag2 = [board[i][3-i] for i in range(4)]
    
    if diag1.count(1) == 3 and diag1.count(0) == 1:
        idx = diag1.index(0)
        return idx, idx
    if diag1.count(-1) == 3 and diag1.count(0) == 1:
        idx = diag1.index(0)
        return idx, idx
    
    if diag2.count(1) == 3 and diag2.count(0) == 1:
        idx = diag2.index(0)
        return idx, 3-idx
    if diag2.count(-1) == 3 and diag2.count(0) == 1:
        idx = diag2.index(0)
        return idx, 3-idx

    # If no immediate win/block, prefer center and corners
    preferred_moves = [(1, 1), (0, 0), (0, 3), (3, 0), (3, 3)]
    for move in preferred_moves:
        if board[move[0]][move[1]] == 0:
            return move

    # Last option: any available cell
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                return i, j

    # In case of no moves (should not happen)
    return -1, -1
