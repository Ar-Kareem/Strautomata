
import numpy as np
from collections import deque, defaultdict

def policy(me, opp, valid_mask):
    N = len(valid_mask)
    valid_cells = []
    idx_arr = [[-1]*N for _ in range(N)]
    for r in range(N):
        for c in range(N):
            if valid_mask[r][c]:
                idx_arr[r][c] = len(valid_cells)
                valid_cells.append((r, c))
    V = len(valid_cells)

    # Build adjacency for the hexagonal board.
    adj = [[] for _ in range(V)]
    for i, (r, c) in enumerate(valid_cells):
        # Same column.
        for dr, dc in [(-1, 0), (1, 0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < N and 0 <= nc < N and valid_mask[nr][nc]:
                adj[i].append(idx_arr[nr][nc])
        # Left/right diagonal columns depend on column parity.
        if c % 2 == 1:
            diag = [(-1, -1), (0, -1), (-1, 1), (0, 1)]
        else:
            diag = [(0, -1), (1, -1), (0, 1), (1, 1)]
        for dr, dc in diag:
            nr, nc = r + dr, c + dc
            if 0 <= nr < N and 0 <= nc < N and valid_mask[nr][nc]:
                adj[i].append(idx_arr[nr][nc])

    boundary = [i for i in range(V) if len(adj[i]) < 6]
    boundary_set = set(boundary)

    # Walk the outer boundary and split it into six edge groups.
    corners = set()
    edge_group = [-1] * V
    if boundary:
        b_neighbors = {i: [j for j in adj[i] if j in boundary_set] for i in boundary}
        start = boundary[0]
        perimeter = []
        prev = None
        curr = start
        for _ in range(len(boundary) + 2):
            perimeter.append(curr)
            nbs = b_neighbors[curr]
            if prev is None:
                nxt = nbs[0]
            else:
                nxt = nbs[0] if nbs[0] != prev else nbs[1]
            prev, curr = curr, nxt
            if curr == start:
                break

        L = len(perimeter)
        dirs = []
        for i in range(L):
            r1, c1 = valid_cells[perimeter[i]]
            r2, c2 = valid_cells[perimeter[(i + 1) % L]]
            dirs.append((r2 - r1, c2 - c1))

        corner_indices = [i for i in range(L) if dirs[(i - 1) % L] != dirs[i]]
        if len(corner_indices) != 6:
            # Fallback: corner cells on a Havannah board have degree exactly 3.
            deg_corners = {i for i in boundary if len(adj[i]) == 3}
            corner_indices = [i for i, cell in enumerate(perimeter) if cell in deg_corners]

        if len(corner_indices) == 6:
            for i in corner_indices:
                corners.add(perimeter[i])
            for k in range(6):
                si = corner_indices[k]
                ei = corner_indices[(k + 1) % 6]
                idx = (si + 1) % L
                while idx != ei:
                    edge_group[perimeter[idx]] = k
                    idx = (idx + 1) % L

    # Find the board center: farthest cell from the boundary.
    dist_boundary = [-1] * V
    q = deque()
    for b in boundary:
        dist_boundary[b] = 0
        q.append(b)
    while q:
        u = q.popleft()
        for nb in adj[u]:
            if dist_boundary[nb] == -1:
                dist_boundary[nb] = dist_boundary[u] + 1
                q.append(nb)
    center_idx = max(range(V), key=lambda i: dist_boundary[i])

    dist_center = [-1] * V
    q = deque([center_idx])
    dist_center[center_idx] = 0
    while q:
        u = q.popleft()
        for nb in adj[u]:
            if dist_center[nb] == -1:
                dist_center[nb] = dist_center[u] + 1
                q.append(nb)

    def make_parent():
        return list(range(V)), [0] * V

    def find(parent, x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(parent, rank, a, b):
        ra = find(parent, a)
        rb = find(parent, b)
        if ra == rb:
            return
        if rank[ra] < rank[rb]:
            ra, rb = rb, ra
        parent[rb] = ra
        if rank[ra] == rank[rb]:
            rank[ra] += 1

    def check_win(stone_set):
        if not stone_set:
            return False

        parent, rank = make_parent()
        for s in stone_set:
            for nb in adj[s]:
                if nb in stone_set:
                    union(parent, rank, s, nb)

        comp_edges = defaultdict(set)
        comp_corners = defaultdict(set)
        for s in stone_set:
            root = find(parent, s)
            if s in corners:
                comp_corners[root].add(s)
            if edge_group[s] != -1:
                comp_edges[root].add(edge_group[s])

        for root, es in comp_edges.items():
            if len(es) >= 3:
                return True
        for root, cs in comp_corners.items():
            if len(cs) >= 2:
                return True

        # Ring detection: after removing all stones of this colour,
        # an enclosed cell is disconnected from the boundary.
        visited = [False] * V
        q = deque()
        for b in boundary:
            if b not in stone_set:
                visited[b] = True
                q.append(b)
        while q:
            u = q.popleft()
            for nb in adj[u]:
                if nb not in stone_set and not visited[nb]:
                    visited[nb] = True
                    q.append(nb)

        for i in range(V):
            if i not in stone_set and not visited[i]:
                return True

        # A ring may also enclose the player's own stones.
        for s in stone_set:
            if s in boundary_set:
                continue
            reachable = False
            for nb in adj[s]:
                if visited[nb]:
                    reachable = True
                    break
            if not reachable:
                return True

        return False

    def state_score(stone_set):
        if not stone_set:
            return 0.0

        parent, rank = make_parent()
        for s in stone_set:
            for nb in adj[s]:
                if nb in stone_set:
                    union(parent, rank, s, nb)

        comp_edges = defaultdict(set)
        comp_corners = defaultdict(set)
        comp_size = defaultdict(int)
        for s in stone_set:
            root = find(parent, s)
            comp_size[root] += 1
            if s in corners:
                comp_corners[root].add(s)
            if edge_group[s] != -1:
                comp_edges[root].add(edge_group[s])

        score = 0.0
        for root, size in comp_size.items():
            edges = len(comp_edges[root])
            cnrs = len(comp_corners[root])

            if edges >= 3 or cnrs >= 2:
                score += 10000
            if edges == 2:
                score += 150 + size * 2
            elif edges == 1:
                score += 35 + size
            if cnrs == 1:
                score += 30 + size
            if edges == 0 and cnrs == 0:
                score += size * 0.8
            score += size * 0.5
            score -= 6.0
        return score

    me_set = set()
    for r, c in me:
        if 0 <= r < N and 0 <= c < N and idx_arr[r][c] != -1:
            me_set.add(idx_arr[r][c])

    opp_set = set()
    for r, c in opp:
        if 0 <= r < N and 0 <= c < N and idx_arr[r][c] != -1:
            opp_set.add(idx_arr[r][c])

    empty = [i for i in range(V) if i not in me_set and i not in opp_set]
    if not empty:
        # No legal move; this should never happen in a real game.
        return valid_cells[0]

    # Opening: play the center.
    if not me_set and not opp_set:
        return valid_cells[center_idx]

    # 1. Immediate win.
    for move in empty:
        if check_win(me_set | {move}):
            return valid_cells[move]

    # 2. Block opponent's immediate winning moves.
    block_moves = []
    for move in empty:
        if check_win(opp_set | {move}):
            block_moves.append(move)

    def move_score(move):
        new_me = me_set | {move}
        new_opp = opp_set | {move}
        center_bonus = max(0, 5 - dist_center[move]) * 2.0
        return state_score(new_me) + 0.85 * state_score(new_opp) + center_bonus

    if block_moves:
        best_move = max(block_moves, key=move_score)
        return valid_cells[best_move]

    # 3. Heuristic one-ply move choice.
    best_move = max(empty, key=move_score)
    return valid_cells[best_move]
