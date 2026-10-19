
def get_valid_moves_ordered(board):
    order = [3, 2, 4, 1, 5, 0, 6]
    return [c for c in order if board[0][c] == 0]

def make_move(board, col, player):
    for r in range(5, -1, -1):
        if board[r][col] == 0:
            board[r][col] = player
            return r
    return -1

def undo_move(board, col, r):
    if r != -1:
        board[r][col] = 0

def has_won(board, player):
    # Horizontal
    for r in range(6):
        for c in range(4):
            if (board[r][c] == player and board[r][c + 1] == player and
                board[r][c + 2] == player and board[r][c + 3] == player):
                return True
    # Vertical
    for c in range(7):
        for r in range(3):
            if (board[r][c] == player and board[r + 1][c] == player and
                board[r + 2][c] == player and board[r + 3][c] == player):
                return True
    # Diagonal /
    for r in range(3):
        for c in range(4):
            if (board[r][c] == player and board[r + 1][c + 1] == player and
                board[r + 2][c + 2] == player and board[r + 3][c + 3] == player):
                return True
    # Diagonal \
    for r in range(3):
        for c in range(3, 7):
            if (board[r][c] == player and board[r + 1][c - 1] == player and
                board[r + 2][c - 2] == player and board[r + 3][c - 3] == player):
                return True
    return False

def evaluate(board, player):
    opp = -player
    score = 0
    col_weight = [4, 5, 7, 10, 7, 5, 4]
    for c in range(7):
        weight = col_weight[c]
        for r in range(6):
            if board[r][c] == player:
                score += weight
            elif board[r][c] == opp:
                score -= weight
    return score

def minimax(board, depth, alpha, beta, maximizing, player):
    opp = -player
    # Terminal checks
    if has_won(board, player):
        return 1000000
    if has_won(board, opp):
        return -1000000
    moves = get_valid_moves_ordered(board)
    if len(moves) == 0:
        return 0
    if depth == 0:
        return evaluate(board, player)
    if maximizing:
        value = -10000000
        for col in moves:
            r = make_move(board, col, player)
            value = max(value, minimax(board, depth - 1, alpha, beta, False, player))
            undo_move(board, col, r)
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    else:
        value = 10000000
        for col in moves:
            r = make_move(board, col, opp)
            value = min(value, minimax(board, depth - 1, alpha, beta, True, player))
            undo_move(board, col, r)
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value

def policy(board: list[list[int]]) -> int:
    player = 1
    moves = get_valid_moves_ordered(board)
    # Check for immediate win
    for col in moves:
        r = make_move(board, col, player)
        if has_won(board, player):
            undo_move(board, col, r)
            return col
        undo_move(board, col, r)
    # Check for immediate block
    for col in moves:
        r = make_move(board, col, -player)
        if has_won(board, -player):
            undo_move(board, col, r)
            return col
        undo_move(board, col, r)
    # Minimax search
    best_value = -10000000
    best_move = moves[0]
    DEPTH = 7
    for col in moves:
        r = make_move(board, col, player)
        value = minimax(board, DEPTH, -10000000, 10000000, False, player)
        undo_move(board, col, r)
        if value > best_value:
            best_value = value
            best_move = col
    return best_move
