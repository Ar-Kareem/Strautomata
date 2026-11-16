
import random
from typing import List, Tuple, Dict

# -------------------------------------------------
# Helpers for board geometry
# -------------------------------------------------
BOARD_SIZE = 10

def in_bounds(r: int, c: int) -> bool:
    return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE

def is_unknown(board: List[List[int]], r: int, c: int) -> bool:
    return board[r][c] == 0

def is_miss(board: List[List[int]], r: int, c: int) -> bool:
    return board[r][c] == -1

def is_hit(board: List[List[int]], r: int, c: int) -> bool:
    return board[r][c] == 1

def neighbours(r: int, c: int) -> List[Tuple[int, int]]:
    return [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]

# -------------------------------------------------
# Cluster detection and classification
# -------------------------------------------------
def find_clusters(board: List[List[int]]):
    """Returns a list of clusters, each a dict with keys:
       - 'id'   : integer identifier
       - 'cells': list of (r,c) belonging to the cluster
       - 'orientation': 'H' (horizontal), 'V' (vertical) or 'U' (unknown, single‑cell)
       Also returns a dict mapping each hit cell to its cluster id.
    """
    visited = [[False] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    clusters = []
    cell_to_id = {}
    cid = 0
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if is_hit(board, r, c) and not visited[r][c]:
                # BFS to collect the whole cluster
                stack = [(r, c)]
                visited[r][c] = True
                cells = []
                while stack:
                    cr, cc = stack.pop()
                    cells.append((cr, cc))
                    cell_to_id[(cr, cc)] = cid
                    for nr, nc in neighbours(cr, cc):
                        if in_bounds(nr, nc) and not visited[nr][nc] and is_hit(board, nr, nc):
                            visited[nr][nc] = True
                            stack.append((nr, nc))
                # Determine orientation
                if len(cells) == 1:
                    orient = 'U'
                else:
                    # all rows equal -> horizontal
                    if all(x[0] == cells[0][0] for x in cells):
                        orient = 'H'
                    else:
                        orient = 'V'
                clusters.append({
                    'id': cid,
                    'cells': cells,
                    'orientation': orient,
                    'cell_set': set(cells)
                })
                cid += 1
    return clusters, cell_to_id

def cluster_is_unsunk(cluster: Dict, board: List[List[int]]) -> bool:
    """True if the cluster can still be extended (there is an adjacent unknown cell)."""
    orient = cluster['orientation']
    cells = cluster['cells']
    if orient == 'H':
        r = cells[0][0]
        cols = sorted(c for r, c in cells)
        left = cols[0]
        right = cols[-1]
        if in_bounds(r, left - 1) and is_unknown(board, r, left - 1):
            return True
        if in_bounds(r, right + 1) and is_unknown(board, r, right + 1):
            return True
        return False
    elif orient == 'V':
        c = cells[0][1]
        rows = sorted(r for r, c in cells)
        top = rows[0]
        bot = rows[-1]
        if in_bounds(top - 1, c) and is_unknown(board, top - 1, c):
            return True
        if in_bounds(bot + 1, c) and is_unknown(board, bot + 1, c):
            return True
        return False
    else:                           # single cell – unknown orientation
        r, c = cells[0]
        for nr, nc in neighbours(r, c):
            if in_bounds(nr, nc) and is_unknown(board, nr, nc):
                return True
        return False

def cluster_is_sunk(cluster: Dict, board: List[List[int]]) -> bool:
    """True iff both ends of the cluster are blocked by misses or board edges."""
    orient = cluster['orientation']
    cells = cluster['cells']
    if orient == 'H':
        r = cells[0][0]
        cols = sorted(c for r, c in cells)
        left = cols[0]
        right = cols[-1]
        left_blocked = not in_bounds(r, left - 1) or is_miss(board, r, left - 1)
        right_blocked = not in_bounds(r, right + 1) or is_miss(board, r, right + 1)
        return left_blocked and right_blocked
    elif orient == 'V':
        c = cells[0][1]
        rows = sorted(r for r, c in cells)
        top = rows[0]
        bot = rows[-1]
        top_blocked = not in_bounds(top - 1, c) or is_miss(board, top - 1, c)
        bot_blocked = not in_bounds(bot + 1, c) or is_miss(board, bot + 1, c)
        return top_blocked and bot_blocked
    else:  # single cell – it can only be "sunk" if all four neighbours are already misses
        r, c = cells[0]
        for nr, nc in neighbours(r, c):
            if in_bounds(nr, nc) and not is_miss(board, nr, nc):
                return False
        return True

# -------------------------------------------------
# Remaining ship inventory
# -------------------------------------------------
def classify_clusters(clusters: List[Dict], board: List[List[int]]):
    """Return (remaining_lengths, unsunk_clusters, sunk_clusters)."""
    # Standard fleet (one 5, one 4, two 3s, one 2)
    remaining = {5: 1, 4: 1, 3: 2, 2: 1}
    unsunk = []
    sunk = []
    for cl in clusters:
        if cluster_is_sunk(cl, board):
            L = len(cl['cells'])
            if remaining.get(L, 0) > 0:
                remaining[L] -= 1
            sunk.append(cl)
        elif cluster_is_unsunk(cl, board):
            unsunk.append(cl)
        else:
            # Should not happen – treat as unsunk to be safe
            unsunk.append(cl)
    return remaining, unsunk, sunk

# -------------------------------------------------
# Candidate cells for a live cluster
# -------------------------------------------------
def candidate_cells_for_unsunk(cluster: Dict, board: List[List[int]]) -> List[Tuple[int, int]]:
    """List of still‑unknown cells that could extend this cluster."""
    orient = cluster['orientation']
    cells = cluster['cells']
    cand = []
    if orient == 'H':
        r = cells[0][0]
        cols = sorted(c for r, c in cells)
        left = cols[0]
        right = cols[-1]
        if in_bounds(r, left - 1) and is_unknown(board, r, left - 1):
            cand.append((r, left - 1))
        if in_bounds(r, right + 1) and is_unknown(board, r, right + 1):
            cand.append((r, right + 1))
    elif orient == 'V':
        c = cells[0][1]
        rows = sorted(r for r, c in cells)
        top = rows[0]
        bot = rows[-1]
        if in_bounds(top - 1, c) and is_unknown(board, top - 1, c):
            cand.append((top - 1, c))
        if in_bounds(bot + 1, c) and is_unknown(board, bot + 1, c):
            cand.append((bot + 1, c))
    else:  # unknown orientation – single cell
        r, c = cells[0]
        for nr, nc in neighbours(r, c):
            if in_bounds(nr, nc) and is_unknown(board, nr, nc):
                cand.append((nr, nc))
    return cand

# -------------------------------------------------
# Probability map for the hunting phase
# -------------------------------------------------
def build_probability_map(board: List[List[int]],
                          remaining: Dict[int, int],
                          unsunk: List[Dict],
                          sunk: List[Dict]) -> Dict[Tuple[int, int], int]:
    """Score each unknown cell by the number of valid placements that cover it."""
    prob: Dict[Tuple[int, int], int] = {}

    # pre‑compute sets for fast intersection tests
    sunk_sets = [cl['cell_set'] for cl in sunk]

    for length, count in remaining.items():
        if count == 0:
            continue
        # Horizontal placements
        for r in range(BOARD_SIZE):
            for c_start in range(0, BOARD_SIZE - length + 1):
                placement = [(r, c_start + d) for d in range(length)]
                placement_set = set(placement)

                # quick miss test
                if any(is_miss(board, rr, cc) for rr, cc in placement):
                    continue

                # cannot intersect any sunk cluster
                if any(placement_set & ss for ss in sunk_sets):
                    continue

                # at most one unsunk cluster may intersect, and only if it is fully contained
                intersected_unsunk = None
                valid = True
                for ucl in unsunk:
                    if placement_set & ucl['cell_set']:
                        if intersected_unsunk is not None:  # two clusters – illegal
                            valid = False
                            break
                        intersected_unsunk = ucl
                        # must contain the whole cluster
                        if not ucl['cell_set'].issubset(placement_set):
                            valid = False
                            break
                        # orientation must match, unless cluster orientation unknown
                        if ucl['orientation'] not in ('U', 'H'):
                            valid = False
                            break
                if not valid:
                    continue

                # If we intersect a horizontal unsunk cluster, the placement orientation must be H.
                if intersected_unsunk and intersected_unsunk['orientation'] == 'H':
                    # allowed (we are already H)
                    pass
                # if no intersection or only an unknown cluster, placement is fine.

                # Add score for every *unknown* cell in this placement
                for rr, cc in placement:
                    if is_unknown(board, rr, cc):
                        prob[(rr, cc)] = prob.get((rr, cc), 0) + 1

        # Vertical placements
        for c in range(BOARD_SIZE):
            for r_start in range(0, BOARD_SIZE - length + 1):
                placement = [(r_start + d, c) for d in range(length)]
                placement_set = set(placement)

                if any(is_miss(board, rr, cc) for rr, cc in placement):
                    continue

                if any(placement_set & ss for ss in sunk_sets):
                    continue

                intersected_unsunk = None
                valid = True
                for ucl in unsunk:
                    if placement_set & ucl['cell_set']:
                        if intersected_unsunk is not None:
                            valid = False
                            break
                        intersected_unsunk = ucl
                        if not ucl['cell_set'].issubset(placement_set):
                            valid = False
                            break
                        if ucl['orientation'] not in ('U', 'V'):
                            valid = False
                            break
                if not valid:
                    continue

                if intersected_unsunk and intersected_unsunk['orientation'] == 'V':
                    # allowed (we are V)
                    pass

                for rr, cc in placement:
                    if is_unknown(board, rr, cc):
                        prob[(rr, cc)] = prob.get((rr, cc), 0) + 1

    return prob

# -------------------------------------------------
# Choose the best hunting cell
# -------------------------------------------------
def select_best_hunt(board: List[List[int]], prob: Dict[Tuple[int, int], int],
                     parity: int = 0) -> Tuple[int, int]:
    """Pick an unknown cell with highest probability, preferring the given parity."""
    unknown = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE)
               if is_unknown(board, r, c)]
    if not unknown:
        # Emergency fallback – should never happen in a real game
        return (0, 0)

    # Prefer cells of the wanted parity, but fall back to all cells if none are left.
    parity_cells = [cell for cell in unknown if (cell[0] + cell[1]) % 2 == parity]
    candidates = parity_cells if parity_cells else unknown

    best_score = -1
    best_cells = []
    for cell in candidates:
        score = prob.get(cell, 0)
        if score > best_score:
            best_score = score
            best_cells = [cell]
        elif score == best_score:
            best_cells.append(cell)

    # If for some reason no cell got a positive score, just pick a random unknown cell.
    if not best_cells:
        best_cells = unknown

    return random.choice(best_cells)

