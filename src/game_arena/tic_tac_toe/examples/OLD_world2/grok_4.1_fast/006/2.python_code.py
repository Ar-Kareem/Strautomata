
def check_win(board, player):
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

def is_terminal(board):
    if check_win(board, 1):
        return 1
    if check_win(board, -1):
        return -1
    # Check for draw
    if all(all(cell != 0 for cell in row) for row in board):
        return 0
    return None

def get_moves(board):
    moves = [(i, j) for i in range(4) for j in range(4) if board[i][j] == 0]
    # Prioritize center moves for better pruning
    moves.sort(key=lambda m: abs(m[0] - 1.5) + abs(m[1] - 1.5))
    return moves

def make_move(board, move, player):
    new_board = [row[:] for row in board]
    r, c = move
    new_board[r][c] = player
    return new_board

def minimax(board, player, alpha=-2, beta=2):
    terminal = is_terminal(board)
    if terminal is not None:
        return terminal

    if player == 1:  # Maximizer
        max_eval = -2
        for move in get_moves(board):
            new_board = make_move(board, move, player)
            eval_score = minimax(new_board, -player, alpha, beta)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, max_eval)
            if beta <= alpha:
                break
        return max_eval
    else:  # Minimizer
        min_eval = 2
        for move in get_moves(board):
            new_board = make_move(board, move, player)
            eval_score = minimax(new_board, -player, alpha, beta)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, min_eval)
            if beta <= alpha:
                break
        return min_eval

def policy(board: list[list[int]]) -> tuple[int, int]:
    moves = get_moves(board)
    if not moves:
        raise ValueError("No moves available")
    
    best_score = -2
    best_move = None
    for move in moves:
        new_board = make_move(board, move, 1)
        score = minimax(new_board, -1)
        if score > best_score:
            best_score = score
            best_move = move
    return best_move
