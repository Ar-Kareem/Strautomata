
import random
from collections import deque

# --- Helpers for Havannah on an NxN (N=15) hex grid mapped to axial-ish coordinates ---
# We assume the neighbor structure for the given (row, col) indexing:
# For a "flat-top" hex with rows as x and cols as y, one common mapping is:
# neighbors: (r-1,c), (r+1,c), (r,c-1), (r,c+1), (r-1,c+1), (r+1,c-1)
# This matches the example: (4,1) touches (5,1),(3,1) and (4,0),(5,0)? wait example says a5 (4,0) and a4 (3,0)
# and to right touches c5 (4,2) and c4 (3,2). That implies neighbors are:
# up: (r-1,c)
# down: (r+1,c)
# left-up: (r-1,c-1)? But example says from (4,1) to (3,0) (row-1,col-1) yes.
# left-down: (r,c-1)? example says (4,0) yes.
# right-up: (r-1,c+1)? example says (3,2) yes.
# right-down: (r,c+1)? example says (4,2) yes.
#
# So neighbor set is:
# (r-1,c), (r+1,c), (r-1,c-1), (r,c-1), (r-1,c+1), (r,c+1), (r+1,c-1) would be extra.
# But we need exactly 6. Let's list consistent with example:
# From (4,1):
# touching b6 (5,1) => (r+1,c)
# touching b4 (3,1) => (r-1,c)
# to its left touching a4 (3,0) => (r-1,c-1)
# to its left touching a5 (4,0) => (r,c-1)
# to its right touching c5 (4,2) => (r,c+1)
# to its right touching c4 (3,2) => (r-1,c+1)
# That's 6: (r+1,c), (r-1,c), (r-1,c-1), (r,c-1), (r,c+1), (r-1,c+1).
# This corresponds to "row-major" stagger where only one diagonal goes down.
#
# We'll use that neighbor rule. It must be consistent with the arena's valid_mask.
#
# Additionally, we rely on valid_mask to determine playable cells; off-board cells are ignored.

NEI_DELTAS = [
    (1, 0),    # (r+1,c)
    (-1, 0),   # (r-1,c)
    (-1, -1),  # (r-1,c-1)
    (0, -1),   # (r,c-1)
    (0, 1),    # (r,c+1)
    (-1, 1),   # (r-1,c+1)
]

def _in_bounds(r, c, n):
    return 0 <= r < n and 0 <= c < n

def _neighbors(cell, valid_mask):
    r, c = cell
    n = len(valid_mask)
    for dr, dc in NEI_DELTAS:
        rr, cc = r + dr, c + dc
        if _in_bounds(rr, cc, n) and valid_mask[rr][cc]:
            yield (rr, cc)

def _make_board(me, opp, valid_mask):
    n = len(valid_mask)
    board = [[-1]*n for _ in range(n)]
    for r, c in me:
        board[r][c] = 0
    for r, c in opp:
        board[r][c] = 1
    return board

def _legal_moves(valid_mask, board):
    n = len(valid_mask)
    moves = []
    for r in range(n):
        for c in range(n):
            if valid_mask[r][c] and board[r][c] == -1:
                moves.append((r, c))
    return moves

def _connected_components(stones_set, valid_mask):
    # stones_set is a set of cells occupied by a player
    visited = set()
    comps = []
    for cell in stones_set:
        if cell in visited:
            continue
        q = deque([cell])
        visited.add(cell)
        comp = []
        while q:
            x = q.popleft()
            comp.append(x)
            for nb in _neighbors(x, valid_mask):
                if nb in stones_set and nb not in visited:
                    visited.add(nb)
                    q.append(nb)
        comps.append(comp)
    return comps

def _bridge_points_corners(n):
    # In Havannah (standard), the six corners are intersection points of board edges.
    # With our (row,col) representation (and valid_mask), easiest is to define them from mask:
    # corners correspond to extreme cells that touch exactly one of the three board edges.
    # But we only have valid_mask; we can approximate corners as cells minimizing/maximizing row/col.
    # For robustness we compute corners as the six extremal cells by (row,col) and (row-col).
    cells = [(r,c) for r in range(n) for c in range(n) if valid_mask_global[r][c]]
    # However we don't have valid_mask here. We'll not use this function.
    return None