# -------------------------------------------------
# Main policy
# -------------------------------------------------
def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Return the next shot for a 10×10 Battleship board.
    Board values: 0 = unknown, -1 = miss, 1 = hit.
    """
    # 1. Discover all hit clusters
    clusters, cell_to_id = find_clusters(board)

    # 2. Classify clusters into unsunk (still alive) and sunk,
    #    and obtain the remaining ship inventory.
    remaining, unsunk, sunk = classify_clusters(clusters, board)

    # 3. If we have a live cluster -> finish it
    if unsunk:
        # Choose the smallest live cluster (shortest ships first)
        # Sort by length, then prefer clusters whose orientation is already known.
        scored = []
        for cl in unsunk:
            length = len(cl['cells'])
            # known orientation has priority (rank 0 vs 1 for unknown)
            rank = 0 if cl['orientation'] != 'U' else 1
            scored.append((length, rank, cl))
        scored.sort(key=lambda x: (x[0], x[1]))
        target_cluster = scored[0][2]

        # List cells that could extend this cluster
        candidates = candidate_cells_for_unsunk(target_cluster, board)
        # Safety: if no candidate is available (very rare), fall back to hunting below.
        if candidates:
            return random.choice(candidates)

    # 4. No live cluster -> hunting phase
    # Build a probability map for all cells that are still unknown.
    prob = build_probability_map(board, remaining, unsunk, sunk)

    # Choose the highest‑probability cell, preferring even (row+col)%2 cells.
    return select_best_hunt(board, prob, parity=0)
