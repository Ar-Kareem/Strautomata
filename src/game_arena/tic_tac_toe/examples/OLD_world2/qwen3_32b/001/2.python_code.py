
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Helper function to check if the current player has won
    def is_win(player):
        # Check rows
        for r in range(4):
            if all(board[r][c] == player for c in range(4)):
                return True
        # Check columns
        for c in range(4):
            if all(board[r][c] == player for r in range(4)):
                return True
        # Check main diagonal
        if all(board[i][i] == player for i in range(4)):
            return True
        # Check anti-diagonal
        if all(board[i][3 - i] == player for i in range(4)):
            return True
        return False

    # Find all empty cells
    empty_cells = [(r, c) for r in range(4) for c in range(4) if board[r][c] == 0]

    # Step 1: Check for our own immediate win
    for (r, c) in empty_cells:
        # Simulate placing our symbol
        board[r][c] = 1
        if is_win(1):
            # Revert and return
            board[r][c] = 0
            return (r, c)
        # Revert
        board[r][c] = 0

    # Step 2: Check for opponent's immediate win and block
    for (r, c) in empty_cells:
        board[r][c] = -1
        if is_win(-1):
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    # Step 3: Choose best move based on line count and additional heuristic
    best_score = -1
    best_moves = []
    for (r, c) in empty_cells:
        score = 2  # Base score for row and column participation
        if r == c:
            score += 1  # On the main diagonal
        if r + c == 3:
            score += 1  # On the anti-diagonal
        if score > best_score:
            best_score = score
            best_moves = [(r, c)]
        elif score == best_score:
            best_moves.append((r, c))

    # If multiple best_moves, choose based on strategic priority
    if len(best_moves) > 1:
        best_move_scores = []
        for (r, c) in best_moves:
            priority = 0
            # Check if the row or column already contains our symbol
            if any(board[r][i] == 1 for i in range(4)):
                priority += 1
            if any(board[i][c] == 1 for i in range(4)):
                priority += 1
            # Check if the diagonal (if applicable) already contains our symbol
            if r == c and any(board[i][i] == 1 for i in range(4)):
                priority += 1
            if (r + c == 3) and any(board[i][3 - i] == 1 for i in range(4)):
                priority += 1
            best_move_scores.append((priority, (r, c)))
        # Sort by descending priority, then by row and column ascending
        best_move_scores.sort(key=lambda x: (-x[0], x[1][0], x[1][1]))
        return best_move_scores[0][1]
    else:
        return best_moves[0]
