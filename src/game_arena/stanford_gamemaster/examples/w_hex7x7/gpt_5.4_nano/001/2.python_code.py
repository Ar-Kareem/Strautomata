
import re
from collections import deque, defaultdict

def policy(state: list[list[object]], role: str) -> str:
    # --- Helpers to parse board from state ---
    # Cells are encoded as: ["cell", <row>, <col>, <color>]
    cell_facts = [p for p in state if len(p) >= 4 and p[0] == "cell"]
    rows = set()
    cols_by_row = defaultdict(set)
    occupied = {}  # (row_char, col_int) -> color
    for p in cell_facts:
        r = p[1]
        c = int(p[2])
        color = p[3]
        rows.add(r)
        cols_by_row[r].add(c)
        occupied[(r, c)] = color

    # If somehow no cell facts exist (early), infer 7x7 standard coords:
    # Common Stanford encoding uses rows 'a'..'g' and cols 1..7.
    if not rows:
        rows = set(chr(ord('a') + i) for i in range(7))
        cols_by_row = {chr(ord('a') + i): set(range(1, 8)) for i in range(7)}
        for r in rows:
            for c in range(1, 8):
                occupied.setdefault((r, c), None)
    else:
        # ensure cols are continuous up to max if partially observed
        for r in list(rows):
            if not cols_by_row[r]:
                continue

    # Determine board bounds
    all_rows = sorted(list(rows))
    max_col = 0
    for r in all_rows:
        if cols_by_row[r]:
            max_col = max(max_col, max(cols_by_row[r]))
    if max_col <= 0:
        max_col = 7

    # Build neighbor relations for hex grid using common axial-like coords:
    # In this GDL, row letters identify diagonals; neighbors depend on relative positions.
    #
    # For a 7x7 hexagon with standard offset layout:
    # We can use coordinate system (x, y) where:
    #   x = index of row (a..g) -> 0..6
    #   y = col-1 -> 0..6
    # Adjacency in "pointy-top" hex grid for axial coords:
    # A common model gives neighbors:
    #   (x-1,y), (x+1,y), (x,y-1), (x,y+1), (x-1,y+1), (x+1,y-1)
    #
    # This matches the known trajectories in the prompt (e.g., last state shows
    # connectivity using adjacent across letters and columns).
    def to_xy(r, c):
        return (ord(r) - ord('a'), c - 1)

    def from_xy(x, y):
        return (chr(ord('a') + x), y + 1)

    def in_bounds(x, y):
        # board is 7x7 in terms of x,y = 0..6
        return 0 <= x <= 6 and 0 <= y <= 6

    # Legal move generation: any empty cell place(rowChar,colInt)
    def is_empty(r, c):
        return occupied.get((r, c)) is None

    def get_color_at(r, c):
        return occupied.get((r, c))

    # --- Determine connectivity / winning for a side ---
    # Red connects upper-left to lower-right.
    # Black connects upper-right to lower-left.
    #
    # Using x,y:
    # Upper-left side for red corresponds to x+y == 0? Actually at (0,0) and along one edge.
    # Lower-right corresponds to x+y == 12? (6,6)
    #
    # For hex, correct edge sets:
    # We'll use:
    #   Red target sides: x == 0 OR y == 0 ??? (upper-left to lower-right)
    #   Black target sides: x == 0 OR y == 6 ??? (upper-right to lower-left)
    #
    # But we need exact for win detection.
    #
    # We'll infer edges from row/col:
    # Observed in examples: red has stones at a1 and a7 and connection uses diagonal.
    # In a standard 7x7 with x,y:
    #   Connect left-down to right-up.
    #
    # We'll choose:
    #   Red connects x==0 to x==6 (top-left to bottom-right) along NW-SE direction:
    #   Specifically: Red connects cells where x==0 (row 'a') to cells where x==6 (row 'g').
    #   Black connects cells where y==0 (col 1) to cells where y==6 (col 7).
    #
    # This can be swapped, but we also check for immediate win consistency
    # by attempting both edge mappings heuristically (cheap): choose mapping that yields
    # a currently-present completed line if present; otherwise default.
    def win_for(color, occ_map):
        # occ_map: (r,c)->color or None
        # Determine edge sets for red/black by trying two common mappings and selecting the one
        # that best matches existing "connected" facts if available.
        # We can directly use current state's "connected" facts to see which side is already connected,
        # but that requires role-specific interpretation. We'll keep deterministic:
        # Use two mappings:
        # Mapping A:
        #   red: x==0 to x==6 ; black: y==0 to y==6
        # Mapping B:
        #   red: y==0 to y==6 ; black: x==0 to x==6
        mappings = []
        # Build BFS to test.
        def bfs(start_cells, goal_pred):
            q = deque(start_cells)
            seen = set(start_cells)
            while q:
                x, y = q.popleft()
                if goal_pred(x, y):
                    return True
                for nx, ny in neighbors_xy(x, y):
                    if (nx, ny) not in seen and in_bounds(nx, ny):
                        r2, c2 = from_xy(nx, ny)
                        if occ_map.get((r2, c2)) == color:
                            seen.add((nx, ny))
                            q.append((nx, ny))
            return False

        def neighbors_xy(x, y):
            # axial-like:
            candidates = [(x-1,y), (x+1,y), (x,y-1), (x,y+1), (x-1,y+1), (x+1,y-1)]
            for nx, ny in candidates:
                if in_bounds(nx, ny):
                    yield nx, ny

        # Map A
        if color == "red":
            start_pred = lambda x,y: x == 0
            goal_pred = lambda x,y: x == 6
        else:
            start_pred = lambda x,y: y == 0
            goal_pred = lambda x,y: y == 6

        start_cells = [(x,y) for x in range(7) for y in range(7) if start_pred(x,y) and occ_map.get(from_xy(x,y)) == color]
        resA = bfs(start_cells, goal_pred)

        # Map B (swap roles for edges)
        if color == "red":
            start_pred = lambda x,y: y == 0
            goal_pred = lambda x,y: y == 6
        else:
            start_pred = lambda x,y: x == 0
            goal_pred = lambda x,y: x == 6

        start_cells = [(x,y) for x in range(7) for y in range(7) if start_pred(x,y) and occ_map.get(from_xy(x,y)) == color]
        resB = bfs(start_cells, goal_pred)

        # If either mapping says win, accept it.
        return resA or resB

    # --- Opponent and immediate win/block checks ---
    opponent = "black" if role == "red" else "red"

    # Build occ_map with all coords in inferred board
    occ_map = {}
    for r in all_rows:
        for c in range(1, max_col + 1):
            occ_map[(r, c)] = occupied.get((r, c))
    # Ensure within 7:
    for x in range(7):
        r = chr(ord('a') + x)
        if r not in occ_map:
            for y in range(7):
                occ_map[(r, y+1)] = None

    # Generate list of all empties
    legal_moves = []
    for x in range(7):
        r = chr(ord('a') + x)
        for y in range(7):
            c = y + 1
            if occ_map.get((r, c)) is None:
                legal_moves.append((r, c))

    # If no empties (shouldn't happen), pick a syntactically valid but would be illegal;
    # however game would be terminal. We'll safeguard:
    if not legal_moves:
        return "place(a,1)"

    # Quick immediate win / block / scoring
    # Heuristic: BFS distance from player's stones to target edges through player's potential
    # We'll compute reachability in graph induced by player's stones only.
    def neighbor_cells(r, c):
        x, y = to_xy(r, c)
        for nx, ny in [(x-1,y), (x+1,y), (x,y-1), (x,y+1), (x-1,y+1), (x+1,y-1)]:
            if in_bounds(nx, ny):
                rr, cc = from_xy(nx, ny)
                yield rr, cc

    def count_adjacent_own(r, c, col):
        cnt = 0
        for rr, cc in neighbor_cells(r, c):
            if occ_map.get((rr, cc)) == col:
                cnt += 1
        return cnt

    # Try each move
    best_move = None
    best_score = -10**9

    # For block simulation, limit to a few opponent winning moves by scanning empties
    # and checking win_for(opponent) after placing there.
    for (r, c) in legal_moves:
        # simulate placing role stone
        occ2 = dict(occ_map)
        occ2[(r, c)] = role

        # Immediate win
        if win_for(role, occ2):
            return f"place({r},{c})"

        # Immediate block: if opponent has any winning move next, prefer moves that eliminate all of them
        # We'll evaluate by computing how many opponent winning replies remain.
        opponent_wins = 0
        for (ro, co) in legal_moves:
            if (ro, co) == (r, c):
                continue
            # after our move, opponent can place on any still-empty cell
            if occ2.get((ro, co)) is None:
                occ3 = dict(occ2)
                occ3[(ro, co)] = opponent
                if win_for(opponent, occ3):
                    opponent_wins += 1
        # If no opponent wins remain, huge bonus
        score = 0
        if opponent_wins == 0:
            score += 10_000_000
        else:
            score -= 1_000_000 * opponent_wins

        # Connectivity score: size of connected component of this move through role stones
        # BFS from (r,c) only through role stones
        def bfs_component(start_r, start_c):
            q = deque()
            q.append((start_r, start_c))
            seen = {(start_r, start_c)}
            while q:
                cr, cc = q.popleft()
                for nr, nc in neighbor_cells(cr, cc):
                    if (nr, nc) not in seen and occ2.get((nr, nc)) == role:
                        seen.add((nr, nc))
                        q.append((nr, nc))
            return len(seen), seen

        comp_size, comp = bfs_component(r, c)
        score += 2000 * comp_size

        # Distance-to-goal: approximate using min distance in Manhattan to target edge with 6-neighbor distance approximated by BFS on empty+own.
        # We'll use cheap metric:
        x, y = to_xy(r, c)
        if role == "red":
            # prefer smaller x and larger x, but also y accordingly: target is opposite edge in mapping; use min distance to either edge across both mappings
            # We'll use best-of two possible mappings:
            d1 = x  # to x==0
            d2 = 6 - x  # to x==6
            dist = min(d1, d2)
        else:
            d1 = y
            d2 = 6 - y
            dist = min(d1, d2)
        score -= 30 * dist

        # Adjacent own stones
        score += 50 * count_adjacent_own(r, c, role)

        # Mild center preference (avoid edges too early doesn't always help; but late-stage it’s fine)
        center_dist = abs(x - 3) + abs(y - 3)
        score -= center_dist

        if score > best_score:
            best_score = score
            best_move = (r, c)

    br, bc = best_move
    return f"place({br},{bc})"
