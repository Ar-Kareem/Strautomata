
import copy

WINNING_LINES = [
    # Rows
    [[i, j] for j in range(4)] for i in range(4)
] + [
    # Columns
    [[i, j] for i in range(4)] for j in range(4)
] + [
    # Main diagonal
    [[i, i] for i in range(4)]
] + [
    # Anti-diagonal
    [[i, 3 - i] for i in range(4)]
]

INF = 10000000

def is_terminal(board):
    # Check if board is full or won
    if all(board[r][c] != 0 for r in range(4) for c in range(4)):
        return True
    for line in WINNING_LINES:
        cells = [board[r][c] for r, c in line]
        if all(cell == 1 for cell in cells) or all(cell == -1 for cell in cells):
            return True
    return False

def evaluate(board):
    if is_terminal(board):
        for line in WINNING_LINES:
            cells = [board[r][c] for r, c in line]
            if all(cell == 1 for cell in cells):
                return INF
            elif all(cell == -1 for cell in cells):
                return -INF
        return 0  # Draw

    score = 0
    for line in WINNING_LINES:
        my_count = sum(1 for r, c in line if board[r][c] == 1)
        opp_count = sum(1 for r, c in line if board[r][c] == -1)
        if opp_count == 0 and my_count > 0:
            score += 10 ** my_count
        if my_count == 0 and opp_count > 0:
            score -= 10 ** opp_count
    return score

def get_legal_moves(board):
    return [(r, c) for r in range(4) for c in range(4) if board[r][c] == 0]

def minimax(board, depth, alpha, beta, maximizing):
    if depth == 0 or is_terminal(board):
        return evaluate(board)

    legal_moves = get_legal_moves(board)
    if maximizing:
        max_eval = -INF
        for move in legal_moves:
            r, c = move
            board[r][c] = 1
            eval_score = minimax(board, depth - 1, alpha, beta, False)
            board[r][c] = 0
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = INF
        for move in legal_moves:
            r, c = move
            board[r][c] = -1
            eval_score = minimax(board, depth - 1, alpha, beta, True)
            board[r][c] = 0
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

def policy(board):
    legal_moves = get_legal_moves(board)
    best_move = None
    best_score = -INF
    current_board = copy.deepcopy(board)
    for move in legal_moves:
        r, c = move
        current_board[r][c] = 1
        score = minimax(current_board, 3, -INF, INF, False)  # False because after my move, opponent's turn
        current_board[r][c] = 0
        if score > best_score:
            best_score = score
            best_move = move
    return best_move
