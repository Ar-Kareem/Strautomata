
import sys
from collections import deque

# ------------------------------------------------------------
# Hex board configuration
N = 11
OFFSETS = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]
INF = 10 ** 9

def in_bounds(r, c):
    return 0 <= r < N and 0 <= c < N

# ------------------------------------------------------------
# Weighted BFS that returns the minimal number of empty cells
# needed for *player* (1 = Black, -1 = White) to connect its
# opposite sides.
def bfs(board, player):
    # Determine start and goal conditions
    if player == 1:                     # Black: top → bottom
        start_cond = lambda r, c: r == 0
        goal_cond  = lambda r, c: r == N - 1
    else:                               # White: left → right
        start_cond = lambda r, c: c == 0
        goal_cond  = lambda r, c: c == N - 1

    # Collect start positions (own stones on the start side)
    start_cells = []
    for i in range(N):
        for j in range(N):
            if start_cond(i, j) and board[i][j] == player:
                start_cells.append((i, j))
    if not start_cells:
        return INF, None, None

    dist = {}
    parent = {}
    q = deque()

    for cell in start_cells:
        dist[cell] = 0
        parent[cell] = None
        q.append(cell)

    while q:
        r, c = q.popleft()
        cur = dist[(r, c)]

        for dr, dc in OFFSETS:
            nr, nc = r + dr, c + dc
            if not in_bounds(nr, nc):
                continue
            # Opponent stones are impassable
            if board[nr][nc] == -player:
                continue
            # Cost: 0 for own stone, 1 for empty cell
            step = 0 if board[nr][nc] == player else 1
            nd = cur + step
            if (nr, nc) not in dist or nd < dist[(nr, nc)]:
                dist[(nr, nc)] = nd
                parent[(nr, nc)] = (r, c)
                q.append((nr, nc))
                if goal_cond(nr, nc):
                    # If the goal cell itself is empty we already added the
                    # cost of occupying it (step == 1).  If it is our stone,
                    # step == 0, so nd == cur.
                    return nd, parent, (nr, nc)

    return INF, None, None

# ------------------------------------------------------------
# Place a stone (player) on (r,c) temporarily, compute our
# distance and the opponent's distance, then restore the board.
def evaluate_move(board, r, c, player):
    orig = board[r][c]
    board[r][c] = player
    d_self, _, _ = bfs(board, player)
    d_opp, _, _ = bfs(board, -player)
    board[r][c] = orig
    score = d_opp - d_self          # higher is better
    return score, d_self, d_opp

# ------------------------------------------------------------
def policy(me, opp, color):
    # Initialise the board
    board = [[0] * N for _ in range(N)]
    player = 1 if color == 'b' else -1
    opponent = -player

    for r, c in me:
        board[r][c] = player
    for r, c in opp:
        board[r][c] = opponent

    # List of empty cells (row‑major order gives a deterministic tie‑break)
    empties = [(r, c) for r in range(N) for c in range(N) if board[r][c] == 0]
    if not empties:
        return (0, 0)   # should never happen in a legal game

    # 1️⃣ Immediate winning move
    for r, c in empties:
        board[r][c] = player
        d_self, _, _ = bfs(board, player)
        if d_self == 0:               # we already have a full connection
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    # 2️⃣ Opponent can win in one move → block a threatening cell
    threats = []
    for r, c in empties:
        board[r][c] = opponent
        d_opp, _, _ = bfs(board, opponent)
        if d_opp == 0:
            threats.append((r, c))
        board[r][c] = 0

    if threats:
        best_block = None
        best_score = -INF
        best_self = INF
        for r, c in threats:
            score, d_self, d_opp2 = evaluate_move(board, r, c, player)
            # Prefer the block that yields the highest score,
            # break ties by the smaller remaining own distance.
            if score > best_score or (score == best_score and d_self < best_self):
                best_score = score
                best_block = (r, c)
                best_self = d_self
        if best_block is not None:
            return best_block

    # 3️⃣ General heuristic – evaluate every empty cell
    best_move = None
    best_score = -INF
    best_self = INF
    for r, c in empties:
        score, d_self, d_opp2 = evaluate_move(board, r, c, player)
        if score > best_score or (score == best_score and d_self < best_self):
            best_score = score
            best_move = (r, c)
            best_self = d_self

    # Fallback (should never be needed)
    if best_move is None:
        import random
        best_move = random.choice(empties)
    return best_move
