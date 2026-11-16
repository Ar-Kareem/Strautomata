
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    me_set = set(me)
    opp_set = set(opp)
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1)]
    center_r, center_c = 7, 7
    valid_moves = [(r, c) for r in range(15) for c in range(15) if valid_mask[r][c] and (r, c) not in me_set and (r, c) not in opp_set]

    best_score = -1.0
    best_move = valid_moves[0]  # Default to the first valid move

    for move in valid_moves:
        r, c = move
        # Count adjacent same-player stones
        adj_count = 0
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 15 and 0 <= nc < 15:
                if (nr, nc) in me_set:
                    adj_count += 1
        # Proximity to the center
        dist = (r - center_r) ** 2 + (c - center_c) ** 2
        center_bonus = 1.0 / (dist + 1.0)
        # Opponent adjacency to block potential expansion
        opp_adj = 0
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 15 and 0 <= nc < 15:
                if (nr, nc) in opp_set:
                    opp_adj += 1
        # Combine metrics into a total score
        total_score = adj_count + center_bonus + 0.1 * opp_adj
        if total_score > best_score:
            best_score = total_score
            best_move = move

    return best_move
