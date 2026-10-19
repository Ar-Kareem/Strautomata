
import numpy as np
import time

# Define game constants
YOU = 1
OPPONENT = 2
directions = [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)]

# Precomputed position weight matrix for Othello
weight_matrix = np.array([
    [120, -20,  20,   5,   5,  20, -20, 120],
    [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
    [ 20,  -5,  15,   3,   3,  15,  -5,  20],
    [  5,  -5,   3,   3,   3,   3,  -5,   5],
    [  5,  -5,   3,   3,   3,   3,  -5,   5],
    [ 20,  -5,  15,   3,   3,  15,  -5,  20],
    [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
    [120, -20,  20,   5,   5,  20, -20, 120]
], dtype=float)

def is_legal_move(you_board, opponent_board, player, r, c):
    if you_board[r][c] != 0 or opponent_board[r][c] != 0:
        return False
    if player == YOU:
        my_board = you_board
        opp_board = opponent_board
    else:
        my_board = opponent_board
        opp_board = you_board
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        if not (0<=nr<8 and 0<=nc<8):
            continue
        if opp_board[nr][nc] != 1:
            continue
        while 0<=nr<8 and 0<=nc<8 and opp_board[nr][nc] == 1:
            nr += dr
            nc += dc
        if 0<=nr<8 and 0<=nc<8 and my_board[nr][nc] == 1:
            return True
    return False

def get_legal_moves(you_board, opponent_board, player):
    moves = []
    for r in range(8):
        for c in range(8):
            if you_board[r][c] == 0 and opponent_board[r][c] == 0:
                if is_legal_move(you_board, opponent_board, player, r, c):
                    moves.append((r,c))
    return moves

def apply_move(you_board, opponent_board, player, r, c):
    new_you = you_board.copy()
    new_opponent = opponent_board.copy()
    if player == YOU:
        new_you[r][c] = 1
        flip_cells = []
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if not (0<=nr<8 and 0<=nc<8):
                continue
            if new_opponent[nr][nc] != 1:
                continue
            path = []
            while 0<=nr<8 and 0<=nc<8 and new_opponent[nr][nc] == 1:
                path.append((nr,nc))
                nr += dr
                nc += dc
            if 0<=nr<8 and 0<=nc<8 and new_you[nr][nc] == 1:
                flip_cells.extend(path)
        for cell in flip_cells:
            new_opponent[cell[0]][cell[1]] = 0
            new_you[cell[0]][cell[1]] = 1
    else:
        new_opponent[r][c] = 1
        flip_cells = []
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if not (0<=nr<8 and 0<=nc<8):
                continue
            if new_you[nr][nc] != 1:
                continue
            path = []
            while 0<=nr<8 and 0<=nc<8 and new_you[nr][nc] == 1:
                path.append((nr,nc))
                nr += dr
                nc += dc
            if 0<=nr<8 and 0<=nc<8 and new_opponent[nr][nc] == 1:
                flip_cells.extend(path)
        for cell in flip_cells:
            new_you[cell[0]][cell[1]] = 0
            new_opponent[cell[0]][cell[1]] = 1
    return new_you, new_opponent

def evaluate_board(you_board, opponent_board):
    disc_diff = you_board.sum() - opponent_board.sum()
    mobility_diff = len(get_legal_moves(you_board, opponent_board, YOU)) - len(get_legal_moves(you_board, opponent_board, OPPONENT))
    position_score = (you_board * weight_matrix).sum() - (opponent_board * weight_matrix).sum()
    return disc_diff * 1.0 + mobility_diff * 10.0 + position_score * 0.1

def minimax(you_board, opponent_board, depth, alpha, beta, maximizing_player):
    if depth == 0:
        return evaluate_board(you_board, opponent_board)
    
    if maximizing_player:
        max_eval = -float('inf')
        legal_moves = get_legal_moves(you_board, opponent_board, YOU)
        if not legal_moves:
            opp_moves = get_legal_moves(you_board, opponent_board, OPPONENT)
            if not opp_moves:
                return evaluate_board(you_board, opponent_board)
            else:
                return minimax(you_board, opponent_board, depth-1, alpha, beta, False)
        else:
            for move in legal_moves:
                new_you, new_opponent = apply_move(you_board, opponent_board, YOU, move[0], move[1])
                eval = minimax(new_you, new_opponent, depth-1, alpha, beta, False)
                if eval > max_eval:
                    max_eval = eval
                if eval > alpha:
                    alpha = eval
                if beta <= alpha:
                    break
            return max_eval
    else:
        min_eval = float('inf')
        legal_moves = get_legal_moves(you_board, opponent_board, OPPONENT)
        if not legal_moves:
            our_moves = get_legal_moves(you_board, opponent_board, YOU)
            if not our_moves:
                return evaluate_board(you_board, opponent_board)
            else:
                return minimax(you_board, opponent_board, depth-1, alpha, beta, True)
        else:
            for move in legal_moves:
                new_you, new_opponent = apply_move(you_board, opponent_board, OPPONENT, move[0], move[1])
                eval = minimax(new_you, new_opponent, depth-1, alpha, beta, True)
                if eval < min_eval:
                    min_eval = eval
                if eval < beta:
                    beta = eval
                if beta <= alpha:
                    break
            return min_eval

def get_best_move(you_board, opponent_board, depth):
    legal_moves = get_legal_moves(you_board, opponent_board, YOU)
    if not legal_moves:
        return None, -float('inf')
    
    best_move = None
    best_value = -float('inf')
    for move in legal_moves:
        new_you, new_opponent = apply_move(you_board, opponent_board, YOU, move[0], move[1])
        value = minimax(new_you, new_opponent, depth-1, -float('inf'), float('inf'), False)
        if value > best_value:
            best_value = value
            best_move = move
    return best_move, best_value

def policy(you, opponent):
    start_time = time.time()
    time_limit = 1.0
    best_move = None
    best_value = -float('inf')
    
    legal_moves = get_legal_moves(you, opponent, YOU)
    if not legal_moves:
        return "pass"
    
    for depth in range(1, 10):
        if time.time() - start_time > time_limit * 0.9:
            break
        move, value = get_best_move(you, opponent, depth)
        if move is not None:
            best_move = move
            best_value = value
    
    if best_move is None:
        best_move = legal_moves[0]
    
    r, c = best_move
    return chr(ord('a') + c) + str(r+1)
