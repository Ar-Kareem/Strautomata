
#!/usr/bin/env python3
"""
Dots and Boxes policy for a 4x4-box grid (5x5 dots).

Implements:
    def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str

Returns a move string "row,col,dir" where dir is "H" or "V".
"""

import numpy as np
from typing import List, Tuple

def _boxes_shape_from_edges(horizontal: np.ndarray) -> Tuple[int,int]:
    # horizontal is expected to be an N x N array for N dots (N=5)
    N = int(horizontal.shape[0])
    # number of boxes per side is N-1 (for 4x4 boxes, N=5)
    return N-1, N-1

def _sides_count(horizontal: np.ndarray, vertical: np.ndarray) -> np.ndarray:
    """
    Return an (N-1)x(N-1) array where each entry is the number of drawn sides
    (nonzero entries in horizontal/vertical) for the corresponding box.
    """
    N = int(horizontal.shape[0])
    R = N - 1
    counts = np.zeros((R, R), dtype=int)
    for r in range(R):
        for c in range(R):
            top = 1 if horizontal[r, c] != 0 else 0
            bottom = 1 if horizontal[r+1, c] != 0 else 0
            left = 1 if vertical[r, c] != 0 else 0
            right = 1 if vertical[r, c+1] != 0 else 0
            counts[r, c] = top + bottom + left + right
    return counts

def _adjacent_boxes_for_edge(row: int, col: int, dirc: str, N: int) -> List[Tuple[int,int]]:
    """
    Return list of (r,c) boxes adjacent to the given edge (row,col,dir).
    N is number of dots per side.
    Boxes indices r,c are in 0..N-2.
    """
    boxes = []
    R = N - 1
    if dirc == 'H':
        # horizontal at (row,col): above box at (row-1,col) if row>0; below box at (row,col) if row<R
        if col < R:
            if row > 0:
                boxes.append((row-1, col))
            if row < R:
                boxes.append((row, col))
    else:  # 'V'
        # vertical at (row,col): left box at (row,col-1) if col>0; right box at (row,col) if col<R
        if row < R:
            if col > 0:
                boxes.append((row, col-1))
            if col < R:
                boxes.append((row, col))
    return boxes

def _simulate_move_and_capture(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray,
                               move: Tuple[int,int,str]) -> Tuple[int, np.ndarray, np.ndarray, np.ndarray]:
    """
    Simulate playing move (row,col,dir) by the current player (we mark edges as 1).
    Then simulate all forced captures: while there is any unclaimed box with 3 sides,
    take its missing edge (which will complete it) and capture it. Continue until none.
    Return (num_captured, new_horizontal, new_vertical, new_capture).
    """
    h = horizontal.copy()
    v = vertical.copy()
    c = capture.copy()
    N = int(h.shape[0])
    row, col, dirc = move
    # Play the edge
    if dirc == 'H':
        h[row, col] = 1
    else:
        v[row, col] = 1

    total_captured = 0

    # First, capture any boxes that were immediately completed by this edge
    boxes = _sides_count(h, v)
    R = N - 1
    # Any box with 4 sides and unclaimed -> capture
    newly_captured = True
    while newly_captured:
        newly_captured = False
        for r in range(R):
            for colb in range(R):
                if c[r, colb] == 0 and boxes[r, colb] == 4:
                    # capture it
                    c[r, colb] = 1
                    total_captured += 1
                    newly_captured = True
        if newly_captured:
            # After marking these as captured, recalc boxes to find any with 3 sides
            boxes = _sides_count(h, v)

        # Now, while there exists any unclaimed box with exactly 3 sides, we can take its missing edge,
        # complete it and capture it (and possibly enable more).
        progress = True
        while progress:
            progress = False
            boxes = _sides_count(h, v)
            for r in range(R):
                for colb in range(R):
                    if c[r, colb] == 0 and boxes[r, colb] == 3:
                        # find the missing edge and play it
                        # check top
                        if h[r, colb] == 0:
                            h[r, colb] = 1
                        elif h[r+1, colb] == 0:
                            h[r+1, colb] = 1
                        elif v[r, colb] == 0:
                            v[r, colb] = 1
                        elif v[r, colb+1] == 0:
                            v[r, colb+1] = 1
                        else:
                            # Should not happen: no missing edge while sides==3
                            continue
                        # After playing that edge, this box will be complete -> capture
                        boxes = _sides_count(h, v)
                        # capture any boxes with 4 sides now
                        for rr in range(R):
                            for cc in range(R):
                                if c[rr, cc] == 0 and boxes[rr, cc] == 4:
                                    c[rr, cc] = 1
                                    total_captured += 1
                        progress = True
                        break
                if progress:
                    break
        # After capturing and forced fillings, recompute boxes to check loop
        boxes = _sides_count(h, v)

    return total_captured, h, v, c

