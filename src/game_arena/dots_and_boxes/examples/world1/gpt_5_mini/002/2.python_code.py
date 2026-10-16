
import numpy as np
import random

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Return a legal move 'row,col,dir' for Dots and Boxes on a 4x4 box grid.
    horizontal: 5x5 array, valid horizontal edges are at cols 0..3, rows 0..4
    vertical:   5x5 array, valid vertical edges are at rows 0..3, cols 0..4
    capture: 4x4 array of box ownerships (not directly needed for move legality)
    """
    # Helper: valid ranges
    def valid_H(r, c):
        return 0 <= r <= 4 and 0 <= c <= 3

    def valid_V(r, c):
        return 0 <= r <= 3 and 0 <= c <= 4

    # Count filled sides of box (br,bc) where 0 <= br,bc <= 3
    def box_filled(br, bc):
        cnt = 0
        # top
        if horizontal[br, bc] != 0:
            cnt += 1
        # bottom
        if horizontal[br + 1, bc] != 0:
            cnt += 1
        # left
        if vertical[br, bc] != 0:
            cnt += 1
        # right
        if vertical[br, bc + 1] != 0:
            cnt += 1
        return cnt

    # Get adjacent boxes for an H edge at (r,c)
    def adjacent_boxes_H(r, c):
        boxes = []
        # box below the horizontal edge is (r, c) if r < 4
        if 0 <= r < 4 and 0 <= c < 4:
            boxes.append((r, c))
        # box above is (r-1, c) if r > 0
        if 1 <= r <= 4 and 0 <= c < 4:
            boxes.append((r - 1, c))
        return boxes

    # Get adjacent boxes for a V edge at (r,c)
    def adjacent_boxes_V(r, c):
        boxes = []
        # box right of the vertical edge is (r, c) if c < 4
        if 0 <= r < 4 and 0 <= c < 4:
            boxes.append((r, c))
        # box left is (r, c-1) if c > 0
        if 0 <= r < 4 and 1 <= c <= 4:
            boxes.append((r, c - 1))
        return boxes

    legal_moves = []

    # Gather legal horizontal moves
    for r in range(0, 5):
        for c in range(0, 4):
            if horizontal[r, c] == 0:
                legal_moves.append(('H', r, c))

    # Gather legal vertical moves
    for r in range(0, 4):
        for c in range(0, 5):
            if vertical[r, c] == 0:
                legal_moves.append(('V', r, c))

    # If no legal moves (game over), return a fallback (shouldn't usually happen)
    if not legal_moves:
        return '0,0,H'

    # Evaluate each legal move
    move_infos = []
    for dirc, r, c in legal_moves:
        if dirc == 'H':
            adj = adjacent_boxes_H(r, c)
        else:
            adj = adjacent_boxes_V(r, c)

        counts = [box_filled(br, bc) for (br, bc) in adj]

        # How many boxes this move would immediately capture? (boxes currently with 3 sides)
        captures_now = sum(1 for x in counts if x == 3)
        # How many boxes would become 3-sided for opponent after this move? (currently 2 sides)
        would_create_threes = sum(1 for x in counts if x == 2)
        # Sum of current counts (lower is safer)
        sum_counts = sum(counts)
        # Number of adjacent boxes (1 or 2)
        adjacent_count = len(adj)

        move_infos.append({
            'dir': dirc,
            'r': r,
            'c': c,
            'captures_now': captures_now,
            'would_create_threes': would_create_threes,
            'sum_counts': sum_counts,
            'adjacent_count': adjacent_count,
            'counts': counts
        })

    # 1) If any immediate captures exist, take the move that captures the most boxes.
    best_captures = max(info['captures_now'] for info in move_infos)
    if best_captures > 0:
        best_moves = [m for m in move_infos if m['captures_now'] == best_captures]
        choice = random.choice(best_moves)
        return f"{choice['r']},{choice['c']},{choice['dir']}"

    # 2) Safe moves: those that do NOT create any 3-sided boxes (i.e., no adjacent box currently has 2 sides)
    safe_moves = [m for m in move_infos if m['would_create_threes'] == 0]
    if safe_moves:
        # Prefer moves that touch boxes with fewer filled sides (favor expansion)
        # Score = (number of adjacent boxes with 0 sides, then -sum_counts)
        def safe_score(m):
            zeros = sum(1 for x in m['counts'] if x == 0)
            return (zeros, -m['sum_counts'])
        best_score = max(safe_score(m) for m in safe_moves)
        best_moves = [m for m in safe_moves if safe_score(m) == best_score]
        choice = random.choice(best_moves)
        return f"{choice['r']},{choice['c']},{choice['dir']}"

    # 3) No safe moves: minimize the number of boxes you'll create that are 3-sided (minimize immediate gifts).
    min_threes = min(m['would_create_threes'] for m in move_infos)
    candidate_moves = [m for m in move_infos if m['would_create_threes'] == min_threes]
    if len(candidate_moves) > 1:
        # Tie-breaker: choose move with smallest sum_counts (less potential for chains)
        min_sum = min(m['sum_counts'] for m in candidate_moves)
        candidate_moves = [m for m in candidate_moves if m['sum_counts'] == min_sum]

    choice = random.choice(candidate_moves)
    return f"{choice['r']},{choice['c']},{choice['dir']}"
