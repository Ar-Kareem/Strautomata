
from typing import List, Tuple, Set, Dict
from collections import deque

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], valid_mask) -> Tuple[int, int]:
    """
    Havannah policy for a 15×15 board (side length 8).
    Returns a legal (row, col) tuple.
    """
    N = 15
    my_set: Set[Tuple[int, int]] = set(me)
    opp_set: Set[Tuple[int, int]] = set(opp)

    # ----------------------------------------------------------------------
    # Board topology (odd‑q vertical layout)
    # ----------------------------------------------------------------------
    # The six corners of the Havannah hexagon
    CORNERS = {(0, 7), (0, 14), (7, 14), (14, 7), (14, 0), (7, 0)}

    # Pre‑compute neighbours and edge membership for every valid cell
    neighbors: Dict[Tuple[int, int], List[Tuple[int, int]]] = {}
    cell_edges: Dict[Tuple[int, int], List[int]] = {}
    valid_cells: List[Tuple[int, int]] = []

    for r in range(N):
        row_mask = valid_mask[r]
        for c in range(N):
            if not row_mask[c]:
                continue
            valid_cells.append((r, c))

            # Neighbour offsets depend on column parity (odd‑q layout)
            if c % 2 == 1:          # odd column → diagonals go up
                deltas = [(-1, 0), (1, 0), (0, -1), (-1, -1), (0, 1), (-1, 1)]
            else:                   # even column → diagonals go down
                deltas = [(-1, 0), (1, 0), (0, -1), (1, -1), (0, 1), (1, 1)]

            neigh = []
            for dr, dc in deltas:
                nr, nc = r + dr, c + dc
                if 0 <= nr < N and 0 <= nc < N and valid_mask[nr][nc]:
                    neigh.append((nr, nc))
            neighbors[(r, c)] = neigh

            # Edge IDs (0‑5). Corners are excluded from edges.
            edges = []
            if r == 0 and 7 < c < 14:               # top edge
                edges.append(0)
            if c == 14 and 0 < r < 7:               # right‑top edge
                edges.append(1)
            if r + c == 21 and 7 < r < 14:          # right‑bottom edge
                edges.append(2)
            if r == 14 and 0 < c < 7:               # bottom edge
                edges.append(3)
            if c == 0 and 7 < r < 14:               # left‑bottom edge
                edges.append(4)
            if r + c == 7 and 0 < r < 7:            # left‑top edge
                edges.append(5)
            cell_edges[(r, c)] = edges

    empty = [cell for cell in valid_cells if cell not in my_set and cell not in opp_set]
    if not empty:          # should never happen
        return valid_cells[0]

    # ----------------------------------------------------------------------
    # Helper: test whether a set of stones wins
    # ----------------------------------------------------------------------
    def is_winning(stones: Set[Tuple[int, int]]) -> bool:
        """Returns True if 'stones' contain a ring, bridge or fork."""
        visited: Set[Tuple[int, int]] = set()
        for start in stones:
            if start in visited:
                continue
            # explore one connected component
            stack = [start]
            visited.add(start)
            comp: List[Tuple[int, int]] = []
            while stack:
                cell = stack.pop()
                comp.append(cell)
                for nb in neighbors[cell]:
                    if nb in stones and nb not in visited:
                        visited.add(nb)
                        stack.append(nb)

            V = len(comp)
            # count internal edges (undirected)
            E = 0
            corner_cnt = 0
            edge_ids: Set[int] = set()
            for cell in comp:
                if cell in CORNERS:
                    corner_cnt += 1
                else:
                    edge_ids.update(cell_edges[cell])
                for nb in neighbors[cell]:
                    if nb in stones and cell < nb:   # count each edge once
                        E += 1

            # Bridge : two corners
            if corner_cnt >= 2:
                return True
            # Fork : three distinct edges (corners do not count)
            if len(edge_ids) >= 3:
                return True
            # Ring : a cycle exists  (E >= V  <=>  at least one cycle)
            if E >= V:
                return True
        return False

    # ----------------------------------------------------------------------
    # 1. Immediate winning move
    # ----------------------------------------------------------------------
    for move in empty:
        if is_winning(my_set | {move}):
            return move

    # ----------------------------------------------------------------------
    # 2. Block opponent's immediate win
    # ----------------------------------------------------------------------
    threats = [m for m in empty if is_winning(opp_set | {m})]
    if threats:
        # choose the blocking move with the best static score
        def static_score(m: Tuple[int, int]) -> int:
            r, c = m
            sc = 0
            # local adjacency
            for nb in neighbors[m]:
                if nb in my_set:
                    sc += 10
                elif nb in opp_set:
                    sc += 5
            # centrality
            sc += (14 - (abs(r - 7) + abs(c - 7))) * 2
            # edge/corner value
            if m in CORNERS:
                sc += 15
            else:
                sc += len(cell_edges[m]) * 5
            return sc

        best = threats[0]
        best_sc = static_score(best)
        for m in threats[1:]:
            s = static_score(m)
            if s > best_sc:
                best_sc = s
                best = m
        return best

    # ----------------------------------------------------------------------
    # 3. Heuristic evaluation for all moves
    # ----------------------------------------------------------------------
    def evaluate(move: Tuple[int, int]) -> int:
        r, c = move
        score = 0

        # local connectivity
        my_nbr = opp_nbr = 0
        for nb in neighbors[move]:
            if nb in my_set:
                my_nbr += 1
            elif nb in opp_set:
                opp_nbr += 1
        score += my_nbr * 10 + opp_nbr * 5

        # positional: prefer centre
        dist_center = abs(r - 7) + abs(c - 7)
        score += (14 - dist_center) * 3

        # edge / corner potential
        if move in CORNERS:
            score += 20
        else:
            score += len(cell_edges[move]) * 8

        # analyse the group that would be created by this move
        visited: Set[Tuple[int, int]] = set()
        stack = [move]
        visited.add(move)
        comp_edges: Set[int] = set()
        comp_corners: Set[Tuple[int, int]] = set()
        while stack:
            cell = stack.pop()
            if cell in CORNERS:
                comp_corners.add(cell)
            else:
                comp_edges.update(cell_edges[cell])
            for nb in neighbors[cell]:
                if nb in my_set and nb not in visited:
                    visited.add(nb)
                    stack.append(nb)

        score += len(comp_edges) * 15
        score += len(comp_corners) * 30
        if len(comp_edges) >= 2:
            score += 50          # threatening a fork
        if len(comp_corners) >= 2:
            score += 100         # threatening a bridge

        # deterministic tie‑breaker
        score += (r * 31 + c) % 13
        return score

    best_move = empty[0]
    best_val = -10**9
    for move in empty:
        val = evaluate(move)
        if val > best_val:
            best_val = val
            best_move = move
    return best_move
