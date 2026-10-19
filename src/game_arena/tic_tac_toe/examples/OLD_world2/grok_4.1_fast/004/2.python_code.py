
def is_winner(board, player):
    # Check rows
    for i in range(4):
        if all(board[i][j] == player for j in range(4)):
            return True
    # Check columns
    for j in range(4):
        if all(board[i][j] == player for i in range(4)):
            return True
    # Check main diagonal
    if all(board[i][i] == player for i in range(4)):
        return True
    # Check anti-diagonal
    if all(board[i][3 - i] == player for i in range(4)):
        return True
    return False


def is_full(board):
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                return False
    return True


def get_moves(board):
    return [(i, j) for i in range(4) for j in range(4) if board[i][j] == 0]


priority = [
    [1, 2, 2, 1],
    [2, 4, 4, 2],
    [2, 4, 4, 2],
    [1, 2, 2, 1]
]


def minimax(board, player, depth, alpha, beta):
    if is_winner(board, 1):
        return 100 - depth
    if is_winner(board, -1):
        return depth - 100
    if is_full(board):
        return 0

    moves = get_moves(board)
    if player == 1:
        moves.sort(key=lambda m: priority[m[0]][m[1]], reverse=True)
        best = -10**9
        for r, c in moves:
            board[r][c] = 1
            val = minimax(board, -1, depth + 1, alpha, beta)
            board[r][c] = 0
            best = max(best, val)
            alpha = max(alpha, best)
            if beta <= alpha:
                break
        return best
    else:
        moves.sort(key=lambda m: priority[m[0]][m[1]])
        best = 10**9
        for r, c in moves:
            board[r][c] = -1
            val = minimax(board, 1, depth + 1, alpha, beta)
            board[r][c] = 0
            best = min(best, val)
            beta = min(beta, best)
            if beta <= alpha:
                break
        return best


def policy(board: list[list[int]]) -> tuple[int, int]:
    working_board = [row[:] for row in board]
    moves = get_moves(working_board)

    # Check for immediate winning moves, prioritize by center
    for r, c in sorted(moves, key=lambda m: priority[m[0]][m[1]], reverse=True):
        working_board[r][c] = 1
        if is_winner(working_board, 1):
            working_board[r][c] = 0
            return (r, c)
        working_board[r][c] = 0

    # Check for opponent threats (immediate losing moves for opponent)
    threats = []
    for r, c in moves:
        working_board[r][c] = -1
        if is_winner(working_board, -1):
            threats.append((r, c))
        working_board[r][c] = 0

    if threats:
        # Block the threat in the best position
        best_threat = max(threats, key=lambda m: priority[m[0]][m[1]])
        return best_threat

    # Minimax for best move
    best_score = -10**9
    best_move = moves[0]
    # Sort root moves by priority
    moves.sort(key=lambda m: priority[m[0]][m[1]], reverse=True)
    for r, c in moves:
        working_board[r][c] = 1
        score = minimax(working_board, -1, 1, -10**9, 10**9)
        working_board[r][c] = 0
        if score > best_score:
            best_score = score
            best_move = (r, c)
    return best_move
