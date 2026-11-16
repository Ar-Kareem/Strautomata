
import math
import copy

# Directions for movement and connectivity (8 directions)
DIRS = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,1),(-1,1),(1,-1)]

def in_bounds(r,c):
    return 0 <= r < 8 and 0 <= c < 8

def line_count(board, r, c, dr, dc):
    # Count all pieces on the line through (r,c) in direction (dr,dc)
    count = 0
    # forward
    rr, cc = r, c
    while in_bounds(rr, cc):
        if board[rr][cc] != 0:
            count += 1
        rr += dr
        cc += dc
    # backward
    rr, cc = r - dr, c - dc
    while in_bounds(rr, cc):
        if board[rr][cc] != 0:
            count += 1
        rr -= dr
        cc -= dc
    return count

def generate_moves(board):
    moves = []
    for r in range(8):
        for c in range(8):
            if board[r][c] == 1:
                for dr, dc in DIRS:
                    cnt = line_count(board, r, c, dr, dc)
                    tr = r + dr * cnt
                    tc = c + dc * cnt
                    if not in_bounds(tr, tc):
                        continue
                    # check path for blocking enemy
                    blocked = False
                    for step in range(1, cnt):
                        rr = r + dr * step
                        cc = c + dc * step
                        if board[rr][cc] == -1:
                            blocked = True
                            break
                    if blocked:
                        continue
                    # target cannot be own piece
                    if board[tr][tc] == 1:
                        continue
                    moves.append(((r,c),(tr,tc)))
    return moves

def apply_move(board, move):
    (r,c),(tr,tc) = move
    newb = [row[:] for row in board]
    newb[tr][tc] = newb[r][c]
    newb[r][c] = 0
    return newb

def count_components(board, player=1):
    visited = [[False]*8 for _ in range(8)]
    comp = 0
    for r in range(8):
        for c in range(8):
            if board[r][c] == player and not visited[r][c]:
                comp += 1
                # BFS
                stack = [(r,c)]
                visited[r][c] = True
                while stack:
                    rr, cc = stack.pop()
                    for dr, dc in DIRS:
                        nr, nc = rr + dr, cc + dc
                        if in_bounds(nr,nc) and not visited[nr][nc] and board[nr][nc] == player:
                            visited[nr][nc] = True
                            stack.append((nr,nc))
    return comp

def spread_score(board, player=1):
    pieces = [(r,c) for r in range(8) for c in range(8) if board[r][c] == player]
    if not pieces:
        return 0
    cr = sum(p[0] for p in pieces) / len(pieces)
    cc = sum(p[1] for p in pieces) / len(pieces)
    spread = 0.0
    for r,c in pieces:
        spread += abs(r-cr) + abs(c-cc)
    return spread

def evaluate(board):
    my_comp = count_components(board, 1)
    opp_comp = count_components(board, -1)
    if my_comp == 1:
        return 100000
    if opp_comp == 1:
        return -100000
    spread = spread_score(board, 1)
    return -my_comp*100 + opp_comp*50 - spread

def policy(board):
    moves = generate_moves(board)
    if not moves:
        # Should never happen, but return a dummy legal format
        return "0,0:0,0"

    best_move = moves[0]
    best_val = -float('inf')

    for mv in moves:
        b1 = apply_move(board, mv)
        # Immediate win
        if count_components(b1, 1) == 1:
            (r,c),(tr,tc) = mv
            return f"{r},{c}:{tr},{tc}"
        # Opponent response (minimax depth 2)
        # Flip board to generate opponent moves
        flipped = [[-x for x in row] for row in b1]
        opp_moves = generate_moves(flipped)
        if not opp_moves:
            val = evaluate(b1)
        else:
            worst = float('inf')
            for omv in opp_moves:
                b2_flipped = apply_move(flipped, omv)
                # flip back
                b2 = [[-x for x in row] for row in b2_flipped]
                val2 = evaluate(b2)
                if val2 < worst:
                    worst = val2
            val = worst
        if val > best_val:
            best_val = val
            best_move = mv

    (r,c),(tr,tc) = best_move
    return f"{r},{c}:{tr},{tc}"
