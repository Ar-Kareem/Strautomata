
def is_winner(board, player):
    # Check rows
    for i in range(4):
        if all(board[i][j] == player for j in range(4)):
            return True
    # Check columns
    for j in range(4):
        if all(board[i][j] == player for i in range(4)):
            return True
    # Main diagonal
    if all(board[i][i] == player for i in range(4)):
        return True
    # Anti diagonal
    if all(board[i][3 - i] == player for i in range(4)):
        return True
    return False

def evaluate(board):
    if is_winner(board, 1):
        return 1
    if is_winner(board, -1):
        return -1
    return 0

def get_moves(board):
    moves = [(i, j) for i in range(4) for j in range(4) if board[i][j] == 0]
    moves.sort(key=lambda m: abs(m[0] - 1.5) + abs(m[1] - 1.5))
    return moves

def make_move(board, move, player):
    new_board = [row[:] for row in board]
    r, c = move
    new_board[r][c] = player
    return new_board

def minimax(board, is_maximizing, alpha, beta):
    score = evaluate(board)
    if score != 0:
        return score
    moves = get_moves(board)
    if not moves:
        return 0
    if is_maximizing:
        max_eval = -float('inf')
        for move in moves:
            new_board = make_move(board, move, 1)
            eval_score = minimax(new_board, False, alpha, beta)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, max_eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in moves:
            new_board = make_move(board, move, -1)
            eval_score = minimax(new_board, True, alpha, beta)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, min_eval)
            if beta <= alpha:
                break
        return min_eval

def policy(board: list[list[int]]) -> tuple[int, int]:
    moves = get_moves(board)
    if not moves:
        # No moves left, return arbitrary invalid move (should not happen)
        return (0, 0)
    
    # Check for immediate winning move
    for move in moves:
        new_board = make_move(board, move, 1)
        if evaluate(new_board) == 1:
            return move
    
    # Check for immediate threats to block
    threats = [m for m in moves if evaluate(make_move(board, m, -1)) == -1]
    if threats:
        return threats[0]
    
    # Minimax for best move
    best_score = -float('inf')
    best_move = moves[0]
    alpha = -float('inf')
    beta = float('inf')
    for move in moves:
        new_board = make_move(board, move, 1)
        score = minimax(new_board, False, alpha, beta)
        if score > best_score:
            best_score = score
            best_move = move
            alpha = max(alpha, score)
        if beta <= alpha:
            break
    return best_move
