
import time
from collections import deque

DIRS = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
N = 6

def gen_moves(board, player):
    moves = []
    for r in range(N):
        for c in range(N):
            if board[r][c] != player:
                continue
            board[r][c] = 0
            for dr, dc in DIRS:
                nr, nc = r+dr, c+dc
                while 0<=nr<N and 0<=nc<N and board[nr][nc]==0:
                    board[nr][nc] = player
                    for ar, ac in DIRS:
                        ar2, ac2 = nr+ar, nc+ac
                        while 0<=ar2<N and 0<=ac2<N and board[ar2][ac2]==0:
                            moves.append((r, c, nr, nc, ar2, ac2))
                            ar2 += ar
                            ac2 += ac
                    board[nr][nc] = 0
                    nr += dr
                    nc += dc
            board[r][c] = player
    return moves

def apply_move(board, m, player):
    fr, fc, tr, tc, ar, ac = m
    board[fr][fc] = 0
    board[tr][tc] = player
    board[ar][ac] = -1

def undo_move(board, m, player):
    fr, fc, tr, tc, ar, ac = m
    board[ar][ac] = 0
    board[tr][tc] = 0
    board[fr][fc] = player

def has_moves(board, player):
    for r in range(N):
        for c in range(N):
            if board[r][c] != player:
                continue
            for dr, dc in DIRS:
                nr, nc = r+dr, c+dc
                if 0<=nr<N and 0<=nc<N and board[nr][nc]==0:
                    return True
    return False

def evaluate(board):
    INF = 999
    d1 = [[INF]*N for _ in range(N)]
    d2 = [[INF]*N for _ in range(N)]
    def bfs(p, dist):
        q = deque()
        for r in range(N):
            for c in range(N):
                if board[r][c] == p:
                    dist[r][c] = 0
                    q.append((r,c))
        while q:
            r, c = q.popleft()
            dd = dist[r][c] + 1
            for dr, dc in DIRS:
                nr, nc = r+dr, c+dc
                while 0<=nr<N and 0<=nc<N and board[nr][nc]==0:
                    if dist[nr][nc] > dd:
                        dist[nr][nc] = dd
                        q.append((nr,nc))
                    nr += dr
                    nc += dc
    bfs(1, d1)
    bfs(2, d2)
    score = 0.0
    for r in range(N):
        for c in range(N):
            if board[r][c] != 0:
                continue
            a, b = d1[r][c], d2[r][c]
            if a == INF and b == INF:
                continue
            if a < b: score += 1
            elif b < a: score -= 1
    my_mob = 0; op_mob = 0
    for r in range(N):
        for c in range(N):
            v = board[r][c]
            if v == 1 or v == 2:
                m = 0
                for dr, dc in DIRS:
                    nr, nc = r+dr, c+dc
                    if 0<=nr<N and 0<=nc<N and board[nr][nc]==0:
                        m += 1
                if v == 1: my_mob += m
                else: op_mob += m
    return score + 0.1 * (my_mob - op_mob)

def format_move(m):
    fr, fc, tr, tc, ar, ac = m
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"

def policy(board_np):
    start = time.time()
    board = [[int(board_np[r][c]) for c in range(6)] for r in range(6)]
    my_moves = gen_moves(board, 1)
    if not my_moves:
        return "0,0:0,0:0,0"
    scored = []
    for m in my_moves:
        apply_move(board, m, 1)
        if not has_moves(board, 2):
            undo_move(board, m, 1)
            return format_move(m)
        s = evaluate(board)
        undo_move(board, m, 1)
        scored.append((s, m))
    scored.sort(reverse=True, key=lambda x: x[0])
    best_move = scored[0][1]
    best_val = -float('inf')
    K = min(len(scored), 6)
    time_limit = 0.75
    for i in range(K):
        if time.time() - start > time_limit:
            break
        s0, m = scored[i]
        apply_move(board, m, 1)
        opp_moves = gen_moves(board, 2)
        if not opp_moves:
            undo_move(board, m, 1)
            return format_move(m)
        opp_scored = []
        for om in opp_moves:
            apply_move(board, om, 2)
            s = evaluate(board)
            undo_move(board, om, 2)
            opp_scored.append((s, om))
        opp_scored.sort(key=lambda x: x[0])
        opp_worst = opp_scored[0][0]
        undo_move(board, m, 1)
        if opp_worst > best_val:
            best_val = opp_worst
            best_move = m
    return format_move(best_move)
