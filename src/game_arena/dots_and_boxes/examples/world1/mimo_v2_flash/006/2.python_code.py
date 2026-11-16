

import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Dots and Boxes policy for 4x4 box grid.
    Plays to avoid giving away boxes, captures when possible, and prefers neutral moves.
    Uses a simple greedy heuristic with safety checks.
    """
    R = 5  # dot grid size (5x5)
    boxes = 4  # 4x4 boxes

    # Find all legal moves (edges with value 0)
    legal_h = np.argwhere((horizontal == 0))
    legal_v = np.argwhere((vertical == 0))

    # If no legal moves, return something (should not happen)
    if len(legal_h) == 0 and len(legal_v) == 0:
        return "0,0,H"

    # Precompute box ownership counts
    owned_me = np.sum(capture == 1)
    owned_opp = np.sum(capture == -1)
    unclaimed = np.sum(capture == 0)

    # Compute edge -> boxes map
    edge_to_boxes = {}
    for r in range(boxes):
        for c in range(boxes):
            # Box corners (r,c) (r,c+1) (r+1,c) (r+1,c+1)
            edges = [
                ('H', r, c),      # top
                ('H', r+1, c),    # bottom
                ('V', r, c),      # left
                ('V', r, c+1)     # right
            ]
            for dir, er, ec in edges:
                key = (dir, er, ec)
                if key not in edge_to_boxes:
                    edge_to_boxes[key] = []
                edge_to_boxes[key].append((r, c))

    def count_box_edges(r, c):
        # Count edges drawn around box (r,c)
        count = 0
        if horizontal[r, c] != 0:
            count += 1
        if horizontal[r+1, c] != 0:
            count += 1
        if vertical[r, c] != 0:
            count += 1
        if vertical[r, c+1] != 0:
            count += 1
        return count

    def would_capture(dir, er, ec):
        # If playing this edge would complete any boxes
        key = (dir, er, ec)
        boxes_on_edge = edge_to_boxes.get(key, [])
        for (r, c) in boxes_on_edge:
            # If the box has exactly 3 edges already drawn, playing the 4th completes it
            if count_box_edges(r, c) == 3:
                return True
        return False

    def would_give_away(dir, er, ec):
        # If playing this edge would create a box with exactly 3 sides after the move,
        # and that box is not captured immediately, it would give away a free box to opponent.
        key = (dir, er, ec)
        boxes_on_edge = edge_to_boxes.get(key, [])
        for (r, c) in boxes_on_edge:
            before = count_box_edges(r, c)
            if before == 2:
                # This move creates a 3-edge box (not captured)
                return True
        return False

    # Scoring function: higher is better
    def score_move(dir, er, ec):
        cap = would_capture(dir, er, ec)
        give = would_give_away(dir, er, ec)

        # Immediate capture is best (unless it gives away multiple boxes, but capturing ends turn)
        if cap:
            return 100

        # Avoid moves that create a 3-edge box
        if give:
            return -50

        # Prefer moves that complete boxes when available (handled above)
        # Otherwise, prefer moves that leave boxes at 1 edge (neutral) over 0 edges
        key = (dir, er, ec)
        boxes_on_edge = edge_to_boxes.get(key, [])
        edges_before = [count_box_edges(r, c) for (r, c) in boxes_on_edge]
        if not edges_before:
            return 0
        # Average edges before move; lower is better (avoid giving away)
        avg = sum(edges_before) / len(edges_before)
        return -avg  # higher when avg is smaller

    # Collect all legal moves and score
    candidates = []
    for (er, ec) in legal_h:
        candidates.append(('H', er, ec, score_move('H', er, ec)))
    for (er, ec) in legal_v:
        candidates.append(('V', er, ec, score_move('V', er, ec)))

    # Sort by score descending
    candidates.sort(key=lambda x: x[3], reverse=True)

    # Pick the best move
    best_dir, best_er, best_ec, best_score = candidates[0]
    return f"{best_er},{best_ec},{best_dir}"

