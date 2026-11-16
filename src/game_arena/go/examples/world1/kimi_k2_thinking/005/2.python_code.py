
def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    """
    Return a legal move for the 19×19 Go board.
    The policy tries to maximise captures, then liberties, then central position.
    """
    # ----------------------------------------------------------------------
    # board representation: 0 = empty, 1 = our stones, 2 = opponent stones
    # indices 1..19 are used; row/col 0 are unused padding.
    board = [[0] * 20 for _ in range(20)]

    for r, c in me:
        board[r][c] = 1
    for r, c in opponent:
        board[r][c] = 2

    # neighbours offsets
    DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    # ----------------------------------------------------------------------
    # helper: return the group (set of coordinates) of a given player
    # and the set of its liberties (adjacent empty points).
    def get_group(bd, r, c, player):
        if bd[r][c] != player:
            return set(), set()
        visited = set()
        group = set()
        libs = set()
        stack = [(r, c)]
        while stack:
            x, y = stack.pop()
            if (x, y) in visited:
                continue
            visited.add((x, y))
            group.add((x, y))
            for dx, dy in DIRS:
                nx, ny = x + dx, y + dy
                if 1 <= nx <= 19 and 1 <= ny <= 19:
                    val = bd[nx][ny]
                    if val == 0:
                        libs.add((nx, ny))
                    elif val == player and (nx, ny) not in visited:
                        stack.append((nx, ny))
        return group, libs

    # ----------------------------------------------------------------------
    best_move = (0, 0)   # pass by default
    best_score = -1      # any legal move will have score >= 0

    # iterate over all board points
    for r in range(1, 20):
        for c in range(1, 20):
            if board[r][c] != 0:
                continue  # occupied – cannot play here

            # ---- simulate the move ------------------------------------------------
            # copy board and place our stone
            bd = [row[:] for row in board]
            bd[r][c] = 1

            # ---- capture opponent groups that lose their last liberty ---------------
            captured = set()          # positions of stones to remove
            # only neighbour opponent groups can be affected
            for dx, dy in DIRS:
                nr, nc = r + dx, c + dy
                if not (1 <= nr <= 19 and 1 <= nc <= 19):
                    continue
                if bd[nr][nc] != 2:
                    continue
                # compute the whole group of this opponent stone
                group, libs = get_group(bd, nr, nc, 2)
                # if the group has no liberties left it is captured
                if len(libs) == 0:
                    captured.update(group)

            # remove the captured stones
            for rr, cc in captured:
                bd[rr][cc] = 0

            # ---- check that our own group has liberties (self‑capture test) -------
            group_new, libs_new = get_group(bd, r, c, 1)
            if len(libs_new) == 0:
                # illegal self‑capture – skip this move
                continue

            # ---- evaluate the move ------------------------------------------------
            capture_cnt = len(captured)
            lib_cnt = len(libs_new)
            dist = abs(r - 10) + abs(c - 10)          # Manhattan distance to centre
            score = capture_cnt * 10000 + lib_cnt * 100 + (20 - dist)

            # keep the best move
            if score > best_score:
                best_score = score
                best_move = (r, c)

    # if no legal move was found we return the pass move (0,0)
    return best_move
