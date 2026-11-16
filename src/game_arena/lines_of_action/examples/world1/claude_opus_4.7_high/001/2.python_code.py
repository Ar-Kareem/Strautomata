
import time

DIRS8 = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
LINE_DIRS = [(0,1),(1,0),(1,1),(1,-1)]

start_time = 0
TIME_LIMIT = 0.85

class SearchTimeout(Exception):
    pass

def count_line(board, r, c, dr, dc):
    sr, sc = r, c
    while 0 <= sr-dr < 8 and 0 <= sc-dc < 8:
        sr -= dr; sc -= dc
    cnt = 0
    while 0 <= sr < 8 and 0 <= sc < 8:
        if board[sr][sc] != 0:
            cnt += 1
        sr += dr; sc += dc
    return cnt

def gen_moves(board, player):
    moves = []
    for r in range(8):
        for c in range(8):
            if board[r][c] != player:
                continue
            for dr, dc in LINE_DIRS:
                n = count_line(board, r, c, dr, dc)
                for sign in (1, -1):
                    ddr, ddc = dr*sign, dc*sign
                    nr, nc = r + ddr*n, c + ddc*n
                    if not (0 <= nr < 8 and 0 <= nc < 8):
                        continue
                    blocked = False
                    for k in range(1, n):
                        if board[r + ddr*k][c + ddc*k] == -player:
                            blocked = True
                            break
                    if blocked:
                        continue
                    if board[nr][nc] == player:
                        continue
                    moves.append((r, c, nr, nc))
    return moves

def num_components_and_max(board, player):
    positions = set()
    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                positions.add((r,c))
    if not positions:
        return 0, 0
    count = 0
    max_size = 0
    while positions:
        start = positions.pop()
        stack = [start]
        size = 1
        while stack:
            r, c = stack.pop()
            for dr, dc in DIRS8:
                nr, nc = r+dr, c+dc
                if (nr,nc) in positions:
                    positions.discard((nr,nc))
                    stack.append((nr,nc))
                    size += 1
        if size > max_size:
            max_size = size
        count += 1
    return count, max_size

def concentration(board, player):
    positions = [(r,c) for r in range(8) for c in range(8) if board[r][c] == player]
    n = len(positions)
    if n == 0:
        return 0
    sr = sum(p[0] for p in positions) / n
    sc = sum(p[1] for p in positions) / n
    return sum(max(abs(r-sr), abs(c-sc)) for r,c in positions)

def evaluate(board):
    my_comp, my_max = num_components_and_max(board, 1)
    opp_comp, opp_max = num_components_and_max(board, -1)
    if my_max == 0:
        return -1000000
    if opp_max == 0:
        return 1000000
    if my_comp == 1:
        return 1000000
    if opp_comp == 1:
        return -1000000
    my_conc = concentration(board, 1)
    opp_conc = concentration(board, -1)
    score = 0
    score += (opp_conc - my_conc) * 3
    score += (opp_comp - my_comp) * 8
    score += (my_max - opp_max) * 4
    score += (my_max + opp_comp) * 1  # prefer larger groups for us, more for opp
    # piece count: total pieces
    my_p = sum(1 for r in range(8) for c in range(8) if board[r][c] == 1)
    opp_p = sum(1 for r in range(8) for c in range(8) if board[r][c] == -1)
    score += (my_p - opp_p) * 2
    return score

def alphabeta(board, depth, alpha, beta, player):
    if time.time() - start_time > TIME_LIMIT:
        raise SearchTimeout()
    
    my_comp, my_max = num_components_and_max(board, 1)
    opp_comp, opp_max = num_components_and_max(board, -1)
    # Check terminal: someone connected or wiped out
    my_win = (my_max > 0 and my_comp == 1) or opp_max == 0
    opp_win = (opp_max > 0 and opp_comp == 1) or my_max == 0
    # If both connected, the player who just moved wins (the opposite of player to move)
    if my_win and opp_win:
        # previous mover won; previous mover was -player
        return (-1000000 + (20 - depth)) if player == 1 else (1000000 - (20 - depth)), None
    if my_win:
        return 1000000 - (20 - depth), None
    if opp_win:
        return -1000000 + (20 - depth), None
    
    if depth == 0:
        return evaluate(board), None
    
    moves = gen_moves(board, player)
    if not moves:
        return (-1000000 + (20 - depth)) if player == 1 else (1000000 - (20 - depth)), None
    
    # Move ordering: captures first
    moves.sort(key=lambda m: 0 if board[m[2]][m[3]] == -player else 1)
    
    best_move = moves[0]
    if player == 1:
        value = -float('inf')
        for m in moves:
            r1,c1,r2,c2 = m
            captured = board[r2][c2]
            board[r2][c2] = 1
            board[r1][c1] = 0
            v, _ = alphabeta(board, depth-1, alpha, beta, -1)
            board[r1][c1] = 1
            board[r2][c2] = captured
            if v > value:
                value = v
                best_move = m
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break
        return value, best_move
    else:
        value = float('inf')
        for m in moves:
            r1,c1,r2,c2 = m
            captured = board[r2][c2]
            board[r2][c2] = -1
            board[r1][c1] = 0
            v, _ = alphabeta(board, depth-1, alpha, beta, 1)
            board[r1][c1] = -1
            board[r2][c2] = captured
            if v < value:
                value = v
                best_move = m
            if value < beta:
                beta = value
            if alpha >= beta:
                break
        return value, best_move

def policy(board):
    global start_time
    start_time = time.time()
    
    b = [[int(board[r][c]) for c in range(8)] for r in range(8)]
    
    moves = gen_moves(b, 1)
    if not moves:
        # No legal moves; return something (we've lost)
        return "0,0:0,0"
    
    best_move = moves[0]
    
    for depth in range(1, 5):
        try:
            score, move = alphabeta(b, depth, -float('inf'), float('inf'), 1)
            if move is not None:
                best_move = move
            if time.time() - start_time > TIME_LIMIT * 0.45:
                break
            if score >= 900000 or score <= -900000:
                break
        except SearchTimeout:
            break
    
    r1, c1, r2, c2 = best_move
    return f"{r1},{c1}:{r2},{c2}"
