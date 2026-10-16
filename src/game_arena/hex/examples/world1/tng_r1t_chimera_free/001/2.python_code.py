
import heapq

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    me = set(me)
    opp = set(opp)
    all_cells = set((i, j) for i in range(11) for j in range(11))
    empty = all_cells - me - opp

    # Determine edges and target test based on color
    if color == 'b':
        my_start = [(0, j) for j in range(11)]
        my_target = lambda i, j: i == 10
        opp_start = [(i, 0) for i in range(11)]
        opp_target = lambda i, j: j == 10
    else:
        my_start = [(i, 0) for i in range(11)]
        my_target = lambda i, j: j == 10
        opp_start = [(0, j) for j in range(11)]
        opp_target = lambda i, j: i == 10

    def shortest_path(start_cells, target_test, own, other, empty_set):
        heap = []
        visited = {}
        dirs = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]
        for cell in start_cells:
            if cell in own:
                heapq.heappush(heap, (0, cell))
                visited[cell] = 0
        while heap:
            dist, (i, j) = heapq.heappop(heap)
            if target_test(i, j):
                return dist
            for di, dj in dirs:
                ni, nj = i + di, j + dj
                if 0 <= ni < 11 and 0 <= nj < 11:
                    neighbor = (ni, nj)
                    if neighbor in other:
                        continue
                    if neighbor in own:
                        new_dist = dist
                    elif neighbor in empty_set:
                        new_dist = dist + 1
                    else:
                        continue
                    if neighbor not in visited or new_dist < visited.get(neighbor, float('inf')):
                        visited[neighbor] = new_dist
                        heapq.heappush(heap, (new_dist, neighbor))
        return float('inf')

    my_current = shortest_path(my_start, my_target, me, opp, empty)
    opp_current = shortest_path(opp_start, opp_target, opp, me, empty)

    best_score = -float('inf')
    best_move = next(iter(empty))  # default to first empty cell

    for cell in empty:
        new_me = me | {cell}
        new_empty = empty - {cell}
        new_my_dist = shortest_path(my_start, my_target, new_me, opp, new_empty)
        new_opp_dist = shortest_path(opp_start, opp_target, opp, new_me, new_empty)
        score = (my_current - new_my_dist) + (new_opp_dist - opp_current)
        if score > best_score or (score == best_score and cell < best_move):
            best_score = score
            best_move = cell

    return best_move
