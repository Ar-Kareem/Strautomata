
import time

# Precompute all 49 winning lines in a 3x3x3 cube
WINNING_LINES = []

# Axis-aligned lines (27 total)
for i in range(3):
    for j in range(3):
        WINNING_LINES.append(((i, j, 0), (i, j, 1), (i, j, 2)))  # Lines parallel to z-axis
for i in range(3):
    for k in range(3):
        WINNING_LINES.append(((i, 0, k), (i, 1, k), (i, 2, k)))  # Lines parallel to y-axis
for j in range(3):
    for k in range(3):
        WINNING_LINES.append(((0, j, k), (1, j, k), (2, j, k)))  # Lines parallel to x-axis

# Face diagonals (18 total)
for k in range(3):
    WINNING_LINES.append(((0, 0, k), (1, 1, k), (2, 2, k)))  # XY-plane main diagonal
    WINNING_LINES.append(((0, 2, k), (1, 1, k), (2, 0, k)))  # XY-plane anti-diagonal
for j in range(3):
    WINNING_LINES.append(((0, j, 0), (1, j, 1), (2, j, 2)))  # XZ-plane main diagonal
    WINNING_LINES.append(((0, j, 2), (1, j, 1), (2, j, 0)))  # XZ-plane anti-diagonal
for i in range(3):
    WINNING_LINES.append(((i, 0, 0), (i, 1, 1), (i, 2, 2)))  # YZ-plane main diagonal
    WINNING_LINES.append(((i, 0, 2), (i, 1, 1), (i, 2, 0)))  # YZ-plane anti-diagonal

# Space diagonals (4 total)
WINNING_LINES.append(((0, 0, 0), (1, 1, 1), (2, 2, 2)))
WINNING_LINES.append(((0, 0, 2), (1, 1, 1), (2, 2, 0)))
WINNING_LINES.append(((0, 2, 0), (1, 1, 1), (2, 0, 2)))
WINNING_LINES.append(((0, 2, 2), (1, 1, 1), (2, 0, 0)))

def check_win(board, player):
    """Check if the given player has won"""
    for a, b, c in WINNING_LINES:
        if board[a[0]][a[1]][a[2]] == player and \
           board[b[0]][b[1]][b[2]] == player and \
           board[c[0]][c[1]][c[2]] == player:
            return True
    return False

def get_empty(board):
    """Get all empty cells as list of (i,j,k) tuples"""
    return [(i, j, k) for i in range(3) for j in range(3) for k in range(3) if board[i][j][k] == 0]

def evaluate(board):
    """Evaluate board position from our perspective (player 1)"""
    # Terminal positions
    if check_win(board, 1):
        return 1000000
    if check_win(board, -1):
        return -1000000
    
    score = 0
    
    # Center control is extremely valuable
    center = board[1][1][1]
    if center == 1:
        score += 1000
    elif center == -1:
        score -= 1000
    
    # Evaluate each winning line for threats and control
    for a, b, c in WINNING_LINES:
        line_sum = board[a[0]][a[1]][a[2]] + board[b[0]][b[1]][b[2]] + board[c[0]][c[1]][c[2]]
        
        # Two of ours + empty = winning threat
        if line_sum == 2:
            score += 100
        # Two of opponent's + empty = need to block
        elif line_sum == -2:
            score -= 100
        # One of ours + two empty = good potential
        elif line_sum == 1:
            score += 10
        # One of opponent's + two empty = opponent's potential
        elif line_sum == -1:
            score -= 10
    
    return score

def minimax(board, depth, alpha, beta, maximizing, start_time):
    """Minimax with alpha-beta pruning and time limit"""
    # Hard time limit to ensure we return on time
    if time.time() - start_time > 0.95:
        return evaluate(board)
    
    # Check terminal states
    if check_win(board, 1):
        return 1000000 - depth  # Prefer faster wins
    if check_win(board, -1):
        return -1000000 + depth  # Prefer slower losses
    
    empty = get_empty(board)
    if not empty:
        return 0  # Draw
    
    if depth == 0:
        return evaluate(board)
    
    if maximizing:
        max_eval = -10000000
        for i, j, k in empty:
            board[i][j][k] = 1
            eval_score = minimax(board, depth-1, alpha, beta, False, start_time)
            board[i][j][k] = 0
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = 10000000
        for i, j, k in empty:
            board[i][j][k] = -1
            eval_score = minimax(board, depth-1, alpha, beta, True, start_time)
            board[i][j][k] = 0
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

def policy(board):
    """
    Main policy function that returns the next move as (i,j,k)
    """
    start_time = time.time()
    empty = get_empty(board)
    
    # 1. Immediate win: If we can win this turn, do it
    for i, j, k in empty:
        board[i][j][k] = 1
        if check_win(board, 1):
            board[i][j][k] = 0
            return (i, j, k)
        board[i][j][k] = 0
    
    # 2. Immediate block: If opponent can win next turn, block it
    for i, j, k in empty:
        board[i][j][k] = -1
        if check_win(board, -1):
            board[i][j][k] = 0
            return (i, j, k)
        board[i][j][k] = 0
    
    # 3. Center control: Take the center if available
    if board[1][1][1] == 0:
        return (1, 1, 1)
    
    # 4. Minimax search with iterative deepening
    best_move = empty[0]
    best_score = -10000000
    
    # Try depth 3 first, then depth 2 if time runs out
    for depth in [3, 2]:
        for i, j, k in empty:
            board[i][j][k] = 1
            score = minimax(board, depth-1, -10000000, 10000000, False, start_time)
            board[i][j][k] = 0
            
            if score > best_score:
                best_score = score
                best_move = (i, j, k)
            
            # Emergency time check - return best move found so far
            if time.time() - start_time > 0.9:
                return best_move
    
    return best_move
