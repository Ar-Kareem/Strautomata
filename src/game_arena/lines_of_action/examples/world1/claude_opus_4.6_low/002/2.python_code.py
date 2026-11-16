
import numpy as np
from collections import deque

def policy(board):
    board = np.array(board)
    moves = get_legal_moves(board, 1)
    if not moves:
        return "0,0:0,0"
    
    best_move = moves[0]
    best_score = -float('inf')
    
    for move in moves:
        new_board = apply_move(board, move)
        score = minimax(new_board, 3, -float('inf'), float('inf'), False)
        if score > best_score:
            best_score = score
            best_move = move
    
    return f"{best_move[0]},{best_move[1]}:{best_move[2]},{best_move[3]}"

def minimax(board, depth, alpha, beta, maximizing):
    player = 1 if maximizing else -1
    
    if check_win(board, 1):
        return 10000
    if check_win(board, -1):
        return -10000
    if depth == 0:
        return evaluate(board)
    
    moves = get_legal_moves(board, player)
    if not moves:
        return evaluate(board)
    
    if maximizing:
        val = -float('inf')
        for move in moves:
            new_board = apply_move(board, move)
            val = max(val, minimax(new_board, depth-1, alpha, beta, False))
            alpha = max(alpha, val)
            if alpha >= beta:
                break
        return val
    else:
        val = float('inf')
        for move in moves:
            new_board = apply_move(board, move)
            val = min(val, minimax(new_board, depth-1, alpha, beta, True))
            beta = min(beta, val)
            if alpha >= beta:
                break
        return val

def evaluate(board):
    return eval_player(board, 1) - eval_player(board, -1)

def eval_player(board, player):
    pieces = list(zip(*np.where(board == player)))
    if len(pieces) <= 1:
        return 1000
    
    # Number of connected components (fewer is better)
    components = count_components(board, player)
    
    # Center of mass concentration
    rows = [p[0] for p in pieces]
    cols = [p[1] for p in pieces]
    cr, cc = np.mean(rows), np.mean(cols)
    dist = sum(abs(r-cr) + abs(c-cc) for r,c in pieces)
    
    return -components * 50 - dist

def count_components(board, player):
    pieces = set(zip(*np.where(board == player)))
    if not pieces:
        return 0
    visited = set()
    components = 0
    for p in pieces:
        if p not in visited:
            components += 1
            q = deque([p])
            while q:
                cur = q.popleft()
                if cur in visited:
                    continue
                visited.add(cur)
                for dr in [-1,0,1]:
                    for dc in [-1,0,1]:
                        if dr==0 and dc==0: continue
                        nb = (cur[0]+dr, cur[1]+dc)
                        if nb in pieces and nb not in visited:
                            q.append(nb)
    return components

def check_win(board, player):
    pieces = list(zip(*np.where(board == player)))
    if len(pieces) <= 1:
        return True
    return count_components(board, player) == 1

def get_legal_moves(board, player):
    moves = []
    pieces = list(zip(*np.where(board == player)))
    for r, c in pieces:
        for dr in [-1,0,1]:
            for dc in [-1,0,1]:
                if dr==0 and dc==0: continue
                count = count_pieces_in_line(board, r, c, dr, dc)
                tr, tc = r + dr*count, c + dc*count
                if 0<=tr<8 and 0<=tc<8:
                    if board[tr][tc] != player:
                        # Check path clear of enemy pieces
                        if path_clear(board, r, c, dr, dc, count, player):
                            moves.append((r,c,tr,tc))
    return moves

def count_pieces_in_line(board, r, c, dr, dc):
    count = 0
    # Count all pieces along the entire line through (r,c) in direction (dr,dc)
    # Go to one end
    for sign in [1, -1]:
        nr, nc = r + sign*dr, c + sign*dc
        while 0<=nr<8 and 0<=nc<8:
            if board[nr][nc] != 0:
                count += 1
            nr += sign*dr
            nc += sign*dc
    # Count the piece itself
    if board[r][c] != 0:
        count += 1
    return count

def path_clear(board, r, c, dr, dc, count, player):
    for i in range(1, count):
        nr, nc = r+dr*i, c+dc*i
        if board[nr][nc] == -player:
            return False
    return True

def apply_move(board, move):
    new_board = board.copy()
    r1,c1,r2,c2 = move
    new_board[r2][c2] = new_board[r1][c1]
    new_board[r1][c1] = 0
    return new_board
