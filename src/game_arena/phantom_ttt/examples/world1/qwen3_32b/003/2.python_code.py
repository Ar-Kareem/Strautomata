
def policy(board: list[list[int]], legal_moves: list[int]) -> int:
    def is_winning_move(r, c):
        # Check row
        row_complete = True
        for c2 in range(3):
            if c2 != c and board[r][c2] != 1:
                row_complete = False
                break
        if row_complete:
            return True
        # Check column
        col_complete = True
        for r2 in range(3):
            if r2 != r and board[r2][c] != 1:
                col_complete = False
                break
        if col_complete:
            return True
        # Check main diagonal
        if r == c:
            diag_complete = True
            for i in range(3):
                if i != r and board[i][i] != 1:
                    diag_complete = False
                    break
            if diag_complete:
                return True
        # Check anti-diagonal
        if r + c == 2:
            diag_complete = True
            for i in range(3):
                if i != r and board[i][2 - i] != 1:
                    diag_complete = False
                    break
            if diag_complete:
                return True
        return False

    # Step 1: Check for winning moves
    for move in legal_moves:
        row, col = move // 3, move % 3
        if is_winning_move(row, col):
            return move

    # Step 2: Compute scores for all legal moves
    best_score = -1
    best_moves = []
    for move in legal_moves:
        row, col = move // 3, move % 3
        score = 0
        # Check row
        row_count = sum(board[row][c2] for c2 in range(3) if c2 != col)
        score += row_count
        # Check column
        col_count = sum(board[r2][col] for r2 in range(3) if r2 != row)
        score += col_count
        # Check main diagonal
        if row == col:
            diag_count = sum(board[i][i] for i in range(3) if i != row)
            score += diag_count
        # Check anti-diagonal
        if row + col == 2:
            diag_count = sum(board[i][2 - i] for i in range(3) if i != row)
            score += diag_count
        # Update best moves
        if score > best_score:
            best_score = score
            best_moves = [move]
        elif score == best_score:
            best_moves.append(move)

    # Step 3: Tie-break among best_moves using priority
    if len(best_moves) == 1:
        return best_moves[0]
    else:
        def get_priority(m):
            r = m // 3
            c = m % 3
            if r == 1 and c == 1:
                return 0  # Center
            elif (r, c) in [(0, 0), (0, 2), (2, 0), (2, 2)]:
                return 1  # Corners
            elif (r, c) in [(0, 1), (1, 0), (1, 2), (2, 1)]:
                return 2  # Edges
            else:
                return 3  # Default, should not happen

        best_moves.sort(key=lambda m: (get_priority(m), m))
        return best_moves[0]
