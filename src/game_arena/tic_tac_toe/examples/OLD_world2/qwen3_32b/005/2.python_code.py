
def policy(board: list[list[int]]) -> tuple[int, int]:
    def is_winning_move(x: int, y: int, player: int) -> bool:
        # Check if placing `player` at (x, y) will lead to a win

        # Row check
        if all(board[x][col] == player or col == y for col in range(4)):
            return True

        # Column check
        if all(board[row][y] == player or row == x for row in range(4)):
            return True

        # Diagonal 1 check (top-left to bottom-right)
        if x == y:
            if all(board[i][i] == player or i == x for i in range(4)):
                return True

        # Diagonal 2 check (top-right to bottom-left)
        if x + y == 3:
            if all(board[i][3 - i] == player or i == x for i in range(4)):
                return True

        return False

    # Try to win
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0 and is_winning_move(i, j, 1):
                return (i, j)

    # Block opponent's win
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0 and is_winning_move(i, j, -1):
                return (i, j)

    # Default: choose the cell that participates in the most winning lines
    best_score = -1
    best_moves = []

    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                # Score: 1 for every line this cell belongs to (row, column, diagonal)
                score = 2  # Always part of a row and a column
                if i == j:
                    score += 1
                if i + j == 3:
                    score += 1

                if score > best_score:
                    best_score = score
                    best_moves = [(i, j)]
                elif score == best_score:
                    best_moves.append((i, j))

    return best_moves[0]
