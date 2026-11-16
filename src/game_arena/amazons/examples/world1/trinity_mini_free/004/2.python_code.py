
import numpy as np

def count_moves(board, player):
    moves = 0
    for i in range(6):
        for j in range(6):
            if board[i][j] == player:
                for dr, dc in [(1,0), (-1,0), (0,1), (0,-1), (1,1), (1,-1), (-1,1), (-1,-1)]:
                    r, c = i, j
                    while True:
                        r += dr
                        c += dc
                        if not (0 <= r < 6 and 0 <= c < 6):
                            break
                        if board[r][c] != 0:
                            break
                        moves += 1
    return moves

def evaluate(board):
    my_moves = count_moves(board, 1)
    opp_moves = count_moves(board, 2)
    center_control = 0
    for i in [2,3]:
        for j in [2,3]:
            if board[i][j] == 1:
                center_control += 1
            elif board[i][j] == 2:
                center_control -= 1
    if opp_moves == 0:
        return float('inf')
    if my_moves == 0:
        return -float('inf')
    return (my_moves - opp_moves) + center_control * 0.1

def generate_moves(board, player):
    moves = []
    for i in range(6):
        for j in range(6):
            if board[i][j] == player:
                for dr, dc in [(1,0), (-1,0), (0,1), (0,-1), (1,1), (1,-1), (-1,1), (-1,-1)]:
                    r, c = i, j
                    while True:
                        r += dr
                        c += dc
                        if not (0 <= r < 6 and 0 <= c < 6):
                            break
                        if board[r][c] != 0:
                            break
                        for adr, adc in [(1,0), (-1,0), (0,1), (0,-1), (1,1), (1,-1), (-1,1), (-1,-1)]:
                            ar, ac = r, c
                            while True:
                                ar += adr
                                ac += adc
                                if not (0 <= ar < 6 and 0 <= ac < 6):
                                    break
                                if board[ar][ac] != 0:
                                    break
                                moves.append((i, j, r, c, ar, ac))
    return moves

def apply_move(board, move):
    new_board = [row[:] for row in board]
    new_board[move[0]][move[1]] = 0
    new_board[move[2]][move[3]] = 1
    new_board[move[4]][move[5]] = -1
    return new_board

def minimax(board, depth, alpha, beta, maximizing_player):
    if depth == 0:
        return evaluate(board), None
    if maximizing_player:
        max_eval = -float('inf')
        best_move = None
        moves = generate_moves(board, 1)
        for move in moves:
            new_board = apply_move(board, move)
            eval, _ = minimax(new_board, depth-1, alpha, beta, False)
            if eval > max_eval:
                max_eval = eval
                best_move = move
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        best_move = None
        moves = generate_moves(board, 2)
        for move in moves:
            new_board = apply_move(board, move)
            eval, _ = minimax(new_board, depth-1, alpha, beta, True)
            if eval < min_eval:
                min_eval = eval
                best_move = move
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval, best_move

def policy(board):
    moves = generate_moves(board, 1)
    if not moves:
        return None
    _, best_move = minimax(board, 2, -float('inf'), float('inf'), True)
    return f"{best_move[0]},{best_move[1]}:{best_move[2]},{best_move[3]}:{best_move[4]},{best_move[5]}"
