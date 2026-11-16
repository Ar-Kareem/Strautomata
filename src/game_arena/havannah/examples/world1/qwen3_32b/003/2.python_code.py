
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0)]
    N = len(valid_mask)
    me_set = set(me)
    opp_set = set(opp)

    valid_moves = []
    for r in range(N):
        for c in range(N):
            if valid_mask[r][c] and (r, c) not in me_set and (r, c) not in opp_set:
                valid_moves.append((r, c))

    best_score = -1
    best_move = valid_moves[0]

    for (r, c) in valid_moves:
        adjacent_count = 0
        for dr, dc in directions:
            nr = r + dr
            nc = c + dc
            if 0 <= nr < N and 0 <= nc < N:
                if (nr, nc) in me_set:
                    adjacent_count += 1

        is_edge = False
        for dr, dc in directions:
            nr = r + dr
            nc = c + dc
            if 0 <= nr < N and 0 <= nc < N:
                if not valid_mask[nr][nc]:
                    is_edge = True
                    break
            else:
                is_edge = True
                break

        invalid_neighbors = 0
        for dr, dc in directions:
            nr = r + dr
            nc = c + dc
            if 0 <= nr < N and 0 <= nc < N:
                if not valid_mask[nr][nc]:
                    invalid_neighbors += 1
            else:
                invalid_neighbors += 1

        is_corner = invalid_neighbors >= 2

        score = adjacent_count * 4 + is_edge * 3 + is_corner * 5

        if score > best_score:
            best_score = score
            best_move = (r, c)

    return best_move
