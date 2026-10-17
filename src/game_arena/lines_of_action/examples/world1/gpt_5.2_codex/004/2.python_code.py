
import math
import random
import time

DIRECTIONS = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]

def in_bounds(r,c):
    return 0 <= r < 8 and 0 <= c < 8

def count_line(board, r, c, dr, dc):
    count = 0
    rr, cc = r, c
    while in_bounds(rr, cc):
        if board[rr][cc] != 0:
            count += 1
        rr -= dr
        cc -= dc
    rr, cc = r + dr, c + dc
    while in_bounds(rr, cc):
        if board[rr][cc] != 0:
            count += 1
        rr += dr
        cc += dc
    return count

def legal_moves(board, player):
    moves = []
    for r in range(8):
        for c in range(8):
            if board[r][c] != player:
                continue
            for dr, dc in DIRECTIONS:
                dist = count_line(board, r, c, dr, dc)
                tr = r + dr * dist
                tc = c + dc * dist
                if not in_bounds(tr, tc):
                    continue
                # check path for enemy blocks
                rr, cc = r + dr, c + dc
                blocked = False
                while (rr, cc) != (tr, tc):
                    if board[rr][cc] == -player:
                        blocked = True
                        break
                    rr += dr
                    cc += dc
                if blocked:
                    continue
                if board[tr][tc] == player:
                    continue
                moves.append((r, c, tr, tc))
    return moves

def apply_move(board, move, player):
    r, c, tr, tc = move
    newb = [row[:] for row in board]
    newb[r][c] = 0
    newb[tr][tc] = player
    return newb

def connected_components(board, player):
    visited = [[False]*8 for _ in range(8)]
    comps = 0
    for r in range(8):
        for c in range(8):
            if board[r][c] == player and not visited[r][c]:
                comps += 1
                stack = [(r,c)]
                visited[r][c] = True
                while stack:
                    rr, cc = stack.pop()
                    for dr, dc in DIRECTIONS:
                        nr, nc = rr + dr, cc + dc
                        if in_bounds(nr, nc) and not visited[nr][nc] and board[nr][nc] == player:
                            visited[nr][nc] = True
                            stack.append((nr,nc))
    return comps

def is_connected(board, player):
    pieces = [(r,c) for r in range(8) for c in range(8) if board[r][c] == player]
    if len(pieces) <= 1:
        return True
    return connected_components(board, player) == 1

def centroid_distance(board, player):
    pieces = [(r,c) for r in range(8) for c in range(8) if board[r][c] == player]
    if not pieces:
        return 0
    cr = sum(p[0] for p in pieces) / len(pieces)
    cc = sum(p[1] for p in pieces) / len(pieces)
    dist = 0.0
    for r,c in pieces:
        dist += abs(r-cr) + abs(c-cc)
    return dist

def evaluate(board, player):
    opp = -player
    if is_connected(board, player):
        return 100000
    if is_connected(board, opp):
        return -100000
    comps_p = connected_components(board, player)
    comps_o = connected_components(board, opp)
    pieces_p = sum(1 for r in range(8) for c in range(8) if board[r][c] == player)
    pieces_o = sum(1 for r in range(8) for c in range(8) if board[r][c] == opp)
    cent_p = centroid_distance(board, player)
    cent_o = centroid_distance(board, opp)
    mob_p = len(legal_moves(board, player))
    mob_o = len(legal_moves(board, opp))
    score = 0
    score += (comps_o - comps_p) * 100
    score += (pieces_p - pieces_o) * 2
    score += (cent_o - cent_p) * 1.5
    score += (mob_p - mob_o) * 0.5
    return score

def alphabeta(board, player, depth, alpha, beta):
    if depth == 0 or is_connected(board, player) or is_connected(board, -player):
        return evaluate(board, player), None
    moves = legal_moves(board, player)
    if not moves:
        return evaluate(board, player), None
    best_move = None
    # move ordering: captures first
    def capture_key(m):
        r,c,tr,tc = m
        return 1 if board[tr][tc] == -player else 0
    moves.sort(key=capture_key, reverse=True)
    for move in moves:
        newb = apply_move(board, move, player)
        score, _ = alphabeta(newb, -player, depth-1, -beta, -alpha)
        score = -score
        if score > alpha:
            alpha = score
            best_move = move
        if alpha >= beta:
            break
    return alpha, best_move

def policy(board):
    moves = legal_moves(board, 1)
    if not moves:
        # Should not happen; return any placeholder legal form
        return "0,0:0,0"
    # decide depth based on branching
    depth = 3 if len(moves) <= 24 else 2
    score, move = alphabeta(board, 1, depth, -1e9, 1e9)
    if move is None:
        move = random.choice(moves)
    r,c,tr,tc = move
    return f"{r},{c}:{tr},{tc}"
