
def policy(board: list[list[int]]) -> tuple[int, int]:
    def is_winner(b, player):
        # Check rows, columns, and diagonals for a win
        return any(all(b[i][j] == player for j in range(3)) for i in range(3)) or \
               any(all(b[j][i] == player for j in range(3)) for i in range(3)) or \
               all(b[i][i] == player for i in range(3)) or \
               all(b[i][2 - i] == player for i in range(3))

    def minimax(b, depth, is_maximizing):
        if is_winner(b, 1):
            return 10 - depth
        if is_winner(b, -1):
            return depth - 10
        if all(b[i][j] != 0 for i in range(3) for j in range(3)):
            return 0
        
        if is_maximizing:
            best_score = float('-inf')
            for i in range(3):
                for j in range(3):
                    if b[i][j] == 0:
                        b[i][j] = 1  # AI's turn
                        score = minimax(b, depth + 1, False)
                        b[i][j] = 0  # Undo move
                        best_score = max(score, best_score)
            return best_score
        else:
            best_score = float('inf')
            for i in range(3):
                for j in range(3):
                    if b[i][j] == 0:
                        b[i][j] = -1  # Opponent's turn
                        score = minimax(b, depth + 1, True)
                        b[i][j] = 0  # Undo move
                        best_score = min(score, best_score)
            return best_score

    best_move = None
    best_value = float('-inf')
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1  # Try this move
                move_value = minimax(board, 0, False)
                board[i][j] = 0  # Undo move
                if move_value > best_value:
                    best_value = move_value
                    best_move = (i, j)

    return best_move
