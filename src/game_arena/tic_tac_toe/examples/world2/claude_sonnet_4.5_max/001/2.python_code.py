
def policy(board: list[list[int]]) -> tuple[int, int]:
    empty_cells = []
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                empty_cells.append((i, j))
    
    if not empty_cells:
        return (0, 0)
    
    # Win if possible
    for row, col in empty_cells:
        board[row][col] = 1
        if check_winner(board) == 1:
            board[row][col] = 0
            return (row, col)
        board[row][col] = 0
    
    # Block opponent win
    for row, col in empty_cells:
        board[row][col] = -1
        if check_winner(board) == -1:
            board[row][col] = 0
            return (row, col)
        board[row][col] = 0
    
    # Adjust depth based on game state
    num_empty = len(empty_cells)
    if num_empty > 12:
        max_depth = 6
    elif num_empty > 8:
        max_depth = 8
    else:
        max_depth = 16
    
    # Use minimax for best move
    best_score = float('-inf')
    best_move = empty_cells[0]
    
    for row, col in empty_cells:
        board[row][col] = 1
        score = minimax(board, 0, False, float('-inf'), float('inf'), max_depth)
        board[row][col] = 0
        
        if score > best_score:
            best_score = score
            best_move = (row, col)
    
    return best_move


def check_winner(board):
    # Check rows
    for i in range(4):
        if all(board[i][j] != 0 and board[i][j] == board[i][0] for j in range(4)):
            return board[i][0]
    
    # Check columns
    for j in range(4):
        if all(board[i][j] != 0 and board[i][j] == board[0][j] for i in range(4)):
            return board[0][j]
    
    # Check diagonals
    if all(board[i][i] != 0 and board[i][i] == board[0][0] for i in range(4)):
        return board[0][0]
    
    if all(board[i][3-i] != 0 and board[i][3-i] == board[0][3] for i in range(4)):
        return board[0][3]
    
    return 0


def get_ordered_moves(board):
    moves = []
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                # Prefer center squares
                center_dist = abs(i - 1.5) + abs(j - 1.5)
                priority = -center_dist
                moves.append((priority, i, j))
    moves.sort(reverse=True)
    return [(i, j) for _, i, j in moves]


def minimax(board, depth, is_maximizing, alpha, beta, max_depth):
    winner = check_winner(board)
    if winner == 1:
        return 100 - depth
    if winner == -1:
        return -100 + depth
    
    moves = get_ordered_moves(board)
    if not moves:
        return 0
    
    if depth >= max_depth:
        return evaluate(board)
    
    if is_maximizing:
        max_score = float('-inf')
        for i, j in moves:
            board[i][j] = 1
            score = minimax(board, depth + 1, False, alpha, beta, max_depth)
            board[i][j] = 0
            max_score = max(max_score, score)
            alpha = max(alpha, score)
            if beta <= alpha:
                break
        return max_score
    else:
        min_score = float('inf')
        for i, j in moves:
            board[i][j] = -1
            score = minimax(board, depth + 1, True, alpha, beta, max_depth)
            board[i][j] = 0
            min_score = min(min_score, score)
            beta = min(beta, score)
            if beta <= alpha:
                break
        return min_score


def evaluate(board):
    score = 0
    
    # Evaluate rows
    for i in range(4):
        score += eval_line([board[i][j] for j in range(4)])
    
    # Evaluate columns
    for j in range(4):
        score += eval_line([board[j][i] for j in range(4)])
    
    # Evaluate diagonals
    score += eval_line([board[i][i] for i in range(4)])
    score += eval_line([board[i][3-i] for i in range(4)])
    
    return score


def eval_line(line):
    ones = line.count(1)
    neg_ones = line.count(-1)
    
    if ones > 0 and neg_ones > 0:
        return 0
    
    if ones == 3:
        return 30
    if ones == 2:
        return 8
    if ones == 1:
        return 1
    
    if neg_ones == 3:
        return -30
    if neg_ones == 2:
        return -8
    if neg_ones == 1:
        return -1
    
    return 0
