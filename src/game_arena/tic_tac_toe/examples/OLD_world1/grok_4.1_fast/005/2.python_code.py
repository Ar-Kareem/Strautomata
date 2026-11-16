
def is_winner(board: list[list[int]], player: int) -> bool:
    # Check rows
    for i in range(3):
        if board[i][0] == player and board[i][1] == player and board[i][2] == player:
            return True
    # Check columns
    for j in range(3):
        if board[0][j] == player and board[1][j] == player and board[2][j] == player:
            return True
    # Check diagonals
    if board[0][0] == player and board[1][1] == player and board[2][2] == player:
        return True
    if board[0][2] == player and board[1][1] == player and board[2][0] == player:
        return True
    return False

def is_full(board: list[list[int]]) -> bool:
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                return False
    return True

def minimax(board: list[list[int]], player: int) -> int:
    if is_winner(board, 1):
        return 1
    if is_winner(board, -1):
        return -1
    if is_full(board):
        return 0

    best_score = -float('inf') if player == 1 else float('inf')
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = player
                score = minimax(board, -player)
                board[i][j] = 0
                if player == 1:
                    best_score = max(best_score, score)
                else:
                    best_score = min(best_score, score)
    return best_score

def policy(board: list[list[int]]) -> tuple[int, int]:
    best_score = -float('inf')
    best_move = (-1, -1)
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1
                score = minimax(board, -1)
                board[i][j] = 0
                if score > best_score:
                    best_score = score
                    best_move = (i, j)
    return best_move
