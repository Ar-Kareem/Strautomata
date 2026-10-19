
def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    me_set = set(me)
    opponent_set = set(opponent)
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    best_move = (0, 0)
    max_score = -float('inf')

    for x in range(1, 20):
        for y in range(1, 20):
            # Skip already occupied cells
            if (x, y) in me_set or (x, y) in opponent_set:
                continue

            # Position value: corners (5), edges (3), others (1)
            if x in (1, 19) and y in (1, 19):
                pos_val = 5
            elif x in (1, 19) or y in (1, 19):
                pos_val = 3
            else:
                pos_val = 1

            # Adjacency bonus: count adjacent me stones
            adj_count = 0
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if (nx, ny) in me_set:
                    adj_count += 1
            adj_score = adj_count * 3

            # Liberties: empty adjacent cells
            liberties = 0
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 1 <= nx <= 19 and 1 <= ny <= 19:
                    if (nx, ny) not in me_set and (nx, ny) not in opponent_set:
                        liberties += 1

            # Total score for the move
            current_score = pos_val + adj_score + liberties

            # Update best move if this move is better
            if current_score > max_score:
                max_score = current_score
                best_move = (x, y)

    return best_move
