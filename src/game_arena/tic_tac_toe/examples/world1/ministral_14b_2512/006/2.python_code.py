
def policy(board: list[list[int]]) -> tuple[int, int]:
    def evaluate(board):
        # Check for win/loss
        if check_win(board, 1):
            return 10
        elif check_win(board, -1):
            return -10

        # Heuristic evaluation
        score = 0
        for i in range(3):
            for j in range(3):
                if board[i][j] == 1:
                    if i == 1 and j == 1:  # Center
                        score += 0.01
                    elif (i in [0, 2] and j in [0, 2]):  # Corners
                        score += 1
                    else:  # Edges
                        score += 0.1
                elif board[i][j] == -1:
                    if i == 1 and j == 1:  # Center
                        score -= 0.01
                    elif (i in [0, 2] and j in [0, 2]):  # Corners
                        score -= 1
                    else:  # Edges
                        score -= 0.1
        return score

    def check_win(board, player):
        # Check rows, columns, diagonals
        for i in range(3):
            if all(board[i][j] == player for j in range(3)):
                return True
            if all(board[j][i] == player for j in range(3)):
                return True
        if all(board[i][i] == player for i in range(3)) or all(board[i][2 - i] == player for i in range(3)):
            return True
        return False

    def is_terminal(board):
        return check_win(board, 1) or check_win(board, -1) or all(cell != 0 for row in board for cell in row)

    def minimax(board, depth, is_maximizing, alpha, beta):
        if is_terminal(board):
            return evaluate(board)

        if is_maximizing:
            best_score = -float('inf')
            for i in range(3):
                for j in range(3):
                    if board[i][j] == 0:
                        board[i][j] = 1
                        score = minimax(board, depth + 1, False, alpha, beta)
                        board[i][j] = 0
                        best_score = max(score, best_score)
                        alpha = max(alpha, score)
                        if beta <= alpha:
                            break
            return best_score
        else:
            best_score = float('inf')
            for i in range(3):
                for j in range(3):
                    if board[i][j] == 0:
                        board[i][j] = -1
                        score = minimax(board, depth + 1, True, alpha, beta)
                        board[i][j] = 0
                        best_score = min(score, best_score)
                        beta = min(beta, score)
                        if beta <= alpha:
                            break
            return best_score

    # Check for immediate win or block
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1
                if check_win(board, 1):
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = -1
                if check_win(board, -1):
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = 0

    # Prefer center, then corners, then edges
    moves = []
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                moves.append((i, j))

    # Sort moves by priority: center > corners > edges
    moves.sort(key=lambda x: (x[0] != 1 or x[1] != 1, (x[0] in [0, 2] and x[1] in [0, 2]), (x[0] in [0, 2] or x[1] in [0, 2])))

    # If no forced move, use minimax
    best_score = -float('inf')
    best_move = None
    for move in moves:
        i, j = move
        board[i][j] = 1
        score = minimax(board, 0, False, -float('inf'), float('inf'))
        board[i][j] = 0
        if score > best_score:
            best_score = score
            best_move = move

    return best_move if best_move else moves[0]  # Fallback to first move if no minimax found (shouldn't happen)