def _evaluate_move_creates_threes(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray,
                                  move: Tuple[int,int,str]) -> int:
    """
    Evaluate how many unclaimed boxes will have exactly 3 sides after playing move (without performing captures).
    This is used to avoid creating 3-sided boxes for the opponent.
    """
    h = horizontal.copy()
    v = vertical.copy()
    row, col, dirc = move
    if dirc == 'H':
        h[row, col] = 1
    else:
        v[row, col] = 1
    boxes = _sides_count(h, v)
    R = boxes.shape[0]
    count = 0
    for r in range(R):
        for cidx in range(R):
            if capture[r, cidx] == 0 and boxes[r, cidx] == 3:
                count += 1
    return count

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Choose a move for the current player following the described heuristic.
    Returns "row,col,dir" where dir is "H" or "V".
    """
    # Ensure numpy arrays
    h = np.array(horizontal, copy=False)
    v = np.array(vertical, copy=False)
    c = np.array(capture, copy=False)

    N = int(h.shape[0])
    # Collect legal moves: any entry equal to 0 in the horizontal or vertical arrays
    legal_moves = []
    for r in range(N):
        for col in range(N):
            if h[r, col] == 0:
                legal_moves.append((r, col, 'H'))
            if v[r, col] == 0:
                legal_moves.append((r, col, 'V'))

    if len(legal_moves) == 0:
        # No legal moves (game finished). Return a default legal-looking move.
        # In practice this should not be called when no moves remain.
        return "0,0,H"

    # 1) If any move captures boxes immediately (possibly with forced follow-up captures), pick the one with max captures.
    best_capture_moves = []
    best_capture_count = -1
    for move in legal_moves:
        cap_count, _, _, _ = _simulate_move_and_capture(h, v, c, move)
        if cap_count > best_capture_count:
            best_capture_count = cap_count
            best_capture_moves = [move]
        elif cap_count == best_capture_count:
            best_capture_moves.append(move)

    if best_capture_count > 0:
        # choose deterministic best among best_capture_moves (lexicographic)
        chosen = min(best_capture_moves, key=lambda mv: (mv[0], mv[1], 0 if mv[2]=='H' else 1))
        return f"{chosen[0]},{chosen[1]},{chosen[2]}"

    # 2) No immediate captures. Prefer moves that create zero new 3-sided boxes.
    # Evaluate number of 3-sided boxes created by each move.
    evaluated = []
    for move in legal_moves:
        threes = _evaluate_move_creates_threes(h, v, c, move)
        # Also compute total sum of sides across boxes after move as a secondary heuristic (lower is better).
        h2 = h.copy()
        v2 = v.copy()
        if move[2] == 'H':
            h2[move[0], move[1]] = 1
        else:
            v2[move[0], move[1]] = 1
        sides_total = int(_sides_count(h2, v2).sum())
        evaluated.append((move, threes, sides_total))

    # Find minimum number of threes created
    min_threes = min(t for (_, t, _) in evaluated)
    candidates = [ (mv, t, s) for (mv,t,s) in evaluated if t == min_threes ]

    # If we can avoid creating any threes, take among them the one with minimal sides_total
    candidates.sort(key=lambda item: (item[1], item[2], item[0][0], item[0][1], 0 if item[0][2]=='H' else 1))
    chosen_move = candidates[0][0]
    return f"{chosen_move[0]},{chosen_move[1]},{chosen_move[2]}"
