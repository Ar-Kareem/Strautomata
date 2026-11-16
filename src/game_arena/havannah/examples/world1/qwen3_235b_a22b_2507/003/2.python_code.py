
import numpy as np

# Precompute neighbors for each cell on a 15x15 rhombic (axial) grid interpreted as hex grid
# Directions in axial coordinates: (d_row, d_col) accounting for offset
# In Havannah, the layout is such that:
# - Moving "up" and "down" in a column keeps the same column
# - Left and right neighbors differ by column and may shift row
HEX_DIRS = [
    (-1, 0),  # up
    (-1, 1),  # up-right
    (0, 1),   # down-right
    (1, 0),   # down
    (1, -1),  # down-left
    (0, -1),  # up-left
]

CORNER_IDS = [
    (0, 0),      # top
    (0, 14),     # top-right
    (7, 14),     # bottom-right (approx)
    (14, 14),    # bottom
    (14, 0),     # bottom-left
    (7, 0),      # top-left
]

EDGE_ID_TO_MASK = {
    'top': lambda r, c: r == 0 and 0 < c < 14,
    'bottom': lambda r, c: r == 14 and 0 < c < 14,
    'left': lambda r, c: c == 0 and 0 < r < 14,
    'right': lambda r, c: c == 14 and 0 < r < 14,
    'topleft': lambda r, c: r + c == 7 and r < 7 and c > 0,
    'bottomright': lambda r, c: r + c == 21 and r > 7 and c < 14,
}

EDGE_NAMES = list(EDGE_ID_TO_MASK.keys())
EDGE_STONES = {name: [] for name in EDGE_NAMES}

# Precompute edge stones
for r in range(15):
    for c in range(15):
        for name, cond in EDGE_ID_TO_MASK.items():
            if cond(r, c):
                EDGE_STONES[name].append((r, c))

def get_neighbors(r, c):
    neighbors = []
    for dr, dc in HEX_DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 15 and 0 <= nc < 15:
            neighbors.append((nr, nc))
    return neighbors

def is_cell_connected_to_edge(stone, edge_name, player_stones):
    """Check if stone is part of a connected group touching the given edge."""
    if stone not in player_stones:
        return False
    edge_stones = EDGE_STONES[edge_name]
    visited = set()
    stack = [stone]
    while stack:
        curr = stack.pop()
        if curr in visited:
            continue
        visited.add(curr)
        if curr in edge_stones:
            return True
        for nb in get_neighbors(*curr):
            if nb in player_stones and nb not in visited:
                stack.append(nb)
    return False

def count_edges_connected(player_stones):
    """Count how many distinct edges the player's stones are connected to."""
    connected = set()
    for name, stones in EDGE_STONES.items():
        for stone in stones:
            if is_cell_connected_to_edge(stone, name, player_stones):
                connected.add(name)
    return len(connected)

def connected_components(stones):
    """Return list of connected components (each as a set) from a list of stones."""
    if not stones:
        return []
    stone_set = set(stones)
    visited = set()
    components = []
    for stone in stones:
        if stone in visited:
            continue
        comp = set()
        stack = [stone]
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            comp.add(node)
            for nb in get_neighbors(*node):
                if nb in stone_set and nb not in visited:
                    stack.append(nb)
        components.append(comp)
    return components

def heuristic_score(me_stones, opp_stones):
    score = 0.0

    # 1. Bridge potential: try to connect corners
    my_corners = set(me_stones) & set(CORNER_IDS)
    if len(my_corners) >= 2:
        # Attempt to see if corners are connected
        comp = connected_components(me_stones)
        for c in comp:
            corner_count = sum(1 for cor in CORNER_IDS if cor in c)
            if corner_count >= 2:
                return 1e6  # Winning bridge!
            score += corner_count * 10

    # 2. Fork potential: connected to 3+ edges
    my_edge_count = count_edges_connected(me_stones)
    opp_edge_count = count_edges_connected(opp_stones)
    if my_edge_count >= 3:
        return 1e6  # Winning fork!
    score += my_edge_count * 30 - opp_edge_count * 25

    # 3. Ring potential: try to enclose area
    # Simple: look for small enclosures or loops
    for comp in connected_components(me_stones):
        if len(comp) >= 6:
            # Estimate convex hull or enclosed voids
            min_r = min(r for r, c in comp)
            max_r = max(r for r, c in comp)
            min_c = min(c for r, c in comp)
            max_c = max(c for r, c in comp)
            area = (max_r - min_r + 1) * (max_c - min_c + 1)
            if len(comp) > area * 0.7 and area - len(comp) > 0:
                # Dense cluster with small holes -> ring candidate
                score += 50

    # 4. Mobility: reward center and openness
    center = (7, 7)
    for (r, c) in me_stones:
        dist = abs(r - center[0]) + abs(c - center[1])
        score += (14 - dist) * 0.5

    return score

def is_legal_move(r, c, valid_mask):
    return 0 <= r < 15 and 0 <= c < 15 and valid_mask[r][c]

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    me_set = set(me)
    opp_set = set(opp)
    all_stones = me_set | opp_set

    # First, check for winning move or block opponent's win
    valid_moves = []
    for r in range(15):
        for c in range(15):
            if is_legal_move(r, c, valid_mask):
                valid_moves.append((r, c))

    if not valid_moves:
        # Shouldn't happen, but fallback
        for r in range(15):
            for c in range(15):
                if valid_mask[r][c]:
                    return (r, c)

    # Evaluate all moves with lookahead 1
    best_move = valid_moves[0]
    best_score = -1e9

    for move in valid_moves:
        # Simulate move
        my_next = me + [move]
        my_set_next = set(my_next)
        # Reuse function to check if this move completes a win
        new_score = heuristic_score(my_next, opp)

        # Check if move would complete a ring (simulate closure)
        # Very simple ring check: if adding this move connects a loop
        comp = None
        for c in connected_components(my_next):
            if move in c:
                comp = c
                break
        if comp and len(comp) >= 6:
            # Try to see if it's a ring: for each empty cell inside bounding box, see if surrounded
            min_r = min(r for r, c in comp)
            max_r = max(r for r, c in comp)
            min_c = min(c for r, c in comp)
            max_c = max(c for r, c in comp)
            enclosed = 0
            for ir in range(min_r + 1, max_r):
                for ic in range(min_c + 1, max_c):
                    if (ir, ic) not in all_stones:
                        neighbors = get_neighbors(ir, ic)
                        if all(nb in comp or nb in all_stones for nb in neighbors):
                            enclosed += 1
            if enclosed > 0:
                new_score += 1000  # Strongly reward ring formation

        # Also penalize moves that let opponent complete bridge/fork
        # Very basic: simulate opponent's response on best threat
        opp_future_score = heuristic_score(opp, my_next)  # from opponent's perspective: our move affects their score
        new_score -= opp_future_score * 0.5

        # Prioritize moves with more future options
        mobility = 0
        for nb in get_neighbors(*move):
            if is_legal_move(nb[0], nb[1], valid_mask) and nb not in all_stones and nb != move:
                mobility += 1
        new_score += mobility * 2

        if new_score > best_score:
            best_score = new_score
            best_move = move

    # Final safety: ensure move is valid
    if is_legal_move(best_move[0], best_move[1], valid_mask) and best_move not in me_set and best_move not in opp_set:
        return best_move

    # Fallback: first valid move
    for r in range(15):
        for c in range(15):
            if valid_mask[r][c]:
                return (r, c)
    return (7, 7)  # absolute fallback
