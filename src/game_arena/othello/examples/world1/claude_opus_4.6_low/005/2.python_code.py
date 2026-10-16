
import numpy as np

DIRS = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

WEIGHTS = np.array([
    [100,-20,10, 5, 5,10,-20,100],
    [-20,-50,-2,-2,-2,-2,-50,-20],
    [ 10, -2,  1, 1, 1, 1, -2, 10],
    [  5, -2,  1, 0, 0, 1, -2,  5],
    [  5, -2,  1, 0, 0, 1, -2,  5],
    [ 10, -2,  1, 1, 1, 1, -2, 10],
    [-20,-50,-2,-2,-2,-2,-50,-20],
    [100,-20,10, 5, 5,10,-20,100],
])

def get_flips(you, opp, r, c):
    if you[r][c] or opp[r][c]:
        return []
    all_flips = []
    for dr, dc in DIRS:
        flips = []
        nr, nc = r+dr, c+dc
        while 0<=nr<8 and 0<=nc<8 and opp[nr][nc]:
            flips.append((nr,nc))
            nr+=dr; nc+=dc
        if flips and 0<=nr<8 and 0<=nc<8 and you[nr][nc]:
            all_flips.extend(flips)
    return all_flips

def legal_moves(you, opp):
    moves = []
    for r in range(8):
        for c in range(8):
            f = get_flips(you, opp, r, c)
            if f:
                moves.append((r, c, f))
    return moves

def apply_move(you, opp, r, c, flips):
    y, o = you.copy(), opp.copy()
    y[r][c] = 1
    for fr, fc in flips:
        y[fr][fc] = 1; o[fr][fc] = 0
    return y, o

def evaluate(you, opp):
    return np.sum(WEIGHTS * you) - np.sum(WEIGHTS * opp)

def minimax(you, opp, depth, alpha, beta, maximizing):
    moves = legal_moves(you, opp)
    if depth == 0 or not moves:
        if not moves:
            opp_moves = legal_moves(opp, you)
            if not opp_moves:
                diff = int(np.sum(you)) - int(np.sum(opp))
                return (1000 if diff > 0 else -1000 if diff < 0 else 0), None
            if not maximizing:
                return minimax(opp, you, depth, -beta, -alpha, True)
            else:
                return minimax(opp, you, depth, -beta, -alpha, False)
        return evaluate(you, opp), None

    # Sort moves by weight heuristic
    moves.sort(key=lambda m: WEIGHTS[m[0]][m[1]], reverse=maximizing)

    if maximizing:
        best = -float('inf'); best_m = moves[0]
        for r, c, flips in moves:
            ny, no = apply_move(you, opp, r, c, flips)
            val, _ = minimax(no, ny, depth-1, -beta, -alpha, False)
            val = -val
            if val > best:
                best = val; best_m = (r, c, flips)
            alpha = max(alpha, best)
            if alpha >= beta: break
        return best, best_m
    else:
        best = float('inf'); best_m = moves[0]
        for r, c, flips in moves:
            ny, no = apply_move(you, opp, r, c, flips)
            val, _ = minimax(no, ny, depth-1, -beta, -alpha, True)
            val = -val
            if val < best:
                best = val; best_m = (r, c, flips)
            beta = min(beta, best)
            if alpha >= beta: break
        return best, best_m

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    moves = legal_moves(you, opponent)
    if not moves:
        return "pass"
    
    total = int(np.sum(you)) + int(np.sum(opponent))
    depth = 4 if total < 52 else 8
    
    _, best = minimax(you, opponent, depth, -float('inf'), float('inf'), True)
    r, c = best[0], best[1]
    return f"{chr(ord('a')+c)}{r+1}"
