
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    def is_connected(a, b, stones_set):
        if a not in stones_set or b not in stones_set:
            return False
        visited = set()
        queue = [a]
        visited.add(a)
        while queue:
            current = queue.pop(0)
            if current == b:
                return True
            r, c = current
            neighbors = [
                (r-1, c),   # up
                (r+1, c),   # down
                (r, c-1),   # left
                (r, c+1),   # right
                (r-1, c-1), # up-left
                (r-1, c+1), # up-right
            ]
            for nr, nc in neighbors:
                if (nr, nc) in stones_set and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    queue.append((nr, nc))
        return False

    possible_moves = []
    for r in range(15):
        for c in range(15):
            if valid_mask[r][c] and ((r, c) not in me) and ((r, c) not in opp):
                possible_moves.append((r, c))

    # Predefined corners for bridge detection
    corners = [(0, 0), (0, 14), (14, 14), (14, 0), (7, 0), (7, 14)]
    opp_set = set(opp)

    # Block opponent's potential win
    for candidate_move in possible_moves:
        temp_opp_set = opp_set | {candidate_move}
        for i in range(len(corners)):
            for j in range(i + 1, len(corners)):
                a, b = corners[i], corners[j]
                if a in temp_opp_set and b in temp_opp_set:
                    if is_connected(a, b, temp_opp_set):
                        return candidate_move  # Block by taking this spot

    me_set = set(me)
    # Check if any move creates a winning bridge
    for move in possible_moves:
        new_me_set = me_set | {move}
        for i in range(len(corners)):
            for j in range(i + 1, len(corners)):
                a, b = corners[i], corners[j]
                if a in new_me_set and b in new_me_set:
                    if is_connected(a, b, new_me_set):
                        return move

    # Evaluate remaining moves using heuristics
    best_score = -1
    best_move = None
    for move in possible_moves:
        r, c = move
        corner_bonus = 1000 if move in corners else 0
        edge_bonus = 500 if ((r in (0, 14) or c in (0, 14)) and move not in corners) else 0
        adj_count = 0
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1)]:
            nr, nc = r + dr, c + dc
            if (nr, nc) in me_set:
                adj_count += 1
        score = corner_bonus + edge_bonus + adj_count * 10
        if score > best_score or (score == best_score and move < best_move):
            best_score = score
            best_move = move
    return best_move
