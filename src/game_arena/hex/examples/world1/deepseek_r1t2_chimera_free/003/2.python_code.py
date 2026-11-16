
import heapq
from collections import defaultdict

# Precompute all valid neighbors for each cell to optimize performance
neighbor_offsets = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]
all_neighbors = {}
for row in range(11):
    for col in range(11):
        neighbors = []
        for dr, dc in neighbor_offsets:
            nr, nc = row + dr, col + dc
            if 0 <= nr < 11 and 0 <= nc < 11:
                neighbors.append((nr, nc))
        all_neighbors[(row, col)] = neighbors

def compute_min_stones(player_stones, opp_stones, color):
    size = 11
    block_set = set(opp_stones)
    mine_set = set(player_stones)
    
    sources, targets = [], []
    if color == 'b':  # Black: top (0,*) to bottom (10,*)
        sources = [(0, c) for c in range(11)]
        targets = [(10, c) for c in range(11)]
    else:  # White: left (*,0) to right (*,10)
        sources = [(r, 0) for r in range(11)]
        targets = [(r, 10) for r in range(11)]

    dist = [[float('inf')] * size for _ in range(size)]
    heap = []

    for (r, c) in sources:
        if (r, c) in block_set:
            continue
        cost = 0 if (r, c) in mine_set else 1
        dist[r][c] = cost
        heapq.heappush(heap, (cost, r, c))

    target_set = set(targets)
    while heap:
        cost, r, c = heapq.heappop(heap)
        if (r, c) in target_set:
            return cost
        if cost > dist[r][c]:
            continue
        for nr, nc in all_neighbors[(r, c)]:
            if (nr, nc) in block_set:
                continue
            new_cost = cost + (0 if (nr, nc) in mine_set else 1)
            if new_cost < dist[nr][nc]:
                dist[nr][nc] = new_cost
                heapq.heappush(heap, (new_cost, nr, nc))

    return float('inf')  # No path found

def policy(me, opp, color):
    current_me = list(me)
    current_opp = list(opp)
    
    # Compute initial minimal stone requirements
    current_me_dist = compute_min_stones(current_me, current_opp, color)
    opp_color = 'w' if color == 'b' else 'b'
    current_opp_dist = compute_min_stones(current_opp, current_me, opp_color)
    
    # Generate list of empty cells
    empty_cells = []
    for r in range(11):
        for c in range(11):
            if (r, c) not in current_me and (r, c) not in current_opp:
                empty_cells.append((r, c))
                
    if not empty_cells:
        return (0, 0)  # Fallback (shouldn't occur in valid game states)
    
    best_move = empty_cells[0]
    best_score = -float('inf')
    
    for cell in empty_cells:
        # Simulate placing stone in this cell for us
        new_me = current_me + [cell]
        new_me_dist = compute_min_stones(new_me, current_opp, color)
        gain_me = current_me_dist - new_me_dist
        
        # Simulate blocking opponent with this cell
        new_opp_blockers = current_me + [cell]
        new_opp_dist = compute_min_stones(current_opp, new_opp_blockers, opp_color)
        gain_opp = current_opp_dist - new_opp_dist
        
        # Combined score prioritizes both connection advancement and opponent blocking
        score = gain_me + 2 * gain_opp  # Weight opponent blocking higher
        
        if score > best_score or (score == best_score and cell < best_move):
            best_score = score
            best_move = cell
            
    return best_move
