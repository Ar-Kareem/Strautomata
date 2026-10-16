
def policy(board: list[list[int]]) -> tuple[int, int]:
    def is_win(b, player):
        # Check rows
        for row in b:
            if all(cell == player for cell in row):
                return True
        # Check columns
        for col in range(4):
            if all(b[row][col] == player for row in range(4)):
                return True
        # Check diagonals
        if all(b[i][i] == player for i in range(4)):
            return True
        if all(b[i][3-i] == player for i in range(4)):
            return True
        return False

    # Check for winning move
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                new_board = [row.copy() for row in board]
                new_board[r][c] = 1
                if is_win(new_board, 1):
                    return (r, c)

    # Check for opponent's winning move to block
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                new_board = [row.copy() for row in board]
                new_board[r][c] = -1
                if is_win(new_board, -1):
                    return (r, c)

    # Evaluate heuristic for remaining cells
    best_score = -float('inf')
    best_move = (0, 0)
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                row_score = sum(board[r])
                col_score = sum(board[i][c] for i in range(4))
                diag_score = 0
                if r == c:
                    diag_score += sum(board[i][i] for i in range(4))
                if r + c == 3:
                    diag_score += sum(board[i][3-i] for i in range(4))
                total = row_score + col_score + diag_score
                # Add center bonus
                if 1 <= r <= 2 and 1 <= c <= 2:
                    total += 2
                # Update best move
                if total > best_score or (total == best_score and (r, c) < best_move):
                    best_score = total
                    best_move = (r, c)
    return best_move
