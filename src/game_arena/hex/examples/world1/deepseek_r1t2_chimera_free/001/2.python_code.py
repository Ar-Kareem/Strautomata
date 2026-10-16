
import heapq

def dijkstra(board_size, grid, start_cells, is_me):
    dist = [[float('inf')] * board_size for _ in range(board_size)]
    heap = []
    for (r, c) in start_cells:
        if grid[r][c] == -1 if not is_me else 1:
            continue
        cost = 0 if (is_me and grid[r][c] == 1) or (not is_me and grid[r][c] == -1) else 1
        if cost < dist[r][c]:
            dist[r][c] = cost
            heapq.heappush(heap, (cost, r, c))
    
    directions = [(0, -1), (0, 1), (-1, 0), (-1, 1), (1, -1), (1, 0)]
    while heap:
        cost, r, c = heapq.heappop(heap)
        if cost > dist[r][c]:
            continue
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < board_size and 0 <= nc < board_size:
                cell_val = grid[nr][nc]
                if (is_me and cell_val == -1) or (not is_me and cell_val == 1):
                    continue
                edge_cost = 1 if cell_val == 0 else 0
                new_cost = cost + edge_cost
                if new_cost < dist[nr][nc]:
                    dist[nr][nc] = new_cost
                    heapq.heappush(heap, (new_cost, nr, nc))
    return dist

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    board_size = 11
    if not me and not opp:
        return (5, 5)
    
    grid = [[0] * board_size for _ in range(board_size)]
    for r, c in me:
        grid[r][c] = 1
    for r, c in opp:
        grid[r][c] = -1
    
    if color == 'b':
        my_start = [(0, c) for c in range(board_size)]
        my_end = [(board_size - 1, c) for c in range(board_size)]
        opp_start = [(r, 0) for r in range(board_size)]
        opp_end = [(r, board_size - 1) for r in range(board_size)]
    else:
        my_start = [(r, 0) for r in range(board_size)]
        my_end = [(r, board_size - 1) for r in range(board_size)]
        opp_start = [(0, c) for c in range(board_size)]
        opp_end = [(board_size - 1, c) for c in range(board_size)]
    
    di_my_start = dijkstra(board_size, grid, my_start, True)
    di_my_end = dijkstra(board_size, grid, my_end, True)
    current_my_dist = min(di_my_start[r][c] + di_my_end[r][c] for r in range(board_size) for c in range(board_size))
    
    di_opp_start = dijkstra(board_size, grid, opp_start, False)
    di_opp_end = dijkstra(board_size, grid, opp_end, False)
    current_opp_dist = min(di_opp_start[r][c] + di_opp_end[r][c] for r in range(board_size) for c in range(board_size))
    
    best_cell = (5, 5)
    best_score = -float('inf')
    
    for r in range(board_size):
        for c in range(board_size):
            if grid[r][c] != 0:
                continue
            
            path_me = di_my_start[r][c] + di_my_end[r][c]
            new_my_cost = path_me - 2
            reduction_me = current_my_dist - min(current_my_dist, new_my_cost)
            
            path_opp = di_opp_start[r][c] + di_opp_end[r][c]
            is_critical = (path_opp == current_opp_dist)
            score = reduction_me + (100 if is_critical else 0)
            
            if score > best_score or (score == best_score and (r, c) == (5, 5)):
                best_score = score
                best_cell = (r, c)
    
    return best_cell
