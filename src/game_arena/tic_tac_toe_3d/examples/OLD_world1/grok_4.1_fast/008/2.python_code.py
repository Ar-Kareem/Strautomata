
def check_win(board, player):
    # Lines along x (fixed z, y)
    for i in range(3):  # z
        for j in range(3):  # y
            if all(board[i][j][k] == player for k in range(3)):
                return True
    # Lines along y (fixed z, x)
    for i in range(3):  # z
        for k in range(3):  # x
            if all(board[i][j][k] == player for j in range(3)):
                return True
    # Lines along z (fixed y, x)
    for j in range(3):  # y
        for k in range(3):  # x
            if all(board[i][j][k] == player for i in range(3)):
                return True
    # Diagonals in xy planes (fixed z)
    for i in range(3):  # z
        if all(board[i][j][j] == player for j in range(3)):
            return True
        if all(board[i][j][2 - j] == player for j in range(3)):
            return True
    # Diagonals in xz planes (fixed y)
    for j in range(3):  # y
        if all(board[i][j][i] == player for i in range(3)):
            return True
        if all(board[i][j][2 - i] == player for i in range(3)):
            return True
    # Diagonals in yz planes (fixed x)
    for k in range(3):  # x
        if all(board[i][i][k] == player for i in range(3)):
            return True
        if all(board[i][2 - i][k] == player for i in range(3)):
            return True
    # Space diagonals
    if all(board[i][i][i] == player for i in range(3)):
        return True
    if all(board[i][i][2 - i] == player for i in range(3)):
        return True
    if all(board[i][2 - i][i] == player for i in range(3)):
        return True
    if all(board[i][2 - i][2 - i] == player for i in range(3)):
        return True
    return False


def is_full(board):
    return all(board[i][j][k] != 0 for i in range(3) for j in range(3) for k in range(3))


def terminal_score(board):
    if check_win(board, 1):
        return 1
    if check_win(board, -1):
        return -1
    if is_full(board):
        return 0
    return None


def get_moves(board):
    moves = [(i, j, k) for i in range(3) for j in range(3) for k in range(3) if board[i][j][k] == 0]
    # Sort by centrality (prefer center)
    def centrality(pos):
        z, y, x = pos
        return -(abs(z - 1) + abs(y - 1) + abs(x - 1))
    moves.sort(key=centrality, reverse=True)
    return moves


def minimax(board, player, alpha, beta):
    score = terminal_score(board)
    if score is not None:
        return score

    moves = get_moves(board)
    if player == 1:  # maximizing player
        max_eval = -2
        for z, y, x in moves:
            board[z][y][x] = 1
            eval_score = minimax(board, -1, alpha, beta)
            board[z][y][x] = 0
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, max_eval)
            if beta <= alpha:
                break
        return max_eval
    else:  # minimizing player
        min_eval = 2
        for z, y, x in moves:
            board[z][y][x] = -1
            eval_score = minimax(board, 1, alpha, beta)
            board[z][y][x] = 0
            min_eval = min(min_eval, eval_score)
            beta = min(beta, min_eval)
            if beta <= alpha:
                break
        return min_eval


def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    moves = get_moves(board)
    if not moves:
        raise ValueError("No legal moves left")

    # Check for immediate winning move
    for z, y, x in moves:
        board[z][y][x] = 1
        if check_win(board, 1):
            board[z][y][x] = 0
            return (z, y, x)
        board[z][y][x] = 0

    # Minimax to find best move
    best_score = -2
    best_move = moves[0]  # Default to first (most central)
    for z, y, x in moves:
        board[z][y][x] = 1
        score = minimax(board, -1, -2, 2)
        board[z][y][x] = 0
        if score > best_score:
            best_score = score
            best_move = (z, y, x)
    return best_move
