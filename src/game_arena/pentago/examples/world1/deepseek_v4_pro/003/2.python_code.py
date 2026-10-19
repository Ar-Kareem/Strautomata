
import numpy as np
from copy import deepcopy

def policy(you, opponent) -> str:
    board = np.array(you, dtype=int) - np.array(opponent, dtype=int)
    empty_count = np.sum(board == 0)
    
    if empty_count > 30:
        depth = 2
    elif empty_count > 15:
        depth = 3
    else:
        depth = 4
    
    best_move = None
    best_score = -float('inf')
    alpha = -float('inf')
    beta = float('inf')
    
    moves = get_all_moves(board, 1)
    if not moves:
        for r in range(6):
            for c in range(6):
                if board[r, c] == 0:
                    for q in range(4):
                        for d in ['L', 'R']:
                            return f"{r+1},{c+1},{q},{d}"
    
    moves.sort(key=lambda m: move_heuristic(board, m), reverse=True)
    
    for move in moves[:15]:
        new_board = apply_move(board, move, 1)
        score = minimax(new_board, depth - 1, alpha, beta, -1)
        if score > best_score:
            best_score = score
            best_move = move
        alpha = max(alpha, score)
    
    if best_move is None:
        best_move = moves[0]
    
    r, c, q, d = best_move
    return f"{r+1},{c+1},{q},{d}"

def get_all_moves(board, player):
    moves = []
    for r in range(6):
        for c in range(6):
            if board[r, c] == 0:
                for q in range(4):
                    for d in ['L', 'R']:
                        moves.append((r, c, q, d))
    return moves

def apply_move(board, move, player):
    r, c, q, d = move
    new_board = board.copy()
    new_board[r, c] = player
    quadrant = get_quadrant(q)
    quad_data = new_board[quadrant[0]:quadrant[0]+3, quadrant[1]:quadrant[1]+3]
    if d == 'L':
        quad_data = np.rot90(quad_data, k=1)
    else:
        quad_data = np.rot90(quad_data, k=-1)
    new_board[quadrant[0]:quadrant[0]+3, quadrant[1]:quadrant[1]+3] = quad_data
    return new_board

def get_quadrant(q):
    return (0, 0) if q == 0 else (0, 3) if q == 1 else (3, 0) if q == 2 else (3, 3)

def move_heuristic(board, move):
    new_board = apply_move(board, move, 1)
    if check_win(new_board, 1):
        return 100000
    if check_win(new_board, -1):
        return -50000
    return evaluate_board(new_board) - evaluate_board(board)

def minimax(board, depth, alpha, beta, player):
    if depth == 0 or np.sum(board == 0) == 0:
        return evaluate_board(board)
    
    if check_win(board, 1):
        return 100000
    if check_win(board, -1):
        return -100000
    
    if player == 1:
        max_eval = -float('inf')
        moves = get_all_moves(board, player)
        if not moves:
            return evaluate_board(board)
        moves.sort(key=lambda m: move_heuristic(board, m), reverse=True)
        for move in moves[:12]:
            new_board = apply_move(board, move, player)
            eval_score = minimax(new_board, depth - 1, alpha, beta, -1)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        moves = get_all_moves(board, player)
        if not moves:
            return evaluate_board(board)
        moves.sort(key=lambda m: move_heuristic(board, m), reverse=True)
        for move in moves[:12]:
            new_board = apply_move(board, move, player)
            eval_score = minimax(new_board, depth - 1, alpha, beta, 1)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

def evaluate_board(board):
    score = 0
    score += 10000 * check_five_count(board, 1)
    score -= 10000 * check_five_count(board, -1)
    score += 100 * count_patterns(board, 1, 4)
    score -= 100 * count_patterns(board, -1, 4)
    score += 10 * count_patterns(board, 1, 3)
    score -= 10 * count_patterns(board, -1, 3)
    score += count_patterns(board, 1, 2)
    score -= count_patterns(board, -1, 2)
    for r in range(6):
        for c in range(6):
            if board[r, c] == 1:
                score += center_weight(r, c)
            elif board[r, c] == -1:
                score -= center_weight(r, c)
    return score

def check_win(board, player):
    return check_five(board, player)

def check_five(board, player):
    for r in range(6):
        for c in range(2):
            if all(board[r, c+i] == player for i in range(5)):
                return True
    for r in range(2):
        for c in range(6):
            if all(board[r+i, c] == player for i in range(5)):
                return True
    for r in range(2):
        for c in range(2):
            if all(board[r+i, c+i] == player for i in range(5)):
                return True
    for r in range(2):
        for c in range(4, 6):
            if all(board[r+i, c-i] == player for i in range(5)):
                return True
    return False

def check_five_count(board, player):
    count = 0
    for r in range(6):
        for c in range(2):
            if all(board[r, c+i] == player for i in range(5)):
                count += 1
    for r in range(2):
        for c in range(6):
            if all(board[r+i, c] == player for i in range(5)):
                count += 1
    for r in range(2):
        for c in range(2):
            if all(board[r+i, c+i] == player for i in range(5)):
                count += 1
    for r in range(2):
        for c in range(4, 6):
            if all(board[r+i, c-i] == player for i in range(5)):
                count += 1
    return count

def count_patterns(board, player, length):
    count = 0
    for r in range(6):
        for c in range(7 - length):
            window = board[r, c:c+length]
            if np.all(window == player):
                count += 1
    for r in range(7 - length):
        for c in range(6):
            window = board[r:r+length, c]
            if np.all(window == player):
                count += 1
    for r in range(7 - length):
        for c in range(7 - length):
            window = [board[r+i, c+i] for i in range(length)]
            if all(v == player for v in window):
                count += 1
    for r in range(7 - length):
        for c in range(length-1, 6):
            window = [board[r+i, c-i] for i in range(length)]
            if all(v == player for v in window):
                count += 1
    return count

def center_weight(r, c):
    weights = [
        [0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 1, 0],
        [0, 1, 2, 2, 1, 0],
        [0, 1, 2, 2, 1, 0],
        [0, 1, 1, 1, 1, 0],
        [0, 0, 0, 0, 0, 0]
    ]
    return weights[r][c]
