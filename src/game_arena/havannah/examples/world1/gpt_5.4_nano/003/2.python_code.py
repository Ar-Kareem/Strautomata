
import random
from collections import deque

# Havannah 15x15 policy
# Representation: caller uses axial-like neighbor pattern mapped to (r,c):
# Using the standard rhombus-to-array mapping where each cell (r,c) has 6 neighbors:
#   (r-1,c), (r+1,c), (r,c-1), (r,c+1), (r-1,c+1), (r+1,c-1)
#
# We use board size from valid_mask.

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    N = len(valid_mask)

    me_set = set(me)
    opp_set = set(opp)
    occ = me_set | opp_set

    # --- helpers ---
    def inb(r, c):
        return 0 <= r < N and 0 <= c < N and valid_mask[r][c]

    # neighbors in the rhombus-mapped hex grid
    NEI = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1)]
    def neighbors(r, c):
        for dr, dc in NEI:
            rr, cc = r + dr, c + dc
            if 0 <= rr < N and 0 <= cc < N and valid_mask[rr][cc]:
                yield rr, cc

    # Determine board corner / edge sets in (r,c) for "corner cells" and "edges" of the 6 sides.
    # For rhombus size N, corner coordinates are:
    #   (0,0), (0,N-1), (N-1,N-1), (N-1,0) are outer corners in array, but Havannah has 6 corners.
    # Because valid_mask may represent a true hex board embedded in NxN, we derive corners as valid cells
    # with maximal distance from center along directions? Too heavy.
    # Instead: we use common mapping for Havannah-on-rhombus with axial coords:
    # Using array coords (r,c) where axial q=c and r=r (dual), the 6 corners for a hex of side N-1 are:
    #   A: (0,0)
    #   B: (0,N-1)
    #   C: (N-1, N-1)
    #   D: (N-1,0)
    # plus two others depend on valid_mask cropping. So we compute "extreme" points by direction scanning.
    #
    # We define 6 border directions as:
    #   dir0: minimize (r+c)   -> corner
    #   dir1: maximize (r)     -> corner
    #   dir2: minimize (r)     -> corner
    #   dir3: maximize (c)     -> corner
    #   dir4: minimize (c)     -> corner
    #   dir5: maximize (r-c)   -> corner
    #
    # Then corners are the set of valid cells achieving extreme along each of the three independent axes
    # converted into 6 sides; we approximate and then use those as "corner candidates".
    coords_valid = [(r, c) for r in range(N) for c in range(N) if valid_mask[r][c]]
    if not coords_valid:
        return (0, 0)

    # center for tie-breaking
    cr = sum(r for r, c in coords_valid) / len(coords_valid)
    cc = sum(c for r, c in coords_valid) / len(coords_valid)

    def pick_extreme(key_fn, want_max):
        best = None
        best_val = None
        for r, c in coords_valid:
            v = key_fn(r, c)
            if best is None:
                best = (r, c); best_val = v
            else:
                if want_max:
                    if v > best_val or (v == best_val and (r-cr)**2+(c-cc)**2 < (best[0]-cr)**2+(best[1]-cc)**2):
                        best = (r, c); best_val = v
                else:
                    if v < best_val or (v == best_val and (r-cr)**2+(c-cc)**2 < (best[0]-cr)**2+(best[1]-cc)**2):
                        best = (r, c); best_val = v
        return best

    # approximate 6 corners from extremes
    corner_cells = set()
    # three axes, each gives two extremes -> 6 corners
    corner_cells.add(pick_extreme(lambda r, c: r + c, False))
    corner_cells.add(pick_extreme(lambda r, c: r + c, True))
    corner_cells.add(pick_extreme(lambda r, c: r - c, False))
    corner_cells.add(pick_extreme(lambda r, c: r - c, True))
    corner_cells.add(pick_extreme(lambda r, c: r, False))
    corner_cells.add(pick_extreme(lambda r, c: r, True))
    # Some duplicates may occur on small boards/crops
    corner_cells = list(corner_cells)

    # edge sides: for forks we need 3 edges among 6.
    # We approximate each edge as cells that achieve extreme on one side direction.
    # Use inequality-based boundary: mark side membership by which extreme axis the cell is close to.
    min_r, max_r = min(r for r, c in coords_valid), max(r for r, c in coords_valid)
    min_c, max_c = min(c for r, c in coords_valid), max(c for r, c in coords_valid)
    min_sum, max_sum = min(r+c for r, c in coords_valid), max(r+c for r, c in coords_valid)
    min_diff, max_diff = min(r-c for r, c in coords_valid), max(r-c for r, c in coords_valid)

    # Six sides: correspond to r=min, r=max, c=min, c=max, r+c=min, r+c=max (covers 6)
    # (This may differ from exact Havannah side definition but works well with symmetric crops.)
    def side_ids(r, c):
        ids = []
        if r == min_r: ids.append(0)
        if r == max_r: ids.append(1)
        if c == min_c: ids.append(2)
        if c == max_c: ids.append(3)
        if r + c == min_sum: ids.append(4)
        if r + c == max_sum: ids.append(5)
        return ids

    def is_corner(cell):
        return cell in set(corner_cells)

    # Union-find for groups after hypothetical move
    def compute_components(stones_set):
        visited = set()
        comps = []
        for s in stones_set:
            if s in visited:
                continue
            q = deque([s])
            visited.add(s)
            comp = []
            while q:
                r, c = q.popleft()
                comp.append((r, c))
                for rr, cc in neighbors(r, c):
                    if (rr, cc) in stones_set and (rr, cc) not in visited:
                        visited.add((rr, cc))
                        q.append((rr, cc))
            comps.append(comp)
        return comps

    def has_bridge(stones_set):
        # Bridge: connect any two of six corner cells.
        comps = compute_components(stones_set)
        corner_set = set(corner_cells)
        for comp in comps:
            touched = set(cell for cell in comp if cell in corner_set)
            if len(touched) >= 2:
                return True
        return False

    def has_fork(stones_set):
        # Fork: connect any three edges (corner points are not considered part of an edge)
        comps = compute_components(stones_set)
        for comp in comps:
            sides = set()
            for r, c in comp:
                if is_corner((r, c)):
                    continue
                for sid in side_ids(r, c):
                    sides.add(sid)
            if len(sides) >= 3:
                return True
        return False

    # Ring detection:
    # A ring exists if a connected component encloses at least one cell/empty region.
    # Practical approach on hex-on-grid:
    # - Build "our stones" component(s).
    # - For each component, treat its stones as walls and check if there exists a region of valid cells not reachable
    #   from the outside through non-stone cells. If yes -> ring for that component.
    #
    # We do this with flood-fill of free cells in the full board graph induced by valid cells, while blocking component stones.
    def has_ring(stones_set):
        comps = compute_components(stones_set)
        if not comps:
            return False

        # Precompute all valid cells set
        valid_set = set(coords_valid)

        # For each component, flood from "outside": outside means any free cell that can reach border of the valid map
        # through free cells. We'll detect reachability to any boundary cell.
        boundary_cells = set()
        for r, c in coords_valid:
            if r == min_r or r == max_r or c == min_c or c == max_c or r+c == min_sum or r+c == max_sum:
                boundary_cells.add((r, c))

        # Graph neighbors already respects valid_mask.
        for comp in comps:
            comp_set = set(comp)
            # If component is too small, it can't ring (heuristic)
            if len(comp_set) < 6:
                continue

            free = valid_set - comp_set
            # outside-reachable from boundary through free cells
            q = deque()
            seen = set()
            for cell in boundary_cells:
                if cell in free and cell not in seen:
                    seen.add(cell)
                    q.append(cell)
            while q:
                r, c = q.popleft()
                for rr, cc in neighbors(r, c):
                    if (rr, cc) in free and (rr, cc) not in seen:
                        seen.add((rr, cc))
                        q.append((rr, cc))
            # If any free cell is not reachable from outside, it's enclosed.
            # Note: This can detect "holes" enclosed by the component.
            if len(seen) != len(free):
                # There exists enclosed region (maybe multiple cells/empty). That is a ring.
                return True
        return False

    def is_win_after(move, player_set):
        # player_set already includes our stones; move is to be added
        test_set = set(player_set)
        test_set.add(move)
        # Check ring/bridge/fork
        return has_ring(test_set) or has_bridge(test_set) or has_fork(test_set)

    # --- candidate generation ---
    def score_cell_basic(r, c):
        # centrality + connectivity
        # centrality: nearer to center better
        d = (r - cr) ** 2 + (c - cc) ** 2
        # connectivity: count occupied neighbors
        conn = sum(1 for rr, cc in neighbors(r, c) if (rr, cc) in occ)
        return -d + 2.0 * conn

    # near existing stones
    frontier = set()
    for r, c in me_set | opp_set:
        for rr, cc in neighbors(r, c):
            if (rr, cc) not in occ:
                frontier.add((rr, cc))
    if not frontier:
        # opening: play toward center
        best = None
        bestv = -1e18
        for r, c in coords_valid:
            if (r, c) in occ:
                continue
            v = score_cell_basic(r, c)
            if v > bestv:
                bestv = v; best = (r, c)
        return best

    # also consider top-k frontier plus some random
    frontier = list(frontier)
    frontier.sort(key=lambda rc: score_cell_basic(rc[0], rc[1]), reverse=True)
    candidates = frontier[:40] if len(frontier) > 40 else frontier
    if len(candidates) < 12:
        # add more from valid cells based on basic heuristic
        remaining = [cell for cell in coords_valid if cell not in occ and cell not in set(candidates)]
        remaining.sort(key=lambda rc: score_cell_basic(rc[0], rc[1]), reverse=True)
        candidates.extend(remaining[:(12 - len(candidates))])

    # --- tactical move selection ---
    # 1) Win immediately
    for mv in candidates:
        if is_win_after(mv, me_set):
            return mv

    # 2) Block opponent immediate wins
    for mv in candidates:
        if is_win_after(mv, opp_set):
            return mv

    # 3) Otherwise evaluate
    opp_c = opp_set
    best_move = None
    best_score = -1e18

    # slight randomness to break ties
    rnd = random.Random(0)

    for mv in candidates:
        r, c = mv
        my_test = set(me_set)
        my_test.add(mv)
        op_test = set(opp_c)
        # opponent doesn't play this move, so for heuristic we just use block potential: how much this move disrupts.
        # We'll approximate by whether it prevents bridge/fork progress: if opponent could win next, it was handled.
        # Now focus on our structure building potential:
        score = 0.0

        # bridge/fork proximity heuristics: count how many corners/sides our component touches after move
        # (exactness not perfect but quick)
        comps = compute_components(my_test)
        corner_set = set(corner_cells)
        for comp in comps:
            comp_set = set(comp)
            touched_corners = sum(1 for cell in comp_set if cell in corner_set)
            if touched_corners >= 2:
                score += 200.0  # near-certain bridge
            else:
                score += 40.0 * touched_corners

            sides = set()
            for rr, cc2 in comp_set:
                if is_corner((rr, cc2)):
                    continue
                sides.update(side_ids(rr, cc2))
            score += 25.0 * len(sides)

            # ring potential: if component would create an internal hole. Expensive but candidates are small.
            # We'll do a light test: if ring not yet, only try expensive check on top few by score.
        # Connection heuristic: number of our neighbors
        score += 5.0 * sum(1 for rr, cc2 in neighbors(r, c) if (rr, cc2) in me_set)
        score -= 3.0 * sum(1 for rr, cc2 in neighbors(r, c) if (rr, cc2) in opp_c)

        score += 0.01 * score_cell_basic(r, c)

        # Expensive ring check for top few
        if score > best_score - 20 and rnd.random() < 0.6:
            if has_ring(my_test):
                score += 120.0

        # Also prefer making big components
        comp_sizes = sorted((len(comp) for comp in comps), reverse=True)
        if comp_sizes:
            score += 3.0 * comp_sizes[0]

        if score > best_score:
            best_score = score
            best_move = mv

    # Ensure legality (should be)
    if best_move is None:
        # fallback: any valid empty near frontier, else any valid empty
        for mv in frontier:
            rr, cc = mv
            if valid_mask[rr][cc] and mv not in occ:
                return mv
        for r in range(N):
            for c in range(N):
                if valid_mask[r][c] and (r, c) not in occ:
                    return (r, c)
        return (0, 0)

    return best_move