def _extract_edges_and_corners(valid_mask):
    # Determine the six "edges" of the hex board in this coordinate system:
    # We approximate by using mask extremes:
    # - Edge A: cells with minimal column
    # - Edge B: cells with minimal "row"
    # - Edge C: cells with maximal column
    # - Edge D: cells with maximal "row"
    # - Edge E: cells with minimal (row-col)
    # - Edge F: cells with maximal (row-col)
    n = len(valid_mask)
    cells = [(r,c) for r in range(n) for c in range(n) if valid_mask[r][c]]
    min_r = min(r for r,c in cells)
    max_r = max(r for r,c in cells)
    min_c = min(c for r,c in cells)
    max_c = max(c for r,c in cells)
    vals = [(r-c, r, c) for r,c in cells]
    min_d = min(d for d,_,_ in vals)
    max_d = max(d for d,_,_ in vals)

    edgeB = [(r,c) for r,c in cells if r == min_r]
    edgeD = [(r,c) for r,c in cells if r == max_r]
    edgeA = [(r,c) for r,c in cells if c == min_c]
    edgeC = [(r,c) for r,c in cells if c == max_c]
    edgeE = [(r,c) for r,c in cells if (r-c) == min_d]
    edgeF = [(r,c) for r,c in cells if (r-c) == max_d]

    # Corners are pairwise intersections of adjacent edges; compute as cells that lie on two edges.
    def on_edge(cell, edge_list_set):
        return cell in edge_list_set

    sets = [set(edgeA), set(edgeB), set(edgeC), set(edgeD), set(edgeE), set(edgeF)]
    # Determine corners as cells belonging to >=2 edge sets.
    corner_cells = [cell for cell in cells if sum(1 for s in sets if cell in s) >= 2]
    # Reduce to 6 by clustering extremal.
    # If more than 6 due to approximation, we pick representative extremes:
    # choose 6 farthest by simple scoring.
    scored = sorted(corner_cells, key=lambda rc: (rc[0], rc[1], rc[0]-rc[1]))
    # If too many, sample based on distinct (r,c) extremes.
    # We'll pick by selecting up to one per direction: min_r, max_r, min_c, max_c, min_d, max_d.
    corners = []
    def pick_first(pred):
        for cell in corner_cells:
            if pred(cell):
                return cell
        return None

    candidates = [
        pick_first(lambda rc: rc[0] == min_r),
        pick_first(lambda rc: rc[0] == max_r),
        pick_first(lambda rc: rc[1] == min_c),
        pick_first(lambda rc: rc[1] == max_c),
        pick_first(lambda rc: (rc[0]-rc[1]) == min_d),
        pick_first(lambda rc: (rc[0]-rc[1]) == max_d),
    ]
    for x in candidates:
        if x is not None and x not in corners:
            corners.append(x)

    # If still not 6, fallback: take any distinct corner_cells up to 6.
    for cell in corner_cells:
        if cell not in corners:
            corners.append(cell)
        if len(corners) == 6:
            break

    corners = corners[:6]
    return (edgeA, edgeB, edgeC, edgeD, edgeE, edgeF), corners

def _check_fork_or_bridge(me_set, valid_mask):
    n = len(valid_mask)
    (edgeA, edgeB, edgeC, edgeD, edgeE, edgeF), corners = _extract_edges_and_corners(valid_mask)
    edge_sets = [set(edgeA), set(edgeB), set(edgeC), set(edgeD), set(edgeE), set(edgeF)]
    corner_set = set(corners)

    # Fork: connected component that touches any 3 edges (not corners only)
    # Bridge: component that connects any two corners.
    comps = _connected_components(me_set, valid_mask)
    bridge = False
    fork = False
    for comp in comps:
        comp_set = set(comp)
        touched_edges = sum(1 for s in edge_sets if any(cell in s for cell in comp_set))
        if touched_edges >= 3:
            fork = True
        touched_corners = [c for c in comp_set if c in corner_set]
        if len(touched_corners) >= 2:
            # connect any two corners
            bridge = True
        if bridge or fork:
            return bridge, fork
    return bridge, fork

def _check_ring(me_set, valid_mask):
    # Ring: a loop around cells (occupied or empty). Practical approach:
    # After placing, if any component is large enough to potentially enclose, we detect
    # whether there exists a cycle on the planar dual.
    #
    # Implementable fast heuristic: For each empty cell not in our component, run flood fill
    # on empty+opponent cells treated as "not ours" and see if it can reach the "outside"
    # boundary of the board. If an area of non-ours is fully enclosed by our stones, that's a ring.
    #
    # We'll treat opponent and empty as passable; only our stones block.
    n = len(valid_mask)
    ours = me_set
    cells = [(r,c) for r in range(n) for c in range(n) if valid_mask[r][c]]
    # Find "outside boundary": non-ours cells that touch the boundary of the hex-board.
    # Approximate boundary as cells on extreme rows/cols/diagonals (same edge extraction as above).
    (edgeA, edgeB, edgeC, edgeD, edgeE, edgeF), _ = _extract_edges_and_corners(valid_mask)
    boundary = set(edgeA) | set(edgeB) | set(edgeC) | set(edgeD) | set(edgeE) | set(edgeF)

    non_ours = set(cells) - ours
    visited = set()
    for start in list(non_ours):
        if start in visited:
            continue
        q = deque([start])
        visited.add(start)
        area = [start]
        reaches_outside = False
        while q:
            x = q.popleft()
            if x in boundary:
                reaches_outside = True
            for nb in _neighbors(x, valid_mask):
                if nb in non_ours and nb not in visited:
                    visited.add(nb)
                    q.append(nb)
        if not reaches_outside:
            # Enclosed area exists => ring
            # Ensure enclosing component exists: since enclosed by "ours", it's a ring.
            return True
    return False

def _is_win_after_move(move, me, opp, valid_mask):
    board = _make_board(me, opp, valid_mask)
    r, c = move
    board[r][c] = 0
    me_set = set(me)
    me_set.add((r,c))
    bridge, fork = _check_fork_or_bridge(me_set, valid_mask)
    if bridge or fork:
        return True
    if _check_ring(me_set, valid_mask):
        return True
    return False

