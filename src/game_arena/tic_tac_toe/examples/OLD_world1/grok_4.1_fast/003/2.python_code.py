
def winner(board: list[list[int]]) -> int:
    # Check rows
    for i in range(3):
        if board[i][0] != 0 and board[i][0] == board[i][1] == board[i][2]:
            return board[i][0]
    # Check columns
    for j in range(3):
        if board[0][j] != 0 and board[0][j] == board[1][j] == board[2][j]:
            return board[0][j]
    # Check main diagonal
    if board[0][0] != 0 and board[0][0] == board[1][1] == board[2][2]:
        return board[0][0]
    # Check anti-diagonal
    if board[0][2] != 0 and board[0][2] == board[1][1] == board[2][0]:
        return board[0][2]
    return 0

def is_full(board: list[list[int]]) -> bool:
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                return False
    return True

def minimax(board: list[list[int]], is_maximizing: bool) -> int:
    score = winner(board)
    if score != 0:
        return score
    if is_full(board):
        return 0

    if is_maximizing:
        max_eval = -float('inf')
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    board[i][j] = 1
                    eval_score = minimax(board, False)
                    board[i][j] = 0
                    max_eval = max(max_eval, eval_score)
        return max_eval
    else:
        min_eval = float('inf')
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    board[i][j] = -1
                    eval_score = minimax(board, True)
                    board[i][j] = 0
                    min_eval = min(min_eval, eval_score)
        return min_eval

def policy(board: list[list[int]]) -> tuple[int, int]:
    if winner(board) != 0 or is_full(board):
        return (-1, -1)  # Game over, no move
    best_score = -float('inf')
    best_move = (-1, -1)
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1
                score = minimax(board, False)
                board[i][j] = 0
                if score > best_score:
                    best_score = score
                    best_move = (i, j)
    return best_move
