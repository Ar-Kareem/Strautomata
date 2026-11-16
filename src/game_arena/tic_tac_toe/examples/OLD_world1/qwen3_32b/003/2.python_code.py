
def policy(board: list[list[int]]) -> tuple[int, int]:
    def get_winner(bd):
        # Check rows
        for row in bd:
            if row[0] != 0 and all(cell == row[0] for cell in row):
                return row[0]
        # Check columns
        for col in range(3):
            if bd[0][col] != 0 and all(bd[row][col] == bd[0][col] for row in range(3)):
                return bd[0][col]
        # Check first diagonal
        if bd[0][0] != 0 and bd[0][0] == bd[1][1] == bd[2][2]:
            return bd[0][0]
        # Check second diagonal
        if bd[0][2] != 0 and bd[0][2] == bd[1][1] == bd[2][0]:
            return bd[0][2]
        return 0

    def minimax(bd, is_maximizing):
        winner = get_winner(bd)
        if winner == 1:
            return 10
        elif winner == -1:
            return -10
        if all(cell != 0 for row in bd for cell in row):
            return 0

        if is_maximizing:
            best_score = -float('inf')
            for i in range(3):
                for j in range(3):
                    if bd[i][j] == 0:
                        bd[i][j] = 1
                        score = minimax(bd, False)
                        bd[i][j] = 0
                        best_score = max(best_score, score)
            return best_score
        else:
            best_score = float('inf')
            for i in range(3):
                for j in range(3):
                    if bd[i][j] == 0:
                        bd[i][j] = -1
                        score = minimax(bd, True)
                        bd[i][j] = 0
                        best_score = min(best_score, score)
            return best_score

    best_move = None
    best_score = -float('inf')
    best_moves = []

    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1
                score = minimax(board, False)
                board[i][j] = 0
                if score > best_score:
                    best_score = score
                    best_moves = [(i, j)]
                elif score == best_score:
                    best_moves.append((i, j))

    # Tie-breaking heuristic: center > corners > edges
    def get_priority(move):
        i, j = move
        if i == 1 and j == 1:
            return 0
        elif (i, j) in [(0, 0), (0, 2), (2, 0), (2, 2)]:
            return 1
        else:
            return 2

    best_moves.sort(key=lambda m: get_priority(m))
    return best_moves[0]
