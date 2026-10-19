import random
from typing import List, Tuple, Dict, Set, Optional

# Battleship AI policy for a 10x10 board.
# Ships lengths: 5, 4, 3, 3, 2
# Observations:
#  0 → unknown
# -1 → miss
#  1 → hit

# We use a closure to maintain persistent targeting state across calls.


def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Returns the next shot (row, col) on a 10x10 board.
    board[r][c] is 0 (unknown), -1 (miss), or 1 (hit).
    """
    return _PolicyHolder.get().next_shot(board)


class _PolicyHolder:
    _instance = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = _BattleshipPolicy()
        return cls._instance


class _BattleshipPolicy:
    def __init__(self):
        self.size = 10
        self.ship_lengths = [5, 4, 3, 3, 2]
        self.rng = random.Random()

        # Persistent state to carry across turns
        self._cluster_map: Dict[Tuple[int, int], int] = {}  # cell -> cluster id
        self._clusters: Dict[int, Dict] = {}  # cluster id -> cluster data
        self._next_cluster_id: int = 1
        self._last_shot: Optional[Tuple[int, int]] = None

    def next_shot(self, board: List[List[int]]) -> Tuple[int, int]:
        # Initialize neighbor maps for hits and misses from current board
        hit_set = set()
        miss_set = set()
        for r in range(self.size):
            for c in range(self.size):
                v = board[r][c]
                if v == 1:
                    hit_set.add((r, c))
                elif v == -1:
                    miss_set.add((r, c))

        # Update clusters based on new hits compared to previous frame
        self._update_clusters(board, hit_set)

        # Try targeted shots from clusters first (shooting ends / gaps)
        if self._clusters:
            target = self._pick_cluster_shot()
            if target is not None:
                self._last_shot = target
                return target

        # Otherwise, fall back to probability-based hunting
        target = self._hunt_shot(miss_set)
        self._last_shot = target
        return target

    def _update_clusters(self, board: List[List[int]], hit_set: Set[Tuple[int, int]]):
        """
        Discover and maintain hit clusters (orthogonally adjacent hits).
        Each cluster records:
          - id, orientation ('H', 'V', or None), cells sorted, min/max per axis,
          - targets: candidate cells to try (ends / gaps), with priorities.
        """
        # Remove any clusters that are now fully contained in a full ship of some length.
        # We simply clear clusters when a ship is sunk (in this simplistic model we rely on
        # subsequent hunting to finish; however, we still clear clusters once they seem complete).
        # To detect completion, we check if every cell along the line between min and max on a known orientation
        # is already hit and matches a valid ship length.
        completed_ids = []
        for cid, cl in self._clusters.items():
            cells = set(cl["cells"])
            # If all cells in this cluster are hit and orientation known, we mark complete
            if cells.issubset(hit_set) and cl["orientation"] in ("H", "V"):
                completed_ids.append(cid)
        for cid in completed_ids:
            # Remove cluster and its cell mappings
            for cell in self._clusters[cid]["cells"]:
                self._cluster_map.pop(cell, None)
            self._clusters.pop(cid, None)

        # Discover new hits that are not yet in any cluster
        new_cells = []
        for cell in hit_set:
            if cell not in self._cluster_map:
                new_cells.append(cell)

        # If we have new isolated hits, create singleton clusters
        for cell in new_cells:
            # Create cluster
            cid = self._next_cluster_id
            self._next_cluster_id += 1
            self._clusters[cid] = {
                "id": cid,
                "orientation": None,
                "cells": [cell],
                "targets": {},  # cell -> priority
            }
            self._cluster_map[cell] = cid

        # Attempt to merge adjacent clusters / assign orientation when two or more cells are aligned
        self._merge_and_resolve_orientations()

        # For each cluster, refresh its target list (ends and gaps) with priorities
        for cl in self._clusters.values():
            self._refresh_cluster_targets(cl, board)

    def _merge_and_resolve_orientations(self):
        """
        Merge clusters if they are orthogonally adjacent and set orientation if all cells share a row or column.
        """
        changed = True
        # Loop until no more merges possible
        while changed:
            changed = False
            # Gather cluster ids that have at least one cell with a neighbor in another cluster
            to_merge: Dict[int, Set[int]] = {cid: set() for cid in self._clusters.keys()}
            for cid, cl in self._clusters.items():
                for (r, c) in cl["cells"]:
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < self.size and 0 <= nc < self.size:
                            neighbor = (nr, nc)
                            if neighbor in self._cluster_map:
                                nid = self._cluster_map[neighbor]
                                if nid != cid:
                                    to_merge[cid].add(nid)

            # Perform merges
            for cid, neighbors in list(to_merge.items()):
                if cid not in self._clusters:
                    continue  # Already merged away
                for nid in list(neighbors):
                    if nid not in self._clusters:
                        continue
                    # Merge nid into cid
                    self._clusters[cid]["cells"].extend(self._clusters[nid]["cells"])
                    for cell in self._clusters[nid]["cells"]:
                        self._cluster_map[cell] = cid
                    self._clusters.pop(nid)
                    changed = True

            # After merges, try to set orientation for each cluster
            for cl in self._clusters.values():
                rows = {r for (r, _) in cl["cells"]}
                cols = {c for (_, c) in cl["cells"]}
                if len(rows) == 1:
                    cl["orientation"] = "H"
                elif len(cols) == 1:
                    cl["orientation"] = "V"
                else:
                    cl["orientation"] = None

    def _refresh_cluster_targets(self, cl: Dict, board: List[List[int]]):
        """
        Update target cells for a cluster: ends and gaps.
        Priority:
          2 → clear end expansion (two or more aligned hits)
          1 → single isolated hit → check orthogonal neighbors first
        """
        cells = cl["cells"]
        targets: Dict[Tuple[int, int], int] = {}
        board_vals = board

        if cl["orientation"] in ("H", "V"):
            # Determine min/max along the line
            if cl["orientation"] == "H":
                row = cells[0][0]
                cols = [c for (_, c) in cells]
                minc, maxc = min(cols), max(cols)
                # Try to expand both ends along row
                for c in (minc - 1, maxc + 1):
                    if 0 <= c < self.size:
                        r = row
                        if board_vals[r][c] == 0:
                            targets[(r, c)] = max(targets.get((r, c), 0), 2)
                # Fill gaps if there are missing cells between minc and maxc
                for c in range(minc, maxc + 1):
                    if board_vals[row][c] == 0:
                        targets[(row, c)] = max(targets.get((row, c), 0), 2)
            else:
                col = cells[0][1]
                rows = [r for (r, _) in cells]
                minr, maxr = min(rows), max(rows)
                # Expand ends
                for r in (minr - 1, maxr + 1):
                    if 0 <= r < self.size:
                        c = col
                        if board_vals[r][c] == 0:
                            targets[(r, c)] = max(targets.get((r, c), 0), 2)
                # Fill gaps
                for r in range(minr, maxr + 1):
                    if board_vals[r][col] == 0:
                        targets[(r, col)] = max(targets.get((r, col), 0), 2)
        else:
            # Orientation unknown: try orthogonal neighbors (priority 1)
            for (r, c) in cells:
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.size and 0 <= nc < self.size:
                        if board_vals[nr][nc] == 0:
                            targets[(nr, nc)] = max(targets.get((nr, nc), 0), 1)
        cl["targets"] = targets

    def _pick_cluster_shot(self) -> Optional[Tuple[int, int]]:
        """
        Pick the highest-priority target among all clusters.
        If multiple targets share the same priority, choose the one closest to any hit (parsimony).
        """
        candidates = []
        for cl in self._clusters.values():
            for cell, pr in cl["targets"].items():
                candidates.append((cell, pr))
        if not candidates:
            return None
        # Pick highest priority
        max_pr = max(pr for (_, pr) in candidates)
        high = [cell for (cell, pr) in candidates if pr == max_pr]
        # Among high-priority, prefer those adjacent to existing hits (distance 1), else any
        best = None
        best_key = None
        # Precompute all hit cells from clusters for distance heuristic
        hit_cells: Set[Tuple[int, int]] = set()
        for cl in self._clusters.values():
            hit_cells.update(cl["cells"])

        for cell in high:
            d = self._min_manhattan(cell, hit_cells)
            key = (d, self.rng.random())
            if best is None or key < best_key:
                best = cell
                best_key = key
        return best

    def _min_manhattan(self, cell: Tuple[int, int], others: Set[Tuple[int, int]]) -> int:
        if not others:
            return 0
        r, c = cell
        return min(abs(r - rr) + abs(c - cc) for (rr, cc) in others)

    def _hunt_shot(self, miss_set: Set[Tuple[int, int]]) -> Tuple[int, int]:
        """
        Compute a probability map over unknown cells by enumerating all valid ship placements
        that do not overlap any known misses and are consistent with known hits (hits must be covered).
        Choose the cell with maximum coverage count; break ties by checkerboard preference.
        """
        size = self.size
        ship_lengths = self.ship_lengths
        unknown_mask = [[board[r][c] == 0 for c in range(size)] for r in range(size)]
        # Build list of unknown cells
        unknown_cells = [(r, c) for r in range(size) for c in range(size) if unknown_mask[r][c]]
        if not unknown_cells:
            # Fallback (shouldn't happen unless board fully shot)
            return (0, 0)

        # Quick target: if any unknown cell is adjacent (orth) to a hit, try that first (search around hits)
        neighbor_to_hits = self._neighbors_of_hits()
        neighbors = [cell for cell in unknown_cells if cell in neighbor_to_hits]
        if neighbors:
            # Prefer the neighbor with the most adjacent hits, then checkerboard tie-break
            best = None
            best_score = -1
            best_key = None
            for cell in neighbors:
                score = neighbor_to_hits[cell]
                key = (-score, self._checkerboard_key(cell), self.rng.random())
                if best is None or key < best_key:
                    best = cell
                    best_score = score
                    best_key = key
            if best is not None:
                return best

        # Otherwise, compute probability map by enumerating placements
        hit_count = [[0 for _ in range(size)] for _ in range(size)]
        placements = 0
        # Known hits must be covered, so if we have any, we can restrict placements to those covering them.
        # Gather coordinates of hits
        hit_coords: List[Tuple[int, int]] = []
        for r in range(size):
            for c in range(size):
                if not unknown_mask[r][c]:
                    # not unknown => either miss (-1) or hit (1)
                    # If it's a hit, we add to hit_coords
                    pass
        # To get hit coords, we can derive from unknown mask and miss_set:
        # All hits are cells not in unknown and not in miss_set.
        # Construct a hits set for filtering placements.
        hit_set_for_filter = set()
        for r in range(size):
            for c in range(size):
                if not unknown_mask[r][c]:
                    if (r, c) not in miss_set:
                        hit_set_for_filter.add((r, c))

        # If there are hits, we can restrict enumeration to placements covering at least one hit to save time.
        cover_a_hit = len(hit_set_for_filter) > 0

        # Precompute valid placements
        valid_placements: List[Tuple[int, int, int]] = []  # (r, c, length) with orientation H
        # Horizontal
        for r in range(size):
            for c in range(size - 4):  # max length 5
                # Check segment [c..c+len-1] for unknown or hit occupancy
                for L in ship_lengths:
                    if c + L > size:
                        continue
                    # If any miss in this segment, invalid
                    ok = True
                    for cc in range(c, c + L):
                        if (r, cc) in miss_set:
                            ok = False
                            break
                    if not ok:
                        continue
                    # If cover-a-hit mode and no hit in this segment, skip
                    if cover_a_hit:
                        has_hit = False
                        for cc in range(c, c + L):
                            if (r, cc) in hit_set_for_filter:
                                has_hit = True
                                break
                        if not has_hit:
                            continue
                    valid_placements.append((r, c, L))
        # Vertical
        for r in range(size - 4):
            for c in range(size):
                for L in ship_lengths:
                    if r + L > size:
                        continue
                    ok = True
                    for rr in range(r, r + L):
                        if (rr, c) in miss_set:
                            ok = False
                            break
                    if not ok:
                        continue
                    if cover_a_hit:
                        has_hit = False
                        for rr in range(r, r + L):
                            if (rr, c) in hit_set_for_filter:
                                has_hit = True
                                break
                        if not has_hit:
                            continue
                    valid_placements.append((r, c, L))

        # If enumeration failed due to constraints (e.g., cover-a-hit too strict), relax and re-enumerate without cover-a-hit
        if not valid_placements:
            cover_a_hit = False
            # Re-enumerate without hit-cover constraint
            for r in range(size):
                for c in range(size - 4):
                    for L in ship_lengths:
                        if c + L > size:
                            continue
                        ok = True
                        for cc in range(c, c + L):
                            if (r, cc) in miss_set:
                                ok = False
                                break
                        if not ok:
                            continue
                        valid_placements.append((r, c, L))
            for r in range(size - 4):
                for c in range(size):
                    for L in ship_lengths:
                        if r + L > size:
                            continue
                        ok = True
                        for rr in range(r, r + L):
                            if (rr, c) in miss_set:
                                ok = False
                                break
                        if not ok:
                            continue
                        valid_placements.append((r, c, L))

        # Aggregate hit counts
        placements = 0
        for (r, c, L) in valid_placements:
            placements += 1
            # Horizontal: (r, c..c+L-1)
            if c + L <= size:
                for cc in range(c, c + L):
                    if unknown_mask[r][cc]:
                        hit_count[r][cc] += 1
            # Vertical: (r..r+L-1, c)
            if r + L <= size:
                for rr in range(r, r + L):
                    if unknown_mask[rr][c]:
                        hit_count[rr][c] += 1

        # Select the unknown cell with maximum hit_count; use checkerboard to break ties
        best_cell = None
        best_score = -1
        best_key = None
        for (r, c) in unknown_cells:
            score = hit_count[r][c]
            key = (-score, self._checkerboard_key((r, c)), self.rng.random())
            if best_cell is None or key < best_key:
                best_cell = (r, c)
                best_score = score
                best_key = key

        # If probability map is flat (e.g., not enough info), fallback to a checkerboard scan for efficiency
        if best_score <= 0:
            return self._checkerboard_pick(unknown_cells)

        return best_cell

    def _neighbors_of_hits(self) -> Dict[Tuple[int, int], int]:
        """
        Return a dict mapping unknown neighbor cells (orth adjacency) of hits to
        the number of adjacent hit cells they have (used for local search).
        """
        result: Dict[Tuple[int, int], int] = {}
        # Build hit set from clusters
        hit_cells: Set[Tuple[int, int]] = set()
        for cl in self._clusters.values():
            for cell in cl["cells"]:
                hit_cells.add(cell)
        if not hit_cells:
            return result
        for (r, c) in hit_cells:
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.size and 0 <= nc < self.size:
                    # We only care about unknown cells; the caller will filter by unknown cells
                    result[(nr, nc)] = result.get((nr, nc), 0) + 1
        return result

    def _checkerboard_key(self, cell: Tuple[int, int]) -> int:
        """
        Checkerboard parity for tie-breaking: prefer black squares (0) then white (1).
        """
        r, c = cell
        return (r + c) % 2

    def _checkerboard_pick(self, unknown_cells: List[Tuple[int, int]]) -> Tuple[int, int]:
        """
        If probability map is uninformative, choose among unknown cells by checkerboard preference and randomness.
        """
        best = None
        best_key = None
        for cell in unknown_cells:
            key = (self._checkerboard_key(cell), self.rng.random())
            if best is None or key < best_key:
                best = cell
                best_key = key
        return best if best is not None else unknown_cells[0]