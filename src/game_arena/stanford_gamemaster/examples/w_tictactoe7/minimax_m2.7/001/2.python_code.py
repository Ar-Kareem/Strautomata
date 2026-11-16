
def policy(state, role):
    # Parse the board from the state representation
    board = [["b" for _ in range(3)] for __ in range(3)]
    for fact in state:
        if fact[0] == "cell":
            row = int(fact[1]) - 1
            col = int(fact[2]) - 1
            player = fact[3]
            board[row][col] = player

    opponent = "o" if role == "x" else "x"

    # Helper: list of empty cells
    def get_empty_cells(b):
        return [(r, c) for r in range(3) for c in range(3) if b[r][c] == "b"]

    # Helper: return the winner ('x', 'o') or None
    def get_winner(b):
        # rows
        for i in range(3):
            if b[i][0] == b[i][1] == b[i][2] and b[i][0] != "b":
                return b[i][0]
        # columns
        for j in range(3):
            if b[0][j] == b[1][j] == b[2][j] and b[0][j] != "b":
                return b[0][j]
        # diagonals
        if b[0][0] == b[1][1] == b[2][2] and b[0][0] != "b":
            return b[0][0]
        if b[0][2] == b[1][1] == b[2][0] and b[0][2] != "b":
            return b[0][2]
        return None

    # Minimax with alpha‑beta pruning
    def minimax(b, is_maximizing, alpha, beta):
        winner = get_winner(b)
        if winner == role:
            return 1
        if winner == opponent:
            return -1
        empties = get_empty_cells(b)
        if not empties:
            return 0

        if is_maximizing:
            max_eval = -float('inf')
            for r, c in empties:
                b[r][c] = role
                if get_winner(b) == role:
                    eval_score = 1
                else:
                    eval_score = minimax(b, False, alpha, beta)
                b[r][c] = "b"
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for r, c in empties:
                b[r][c] = opponent
                if get_winner(b) == opponent:
                    eval_score = -1
                else:
                    eval_score = minimax(b, True, alpha, beta)
                b[r][c] = "b"
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    empties = get_empty_cells(board)
    best_move = None
    best_score = -float('inf')
    alpha = -float('inf')
    beta = float('inf')
    for r, c in empties:
        board[r][c] = role
        if get_winner(board) == role:
            score = 1
        else:
            score = minimax(board, False, alpha, beta)
        board[r][c] = "b"
        if score > best_score:
            best_score = score
            best_move = (r, c)
            alpha = max(alpha, score)
            if score == 1:
                break

    # Fallback (should not be needed)
    if best_move is None:
        best_move = empties[0]

    row, col = best_move
    return f"mark({row+1},{col+1})"
