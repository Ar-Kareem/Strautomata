
import math

def get_hex_neighbors(r: int, c: int) -> list[tuple[int, int]]:
    """Returns the 6 hexagonal neighbors in the offset coordinate system."""
    if c % 2 == 1:
        return [(r - 1, c), (r + 1, c), (r, c - 1), (r - 1, c - 1), (r, c + 1), (r - 1, c + 1)]
    else:
        return [(r - 1, c), (r + 1, c), (r, c - 1), (r + 1, c - 1), (r, c + 1), (r + 1, c + 1)]

def to_cube(r: int, c: int) -> tuple[int, int, int]:
    """Converts 2D offset coordinates to 3D cube coordinates."""
    x = c
    z = r - (c + (c & 1)) // 2
    y = -x - z
    return (x, y, z)

def hex_distance(c1: tuple[int, int], c2: tuple[int, int]) -> int:
    """Computes exact hexagonal distance between two cells."""
    x1, y1, z1 = to_cube(c1[0], c1[1])
    x2, y2, z2 = to_cube(c2[0], c2[1])
    return (abs(x1 - x2) + abs(y1 - y2) + abs(z1 - z2)) // 2

class DSU:
    def __init__(self, elements):
        self.parent = {x: x for x in elements}
        self.corners = {x: 0 for x in elements}
        self.edges = {x: 0 for x in elements}

    def find(self, x):
        path = []
        while self.parent[x] != x:
            path.append(x)
            x = self.parent[x]
        for node in path:
            self.parent[node] = x
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra
            self.corners[ra] |= self.corners[rb]
            self.edges[ra] |= self.edges[rb]

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    rows, cols = len(valid_mask), len(valid_mask[0])
    valid_cells = set()
    for r in range(rows):
        for c in range(cols):
            if valid_mask[r][c]:
                valid_cells.add((r, c))

    me_set = set(me)
    opp_set = set(opp)
    empty_cells = [cell for cell in valid_cells if cell not in me_set and cell not in opp_set]
    if not empty_cells:
        return (0, 0)

    # Build adjacency graph for valid cells
    adj = {}
    for cell in valid_cells:
        adj[cell] = [nb for nb in get_hex_neighbors(cell[0], cell[1]) if nb in valid_cells]

    # Identify corners (degree == 3) and perimeter cells (degree < 6)
    perimeter_cells = {cell for cell, nbrs in adj.items() if len(nbrs) < 6}
    corners_list = [cell for cell in perimeter_cells if len(adj[cell]) == 3]

    corner_map = {}
    for idx, corner in enumerate(corners_list):
        corner_map[corner] = idx

    # Identify 6 distinct edges by connected components of non-corner perimeter cells
    non_corner_perim = perimeter_cells - set(corners_list)
    edge_map = {}
    visited_perim = set()
    edge_id = 0
    for cell in non_corner_perim:
        if cell not in visited_perim:
            q = [cell]
            visited_perim.add(cell)
            while q:
                curr = q.pop()
                edge_map[curr] = edge_id
                for nb in adj[curr]:
                    if nb in non_corner_perim and nb not in visited_perim:
                        visited_perim.add(nb)
                        q.append(nb)
            edge_id += 1

    # Approximate center of the board
    if corners_list:
        cx = sum(to_cube(c[0], c[1])[0] for c in corners_list) / len(corners_list)
        cy = sum(to_cube(c[0], c[1])[1] for c in corners_list) / len(corners_list)
        cz = -cx - cy
    else:
        cx, cy, cz = to_cube(7, 7)

    def dist_to_center(cell: tuple[int, int]) -> int:
        x, y, z = to_cube(cell[0], cell[1])
        return int((abs(x - cx) + abs(y - cy) + abs(z - cz)) / 2)

    # Fast opening move: take the center if available
    if len(me) == 0 and len(opp) <= 1:
        best_open = min(empty_cells, key=dist_to_center)
        return best_open

    def check_ring(player_stones: set, move: tuple[int, int]) -> bool:
        """Determines if placing 'move' forms an unbroken ring enclosing any cell(s)."""
        test_stones = player_stones | {move}
        reached_boundary = set(perimeter_cells) - test_stones

        for nbr in adj[move]:
            if nbr in test_stones or nbr in reached_boundary:
                continue
            # BFS through non-player cells to verify if they can escape to the perimeter
            q = [nbr]
            visited = {nbr}
            trapped = True
            while q:
                curr = q.pop()
                if curr in reached_boundary:
                    trapped = False
                    break
                for next_nb in adj[curr]:
                    if next_nb not in test_stones and next_nb not in visited:
                        visited.add(next_nb)
                        q.append(next_nb)
            if trapped:
                return True
            else:
                reached_boundary.update(visited)
        return False

    def build_player_dsu(player_stones: set):
        dsu = DSU(player_stones)
        for stone in player_stones:
            if stone in corner_map:
                dsu.corners[stone] = (1 << corner_map[stone])
            if stone in edge_map:
                dsu.edges[stone] = (1 << edge_map[stone])
        for stone in player_stones:
            for nb in adj[stone]:
                if nb in player_stones:
                    dsu.union(stone, nb)
        return dsu

    dsu_me = build_player_dsu(me_set)
    dsu_opp = build_player_dsu(opp_set)

    def is_winning_move(player_stones: set, dsu: DSU, move: tuple[int, int]) -> bool:
        c_mask = (1 << corner_map[move]) if move in corner_map else 0
        e_mask = (1 << edge_map[move]) if move in edge_map else 0

        friendly_nbrs = [nb for nb in adj[move] if nb in player_stones]
        seen_roots = set()
        for nb in friendly_nbrs:
            root = dsu.find(nb)
            if root not in seen_roots:
                seen_roots.add(root)
                c_mask |= dsu.corners[root]
                e_mask |= dsu.edges[root]

        # Bridge condition: >= 2 corners
        if bin(c_mask).count('1') >= 2:
            return True
        # Fork condition: >= 3 edges
        if bin(e_mask).count('1') >= 3:
            return True
        # Ring condition: requires at least 2 friendly neighbors to enclose space
        if len(friendly_nbrs) >= 2 and check_ring(player_stones, move):
            return True
        return False

    # 1. Immediate Win: If any move wins the game right now, take it
    for move in empty_cells:
        if is_winning_move(me_set, dsu_me, move):
            return move

    # 2. Urgent Threat Blocking: If opponent can win on their next move, block it
    opp_winning_moves = []
    for move in empty_cells:
        if is_winning_move(opp_set, dsu_opp, move):
            opp_winning_moves.append(move)

    if opp_winning_moves:
        # If multiple threats exist, pick the move that benefits our structure most
        best_block = max(
            opp_winning_moves,
            key=lambda m: (
                len([nb for nb in adj[m] if nb in me_set]),
                -dist_to_center(m)
            )
        )
        return best_block

    # 3. Heuristic Strategic Selection
    best_move = empty_cells[0]
    best_score = -float('inf')

    for move in empty_cells:
        score = 0.0
        me_nbrs = [nb for nb in adj[move] if nb in me_set]
        opp_nbrs = [nb for nb in adj[move] if nb in opp_set]

        # Corner and Edge membership values
        if move in corner_map:
            score += 180.0
        elif move in edge_map:
            score += 45.0

        # Component union potential
        seen_roots_me = set()
        merged_corners = (1 << corner_map[move]) if move in corner_map else 0
        merged_edges = (1 << edge_map[move]) if move in edge_map else 0

        for nb in me_nbrs:
            root = dsu_me.find(nb)
            if root not in seen_roots_me:
                seen_roots_me.add(root)
                merged_corners |= dsu_me.corners[root]
                merged_edges |= dsu_me.edges[root]

        # Multi-group connection bonus
        if len(seen_roots_me) >= 2:
            score += 250.0 * len(seen_roots_me)
        elif len(seen_roots_me) == 1:
            score += 60.0

        # Edge expansion towards a Fork
        num_edges = bin(merged_edges).count('1')
        if num_edges == 2:
            score += 450.0  # One edge away from winning fork
        elif num_edges == 1:
            score += 90.0

        # Corner expansion towards a Bridge
        num_corners = bin(merged_corners).count('1')
        if num_corners == 1:
            score += 150.0
            # Bonus for moving towards another corner
            if corners_list:
                min_c_dist = min(hex_distance(move, c) for c in corners_list if c not in corner_map or (1 << corner_map[c]) & merged_corners == 0)
                score += max(0, 10 - min_c_dist) * 20.0

        # Disrupting opponent components
        seen_roots_opp = set()
        opp_merged_edges = 0
        opp_merged_corners = 0
        for nb in opp_nbrs:
            root = dsu_opp.find(nb)
            if root not in seen_roots_opp:
                seen_roots_opp.add(root)
                opp_merged_edges |= dsu_opp.edges[root]
                opp_merged_corners |= dsu_opp.corners[root]

        # Block opponent multi-edge or multi-corner expansion
        if bin(opp_merged_edges).count('1') >= 2:
            score += 320.0
        if bin(opp_merged_corners).count('1') >= 1:
            score += 160.0
        if len(seen_roots_opp) >= 2:
            score += 180.0

        # Virtual Connection (2-Bridge) creation with friendly stones
        for nb in adj[move]:
            if nb not in me_set and nb not in opp_set:
                for second_nb in adj[nb]:
                    if second_nb in me_set and second_nb not in me_nbrs:
                        # Shared empty neighbor check
                        common_empty = sum(1 for shared in adj[move] if shared in adj[second_nb] and shared not in me_set and shared not in opp_set)
                        if common_empty >= 2:
                            score += 85.0

        # Centrality preference
        score += max(0, 8 - dist_to_center(move)) * 14.0

        if score > best_score:
            best_score = score
            best_move = move

    return (int(best_move[0]), int(best_move[1]))
