
def is_winner(board: list[list[list[int]]], player: int) -> bool:
    # function to check if a player has won
    target = player * 3

    # Check rows, columns, and depths
    for i in range(3):
        for j in range(3):
            if sum(board[i][j]) == target:  # rows
                return True
            if sum(board[k][i][j] for k in range(3)) == target:  # columns
                return True
            
    for k in range(3):
        if sum(board[k][i][j] for i in range(3) for j in range(3)) == target:  # depths
            return True

    # Check diagonals
    for i in range(3):
        if sum(board[i][i][j] for j in range(3)) == target:  # diagonal in each layer
            return True
        if sum(board[i][2-i][j] for j in range(3)) == target:  # anti-diagonal in each layer
            return True
    for j in range(3):
        if sum(board[i][j][i] for i in range(3)) == target:  # diagonal through depth
            return True
        if sum(board[i][j][2-i] for i in range(3)) == target:  # anti-diagonal through depth
            return True
    if sum(board[i][i][i] for i in range(3)) == target:  # main diagonal
        return True
    if sum(board[i][i][2-i] for i in range(3)) == target:  # anti main diagonal
        return True
    return False


def minimax(board: list[list[list[int]]], depth: int, maximizing_player: bool) -> int:
    if is_winner(board, 1):  # Check if our side has won
        return 10 - depth
    if is_winner(board, -1):  # Check if the opponent has won
        return depth - 10
    if all(cell != 0 for layer in board for row in layer for cell in row):  # Check for a draw
        return 0

    if maximizing_player:
        max_eval = float('-inf')
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    if board[i][j][k] == 0:  # Check for an empty cell
                        board[i][j][k] = 1  # Simulate our move
                        eval = minimax(board, depth + 1, False)
                        board[i][j][k] = 0  # Undo move
                        max_eval = max(max_eval, eval)
        return max_eval
    else:
        min_eval = float('inf')
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    if board[i][j][k] == 0:  # Check for an empty cell
                        board[i][j][k] = -1  # Simulate opponent's move
                        eval = minimax(board, depth + 1, True)
                        board[i][j][k] = 0  # Undo move
                        min_eval = min(min_eval, eval)
        return min_eval


def best_move(board: list[list[list[int]]]) -> tuple[int, int, int]:
    best_eval = float('-inf')
    move = (-1, -1, -1)

    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:  # Check for an empty cell
                    board[i][j][k] = 1  # Simulate our move
                    move_eval = minimax(board, 0, False)
                    board[i][j][k] = 0  # Undo move
                    if move_eval > best_eval:
                        best_eval = move_eval
                        move = (i, j, k)

    return move


def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    return best_move(board)
