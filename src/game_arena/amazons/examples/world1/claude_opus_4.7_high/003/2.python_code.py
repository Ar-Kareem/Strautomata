
import numpy as np
from collections import deque
import time

def policy(board) -> str:
    N = 6
    DIRS = ((-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1))
    start = time.time()
    TIME_LIMIT = 0.85

    b_np = np.asarray(board)
    b = [[int(b_np[r, c]) for c in range(N)] for r in range(N)]

    def bfs(sources):
        dist = [[999]*N for _ in range(N)]
        q = deque()
        for r, c in sources:
            dist[r][c] = 0
            q.append((r, c))
        while q:
            r, c = q.popleft()
            d = dist[r][c] + 1
            for dr, dc in DIRS:
                nr, nc = r+dr, c+dc
                while 0 <= nr < N and 0 <= nc < N and b[nr][nc] == 0:
                    if dist[nr][nc] > d:
                        dist[nr][nc] = d
                        q.append((nr, nc))
                    nr += dr
                    nc += dc
        return dist

    def evaluate():
        my = []
        op = []
        for r in range(N):
            for c in range(N):
                v = b[r][c]
                if v == 1:
                    my.append((r, c))
                elif v == 2:
                    op.append((r, c))
        if not my:
            return -100000.0
        if not op:
            return 100000.0
        d1 = bfs(my)
        d2 = bfs(op)
        t = 0.0
        my_can = False
        op_can = False
        for r in range(N):
            for c in range(N):
                if b[r][c] != 0:
                    continue
                a = d1[r][c]
                bb = d2[r][c]
                if a < 999:
                    my_can = True
                if bb < 999:
                    op_can = True
                if a < bb:
                    t += 1.0
                elif bb < a:
                    t -= 1.0
                if a < 20:
                    t += 0.08 * (0.5 ** a)
                if bb < 20:
                    t -= 0.08 * (0.5 ** bb)
        # It's opponent's turn after my move; if they can't move, I win.
        if not op_can:
            return 100000.0
        if not my_can:
            return -100000.0
        return t

    def gen_moves(player):
        moves = []
        for r in range(N):
            for c in range(N):
                if b[r][c] != player:
                    continue
                for dr, dc in DIRS:
                    nr, nc = r+dr, c+dc
                    while 0 <= nr < N and 0 <= nc < N and b[nr][nc] == 0:
                        b[r][c] = 0
                        b[nr][nc] = player
                        for ar, ac in DIRS:
                            tr, tc = nr+ar, nc+ac
                            while 0 <= tr < N and 0 <= tc < N and b[tr][tc] == 0:
                                moves.append((r, c, nr, nc, tr, tc))
                                tr += ar
                                tc += ac
                        b[nr][nc] = 0
                        b[r][c] = player
                        nr += dr
                        nc += dc
        return moves

    moves = gen_moves(1)
    if not moves:
        # No legal move - return a dummy (shouldn't be called)
        return "0,0:0,0:0,0"

    best_move = moves[0]
    best_score = -float('inf')

    # Quick instant-win scan first
    for m in moves:
        fr, fc, tr, tc, ar, ac = m
        b[fr][fc] = 0
        b[tr][tc] = 1
        b[ar][ac] = -1
        # Quick check: does opponent have any move?
        opp_has = False
        for r in range(N):
            if opp_has:
                break
            for c in range(N):
                if b[r][c] == 2:
                    for dr, dc in DIRS:
                        nr2, nc2 = r+dr, c+dc
                        if 0 <= nr2 < N and 0 <= nc2 < N and b[nr2][nc2] == 0:
                            opp_has = True
                            break
                    if opp_has:
                        break
        b[ar][ac] = 0
        b[tr][tc] = 0
        b[fr][fc] = 1
        if not opp_has:
            fr, fc, tr, tc, ar, ac = m
            return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"

    for m in moves:
        if time.time() - start > TIME_LIMIT:
            break
        fr, fc, tr, tc, ar, ac = m
        b[fr][fc] = 0
        b[tr][tc] = 1
        b[ar][ac] = -1
        score = evaluate()
        b[ar][ac] = 0
        b[tr][tc] = 0
        b[fr][fc] = 1
        if score > best_score:
            best_score = score
            best_move = m

    fr, fc, tr, tc, ar, ac = best_move
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
