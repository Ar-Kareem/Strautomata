
import time
import numpy as np

def get_neighbors(r: int, c: int, valid_mask) -> list[tuple[int, int]]:
    """Return all valid adjacent hexagonal cells using odd-q coordinates."""
    if c % 2 == 1:
        offsets = [(-1, 0), (1, 0), (0, -1), (-1, -1), (0, 1), (-1, 1)]
    else:
        offsets = [(-1, 0), (1, 0), (0, -1), (1, -1), (0, 1), (1, 1)]
    
    nrows, ncols = valid_mask.shape
    neighbors = []
    for dr, dc in offsets:
        nr, nc = r + dr, c + dc
        if 0 <= nr < nrows and 0 <= nc < ncols and valid_mask[nr][nc]:
            neighbors.append((nr, nc))
    return neighbors


def identify_board_features(valid_mask):
    """
    Identifies the 6 corners and 6 edges of the Havannah board.
    In Havannah, corners have degree 3 on the board boundary,
    and edges are boundary cells between corners (excluding corners).
    """
    nrows, ncols = valid_mask.shape
    deg = {}
    valid_cells = []
    for r in range(nrows):
        for c in range(ncols):
            if valid_mask[r][c]:
                valid_cells.append((r, c))
                deg[(r, c)] = len(get_neighbors(r, c, valid_mask))
    
    # Corners on a hex board have degree 3 (or the minimum degree on the perimeter)
    min_deg = min(deg.values())
    corners = [cell for cell, d in deg.items() if d == min_deg]
    
    # In case there are more or less due to grid orientation, pick the 6 extreme points
    if len(corners) != 6:
        corners = sorted(valid_cells, key=lambda p: (deg[p], abs(p[0] - nrows/2) + abs(p[1] - ncols/2)), reverse=True)[:6]

    corner_set = set(corners)
    
    # Perimeter cells have degree < 6
    perimeter = [cell for cell, d in deg.items() if d < 6 and cell not in corner_set]
    
    # Group perimeter cells into 6 continuous edges
    # We can group them by running connected components on perimeter cells
    edges = []
    visited = set()
    for p in perimeter:
        if p not in visited:
            comp = []
            queue = [p]
            visited.add(p)
            while queue:
                curr = queue.pop()
                comp.append(curr)
                for nb in get_neighbors(curr[0], curr[1], valid_mask):
                    if nb in perimeter and nb not in visited:
                        visited.add(nb)
                        queue.append(nb)
            edges.append(set(comp))
            
    # Assign each edge an index 0..5
    edge_map = {}
    for i, edge in enumerate(edges):
        for cell in edge:
            edge_map[cell] = i

    return corner_set, edge_map


class HavannahUnionFind:
    def __init__(self, corner_set, edge_map):
        self.parent = {}
        self.corners = {}
        self.edges = {}
        self.corner_set = corner_set
        self.edge_map = edge_map

    def add(self, cell):
        if cell in self.parent:
            return
        self.parent[cell] = cell
        self.corners[cell] = {cell} if cell in self.corner_set else set()
        self.edges[cell] = {self.edge_map[cell]} if cell in self.edge_map else set()

    def find(self, cell):
        path = []
        while self.parent[cell] != cell:
            path.append(cell)
            cell = self.parent[cell]
        for node in path:
            self.parent[node] = cell
        return cell

    def union(self, c1, c2):
        r1, r2 = self.find(c1), self.find(c2)
        if r1 != r2:
            self.parent[r2] = r1
            self.corners[r1] |= self.corners[r2]
            self.edges[r1] |= self.edges[r2]
            return False
        return True  # Cycle detected


def check_win_by_move(move, stones, opp_stones, valid_mask, corner_set, edge_map):
    """Checks if playing 'move' completes a Bridge, Fork, or Ring."""
    uf = HavannahUnionFind(corner_set, edge_map)
    all_stones = set(stones)
    all_stones.add(move)

    for s in all_stones:
        uf.add(s)

    cycle_created = False
    move_neighbors = get_neighbors(move[0], move[1], valid_mask)
    for nb in move_neighbors:
        if nb in all_stones:
            if uf.union(move, nb):
                cycle_created = True

    for s in all_stones:
        for nb in get_neighbors(s[0], s[1], valid_mask):
            if nb in all_stones:
                uf.union(s, nb)

    root = uf.find(move)
    # Bridge: connects at least 2 corners
    if len(uf.corners[root]) >= 2:
        return True
    # Fork: connects at least 3 edges
    if len(uf.edges[root]) >= 3:
        return True

    # Ring check: if a cycle was created, check if it encloses at least one cell
    if cycle_created:
        if has_ring(all_stones, valid_mask):
            return True

    return False


