
# Pure‑Python Go policy for a 19×19 board.
# Legal moves are detected by simulation, and each move is scored by:
#   – number of opponent stones captured,
#   – number of own stones saved from atari,
#   – total liberties after the move.
# The highest‑scoring legal move is played; if none exist the policy passes.

# Directions for adjacency (up, down, left, right)
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def _get_groups(board, colour):
    """
    Return a list of all groups of the given colour on the board.
    Each group is a dict:
        {'points': set((r,c), …),   # stones belonging to the group
         'liberties': set((r,c), …)} # empty intersections adjacent to the group
    board is a 2‑D list indexed 1..19, 0 = empty, 1 = us, -1 = opponent.
    colour is 1 (us) or -1 (opponent).
    """
    visited = [[False] * 20 for _ in range(20)]   # 0‑index unused, board is 1‑based
    groups = []

    for r in range(1, 20):
        for c in range(1, 20):
            if board[r][c] != colour or visited[r][c]:
                continue
            # BFS/DFS for this group
            stack = [(r, c)]
            points = set()
            liberties = set()
            while stack:
                cr, cc = stack.pop()
                if visited[cr][cc]:
                    continue
                visited[cr][cc] = True
                points.add((cr, cc))
                for dr, dc in DIRS:
                    nr, nc = cr + dr, cc + dc
                    if nr < 1 or nr > 19 or nc < 1 or nc > 19:
                        continue
                    val = board[nr][nc]
                    if val == colour and not visited[nr][nc]:
                        stack.append((nr, nc))
                    elif val == 0:          # empty intersection
                        liberties.add((nr, nc))
            groups.append({'points': points, 'liberties': liberties})
    return groups


def _simulate(board, move):
    """
    Simulate playing our stone at `move` (tuple row,col).
    Returns:
        new_board   – board after the move and after any captures,
        captured    – number of opponent stones captured,
        legal       – True iff the move is legal (no self‑atari).
    """
    r, c = move
    # copy board
    new_board = [row[:] for row in board]
    new_board[r][c] = 1                     # place our stone

    # 1) capture opponent groups that now have zero liberties
    opp_groups = _get_groups(new_board, -1)
    captured_points = []
    captured_cnt = 0
    for g in opp_groups:
        if not g['liberties']:               # group is dead
            captured_points.extend(g['points'])
            captured_cnt += len(g['points'])

    for (pr, pc) in captured_points:
        new_board[pr][pc] = 0                # remove captured stones

    # 2) after captures, check that none of our groups is left with zero liberties
    my_groups = _get_groups(new_board, 1)
    for g in my_groups:
        if not g['liberties']:               # self‑atari → illegal
            return None, 0, False

    return new_board, captured_cnt, True


def policy(me, opponent):
    """
    Return a legal move for the current position.
    `me`      – list of (row, col) of our stones.
    `opponent` – list of (row, col) of opponent stones.
    The returned move is a tuple (row, col); (0,0) means pass.
    """
    # ---- build board representation ----
    board = [[0] * 20 for _ in range(20)]   # index 0 unused
    for (r, c) in me:
        board[r][c] = 1
    for (r, c) in opponent:
        board[r][c] = -1

    # ---- current groups (used for quick defensive/capture bonus) ----
    my_groups = _get_groups(board, 1)
    opp_groups = _get_groups(board, -1)

    # ---- all empty intersections ----
    empty = [(r, c) for r in range(1, 20) for c in range(1, 20) if board[r][c] == 0]
    if not empty:          # board full – no legal move except pass
        return (0, 0)

    # ---- scoring constants ----
    CAPTURE_WEIGHT = 100
    DEFENSE_WEIGHT = 50
    LIBERTY_WEIGHT = 1

    best_move = None
    best_score = -1

    for mv in empty:
        # quick capture/defense bonuses based on current groups
        capture_bonus = sum(len(g['points']) for g in opp_groups if g['liberties'] == {mv})
        defense_bonus = sum(len(g['points']) for g in my_groups if g['liberties'] == {mv})

        # simulate the move (also checks legality)
        new_board, captured_cnt, legal = _simulate(board, mv)
        if not legal:
            continue

        # total liberties after the move (measure of future flexibility)
        my_groups_after = _get_groups(new_board, 1)
        total_liberties = sum(len(g['liberties']) for g in my_groups_after)

        # ----- final score -----
        score = (captured_cnt * CAPTURE_WEIGHT +
                 defense_bonus * DEFENSE_WEIGHT +
                 total_liberties * LIBERTY_WEIGHT)

        # keep the best move (strictly greater – first encountered wins ties)
        if score > best_score:
            best_score = score
            best_move = mv

    if best_move is None:      # no legal move found
        return (0, 0)
    return best_move
