
import sys

# Precompute all lines (rows, cols, diagonals) for 4x4 board
LINES = []
# Rows
for r in range(4):
    LINES.append([(r, c) for c in range(4)])
# Cols
for c in range(4):
    LINES.append([(r, c) for r in range(4)])
# Diagonals
LINES.append([(i, i) for i in range(4)])
LINES.append([(i, 3 - i) for i in range(4)])

def get_valid_moves(board):
    moves = []
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                moves.append((r, c))
    return moves

def check_winner(board):
    for line in LINES:
        s = sum(board[r][c] for r, c in line)
        if s == 4:
            return 1
        if s == -4:
            return -1
    return 0

def is_board_full(board):
    return all(board[r][c] != 0 for r in range(4) for c in range(4))

def evaluate(board):
    winner = check_winner(board)
    if winner == 1: return 10000
    if winner == -1: return -10000
    
    score = 0
    for line in LINES:
        line_vals = [board[r][c] for r, c in line]
        my_count = line_vals.count(1)
        opp_count = line_vals.count(-1)
        
        # Only score lines that are not blocked
        if my_count > 0 and opp_count == 0:
            if my_count == 1: score += 1
            elif my_count == 2: score += 10
            elif my_count == 3: score += 100
        elif opp_count > 0 and my_count == 0:
            if opp_count == 1: score -= 1
            elif opp_count == 2: score -= 10
            elif opp_count == 3: score -= 100
            
    return score

def minimax(board, depth, alpha, beta, maximizing_player):
    winner = check_winner(board)
    if winner != 0:
        return winner * 10000
    if depth == 0 or is_board_full(board):
        return evaluate(board)
    
    moves = get_valid_moves(board)
    
    # Simple move ordering: Center/Corners first might help pruning
    # Priority: Center(3), Corner(2), Edge(1)
    def move_priority(move):
        r, c = move
        if (r, c) in [(1, 1), (1, 2), (2, 1), (2, 2)]: return 3
        if (r, c) in [(0, 0), (0, 3), (3, 0), (3, 3)]: return 2
        return 1
    moves.sort(key=move_priority, reverse=True)

    if maximizing_player:
        max_eval = -sys.maxsize
        for r, c in moves:
            board[r][c] = 1
            eval_val = minimax(board, depth - 1, alpha, beta, False)
            board[r][c] = 0
            max_eval = max(max_eval, eval_val)
            alpha = max(alpha, eval_val)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = sys.maxsize
        for r, c in moves:
            board[r][c] = -1
            eval_val = minimax(board, depth - 1, alpha, beta, True)
            board[r][c] = 0
            min_eval = min(min_eval, eval_val)
            beta = min(beta, eval_val)
            if beta <= alpha:
                break
        return min_eval

def policy(board):
    # 1. Check for immediate win
    valid_moves = get_valid_moves(board)
    for r, c in valid_moves:
        board[r][c] = 1
        if check_winner(board) == 1:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    # 2. Check for immediate block
    for r, c in valid_moves:
        board[r][c] = -1
        if check_winner(board) == -1:
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    # 3. Minimax for strategic move
    # Adjust depth based on remaining moves
    empty_count = len(valid_moves)
    if empty_count > 10:
        depth = 4
    elif empty_count > 5:
        depth = 6
    else:
        depth = 8

    best_score = -sys.maxsize
    best_move = valid_moves[0] # Default fallback
    
    # Re-order moves for the root call to improve pruning
    def move_priority(move):
        r, c = move
        if (r, c) in [(1, 1), (1, 2), (2, 1), (2, 2)]: return 3
        if (r, c) in [(0, 0), (0, 3), (3, 0), (3, 3)]: return 2
        return 1
    valid_moves.sort(key=move_priority, reverse=True)

    for r, c in valid_moves:
        board[r][c] = 1
        # We are maximizing, so next call is minimizing
        score = minimax(board, depth - 1, -sys.maxsize, sys.maxsize, False)
        board[r][c] = 0
        
        if score > best_score:
            best_score = score
            best_move = (r, c)

    return best_move