def has_ring(stones_set, valid_mask):
    """
    Checks if stones_set encloses any cell not in stones_set that cannot reach the board boundary.
    """
    nrows, ncols = valid_mask.shape
    visited = set()
    queue = []

    # All unvisited boundary non-stone valid cells start flood fill
    for r in range(nrows):
        for c in range(ncols):
            if valid_mask[r][c] and (r, c) not in stones_set:
                nb = get_neighbors(r, c, valid_mask)
                if len(nb) < 6:  # Board boundary
                    queue.append((r, c))
                    visited.add((r, c))

    while queue:
        curr = queue.pop()
        for nb in get_neighbors(curr[0], curr[1], valid_mask):
            if nb not in stones_set and nb not in visited:
                visited.add(nb)
                queue.append(nb)

    # If any valid cell is not in stones_set and not visited, it is enclosed!
    for r in range(nrows):
        for c in range(ncols):
            if valid_mask[r][c] and (r, c) not in stones_set and (r, c) not in visited:
                return True
    return False


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    start_time = time.time()
    
    # 1. Precalculate board features
    corner_set, edge_map = identify_board_features(valid_mask)
    my_set = set(me)
    opp_set = set(opp)
    
    nrows, ncols = valid_mask.shape
    center_r, center_c = nrows / 2.0, ncols / 2.0

    # 2. Generate legal candidates
    legal_moves = []
    for r in range(nrows):
        for c in range(ncols):
            if valid_mask[r][c] and (r, c) not in my_set and (r, c) not in opp_set:
                legal_moves.append((r, c))

    if not legal_moves:
        return (0, 0)
    
    # Opening move: take center or near center
    if not me and not opp:
        legal_moves.sort(key=lambda p: (p[0] - center_r)**2 + (p[1] - center_c)**2)
        return legal_moves[0]

    # 3. Tactical check: Immediate Win
    for move in legal_moves:
        if time.time() - start_time > 0.85:
            break
        # Quick filter: only check moves adjacent to existing stones or corners/edges
        nb = get_neighbors(move[0], move[1], valid_mask)
        if any(n in my_set for n in nb) or move in corner_set:
            if check_win_by_move(move, my_set, opp_set, valid_mask, corner_set, edge_map):
                return move

    # 4. Tactical check: Immediate Opponent Win (Block)
    for move in legal_moves:
        if time.time() - start_time > 0.85:
            break
        nb = get_neighbors(move[0], move[1], valid_mask)
        if any(n in opp_set for n in nb) or move in corner_set:
            if check_win_by_move(move, opp_set, my_set, valid_mask, corner_set, edge_map):
                return move

    # 5. Heuristic evaluation of moves
    best_score = -float('inf')
    best_move = legal_moves[0]

    for move in legal_moves:
        r, c = move
        score = 0.0

        # Distance to center bonus
        dist_to_center = ((r - center_r) ** 2 + (c - center_c) ** 2) ** 0.5
        score -= dist_to_center * 1.5

        # Proximity and connectivity to own stones
        nb = get_neighbors(r, c, valid_mask)
        my_adj = sum(1 for n in nb if n in my_set)
        opp_adj = sum(1 for n in nb if n in opp_set)
        empty_adj = len(nb) - my_adj - opp_adj

        score += my_adj * 10.0
        score += opp_adj * 6.0  # Interference with opponent
        score += empty_adj * 1.0  # Potential degrees of freedom

        # Bridge connectivity bonus (corners)
        if move in corner_set:
            score += 15.0
        elif any(n in corner_set for n in nb):
            score += 8.0

        # Edge connectivity bonus
        if move in edge_map:
            score += 4.0

        # Avoid self-crowding (4+ friendly neighbors rarely optimal unless winning)
        if my_adj >= 4:
            score -= 8.0

        if score > best_score:
            best_score = score
            best_move = move

    return best_move
