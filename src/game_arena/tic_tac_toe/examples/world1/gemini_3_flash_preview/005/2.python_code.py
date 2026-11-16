
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Implements an optimal Minimax strategy for Tic Tac Toe.
    1 is the player, -1 is the opponent.
    """

    def check_winner(b):
        # Rows and Columns
        for i in range(3):
            if sum(b[i]) == 3 or sum(b[j][i] for j in range(3)) == 3:
                return 1
            if sum(b[i]) == -3 or sum(b[j][i] for j in range(3)) == -3:
                return -1
        # Diagonals
        if b[0][0] + b[1][1] + b[2][2] == 3 or b[0][2] + b[1][1] + b[2][0] == 3:
            return 1
        if b[0][0] + b[1][1] + b[2][2] == -3 or b[0][2] + b[1][1] + b[2][0] == -3:
            return -1
        # Draw or Ongoing
        if all(cell != 0 for row in b for cell in row):
            return 0
        return None

    def minimax(b, depth, is_maximizing):
        res = check_winner(b)
        if res is not None:
            return res

        if is_maximizing:
            best_score = -float('inf')
            for r in range(3):
                for c in range(3):
                    if b[r][c] == 0:
                        b[r][c] = 1
                        score = minimax(b, depth + 1, False)
                        b[r][c] = 0
                        best_score = max(score, best_score)
            return best_score
        else:
            best_score = float('inf')
            for r in range(3):
                for c in range(3):
                    if b[r][c] == 0:
                        b[r][c] = -1
                        score = minimax(b, depth + 1, True)
                        b[r][c] = 0
                        best_score = min(score, best_score)
            return best_score

    best_val = -float('inf')
    best_move = (-1, -1)

    # Initial move logic: if board is empty, center is usually best
    if all(cell == 0 for row in board for cell in row):
        return (1, 1)

    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                board[r][c] = 1
                move_val = minimax(board, 0, False)
                board[r][c] = 0
                if move_val > best_val:
                    best_val = move_val
                    best_move = (r, c)

    return best_move
