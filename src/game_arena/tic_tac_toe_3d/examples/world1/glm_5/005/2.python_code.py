
import math

# Precompute all 49 winning lines for a 3x3x3 board
LINES = []

def generate_lines():
    global LINES
    if LINES:
        return
    
    # Rows (vary k)
    for i in range(3):
        for j in range(3):
            LINES.append([(i, j, k) for k in range(3)])
    # Columns (vary j)
    for i in range(3):
        for k in range(3):
            LINES.append([(i, j, k) for j in range(3)])
    # Pillars (vary i)
    for j in range(3):
        for k in range(3):
            LINES.append([(i, j, k) for i in range(3)])
    
    # 2D Diagonals within planes
    # Planes i=const
    for i in range(3):
        LINES.append([(i, d, d) for d in range(3)])
        LINES.append([(i, d, 2 - d) for d in range(3)])
    # Planes j=const
    for j in range(3):
        LINES.append([(d, j, d) for d in range(3)])
        LINES.append([(d, j, 2 - d) for d in range(3)])
    # Planes k=const
    for k in range(3):
        LINES.append([(d, d, k) for d in range(3)])
        LINES.append([(d, 2 - d, k) for d in range(3)])
        
    # Main 3D Diagonals
    LINES.append([(d, d, d) for d in range(3)])
    LINES.append([(d, d, 2 - d) for d in range(3)])
    LINES.append([(d, 2 - d, d) for d in range(3)])
    LINES.append([(d, 2 - d, 2 - d) for d in range(3)])

generate_lines()

def check_winner(board):
    for line in LINES:
        s = sum(board[i][j][k] for i, j, k in line)
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0

def evaluate(board):
    score = 0
    for line in LINES:
        vals = [board[i][j][k] for i, j, k in line]
        p_count = vals.count(1)
        o_count = vals.count(-1)
        
        if p_count > 0 and o_count > 0:
            continue  # Mixed line, no value
        
        if p_count == 2:
            score += 100
        elif p_count == 1:
            score += 10
        
        if o_count == 2:
            score -= 100
        elif o_count == 1:
            score -= 10
            
    return score

def get_valid_moves(board):
    moves = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    moves.append((i, j, k))
    return moves

def minimax(board, depth, alpha, beta, maximizing_player):
    winner = check_winner(board)
    if winner != 0:
        return 10000 * winner * (depth + 1)
    
    moves = get_valid_moves(board)
    if not moves:
        return 0
    
    if depth == 0:
        return evaluate(board)
    
    if maximizing_player:
        max_eval = -float('inf')
        for i, j, k in moves:
            board[i][j][k] = 1
            eval_val = minimax(board, depth - 1, alpha, beta, False)
            board[i][j][k] = 0
            max_eval = max(max_eval, eval_val)
            alpha = max(alpha, eval_val)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for i, j, k in moves:
            board[i][j][k] = -1
            eval_val = minimax(board, depth - 1, alpha, beta, True)
            board[i][j][k] = 0
            min_eval = min(min_eval, eval_val)
            beta = min(beta, eval_val)
            if beta <= alpha:
                break
        return min_eval

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # 1. Check for immediate win
    for line in LINES:
        coords = [(i, j, k) for i, j, k in line]
        vals = [board[i][j][k] for i, j, k in line]
        if sum(vals) == 2:
            for i, j, k in coords:
                if board[i][j][k] == 0:
                    return (i, j, k)
    
    # 2. Check for immediate block
    for line in LINES:
        coords = [(i, j, k) for i, j, k in line]
        vals = [board[i][j][k] for i, j, k in line]
        if sum(vals) == -2:
            for i, j, k in coords:
                if board[i][j][k] == 0:
                    return (i, j, k)

    moves = get_valid_moves(board)
    if not moves:
        return (-1, -1, -1)

    # Optimization: Take center if available (strong strategic position)
    if (1, 1, 1) in moves:
        return (1, 1, 1)
        
    # Determine search depth based on game complexity
    num_moves = len(moves)
    if num_moves > 15:
        depth = 2
    elif num_moves > 8:
        depth = 3
    else:
        depth = 4

    # Move ordering heuristic: prioritize corners, then edges, then faces
    # Corners: indices 0 or 2. Face centers: index 1.
    # Center handled above.
    def move_score(move):
        i, j, k = move
        # Corners have 0 or 2 in all coords. Sum is even? 0+0+0=0, 2+2+2=6...
        # Center is 1,1,1.
        # This is a simple heuristic to check non-center importance.
        # Corners are part of more lines than face-centers.
        # Let's just rely on minimax evaluation, but we can sort 'moves' list
        # so promising moves are checked first for alpha-beta pruning.
        is_corner = (i in (0, 2) and j in (0, 2) and k in (0, 2))
        if is_corner:
            return 0 # High priority
        return 1
        
    moves.sort(key=move_score)

    best_score = -float('inf')
    best_move = moves[0]
    
    for i, j, k in moves:
        board[i][j][k] = 1
        score = minimax(board, depth - 1, -float('inf'), float('inf'), False)
        board[i][j][k] = 0
        
        if score > best_score:
            best_score = score
            best_move = (i, j, k)
            
    return best_move
