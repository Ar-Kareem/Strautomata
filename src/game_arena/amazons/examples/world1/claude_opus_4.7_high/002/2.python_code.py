
from collections import deque

DIRS = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

def gen_moves(board, player):
    moves = []
    for r in range(6):
        for c in range(6):
            if board[r][c] != player:
                continue
            for dr, dc in DIRS:
                nr, nc = r+dr, c+dc
                while 0 <= nr < 6 and 0 <= nc < 6 and board[nr][nc] == 0:
                    board[r][c] = 0
                    for ddr, ddc in DIRS:
                        ar, ac = nr+ddr, nc+ddc
                        while 0 <= ar < 6 and 0 <= ac < 6 and board[ar][ac] == 0:
                            moves.append((r,c,nr,nc,ar,ac))
                            ar += ddr; ac += ddc
                    board[r][c] = player
                    nr += dr; nc += dc
    return moves

def count_mobility(board, player):
    count = 0
    for r in range(6):
        for c in range(6):
            if board[r][c] != player: continue
            for dr, dc in DIRS:
                nr, nc = r+dr, c+dc
                while 0 <= nr < 6 and 0 <= nc < 6 and board[nr][nc] == 0:
                    count += 1
                    nr += dr; nc += dc
    return count

def queen_bfs(board, player):
    INF = 99
    dist = [[INF]*6 for _ in range(6)]
    q = deque()
    for r in range(6):
        for c in range(6):
            if board[r][c] == player:
                dist[r][c] = 0
                q.append((r,c))
    while q:
        r,c = q.popleft()
        nd = dist[r][c] + 1
        for dr, dc in DIRS:
            nr, nc = r+dr, c+dc
            while 0 <= nr < 6 and 0 <= nc < 6 and board[nr][nc] == 0:
                if dist[nr][nc] > nd:
                    dist[nr][nc] = nd
                    q.append((nr,nc))
                nr += dr; nc += dc
    return dist

def evaluate(board):
    d1 = queen_bfs(board, 1)
    d2 = queen_bfs(board, 2)
    territory = 0
    for r in range(6):
        for c in range(6):
            if board[r][c] == 0:
                a, b = d1[r][c], d2[r][c]
                if a < b: territory += 1
                elif b < a: territory -= 1
                elif a < 99: territory += 0  # contested
    m1 = count_mobility(board, 1)
    m2 = count_mobility(board, 2)
    return territory + 0.15 * (m1 - m2)

def policy(board_np):
    board = [[int(board_np[r][c]) for c in range(6)] for r in range(6)]
    moves = gen_moves(board, 1)
    if not moves:
        return "0,0:0,0:0,0"
    scored = []
    for move in moves:
        r,c,nr,nc,ar,ac = move
        board[r][c] = 0; board[nr][nc] = 1; board[ar][ac] = -1
        m2 = count_mobility(board, 2)
        if m2 == 0:
            board[ar][ac] = 0; board[nr][nc] = 0; board[r][c] = 1
            return f"{r},{c}:{nr},{nc}:{ar},{ac}"
        m1 = count_mobility(board, 1)
        board[ar][ac] = 0; board[nr][nc] = 0; board[r][c] = 1
        scored.append((m1 - 2*m2, move))
    scored.sort(key=lambda x: -x[0])
    K = min(60, len(scored))
    best_score = -1e18
    best_move = scored[0][1]
    for _, move in scored[:K]:
        r,c,nr,nc,ar,ac = move
        board[r][c] = 0; board[nr][nc] = 1; board[ar][ac] = -1
        score = evaluate(board)
        board[ar][ac] = 0; board[nr][nc] = 0; board[r][c] = 1
        if score > best_score:
            best_score = score
            best_move = move
    r,c,nr,nc,ar,ac = best_move
    return f"{r},{c}:{nr},{nc}:{ar},{ac}"
