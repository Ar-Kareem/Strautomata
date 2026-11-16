
def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    # Build the board as a 2D array (0: empty, 1: our stone, -1: opponent stone)
    board = [[0] * 19 for _ in range(19)]
    for (r, c) in me:
        if 1 <= r <= 19 and 1 <= c <= 19:
            board[r-1][c-1] = 1
    for (r, c) in opponent:
        if 1 <= r <= 19 and 1 <= c <= 19:
            board[r-1][c-1] = -1

    # Track empty points
    empty_points = set()
    for r in range(19):
        for c in range(19):
            if board[r][c] == 0:
                empty_points.add((r+1, c+1))

    # Helper function to find groups and their liberties
    def find_groups(color: int):
        visited = set()
        groups = []
        for r in range(19):
            for c in range(19):
                if board[r][c] == color and (r, c) not in visited:
                    group = []
                    queue = [(r, c)]
                    visited.add((r, c))
                    liberties = set()
                    while queue:
                        node = queue.pop(0)
                        group.append(node)
                        for dr, dc in [(0,1), (0,-1), (1,0), (-1,0)]:
                            nr, nc = node[0] + dr, node[1] + dc
                            if 0 <= nr < 19 and 0 <= nc < 19:
                                if board[nr][nc] == 0:
                                    liberties.add((nr+1, nc+1))
                                elif board[nr][nc] == color and (nr, nc) not in visited:
                                    visited.add((nr, nc))
                                    queue.append((nr, nc))
                    groups.append((group, liberties))
        return groups

    # Step 1: Defend our atari groups
    our_groups = find_groups(1)
    for _, liberties in our_groups:
        if len(liberties) == 1:
            return list(liberties)[0]

    # Step 2: Attack opponent's atari groups
    opp_groups = find_groups(-1)
    for _, liberties in opp_groups:
        if len(liberties) == 1:
            liberty = list(liberties)[0]
            if liberty in empty_points:
                r0, c0 = liberty[0]-1, liberty[1]-1
                # Check if we have adjacent stones
                for dr, dc in [(0,1), (0,-1), (1,0), (-1,0)]:
                    nr, nc = r0+dr, c0+dc
                    if 0 <= nr < 19 and 0 <= nc < 19:
                        if board[nr][nc] == 1:
                            return liberty

    # Step 3: Play standard opening moves
    fuseki_candidates = [
        (3, 3), (4, 4),
        (3, 17), (4, 16),
        (17, 3), (16, 4),
        (17, 17), (16, 16)
    ]
    for candidate in fuseki_candidates:
        if candidate in empty_points:
            return candidate

    # Step 4: Score remaining moves
    best_score = -1
    best_move = None
    for r in range(1, 20):
        for c in range(1, 20):
            if (r, c) in empty_points:
                own_adj = opp_adj = empty_adj = 0
                for dr, dc in [(0,1), (0,-1), (1,0), (-1,0)]:
                    nr, nc = r-1+dr, c-1+dc
                    if 0 <= nr < 19 and 0 <= nc < 19:
                        val = board[nr][nc]
                        if val == 1:
                            own_adj += 1
                        elif val == -1:
                            opp_adj += 1
                        else:
                            empty_adj += 1
                # Skip suicide moves
                if own_adj == 0 and opp_adj == 4 and empty_adj == 0:
                    continue
                base_score = 2 * own_adj - 1.5 * opp_adj + 0.1 * empty_adj
                # Position weight
                if (r <= 3 and c <= 3) or (r <= 3 and c >= 17) or (r >= 17 and c <= 3) or (r >= 17 and c >= 17):
                    weight = 10
                elif r <= 3 or c <= 3 or r >= 17 or c >= 17:
                    weight = 5
                else:
                    weight = 0
                total_score = base_score + weight
                if total_score > best_score:
                    best_score = total_score
                    best_move = (r, c)

    return best_move if best_move is not None else (0, 0)
