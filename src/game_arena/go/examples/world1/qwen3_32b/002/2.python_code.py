
def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    # Create grid
    grid = [[0]*20 for _ in range(20)]  # indexes 1-19 for rows and columns
    for (r, c) in me:
        grid[r][c] = 1
    for (r, c) in opponent:
        grid[r][c] = -1

    # Generate empty points
    empty_points = []
    for r in range(1, 20):
        for c in range(1, 20):
            if grid[r][c] == 0:
                empty_points.append((r, c))
    if not empty_points:
        return (0, 0)

    # Helper functions
    def find_group_and_liberties(start_r, start_c, player):
        visited = set()
        group = []
        liberties = set()
        stack = [(start_r, start_c)]
        visited.add((start_r, start_c))
        while stack:
            current_r, current_c = stack.pop()
            if grid[current_r][current_c] != player:
                continue
            if (current_r, current_c) not in group:
                group.append((current_r, current_c))
            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                nr, nc = current_r + dr, current_c + dc
                if 1 <= nr <= 19 and 1 <= nc <= 19:
                    if grid[nr][nc] == 0:
                        liberties.add((nr, nc))
                    elif grid[nr][nc] == player and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        stack.append((nr, nc))
        return group, liberties

    def calculate_attack_score(r, c):
        attack_score = 0
        visited_groups = set()
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= 19 and 1 <= nc <= 19:
                if grid[nr][nc] == -1:  # Opponent's stone
                    group, group_liberties = find_group_and_liberties(nr, nc, -1)
                    group_key = tuple(sorted(group))
                    if group_key not in visited_groups:
                        visited_groups.add(group_key)
                        if (r, c) in group_liberties:
                            if len(group_liberties) == 1:
                                attack_score += len(group)
        return attack_score

    def calculate_defense_score(r, c):
        defense_score = 0
        visited_groups = set()
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= 19 and 1 <= nc <= 19:
                if grid[nr][nc] == 1:  # My stone
                    group, group_liberties = find_group_and_liberties(nr, nc, 1)
                    group_key = tuple(sorted(group))
                    if group_key not in visited_groups:
                        visited_groups.add(group_key)
                        if (r, c) in group_liberties:
                            if len(group_liberties) == 1:
                                defense_score += len(group)
        return defense_score

    def calculate_positional_score(r, c):
        if (r in (1, 19) and c in (1, 19)):
            return 10
        elif r in (1, 19) or c in (1, 19):
            return 5
        else:
            return 1

    # Evaluate each empty point
    best_score = -1
    best_moves = []
    for (r, c) in empty_points:
        attack = calculate_attack_score(r, c)
        defense = calculate_defense_score(r, c)
        pos = calculate_positional_score(r, c)
        total = attack * 10000 + defense * 5000 + pos
        if total > best_score:
            best_score = total
            best_moves = [(r, c)]
        elif total == best_score:
            best_moves.append((r, c))

    # Choose best move (prioritize corners first)
    if best_moves:
        # Sort by positional score descending, then row and column ascending
        best_moves.sort(key=lambda move: (-calculate_positional_score(move[0], move[1]), move[0], move[1]))
        return best_moves[0]
    else:
        return (0, 0)
