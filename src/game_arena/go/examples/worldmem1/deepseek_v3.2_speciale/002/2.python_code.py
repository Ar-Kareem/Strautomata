
import collections
import random

BOARD_SIZE = 19
EMPTY = 0
MY = 1
OPP = 2
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]

# Positional bias: encourages opening moves near 3-3 / 4-4 points.
POS_BIAS = [[20 - (abs(min(r, 18 - r) - 3) + abs(min(c, 18 - c) - 3))
             for c in range(BOARD_SIZE)] for r in range(BOARD_SIZE)]

class Board:
    def __init__(self, my_set=None, opp_set=None, grid=None):
        if grid is not None:
            self.grid = grid
        else:
            self.grid = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]
            if my_set:
                for r, c in my_set:
                    self.grid[r - 1][c - 1] = MY
            if opp_set:
                for r, c in opp_set:
                    self.grid[r - 1][c - 1] = OPP

    def copy(self):
        return Board(grid=[row[:] for row in self.grid])

    def is_on_board(self, r, c):
        return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE

    def get_group_and_liberties(self, r, c, color):
        if not self.is_on_board(r, c) or self.grid[r][c] != color:
            return set(), set()
        visited = [[False] * BOARD_SIZE for _ in range(BOARD_SIZE)]
        stack = [(r, c)]
        group = set()
        liberties = set()
        while stack:
            x, y = stack.pop()
            if visited[x][y]:
                continue
            visited[x][y] = True
            group.add((x, y))
            for dx, dy in DIRS:
                nx, ny = x + dx, y + dy
                if not self.is_on_board(nx, ny):
                    continue
                if self.grid[nx][ny] == EMPTY:
                    liberties.add((nx, ny))
                elif self.grid[nx][ny] == color and not visited[nx][ny]:
                    stack.append((nx, ny))
        return group, liberties

    def to_sets(self):
        my_set = set()
        opp_set = set()
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                if self.grid[i][j] == MY:
                    my_set.add((i + 1, j + 1))
                elif self.grid[i][j] == OPP:
                    opp_set.add((i + 1, j + 1))
        return my_set, opp_set


def evaluate(board):
    """Return a score from MY's perspective."""
    # ---------- Distance to nearest MY ----------
    dist_me = [[-1] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    q = collections.deque()
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if board.grid[i][j] == MY:
                dist_me[i][j] = 0
                q.append((i, j))
    while q:
        x, y = q.popleft()
        d = dist_me[x][y] + 1
        for dx, dy in DIRS:
            nx, ny = x + dx, y + dy
            if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE and dist_me[nx][ny] == -1:
                dist_me[nx][ny] = d
                q.append((nx, ny))

    # ---------- Distance to nearest OPP ----------
    dist_opp = [[-1] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    q = collections.deque()
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if board.grid[i][j] == OPP:
                dist_opp[i][j] = 0
                q.append((i, j))
    while q:
        x, y = q.popleft()
        d = dist_opp[x][y] + 1
        for dx, dy in DIRS:
            nx, ny = x + dx, y + dy
            if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE and dist_opp[nx][ny] == -1:
                dist_opp[nx][ny] = d
                q.append((nx, ny))

    # ---------- Territory score (Voronoi) ----------
    territory = 0
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            d_me = dist_me[i][j] if dist_me[i][j] != -1 else 1000
            d_opp = dist_opp[i][j] if dist_opp[i][j] != -1 else 1000
            if d_me < d_opp:
                territory += 1
            elif d_opp < d_me:
                territory -= 1

    # ---------- Liberty safety ----------
    safety = 0

    # MY groups: penalty for few liberties
    visited = [[False] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if board.grid[i][j] == MY and not visited[i][j]:
                group, libs = board.get_group_and_liberties(i, j, MY)
                size = len(group)
                lib_cnt = len(libs)
                for x, y in group:
                    visited[x][y] = True
                if lib_cnt == 1:
                    safety -= size * 50
                elif lib_cnt == 2:
                    safety -= size * 10
                elif lib_cnt == 3:
                    safety -= size * 2

    # OPP groups: bonus for opponent groups in danger
    visited = [[False] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if board.grid[i][j] == OPP and not visited[i][j]:
                group, libs = board.get_group_and_liberties(i, j, OPP)
                size = len(group)
                lib_cnt = len(libs)
                for x, y in group:
                    visited[x][y] = True
                if lib_cnt == 1:
                    safety += size * 40
                elif lib_cnt == 2:
                    safety += size * 8
                elif lib_cnt == 3:
                    safety += size * 1

    return territory + safety


def policy(me, opponent, memory):
    my_set = set(me)
    opp_set = set(opponent)
    board = Board(my_set=my_set, opp_set=opp_set)

    # Retrieve previous board for ko (stored as frozensets)
    prev_my = prev_opp = None
    if 'prev_board' in memory:
        prev_my, prev_opp = memory['prev_board']

    best_score = -10**9
    best_move = None          # internal (r,c) 0‑index
    best_captured = None      # set of (x,y) 0‑index

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board.grid[r][c] != EMPTY:
                continue

            # ---- Simulate the move ----
            test_board = board.copy()
            test_board.grid[r][c] = MY

            # Find opponent groups with zero liberties (captures)
            captured = set()
            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                if test_board.is_on_board(nr, nc) and test_board.grid[nr][nc] == OPP:
                    group, libs = test_board.get_group_and_liberties(nr, nc, OPP)
                    if not libs:
                        captured.update(group)

            # Remove captured stones
            for x, y in captured:
                test_board.grid[x][y] = EMPTY

            # Suicide check
            own_group, own_libs = test_board.get_group_and_liberties(r, c, MY)
            if not own_libs:
                continue

            # Ko check (compare stone sets)
            if prev_my is not None:
                new_my = my_set | {(r + 1, c + 1)}
                new_opp = opp_set - {(x + 1, y + 1) for x, y in captured}
                if new_my == prev_my and new_opp == prev_opp:
                    continue

            # Evaluate the resulting board
            score = evaluate(test_board) + POS_BIAS[r][c]  # positional bias
            score += random.random() * 0.1                # tie‑breaker

            if score > best_score:
                best_score = score
                best_move = (r, c)
                best_captured = captured

    # ---- Choose action and update memory ----
    if best_move is None:          # no legal moves → pass
        action = (0, 0)
        new_my_set, new_opp_set = my_set, opp_set
    else:
        r, c = best_move
        action = (r + 1, c + 1)
        new_my_set = my_set | {(r + 1, c + 1)}
        new_opp_set = opp_set - {(x + 1, y + 1) for x, y in best_captured}

    memory['prev_board'] = (frozenset(new_my_set), frozenset(new_opp_set))
    return (action, memory)
