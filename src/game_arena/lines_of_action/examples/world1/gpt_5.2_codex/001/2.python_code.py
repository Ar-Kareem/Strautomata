
import math
import random
from collections import deque

# Directions: 8-connected
DIRS = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]

def inside(r,c):
    return 0 <= r < 8 and 0 <= c < 8

def count_line(board, r, c, dr, dc):
    # Count all pieces (both players) on the line through (r,c) in direction dr,dc
    cnt = 1  # include self
    rr, cc = r+dr, c+dc
    while inside(rr,cc):
        if board[rr][cc] != 0:
            cnt += 1
        rr += dr
        cc += dc
    rr, cc = r-dr, c-dc
    while inside(rr,cc):
        if board[rr][cc] != 0:
            cnt += 1
        rr -= dr
        cc -= dc
    return cnt

def generate_moves(board, player):
    moves = []
    for r in range(8):
        for c in range(8):
            if board[r][c] != player:
                continue
            for dr,dc in DIRS:
                dist = count_line(board,r,c,dr,dc)
                tr, tc = r + dr*dist, c + dc*dist
                if not inside(tr,tc):
                    continue
                # cannot land on own piece
                if board[tr][tc] == player:
                    continue
                # path must not cross enemy
                blocked = False
                for step in range(1, dist):
                    rr, cc = r+dr*step, c+dc*step
                    if board[rr][cc] == -player:
                        blocked = True
                        break
                if blocked:
                    continue
                moves.append((r,c,tr,tc))
    return moves

def apply_move(board, move, player):
    r,c,tr,tc = move
    newb = [row[:] for row in board]
    newb[r][c] = 0
    newb[tr][tc] = player
    return newb

def components(board, player):
    visited = [[False]*8 for _ in range(8)]
    comp = 0
    for r in range(8):
        for c in range(8):
            if board[r][c]==player and not visited[r][c]:
                comp += 1
                q = deque([(r,c)])
                visited[r][c]=True
                while q:
                    rr,cc = q.popleft()
                    for dr,dc in DIRS:
                        nr,nc = rr+dr, cc+dc
                        if inside(nr,nc) and not visited[nr][nc] and board[nr][nc]==player:
                            visited[nr][nc]=True
                            q.append((nr,nc))
    return comp

def evaluate(board):
    myc = components(board, 1)
    oppc = components(board, -1)
    if myc == 1:
        return 10000
    if oppc == 1:
        return -10000
    mypieces = sum(1 for r in range(8) for c in range(8) if board[r][c]==1)
    opppieces = sum(1 for r in range(8) for c in range(8) if board[r][c]==-1)
    score = (oppc - myc) * 100 + (mypieces - opppieces) * 10
    return score

def policy(board):
    moves = generate_moves(board, 1)
    if not moves:
        # fallback: should not happen in LOA, but return dummy
        return "0,0:0,0"
    best_move = moves[0]
    best_score = -float('inf')
    for mv in moves:
        newb = apply_move(board, mv, 1)
        if components(newb, 1) == 1:
            # immediate win
            r,c,tr,tc = mv
            return f"{r},{c}:{tr},{tc}"
        opp_moves = generate_moves(newb, -1)
        if not opp_moves:
            score = evaluate(newb)
        else:
            # opponent minimizes our evaluation
            worst = float('inf')
            for omv in opp_moves:
                nb2 = apply_move(newb, omv, -1)
                sc = evaluate(nb2)
                if sc < worst:
                    worst = sc
            score = worst
        if score > best_score:
            best_score = score
            best_move = mv
    r,c,tr,tc = best_move
    return f"{r},{c}:{tr},{tc}"
