
import numpy as np
from collections import deque
import math
import itertools
import random

DIRECTIONS = [(1,0), (-1,0), (0,1), (0,-1),
              (1,1), (1,-1), (-1,1), (-1,-1)]

def count_groups(board, player):
    """Count number of 8-connected groups for given player."""
    visited = set()
    groups = 0
    for r in range(8):
        for c in range(8):
            if board[r][c] == player and (r,c) not in visited:
                groups += 1
                # BFS
                q = deque([(r,c)])
                visited.add((r,c))
                while q:
                    cr, cc = q.popleft()
                    for dr, dc in DIRECTIONS:
                        nr, nc = cr+dr, cc+dc
                        if 0 <= nr < 8 and 0 <= nc < 8:
                            if board[nr][nc] == player and (nr,nc) not in visited:
                                visited.add((nr,nc))
                                q.append((nr,nc))
    return groups

def line_count(board, start_r, start_c, dr, dc):
    """Count pieces (both players) in line from start in direction (dr,dc)"""
    cnt = 0
    r, c = start_r, start_c
    while 0 <= r < 8 and 0 <= c < 8:
        if board[r][c] != 0:
            cnt += 1
        r += dr
        c += dc
    return cnt

def generate_moves(board, player):
    moves = []
    pieces = []
    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                pieces.append((r,c))
    for sr, sc in pieces:
        for dr, dc in DIRECTIONS:
            # length is number of pieces in this line
            length = line_count(board, sr, sc, dr, dc)
            if length == 0:
                continue
            tr, tc = sr + dr*length, sc + dc*length
            if 0 <= tr < 8 and 0 <= tc < 8:
                # check for enemy jump over
                blocked = False
                r, c = sr, sc
                for step in range(1, length+1):
                    nr, nc = sr + dr*step, sc + dc*step
                    if board[nr][nc] == -player:
                        if step < length:
                            blocked = True
                            break
                if not blocked:
                    # landing cell must be empty or enemy (capture)
                    if board[tr][tc] != player:
                        moves.append((sr, sc, tr, tc))
    return moves

def apply_move(board, move, player):
    """Return new board after move."""
    sr, sc, tr, tc = move
    new_board = [row[:] for row in board]
    new_board[sr][sc] = 0
    new_board[tr][tc] = player
    return new_board

def heuristic(board, player):
    """Evaluate board for player."""
    my_groups = count_groups(board, player)
    opp_groups = count_groups(board, -player)
    
    if my_groups == 1:
        # winning
        return 1000
    if opp_groups == 1:
        return -1000
    
    # piece count difference
    my_pieces = sum(1 for r in range(8) for c in range(8) if board[r][c] == player)
    opp_pieces = sum(1 for r in range(8) for c in range(8) if board[r][c] == -player)
    piece_diff = my_pieces - opp_pieces
    
    # central control
    center = [(3,3),(3,4),(4,3),(4,4)]
    center_control = sum(1 for r,c in center if board[r][c] == player)
    
    # group size maximization: prefer fewer groups
    score = -my_groups*10 + opp_groups*5 + piece_diff*2 + center_control
    return score

def order_moves(moves, board, player):
    """Simple move ordering: captures first."""
    def move_score(move):
        sr, sc, tr, tc = move
        if board[tr][tc] == -player:
            return 1
        return 0
    return sorted(moves, key=move_score, reverse=True)

def minimax(board, player, depth, alpha, beta, maximizing):
    if depth == 0:
        return heuristic(board, player), None
    moves = generate_moves(board, player if maximizing else -player)
    if not moves:
        return heuristic(board, player), None
    moves = order_moves(moves, board, player if maximizing else -player)
    if maximizing:
        best_val = -math.inf
        best_move = None
        for move in moves:
            new_board = apply_move(board, move, player)
            val, _ = minimax(new_board, player, depth-1, alpha, beta, False)
            if val > best_val:
                best_val = val
                best_move = move
            alpha = max(alpha, val)
            if beta <= alpha:
                break
        return best_val, best_move
    else:
        best_val = math.inf
        best_move = None
        for move in moves:
            new_board = apply_move(board, move, -player)
            val, _ = minimax(new_board, player, depth-1, alpha, beta, True)
            if val < best_val:
                best_val = val
                best_move = move
            beta = min(beta, val)
            if beta <= alpha:
                break
        return best_val, best_move

def policy(board):
    # board is given as list of lists of ints
    player = 1  # we are player 1
    moves = generate_moves(board, player)
    if not moves:
        # should not happen in valid game
        return "0,0:0,0"
    
    # check immediate win
    for move in moves:
        new_board = apply_move(board, move, player)
        if count_groups(new_board, player) == 1:
            sr, sc, tr, tc = move
            return f"{sr},{sc}:{tr},{tc}"
    
    # use minimax depth 2
    _, best_move = minimax(board, player, depth=2, alpha=-math.inf, beta=math.inf, maximizing=True)
    if best_move is None:
        # fallback: first legal move
        best_move = moves[0]
    
    sr, sc, tr, tc = best_move
    return f"{sr},{sc}:{tr},{tc}"
