
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    b = np.array(board, dtype=np.int8)
    
    # Get all empty positions
    empty = [(i, j) for i in range(4) for j in range(4) if b[i, j] == 0]
    
    if not empty:
        return (0, 0)
    
    if len(empty) == 16:
        return (1, 1)  # Start near center
    
    # Check for immediate win
    for pos in empty:
        b[pos] = 1
        if check_win(b, 1):
            return pos
        b[pos] = 0
    
    # Check for immediate block
    for pos in empty:
        b[pos] = -1
        if check_win(b, -1):
            b[pos] = 0
            return pos
        b[pos] = 0
    
    # Use minimax with alpha-beta pruning
    best_move = empty[0]
    best_score = -float('inf')
    
    # Adaptive depth based on number of empty squares
    depth = 5 if len(empty) <= 10 else 4 if len(empty) <= 12 else 3
    
    for pos in empty:
        b[pos] = 1
        score = minimax(b, depth, -float('inf'), float('inf'), False)
        b[pos] = 0
        if score > best_score:
            best_score = score
            best_move = pos
    
    return best_move

def check_win(board, player):
    # Check rows
    for i in range(4):
        if board[i, 0] == board[i, 1] == board[i, 2] == board[i, 3] == player:
            return True
    # Check columns
    for j in range(4):
        if board[0, j] == board[1, j] == board[2, j] == board[3, j] == player:
            return True
    # Check diagonals
    if board[0, 0] == board[1, 1] == board[2, 2] == board[3, 3] == player:
        return True
    if board[0, 3] == board[1, 2] == board[2, 1] == board[3, 0] == player:
        return True
    return False

def evaluate(board):
    # Check for wins
    if check_win(board, 1):
        return 10000
    if check_win(board, -1):
        return -10000
    
    score = 0
    lines = get_lines(board)
    
    for line in lines:
        score += evaluate_line(line)
    
    return score

def get_lines(board):
    lines = []
    # Rows
    for i in range(4):
        lines.append([board[i, j] for j in range(4)])
    # Columns
    for j in range(4):
        lines.append([board[i, j] for i in range(4)])
    # Diagonals
    lines.append([board[i, i] for i in range(4)])
    lines.append([board[i, 3-i] for i in range(4)])
    return lines

def evaluate_line(line):
    my_count = line.count(1)
    opp_count = line.count(-1)
    
    if my_count > 0 and opp_count > 0:
        return 0  # Blocked line
    
    if my_count == 4:
        return 10000
    if opp_count == 4:
        return -10000
    if my_count == 3:
        return 100
    if opp_count == 3:
        return -100
    if my_count == 2:
        return 10
    if opp_count == 2:
        return -10
    if my_count == 1:
        return 1
    if opp_count == 1:
        return -1
    return 0

def minimax(board, depth, alpha, beta, is_maximizing):
    if check_win(board, 1):
        return 10000 + depth
    if check_win(board, -1):
        return -10000 - depth
    
    empty = [(i, j) for i in range(4) for j in range(4) if board[i, j] == 0]
    
    if not empty or depth == 0:
        return evaluate(board)
    
    if is_maximizing:
        max_eval = -float('inf')
        for pos in empty:
            board[pos] = 1
            eval_score = minimax(board, depth - 1, alpha, beta, False)
            board[pos] = 0
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for pos in empty:
            board[pos] = -1
            eval_score = minimax(board, depth - 1, alpha, beta, True)
            board[pos] = 0
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval
