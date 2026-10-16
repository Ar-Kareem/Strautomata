
import numpy as np

def boxes_for_edge(r: int, c: int, dir: str):
    """Return the box indices that share the edge at (r,c,dir)."""
    boxes = []
    if dir == 'H':
        boxes.append((r, c))                     # top box
        if r + 1 < 4:                           # bottom box exists
            boxes.append((r + 1, c))
    else:  # dir == 'V'
        boxes.append((r, c))                     # left box
        if c + 1 < 4:
            boxes.append((r, c + 1))             # right box
    return boxes


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # -----------------------------------------------------------------
    # 1. Box‑level statistics (only for unclaimed boxes)
    # -----------------------------------------------------------------
    rows, cols = horizontal.shape
    assert rows == cols == 5, "state arrays must be 5×5"

    # Pre‑compute box info for all 16 boxes
    box_drawn = np.zeros((4, 4), dtype=int)
    box_my   = np.zeros((4, 4), dtype=int)
    box_opp  = np.zeros((4, 4), dtype=int)
    missing_edges_of_box = {}

    for i in range(4):
        for j in range(4):
            edges = []
            # top horizontal
            if horizontal[i, j] == 0:
                edges.append((i, j, 'H'))
            # bottom horizontal
            if i + 1 < 5 and horizontal[i + 1, j] == 0:
                edges.append((i + 1, j, 'H'))
            # left vertical
            if vertical[i, j] == 0:
                edges.append((i, j, 'V'))
            # right vertical
            if j + 1 < 5 and vertical[i, j + 1] == 0:
                edges.append((i, j + 1, 'V'))

            missing_edges_of_box[(i, j)] = edges

            # Count existing edges and who drew them
            drawn = 0
            my = opp = 0
            for edge in edges:
                e_r, e_c, e_dir = edge
                v = horizontal[e_r, e_c] if e_dir == 'H' else vertical[e_r, e_c]
                if v != 0:
                    drawn += 1
                    if v == 1:
                        my += 1
                    else:
                        opp += 1
            box_drawn[i, j] = drawn
            box_my[i, j]   = my
            box_opp[i, j]  = opp

    # -----------------------------------------------------------------
    # 2. Detect opponent’s long chains (size ≥ 2)
    # -----------------------------------------------------------------
    opp_boxes = []   # boxes where opponent has >0 lines and we have 0
    for i in range(4):
        for j in range(4):
            if capture[i, j] != 0:        # already claimed
                continue
            if box_opp[i, j] > 0 and box_my[i, j] == 0:
                opp_boxes.append((i, j))

    # Build adjacency via shared missing edges
    opp_adj = {box: set() for box in opp_boxes}
    edge_to_boxes = {}   # (r,c,dir) -> boxes

    for box in opp_boxes:
        for edge in missing_edges_of_box[box]:
            edge_to_boxes.setdefault(edge, []).append(box)

    for box in opp_boxes:
        for edge in missing_edges_of_box[box]:
            other_boxes = edge_to_boxes[edge]
            for o in other_boxes:
                if o != box and o in opp_boxes:
                    opp_adj[box].add(o)

    # Find components with BFS
    visited = set()
    opp_chain_lengths = []
    opponent_has_long_chain = False
    for box in opp_boxes:
        if box not in visited:
            stack = [box]
            visited.add(box)
            comp_sz = 1
            while stack:
                cur = stack.pop()
                for nb in opp_adj[cur]:
                    if nb not in visited:
                        visited.add(nb)
                        comp_sz += 1
                        stack.append(nb)
            opp_chain_lengths.append(comp_sz)
            if comp_sz >= 2:
                opponent_has_long_chain = True

    # -----------------------------------------------------------------
    # 3. Enumerate all legal moves (empty edges)
    # -----------------------------------------------------------------
    candidates = []
    for r in range(5):
        for c in range(5):
            if horizontal[r, c] == 0:
                candidates.append((r, c, 'H'))
            if vertical[r, c] == 0:
                candidates.append((r, c, 'V'))

    capture_candidates = []   # (r,c,dir, opponent_line_score)
    safe_candidates = []       # (r,c,dir, advantage)

    for r, c, dir in candidates:
        boxes = boxes_for_edge(r, c, dir)
        capture_flag = False
        opp_score = 0
        adv = 0
        for box in boxes:
            if capture[box] != 0:          # box already claimed → ignore
                continue
            # Will this edge close a box?
            drawn_before = box_drawn[box]
            if drawn_before == 3:
                capture_flag = True
                opp_score += box_opp[box]    # how many opponent sides already drawn
            else:
                # safe move – count our net advantage in this box
                adv += box_my[box] - box_opp[box]
        if capture_flag:
            capture_candidates.append((r, c, dir, opp_score))
        else:
            safe_candidates.append((r, c, dir, adv))

    # -----------------------------------------------------------------
    # 4. Choose the move according to the game phase
    # -----------------------------------------------------------------
    # Dual phase (opponent has a chain ≥ 2)
    if opponent_has_long_chain:
        # Among capture moves pick the one that gives opponent the fewest lines
        best = None
        min_score = None
        for edge in capture_candidates:
            score = edge[3]
            if min_score is None or score < min_score:
                min_score = score
                best = edge
        # If for some reason no capture edge exists (unlikely), fall back to a safe one
        if best is None:
            best = max(safe_candidates, key=lambda x: x[1])
        move = f"{best[0]},{best[1]},{best[2]}"
        return move

    # Short‑endgame (no long opponent chain)
    # First try to capture a box that cuts the opponent’s short chain,
    # i.e. pick a capture edge with the largest opponent‑line count.
    if capture_candidates:
        # maximise opponent's current lines – we want to steal their box
        best = max(capture_candidates, key=lambda x: x[3])
    else:
        # No capture edge – pick the safe move with the biggest net advantage
        best = max(safe_candidates, key=lambda x: x[1])

    # Deterministic tie‑breaking
    #   – lower row, then column, then 'H' before 'V'
    candidates_sorted = sorted(
        [(r, c, dir) for (r, c, dir, _score) in (capture_candidates or safe_candidates)],
        key=lambda rc: (rc[2] == 'V', rc[1], rc[0])   # makes H < V
    )
    for (r, c, dir) in candidates_sorted:
        if (r, c, dir) == best[0:3]:
            move = f"{r},{c},{dir}"
            break

    return move
