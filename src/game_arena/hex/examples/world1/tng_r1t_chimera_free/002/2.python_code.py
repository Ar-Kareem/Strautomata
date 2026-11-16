
import heapq
from collections import defaultdict

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    my_stones = set(me)
    opp_stones = set(opp)
    empty_cells = [(i, j) for i in range(11) for j in range(11) if (i, j) not in my_stones and (i, j) not in opp_stones]

    if not empty_cells:
        return (0, 0)  # Fallback, though per rules there's always a move.

    # Define edges based on color
    if color == 'b':
        my_start = [(0, c) for c in range(11)]
        my_end = [(10, c) for c in range(11)]
        opp_start = [(r, 0) for r in range(11)]
        opp_end = [(r, 10) for r in range(11)]
    else:
        my_start = [(r, 0) for r in range(11)]
        my_end = [(r, 10) for r in range(11)]
        opp_start = [(0, c) for c in range(11)]
        opp_end = [(10, c) for c in range(11)]

    def compute_distances(start_edges, is_my_turn):
        dist = defaultdict(lambda: float('inf'))
        heap = []
        for (r, c) in start_edges:
            if (r, c) in my_stones and is_my_turn:
                heapq.heappush(heap, (0, r, c))
                dist[(r, c)] = 0
            elif (r, c) in opp_stones and not is_my_turn:
                heapq.heappush(heap, (0, r, c))
                dist[(r, c)] = 0
            elif (r, c) not in my_stones and (r, c) not in opp_stones:
                heapq.heappush(heap, (1, r, c))
                dist[(r, c)] = 1

        visited = set()
        while heap:
            d, r, c = heapq.heappop(heap)
            if (r, c) in visited:
                continue
            visited.add((r, c))
            for dr, dc in [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 11 and 0 <= nc < 11:
                    if (nr, nc) in my_stones:
                        new_d = d if is_my_turn else float('inf')
                    elif (nr, nc) in opp_stones:
                        new_d = d if not is_my_turn else float('inf')
                    else:
                        new_d = d + 1
                    if new_d < dist[(nr, nc)]:
                        dist[(nr, nc)] = new_d
                        heapq.heappush(heap, (new_d, nr, nc))
        return dist

    my_dist_start = compute_distances(my_start, True)
    my_dist_end = compute_distances(my_end, True)
    opp_dist_start = compute_distances(opp_start, False)
    opp_dist_end = compute_distances(opp_end, False)

    best_move = None
    max_score = -float('inf')
    best_adj = -1

    for (r, c) in empty_cells:
        my_score = my_dist_start[(r, c)] + my_dist_end[(r, c)]
        opp_score = opp_dist_start[(r, c)] + opp_dist_end[(r, c)]
        score = opp_score - my_score

        adjacent = 0
        for dr, dc in [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]:
            nr, nc = r + dr, c + dc
            if (nr, nc) in my_stones:
                adjacent += 1
        score += adjacent * 0.1  # Prefer connecting to existing stones

        if score > max_score or (score == max_score and adjacent > best_adj):
            max_score = score
            best_move = (r, c)
            best_adj = adjacent

    return best_move if best_move is not None else empty_cells[0]
