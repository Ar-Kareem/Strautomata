
def check_win(board, player):
    for i in range(4):
        for j in range(2):
            if board[i][j] == board[i][j+1] == board[i][j+2] == player:
                return True
    for j in range(4):
        for i in range(2):
            if board[i][j] == board[i+1][j] == board[i+2][j] == player:
                return True
    for i in range(2):
        for j in range(2):
            if board[i][j] == board[i+1][j+1] == board[i+2][j+2] == player:
                return True
    for i in range(2):
        for j in range(2, 4):
            if board[i][j] == board[i+1][j-1] == board[i+2][j-2] == player:
                return True
    return False

def policy(board: list[list[int]]) -> tuple[int, int]:
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                board[i][j] = 1
                if check_win(board, 1):
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = 0
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                board[i][j] = -1
                if check_win(board, -1):
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = 0
    priority = [
        [1, 2, 2, 1],
        [2, 3, 3, 2],
        [2, 3, 3, 2],
        [1, 2, 2, 1]
    ]
    best_moves = []
    best_score = -1
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                if priority[i][j] > best_score:
                    best_score = priority[i][j]
                    best_moves = [(i, j)]
                elif priority[i][j] == best_score:
                    best_moves.append((i, j))
    if best_moves:
        return best_moves[0]
    return (0, 0)
