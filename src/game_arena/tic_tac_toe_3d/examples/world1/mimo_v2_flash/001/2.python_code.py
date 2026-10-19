
import sys
import time

# Precompute all 49 winning lines for a 3x3x3 cube.
# A line is a list of 3 coordinates (i, j, k).
WINNING_LINES = []

def generate_lines():
    # 1. Axes lines (Rows, Columns, Pillars)
    # Rows: (x, y, k) fixed k, y; vary x
    for k in range(3):
        for y in range(3):
            WINNING_LINES.append([(x, y, k) for x in range(3)])
    # Columns: (x, y, k) fixed k, x; vary y
    for k in range(3):
        for x in range(3):
            WINNING_LINES.append([(x, y, k) for y in range(3)])
    # Pillars: (x, y, k) fixed x, y; vary k
    for x in range(3):
        for y in range(3):
            WINNING_LINES.append([(x, y, k) for k in range(3)])

    # 2. Face Diagonals
    # XY planes (k fixed)
    for k in range(3):
        WINNING_LINES.append([(0, 0, k), (1, 1, k), (2, 2, k)]) # Main diag
        WINNING_LINES.append([(0, 2, k), (1, 1, k), (2, 0, k)]) # Anti diag
    # XZ planes (y fixed)
    for y in range(3):
        WINNING_LINES.append([(0, y, 0), (1, y, 1), (2, y, 2)]) # Main diag
        WINNING_LINES.append([(0, y, 2), (1, y, 1), (2, y, 0)]) # Anti diag
    # YZ planes (x fixed)
    for x in range(3):
        WINNING_LINES.append([(x, 0, 0), (x, 1, 1), (x, 2, 2)]) # Main diag
        WINNING_LINES.append([(x, 0, 2), (x, 1, 1), (x, 2, 0)]) # Anti diag

    # 3. Space Diagonals (4 total)
    WINNING_LINES.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)]) # Main
    WINNING_LINES.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
    WINNING_LINES.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
    WINNING_LINES.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])

# Generate lines once at startup
generate_lines()

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Determines the next best move for 3D Tic Tac Toe.
    Uses Minimax with Alpha-Beta pruning and a heuristic based on line threats.
    """
    
    # 1. Flatten the board for faster access if needed, but we can stick to 3D list
    # 2. Identify valid moves
    valid_moves = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    valid_moves.append((i, j, k))
    
    if not valid_moves:
        return (0, 0, 0) # Should not happen if game is over, but safety

    # 3. Immediate Win / Block Check
    # Check if we can win immediately
    for move in valid_moves:
        i, j, k = move
        board[i][j][k] = 1
        if check_win(board, 1):
            board[i][j][k] = 0
            return move
        board[i][j][k] = 0

    # Check if opponent can win immediately (and block)
    for move in valid_moves:
        i, j, k = move
        board[i][j][k] = -1
        if check_win(board, -1):
            board[i][j][k] = 0
            return move
        board[i][j][k] = 0

    # 4. Minimax Search
    # Depth limit: 4 is usually enough for 3D Tic Tac Toe to find forced wins.
    # Since total moves are small, we can go deeper, but 4-5 is safe for <1s time limit.
    best_move = None
    best_score = -float('inf')
    
    # Move ordering: prioritize center and corners to improve alpha-beta pruning
    # Center of cube is (1,1,1). Corners are (0,0,0) etc.
    # Heuristic ordering helps prune the tree faster.
    def move_score(m):
        i, j, k = m
        score = 0
        if (i, j, k) == (1, 1, 1): score += 5
        elif i in [0, 2] and j in [0, 2] and k in [0, 2]: score += 3 # Corner
        elif i in [0, 2] or j in [0, 2] or k in [0, 2]: score += 1
        return score

    valid_moves.sort(key=move_score, reverse=True)

    # Alpha-Beta Pruning
    alpha = -float('inf')
    beta = float('inf')
    depth = 5 # Lookahead depth

    for move in valid_moves:
        i, j, k = move
        board[i][j][k] = 1
        score = minimax(board, depth - 1, alpha, beta, False)
        board[i][j][k] = 0

        if score > best_score:
            best_score = score
            best_move = move
        
        alpha = max(alpha, best_score)
        if beta <= alpha:
            break

    if best_move is None:
        # Fallback if search fails (shouldn't happen)
        return valid_moves[0]
        
    return best_move

def check_win(board, player):
    """Checks if a player has won."""
    for line in WINNING_LINES:
        if all(board[i][j][k] == player for i, j, k in line):
            return True
    return False

def evaluate(board, player):
    """
    Heuristic evaluation function.
    Positive score favors 'player'.
    Tries to count potential winning lines (threats).
    """
    opponent = -player
    score = 0
    
    for line in WINNING_LINES:
        p_count = 0
        o_count = 0
        empty = 0
        
        for i, j, k in line:
            val = board[i][j][k]
            if val == player: p_count += 1
            elif val == opponent: o_count += 1
            else: empty += 1
        
        # Scoring logic:
        # If we have 2 and empty 1 -> Great (1000) almost win
        # If opp has 2 and empty 1 -> Bad ( -1000) must block next
        # If we have 1 and empty 2 -> Good (10) potential
        # If opp has 1 and empty 2 -> Bad (-10)
        
        if p_count == 3: return 100000 # Win
        if o_count == 3: return -100000 # Loss
        
        if p_count == 2 and empty == 1: score += 1000
        elif p_count == 1 and empty == 2: score += 10
        
        if o_count == 2 and empty == 1: score -= 1200 # Block priority slightly higher than create
        elif o_count == 1 and empty == 2: score -= 20
        
    return score

def minimax(board, depth, alpha, beta, is_maximizing):
    # Terminal conditions
    if check_win(board, 1): return 100000 + depth # Prefer faster wins
    if check_win(board, -1): return -100000 - depth # Prefer slower losses
    
    if depth == 0:
        return evaluate(board, 1) # Evaluate assuming player 1 (us)

    # Generate valid moves
    moves = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    moves.append((i, j, k))
    
    if not moves: return 0 # Draw

    # Move ordering (simple center/corner bias for deeper nodes)
    moves.sort(key=lambda m: 1 if m == (1,1,1) else 0, reverse=True)

    if is_maximizing:
        max_eval = -float('inf')
        for i, j, k in moves:
            board[i][j][k] = 1
            eval_score = minimax(board, depth - 1, alpha, beta, False)
            board[i][j][k] = 0
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for i, j, k in moves:
            board[i][j][k] = -1
            eval_score = minimax(board, depth - 1, alpha, beta, True)
            board[i][j][k] = 0
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval
