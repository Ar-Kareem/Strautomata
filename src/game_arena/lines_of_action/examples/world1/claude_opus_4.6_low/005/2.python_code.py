
import numpy as np
from collections import deque

def policy(board):
    board = np.array(board)
    moves = get_all_moves(board, 1)
    if not moves:
        return "0,0:0,0"
    
    best_move = None
    best_score = -float('inf')
    alpha, beta = -float('inf'), float('inf')
    
    for m in moves:
        nb = apply_move(board, m, 1)
        score = minimax(nb, 2, False, alpha, beta)
        if score > best_score:
            best_score = score
            best_move = m
        alpha = max(alpha, score)
    
    return f"{best_move[0]},{best_move[1]}:{best_move[2]},{best_move[3]}"

def minimax(board, depth, maximizing, alpha, beta):
    player = 1 if maximizing else -1
    
    # Check wins
    if check_connected(board, 1): return 100000
    if check_connected(board, -1): return -100000
    if depth == 0:
        return evaluate(board)
    
    moves = get_all_moves(board, player)
    if not moves:
        return evaluate(board)
    
    if maximizing:
        val = -float('inf')
        for m in moves:
            nb = apply_move(board, m, player)
            val = max(val, minimax(nb, depth-1, False, alpha, beta))
            alpha = max(alpha, val)
            if alpha >= beta: break
        return val
    else:
        val = float('inf')
        for m in moves:
            nb = apply_move(board, m, player)
            val = min(val, minimax(nb, depth-1, True, alpha, beta))
            beta = min(beta, val)
            if alpha >= beta: break
        return val

def evaluate(board):
    return -connectivity_score(board, 1) + connectivity_score(board, -1)

def connectivity_score(board, player):
    pieces = list(zip(*np.where(board == player)))
    if len(pieces) <= 1: return 0
    # Number of connected components * 100 + sum of pairwise distances
    visited = set()
    components = 0
    for p in pieces:
        if p not in visited:
            components += 1
            q = deque([p])
            visited.add(p)
            while q:
                r, c = q.popleft()
                for dr in [-1,0,1]:
                    for dc in [-1,0,1]:
                        if dr==0 and dc==0: continue
                        nb = (r+dr, c+dc)
                        if nb not in visited and nb in set(pieces):
                            visited.add(nb)
                            q.append(nb)
    # Also add center distance
    cr = sum(p[0] for p in pieces)/len(pieces)
    cc = sum(p[1] for p in pieces)/len(pieces)
    spread = sum(abs(p[0]-cr)+abs(p[1]-cc) for p in pieces)
    return (components - 1) * 200 + spread

def check_connected(board, player):
    pieces = list(zip(*np.where(board == player)))
    if len(pieces) <= 1: return True
    visited = {pieces[0]}
    q = deque([pieces[0]])
    ps = set(pieces)
    while q:
        r, c = q.popleft()
        for dr in [-1,0,1]:
            for dc in [-1,0,1]:
                if dr==0 and dc==0: continue
                nb = (r+dr, c+dc)
                if nb in ps and nb not in visited:
                    visited.add(nb)
                    q.append(nb)
    return len(visited) == len(pieces)

def get_all_moves(board, player):
    moves = []
    pieces = zip(*np.where(board == player))
    for r, c in pieces:
        for dr in [-1,0,1]:
            for dc in [-1,0,1]:
                if dr==0 and dc==0: continue
                # Count pieces in this line
                count = count_pieces_in_line(board, r, c, dr, dc)
                tr, tc = r + dr*count, c + dc*count
                if 0 <= tr < 8 and 0 <= tc < 8:
                    if board[tr][tc] != player:
                        # Check path - can't jump over enemy
                        blocked = False
                        for step in range(1, count):
                            mr, mc = r+dr*step, c+dc*step
                            if board[mr][mc] == -player:
                                blocked = True; break
                        if not blocked:
                            moves.append((r, c, tr, tc))
    return moves

def count_pieces_in_line(board, r, c, dr, dc):
    count = 0
    if dr == 0 and dc == 0: return 0
    # For horizontal (dr=0): count all pieces in row
    # For vertical (dc=0): count all pieces in column
    # For diagonal: count all pieces on that diagonal
    # Actually: count pieces along the entire line through (r,c) in direction (dr,dc)
    # Go to one end
    sr, sc = r, c
    while 0 <= sr-dr < 8 and 0 <= sc-dc < 8:
        sr -= dr; sc -= dc
    # Count
    cr, cc = sr, sc
    while 0 <= cr < 8 and 0 <= cc < 8:
        if board[cr][cc] != 0:
            count += 1
        cr += dr; cc += dc
    return count

def apply_move(board, move, player):
    nb = board.copy()
    r, c, tr, tc = move
    nb[r][c] = 0
    nb[tr][tc] = player
    return nb
