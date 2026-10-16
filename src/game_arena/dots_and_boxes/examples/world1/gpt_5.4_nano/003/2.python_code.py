
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Dots and Boxes (4x4 boxes). State is given by:
      - horizontal: 5x5, edges between (r,c) and (r,c+1) for r in [0..4], c in [0..4]
      - vertical:   5x5, edges between (r,c) and (r+1,c) for r in [0..4], c in [0..4]
      - capture: 4x4 boxes: 1 if owned by current player, -1 if by opponent, 0 unclaimed

    Returns: 'row,col,dir' where dir in {'H','V'}.
    """
    # Ensure numpy arrays
    horizontal = np.asarray(horizontal)
    vertical = np.asarray(vertical)
    capture = np.asarray(capture)

    N = 4  # 4x4 boxes
    # Helper to compute whether a box would be completed after placing a specific edge
    # We'll evaluate hypothetical move effects on box edge counts.
    def box_edges_filled(bx, by, h_arr, v_arr):
        """
        For box with top-left corner at (bx,by) in box-grid coordinates:
        edges:
          top:    horizontal[bx,   by]
          bottom: horizontal[bx+1, by]
          left:   vertical[bx,   by]
          right:  vertical[bx,   by+1]
        """
        return (
            int(h_arr[bx, by] != 0) +
            int(h_arr[bx+1, by] != 0) +
            int(v_arr[bx, by] != 0) +
            int(v_arr[bx, by+1] != 0)
        )

    # List all legal moves
    legal_moves = []
    # horizontal edges: size 5x5; playable edges that affect boxes are those where
    # horizontal[r,c] with r in [0..4], c in [0..4], but boxes only use c in [0..3]
    # For box (bx,by): top uses horizontal[bx,by] with by in [0..3], bottom uses horizontal[bx+1,by]
    # We'll still consider all 5x5, but legality only for empty edges; effect on boxes computed via bounds.
    for r in range(5):
        for c in range(5):
            if horizontal[r, c] == 0:
                legal_moves.append((r, c, 'H'))
            if vertical[r, c] == 0:
                legal_moves.append((r, c, 'V'))

    # If no moves, should not happen in arena; but return some legal format fallback
    if not legal_moves:
        return "0,0,H"

    # Evaluate each move with a fast local simulation:
    # - capture_count: how many boxes would be completed (4 edges filled) by this move
    # - gives_trap_count: how many boxes would end up at exactly 3 edges filled after this move
    # - Also compute newly_created_3_edge_boxes more generally.
    best_moves_capture = []
    best_moves_safe = []
    best_score = None  # lower is better for safe moves: (traps, total3, deterministic tie)

    # Current arrays
    h0 = horizontal
    v0 = vertical

    for r, c, d in legal_moves:
        # Create copies only if needed; but we can reason locally.
        # We'll compute affected boxes for this edge.
        capture_count = 0
        trap_count = 0
        total3_after = 0  # count of boxes that are 3 after move (useful tie-break)

        # Determine which boxes (bx,by) are adjacent to this edge.
        affected_boxes = []
        if d == 'H':
            # horizontal[r,c] is the edge between dots (r,c)-(r,c+1)
            # It can be top edge of box (r, c) if r in [0..3], c in [0..3]
            # and bottom edge of box (r-1, c) if r in [1..4], c in [0..3]
            if 0 <= r <= 3 and 0 <= c <= 3:
                affected_boxes.append((r, c))
            if 1 <= r <= 4 and 0 <= c <= 3:
                affected_boxes.append((r-1, c))
        else:  # 'V'
            # vertical[r,c] is the edge between dots (r,c)-(r+1,c)
            # It can be left edge of box (r, c) if r in [0..3], c in [0..3]
            # and right edge of box (r, c-1) if c in [1..4], r in [0..3]
            if 0 <= r <= 3 and 0 <= c <= 3:
                affected_boxes.append((r, c))
            if 0 <= r <= 3 and 1 <= c <= 4:
                affected_boxes.append((r, c-1))

        # Use current edge filled status; compute for each affected box only.
        # Determine whether this move sets that specific edge to filled.
        # Since the edge is currently 0 (empty), after move it becomes filled.
        # We'll compute box edge count before and after for affected boxes.
        for bx, by in affected_boxes:
            if not (0 <= bx < N and 0 <= by < N):
                continue
            # Before:
            before = box_edges_filled(bx, by, h0, v0)

            after = before + 1  # because edge is currently empty and we fill it
            if after >= 4:
                capture_count += 1
            elif after == 3:
                trap_count += 1
            # count total3_after only for tie-breaking among safe moves
            if after == 3:
                total3_after += 1

        # Decision:
        if capture_count > 0:
            best_moves_capture.append((capture_count, r, c, d))
        else:
            # Prefer moves that do not create any 3-edge boxes (trap_count == 0)
            # Primary score: traps, then total3_after, then deterministic
            score = (trap_count, total3_after, r, c, d)
            if best_score is None or score < best_score:
                best_score = score
                best_moves_safe = [(r, c, d)]
            elif score == best_score:
                best_moves_safe.append((r, c, d))

    # If we can capture, take the best capture move (maximize capture_count, then deterministic tie)
    if best_moves_capture:
        best_moves_capture.sort(reverse=True)  # sort by capture_count then r,c,d lexicographically
        # But reverse affects lexicographic; handle explicitly:
        max_cap = max(m[0] for m in best_moves_capture)
        candidates = [m for m in best_moves_capture if m[0] == max_cap]
        # deterministic tie-break: smallest (r,c,dir) by ord
        def dir_key(dd):
            return 0 if dd == 'H' else 1
        candidates.sort(key=lambda m: (m[1], m[2], dir_key(m[3])))
        _, r, c, d = candidates[0]
        return f"{r},{c},{d}"

    # Otherwise choose best safe move deterministically
    if best_moves_safe:
        def dir_key(dd):
            return 0 if dd == 'H' else 1
        best_moves_safe.sort(key=lambda m: (m[0], m[1], dir_key(m[2])))
        r, c, d = best_moves_safe[0]
        return f"{r},{c},{d}"

    # Fallback (should be unreachable): return first legal move
    r, c, d = legal_moves[0]
    return f"{r},{c},{d}"
