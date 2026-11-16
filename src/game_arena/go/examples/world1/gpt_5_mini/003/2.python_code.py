
import collections

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    """
    Heuristic Go policy for 19x19 board.

    Arguments:
    - me: list of (row, col) tuples for our stones (1-indexed).
    - opponent: list of (row, col) tuples for opponent stones (1-indexed).

    Returns:
    - (row, col) 1-indexed move tuple. (0,0) to pass.
    """
    N = 19
    # Build board: 0 empty, 1 me, 2 opponent. Use 0-based indexing internally.
    board = [[0] * N for _ in range(N)]
    for (r, c) in me:
        if 1 <= r <= N and 1 <= c <= N:
            board[r - 1][c - 1] = 1
    for (r, c) in opponent:
        if 1 <= r <= N and 1 <= c <= N:
            board[r - 1][c - 1] = 2

    # Helpers
    def neighbors(r, c):
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < N and 0 <= nc < N:
                yield nr, nc

    def flood_group_and_liberties(bd, sr, sc):
        """Return set of stones coords and set of liberty coords for the group at (sr,sc)."""
        player = bd[sr][sc]
        if player == 0:
            return set(), set()
        visited = set()
        liberties = set()
        stack = [(sr, sc)]
        visited.add((sr, sc))
        while stack:
            r, c = stack.pop()
            for nr, nc in neighbors(r, c):
                v = bd[nr][nc]
                if v == 0:
                    liberties.add((nr, nc))
                elif v == player and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    stack.append((nr, nc))
        return visited, liberties

    def compute_groups(player):
        """Return mapping from coord->group_id and group_id->(stones_set, liberties_set)."""
        gid_map = {}
        groups = {}
        seen = set()
        gid = 0
        for r in range(N):
            for c in range(N):
                if board[r][c] == player and (r, c) not in seen:
                    stones, libs = flood_group_and_liberties(board, r, c)
                    for s in stones:
                        gid_map[s] = gid
                    groups[gid] = (stones, libs)
                    seen |= stones
                    gid += 1
        return gid_map, groups

    opp_gid_map, opp_groups = compute_groups(2)
    # own groups not strictly necessary for capture detection, but could be used; compute anyway
    own_gid_map, own_groups = compute_groups(1)

    best_move = None
    best_score = float("-inf")
    center = (9, 9)  # 0-based approx center (10,10 in 1-based)

    # Evaluate all empty intersections
    for r in range(N):
        for c in range(N):
            if board[r][c] != 0:
                continue  # occupied

            # Check adjacent opponent groups: are any captured by playing here?
            adj_opp_gids = set()
            for nr, nc in neighbors(r, c):
                if board[nr][nc] == 2:
                    gid = opp_gid_map.get((nr, nc))
                    if gid is not None:
                        adj_opp_gids.add(gid)

            captured_coords = []
            capture_count = 0
            for gid in adj_opp_gids:
                stones, libs = opp_groups[gid]
                # If the group's liberties are exactly { (r,c) } then placing here captures it
                if (r, c) in libs and len(libs) == 1:
                    capture_count += len(stones)
                    captured_coords.extend(stones)

            # Simulate board after placing and removing captured groups
            board2 = [row[:] for row in board]
            board2[r][c] = 1
            for (cr, cc) in captured_coords:
                board2[cr][cc] = 0

            # Compute the placed stone's group liberties to detect suicide
            stones_after, libs_after = flood_group_and_liberties(board2, r, c)
            if len(libs_after) == 0:
                # illegal suicide (no capture happened or stone has no liberties)
                # skip move
                continue

            # Heuristic scoring
            # Base: capture is highest priority
            score = capture_count * 1000
            # Favor more liberties for the placed group
            score += len(libs_after) * 50
            # Reward attacking adjacency (neighboring opponent stones)
            adj_opp_count = sum(1 for nr, nc in neighbors(r, c) if board[nr][nc] == 2)
            score += adj_opp_count * 20
            # Reward connecting to own stones
            adj_own_count = sum(1 for nr, nc in neighbors(r, c) if board[nr][nc] == 1)
            score += adj_own_count * 8
            # Center influence (prefer more central moves mildly)
            manhattan_to_center = abs(r - center[0]) + abs(c - center[1])
            score += (20 - manhattan_to_center) * 2

            # Penalize self-atari (leaving the placed group with only 1 liberty) unless it captured
            if len(libs_after) == 1 and capture_count == 0:
                score -= 200

            # Deterministic tie-break: prefer smaller (row, col)
            move = (r + 1, c + 1)
            if score > best_score or (score == best_score and (best_move is None or move < best_move)):
                best_score = score
                best_move = move

    if best_move is None:
        # No legal move found (highly unlikely) -> pass
        return (0, 0)
    return best_move
