
import numpy as np
import time

DIRS = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

def generate_moves(board, player):
    moves = []
    N = 6
    ps = [(r,c) for r in range(N) for c in range(N) if board[r,c] == player]
    for r, c in ps:
        board[r,c] = 0
        for dr, dc in DIRS:
            nr, nc = r+dr, c+dc
            while 0 <= nr < N and 0 <= nc < N and board[nr,nc] == 0:
                board[nr,nc] = player
                for dr2, dc2 in DIRS:
                    ar, ac = nr+dr2, nc+dc2
                    while 0 <= ar < N and 0 <= ac < N and board[ar,ac] == 0:
                        moves.append((r,c,nr,nc,ar,ac))
                        ar += dr2; ac += dc2
                board[nr,nc] = 0
                nr += dr; nc += dc
        board[r,c] = player
    return moves

def mobility(board, player):
    N = 6
    count = 0
    for r in range(N):
        for c in range(N):
            if board[r,c] != player:
                continue
            for dr, dc in DIRS:
                nr, nc = r+dr, c+dc
                while 0 <= nr < N and 0 <= nc < N and board[nr,nc] == 0:
                    count += 1
                    nr += dr; nc += dc
    return count

def evaluate(board):
    return mobility(board, 1) - mobility(board, 2)

def policy(board):
    b = np.array(board, dtype=int)
    start = time.time()

    my_moves = generate_moves(b, 1)
    if not my_moves:
        return "0,0:0,0:0,0"

    scored = []
    for m in my_moves:
        r,c,tr,tc,ar,ac = m
        b[r,c] = 0; b[tr,tc] = 1; b[ar,ac] = -1
        s = evaluate(b)
        b[ar,ac] = 0; b[tr,tc] = 0; b[r,c] = 1
        scored.append((s, m))
    scored.sort(key=lambda x: -x[0])

    best_move = scored[0][1]
    K = min(25, len(scored))
    top = scored[:K]

    best_score = -10**9
    TIME_LIMIT = 0.80

    for s0, m in top:
        if time.time() - start > TIME_LIMIT:
            break
        r,c,tr,tc,ar,ac = m
        b[r,c] = 0; b[tr,tc] = 1; b[ar,ac] = -1

        op_moves = generate_moves(b, 2)
        if not op_moves:
            b[ar,ac] = 0; b[tr,tc] = 0; b[r,c] = 1
            return f"{r},{c}:{tr},{tc}:{ar},{ac}"

        worst = 10**9
        for om in op_moves:
            r2,c2,tr2,tc2,ar2,ac2 = om
            b[r2,c2] = 0; b[tr2,tc2] = 2; b[ar2,ac2] = -1
            es = evaluate(b)
            b[ar2,ac2] = 0; b[tr2,tc2] = 0; b[r2,c2] = 2
            if es < worst:
                worst = es
                if worst <= best_score:
                    break

        b[ar,ac] = 0; b[tr,tc] = 0; b[r,c] = 1

        if worst > best_score:
            best_score = worst
            best_move = m

    r,c,tr,tc,ar,ac = best_move
    return f"{r},{c}:{tr},{tc}:{ar},{ac}"
