
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    def get_neighbors(r, c):
        neighbors = [
            (r-1, c),
            (r+1, c),
            (r, c-1),
            (r-1, c-1),
            (r, c+1),
            (r-1, c+1)
        ]
        valid = []
        for (nr, nc) in neighbors:
            if 0 <= nr < 15 and 0 <= nc < 15:
                valid.append((nr, nc))
        return valid

    me_set = set(me)
    opp_set = set(opp)
    corners = [(0, 0), (0, 14), (14, 0), (14, 14), (7, 0), (7, 14)]
    best_score = -float('inf')
    best_move = None

    for r in range(15):
        for c in range(15):
            if valid_mask[r][c] and (r, c) not in me_set and (r, c) not in opp_set:
                neighbors = get_neighbors(r, c)
                adjacent_me = sum(1 for (nr, nc) in neighbors if (nr, nc) in me_set)
                adjacent_opp = sum(1 for (nr, nc) in neighbors if (nr, nc) in opp_set)
                d_center = abs(r - 7) + abs(c - 7)
                center_score = 1.0 / (d_center + 1)
                corner_score = sum(1.0 / (abs(r - x) + abs(c - y) + 1) for (x, y) in corners)
                score = 3.0 * adjacent_me + 2.0 * corner_score + 1.5 * center_score - 2.0 * adjacent_opp
                if score > best_score or (score == best_score and (r + c) < (best_move[0] + best_move[1] if best_move else 0)):
                    best_score = score
                    best_move = (r, c)

    return best_move if best_move is not None else (0, 0)
