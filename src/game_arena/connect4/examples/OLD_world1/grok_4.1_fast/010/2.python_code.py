
def get_valid_cols(board):
    return [c for c in range(7) if board[5][c] == 0]

def order_valid_cols(valid_cols):
    return sorted(valid_cols, key=lambda c: (abs(c - 3), c))

def drop(board, col, player):
    new_board = [row[:] for row in board]
    for r in range(5, -1, -1):
        if new_board[r][col] == 0:
            new_board[r][col] = player
            return new_board
    return None

def check_win(board, player):
    # horizontal
    for r in range(6):
        for c in range(4):
            if all(board[r][c + i] == player for i in range(4)):
                return True
    # vertical
    for c in range(7):
        for r in range(3):
            if all(board[r + i][c] == player for i in range(4)):
                return True
    # diagonal /
    for r in range(3):
        for c in range(4):
            if all(board[r + i][c + i] == player for i in range(4)):
                return True
    # diagonal \
    for r in range(3):
        for c in range(3, 7):
            if all(board[r + i][c - i] == player for i in range(4)):
                return True
    return False

def get_threat_score(line, player):
    my_count = sum(1 for x in line if x == player)
    opp_count = sum(1 for x in line if x == -player)
    empty_count = 4 - my_count - opp_count
    if my_count == 3 and empty_count == 1:
        return 100
    if my_count == 2 and empty_count == 2:
        return 10
    if my_count == 1 and empty_count == 3:
        return 1
    return 0

def heuristic(board):
    score = 0
    for player in [1, -1]:
        multiplier = 1 if player == 1 else -1
        # horizontal
        for r in range(6):
            for c in range(4):
                line = [board[r][c + i] for i in range(4)]
                score += multiplier * get_threat_score(line, player)
        # vertical
        for c in range(7):
            for r in range(3):
                line = [board[r + i][c] for i in range(4)]
                score += multiplier * get_threat_score(line, player)
        # diagonal /
        for r in range(3):
            for c in range(4):
                line = [board[r + i][c + i] for i in range(4)]
                score += multiplier * get_threat_score(line, player)
        # diagonal \
        for r in range(3):
            for c in range(3, 7):
                line = [board[r + i][c - i] for i in range(4)]
                score += multiplier * get_threat_score(line, player)
    return score

def minimax(board, depth, alpha, beta, maximizing_player):
    if check_win(board, 1):
        return 10000 + depth
    if check_win(board, -1):
        return -10000 - depth
    valid_cols = get_valid_cols(board)
    if len(valid_cols) == 0:
        return 0
    if depth == 0:
        return heuristic(board)
    ordered_cols = order_valid_cols(valid_cols)
    if maximizing_player:
        max_eval = -float('inf')
        for col in ordered_cols:
            new_board = drop(board, col, 1)
            eval_score = minimax(new_board, depth - 1, alpha, beta, False)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, max_eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for col in ordered_cols:
            new_board = drop(board, col, -1)
            eval_score = minimax(new_board, depth - 1, alpha, beta, True)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, min_eval)
            if beta <= alpha:
                break
        return min_eval

MAX_DEPTH = 10

def policy(board: list[list[int]]) -> int:
    valid_cols = get_valid_cols(board)
    if not valid_cols:
        return 0  # shouldn't happen
    ordered_cols = order_valid_cols(valid_cols)
    # Check for immediate win
    for col in ordered_cols:
        new_board = drop(board, col, 1)
        if check_win(new_board, 1):
            return col
    # Check for immediate block
    for col in ordered_cols:
        new_board = drop(board, col, -1)
        if check_win(new_board, -1):
            return col
    # Minimax
    best_score = -float('inf')
    best_col = ordered_cols[0]
    for col in ordered_cols:
        new_board = drop(board, col, 1)
        score = minimax(new_board, MAX_DEPTH, -float('inf'), float('inf'), False)
        if score > best_score:
            best_score = score
            best_col = col
    return best_col
