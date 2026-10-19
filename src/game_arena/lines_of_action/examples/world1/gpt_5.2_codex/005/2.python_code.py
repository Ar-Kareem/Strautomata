
import math
import random

DIRECTIONS = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]

def in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8

def line_count(board, r, c, dr, dc):
    rr, cc = r, c
    # move to one end of the line
    while in_bounds(rr - dr, cc - dc):
        rr -= dr
        cc -= dc
    count = 0
    # count pieces along the line
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
            if board[r][c] == player:
                for dr, dc in DIRECTIONS:
                    count = line_count(board, r, c, dr, dc)
                    if count == 0:
                        continue
                    tr = r + dr * count
                    tc = c + dc * count
                    if not in_bounds(tr, tc):
                        continue
                    blocked = False
                    for i in range(1, count):
                        rr = r + dr * i
                        cc = c + dc * i
                        if board[rr][cc] == -player:
                            blocked = True
                            break
                    if blocked:
                        continue
                    if board[tr][tc] == player:
                        continue
                    moves.append((r, c, tr, tc))
    return moves

def apply_move(board, move, player):
    fr, fc, tr, tc = move
    newb = [row[:] for row in board]
    newb[tr][tc] = player
    newb[fr][fc] = 0
    return newb

def count_components(board, player):
    visited = [[False]*8 for _ in range(8)]
    comp = 0
    for r in range(8):
        for c in range(8):
            if board[r][c] == player and not visited[r][c]:
                comp += 1
                stack = [(r, c)]
                visited[r][c] = True
                while stack:
                    rr, cc = stack.pop()
                    for dr, dc in DIRECTIONS:
                        nr, nc = rr + dr, cc + dc
                        if in_bounds(nr, nc) and not visited[nr][nc] and board[nr][nc] == player:
                            visited[nr][nc] = True
                            stack.append((nr, nc))
    return comp

def is_connected(board, player):
    # If no pieces, consider not connected
    count = 0
    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                count += 1
    if count == 0:
        return False
    return count_components(board, player) == 1

def spread(positions):
    if not positions:
        return 0
    rs = [p[0] for p in positions]
    cs = [p[1] for p in positions]
    min_r, max_r = min(rs), max(rs)
    min_c, max_c = min(cs), max(cs)
    area = (max_r - min_r + 1) * (max_c - min_c + 1)
    cr = sum(rs) / len(rs)
    cc = sum(cs) / len(cs)
    dist = sum(abs(r - cr) + abs(c - cc) for r, c in positions) / len(rs)
    return area + dist

def evaluate(board):
    my_pos = []
    opp_pos = []
    for r in range(8):
        for c in range(8):
            if board[r][c] == 1:
                my_pos.append((r, c))
            elif board[r][c] == -1:
                opp_pos.append((r, c))
    if not my_pos:
        return -10000
    if not opp_pos:
        return 10000

    my_comp = count_components(board, 1)
    opp_comp = count_components(board, -1)
    my_spread = spread(my_pos)
    opp_spread = spread(opp_pos)
    my_mob = len(legal_moves(board, 1))
    opp_mob = len(legal_moves(board, -1))

    score = (opp_comp - my_comp) * 120
    score += (opp_spread - my_spread) * 3
    score += (my_mob - opp_mob) * 1
    return score

def terminal_score(board, player_to_move):
    my_conn = is_connected(board, 1)
    opp_conn = is_connected(board, -1)
    if my_conn or opp_conn:
        if my_conn and opp_conn:
            # winner is the player who just moved
            if player_to_move == 1:
                return -10000
            else:
                return 10000
        elif my_conn:
            return 10000
        else:
            return -10000
    return None

def minimax(board, depth, alpha, beta, player):
    tscore = terminal_score(board, player)
    if tscore is not None:
        return tscore
    if depth == 0:
        return evaluate(board)

    moves = legal_moves(board, player)
    if not moves:
        return evaluate(board)

    if player == 1:
        value = -1e9
        for m in moves:
            nb = apply_move(board, m, player)
            value = max(value, minimax(nb, depth - 1, alpha, beta, -1))
            alpha = max(alpha, value)
            if beta <= alpha:
                break
        return value
    else:
        value = 1e9
        for m in moves:
            nb = apply_move(board, m, player)
            value = min(value, minimax(nb, depth - 1, alpha, beta, 1))
            beta = min(beta, value)
            if beta <= alpha:
                break
        return value

def policy(board) -> str:
    moves = legal_moves(board, 1)
    if not moves:
        return "0,0:0,0"  # fallback (should not happen)

    depth = 2
    if len(moves) <= 6:
        depth = 3

    # Order moves by quick eval
    scored = []
    for m in moves:
        nb = apply_move(board, m, 1)
        scored.append((evaluate(nb), m))
    scored.sort(reverse=True, key=lambda x: x[0])

    best_move = scored[0][1]
    best_score = -1e9
    for _, m in scored:
        nb = apply_move(board, m, 1)
        score = minimax(nb, depth - 1, -1e9, 1e9, -1)
        if score > best_score:
            best_score = score
            best_move = m

    fr, fc, tr, tc = best_move
    return f"{fr},{fc}:{tr},{tc}"