def _score_move(move, me_set, opp_set, valid_mask):
    # Local tactical and strategic scoring.
    # Bridge/fork potential via distance to edges/corners on our component graph.
    n = len(valid_mask)
    r, c = move
    # Neighbors
    neigh = list(_neighbors((r,c), valid_mask))
    my_nei = sum(1 for nb in neigh if nb in me_set)
    opp_nei = sum(1 for nb in neigh if nb in opp_set)

    # Edge proximity
    (edgeA, edgeB, edgeC, edgeD, edgeE, edgeF), corners = _extract_edges_and_corners(valid_mask)
    edge_sets = [set(edgeA), set(edgeB), set(edgeC), set(edgeD), set(edgeE), set(edgeF)]
    corner_set = set(corners)

    # Connectivity scoring: if we place at move, it will join all neighboring components.
    # Estimate which edges/corners become reachable by running BFS in graph of our stones plus the move.
    temp_me = set(me_set)
    temp_me.add((r,c))

    # Determine component containing the move (BFS over temp_me)
    q = deque([(r,c)])
    visited = {(r,c)}
    while q:
        x = q.popleft()
        for nb in _neighbors(x, valid_mask):
            if nb in temp_me and nb not in visited:
                visited.add(nb); q.append(nb)

    touched_edges = sum(1 for s in edge_sets if any(cell in s for cell in visited))
    touched_corners = sum(1 for cn in corner_set if cn in visited)

    # Ring potential heuristic: prefer moves that increase enclosed potential by being on boundary of large component
    # approximate by component size and boundary contact
    comp_size = len(visited)
    boundary = set().union(*edge_sets)
    boundary_contact = sum(1 for cell in visited if cell in boundary)

    # Mix: prioritize tactical and immediate structure creation
    score = 0
    score += 6.0 * my_nei
    score += 2.0 * opp_nei  # cutting/contesting adjacency
    score += 10.0 * touched_edges
    score += 9.0 * touched_corners

    # Centering: board tends to have largest playable area near center of mask extents
    cells = [(rr,cc) for rr in range(n) for cc in range(n) if valid_mask[rr][cc]]
    min_r = min(rr for rr,cc in cells); max_r = max(rr for rr,cc in cells)
    min_c = min(cc for rr,cc in cells); max_c = max(cc for rr,cc in cells)
    center_r = (min_r + max_r) / 2
    center_c = (min_c + max_c) / 2
    dist = abs(r - center_r) + abs(c - center_c)
    score += -0.15 * dist

    # Favor growing big component
    score += 0.25 * comp_size
    score += 0.05 * boundary_contact
    return score

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    n = len(valid_mask)
    # Build sets
    me_set = set(me)
    opp_set = set(opp)

    # Create board
    board = [[-1]*n for _ in range(n)]
    for r,c in me:
        board[r][c] = 0
    for r,c in opp:
        board[r][c] = 1

    legal = _legal_moves(valid_mask, board)
    if not legal:
        # Should not happen; but return something legal if possible
        for r in range(n):
            for c in range(n):
                if valid_mask[r][c] and board[r][c] == -1:
                    return (r,c)
        return (0,0)

    # 1) Immediate win
    for mv in legal:
        if _is_win_after_move(mv, me, opp, valid_mask):
            return mv

    # 2) Immediate defense: block opponent wins in one
    # If opponent can win with some move, we try to prevent by selecting moves that
    # stop at least one of their winning moves. We'll approximate by: if any move we play
    # results in opponent having no immediate win (i.e., after our move, check their wins).
    opp_can_win = []
    for omv in legal:
        if _is_win_after_move(omv, opp, me, valid_mask):  # check opponent win if they played it
            opp_can_win.append(omv)

    if opp_can_win:
        # Choose a move that blocks most of those immediate winning moves in practice
        # by selecting moves that (a) have high value to us and (b) are near opponent stones.
        best = None
        best_score = -1e9
        for mv in legal:
            # simulate our move and see if any opponent immediate win still exists (expensive),
            # so we do a cheaper criterion first; then a limited verification.
            # We'll verify on top candidates.
            # Quick score
            temp_board = [row[:] for row in board]
            rr,cc = mv
            temp_board[rr][cc] = 0

            # Approx: compute heuristic score, plus threat reduction (min distance to opp winning moves)
            base = _score_move(mv, me_set, opp_set, valid_mask)
            # Threat reduction
            threat_red = 0.0
            for w in opp_can_win:
                if w == mv:
                    threat_red += 8.0  # directly blocks if same cell
                else:
                    # adjacency penalty
                    # (use neighbor distance 1 as indicator)
                    if w in set(_neighbors(mv, valid_mask)):
                        threat_red += 2.5

            cand_score = base + threat_red

            # Verify for top few candidates
            if cand_score > best_score:
                best_score = cand_score
                best = mv

        # Optional verification: pick best among top 3 by full check
        candidates = sorted(legal, key=lambda mv: _score_move(mv, me_set, opp_set, valid_mask), reverse=True)[:5]
        final_best = None
        final_best_score = -1e9
        for mv in candidates:
            # After our move, check if opponent has any immediate win
            new_me = list(me_set) + [mv]
            opp_wins_next = False
            for omv in _legal_moves(valid_mask, _make_board(new_me, list(opp_set), valid_mask)):
                if _is_win_after_move(omv, list(opp_set), new_me, valid_mask):
                    opp_wins_next = True
                    break
            # If we blocked all immediate wins, that's great.
            if not opp_wins_next:
                s = 1e6 + _score_move(mv, me_set, opp_set, valid_mask)
            else:
                s = _score_move(mv, me_set, opp_set, valid_mask)
            if s > final_best_score:
                final_best_score = s
                final_best = mv
        return final_best if final_best is not None else best

    # 3) General heuristic best move
    # Break ties deterministically but with slight randomness based on hash to avoid mirror traps
    scored = []
    for mv in legal:
        s = _score_move(mv, me_set, opp_set, valid_mask)
        scored.append((s, mv))
    scored.sort(key=lambda x: (x[0], -x[1][0], -x[1][1]), reverse=True)

    # Add tiny deterministic jitter for variety while keeping legality
    top_score = scored[0][0]
    best_candidates = [mv for s, mv in scored if abs(s - top_score) < 1e-9]
    if len(best_candidates) == 1:
        return best_candidates[0]
    # deterministic pseudo-random choice based on move coordinates
    best_candidates.sort()
    return best_candidates[0]
