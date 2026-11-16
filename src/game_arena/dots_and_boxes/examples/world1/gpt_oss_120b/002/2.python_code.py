
import numpy as np

def _adjacent_boxes(row: int, col: int, dir: str):
    """Return list of (box_row, box_col) that are touched by the edge."""
    boxes = []
    if dir == 'H':
        # horizontal edge at (row, col) touches box above (row-1,col) and below (row,col)
        if row > 0:
            boxes.append((row - 1, col))
        if row < 4:  # there are only 4 rows of boxes
            boxes.append((row, col))
    else:  # dir == 'V'
        # vertical edge at (row, col) touches box left (row,col-1) and right (row,col)
        if col > 0:
            boxes.append((row, col - 1))
        if col < 4:  # there are only 4 columns of boxes
            boxes.append((row, col))
    return boxes

def _box_side_count(box_row: int, box_col: int, horiz: np.ndarray, vert: np.ndarray):
    """Count how many of the four sides of the box are already drawn."""
    cnt = 0
    # top
    if horiz[box_row, box_col] != 0:
        cnt += 1
    # bottom
    if horiz[box_row + 1, box_col] != 0:
        cnt += 1
    # left
    if vert[box_row, box_col] != 0:
        cnt += 1
    # right
    if vert[box_row, box_col + 1] != 0:
        cnt += 1
    return cnt

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Return a legal move string 'row,col,dir' for a 4x4 Dots and Boxes board.
    """
    # ------------------------------------------------------------
    # 1. Gather all empty edges
    # ------------------------------------------------------------
    empty_edges = []

    # Horizontal edges: rows 0..4, cols 0..3
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] == 0:
                empty_edges.append((r, c, 'H'))

    # Vertical edges: rows 0..3, cols 0..4
    for r in range(4):
        for c in range(5):
            if vertical[r, c] == 0:
                empty_edges.append((r, c, 'V'))

    # ------------------------------------------------------------
    # 2. Look for capture moves (edges that close at least one box)
    # ------------------------------------------------------------
    capture_moves = []
    max_boxes = 0

    for (r, c, d) in empty_edges:
        boxes = _adjacent_boxes(r, c, d)
        completed = 0
        for br, bc in boxes:
            if _box_side_count(br, bc, horizontal, vertical) == 3:
                completed += 1
        if completed > 0:
            if completed > max_boxes:
                max_boxes = completed
                capture_moves = [(r, c, d)]
            elif completed == max_boxes:
                capture_moves.append((r, c, d))

    if capture_moves:
        # Prefer the move that captures the most boxes (all in list have same count)
        r, c, d = capture_moves[np.random.randint(len(capture_moves))]
        return f"{r},{c},{d}"

    # ------------------------------------------------------------
    # 3. Safe moves – avoid creating a box with exactly three sides
    # ------------------------------------------------------------
    safe_moves = []
    for (r, c, d) in empty_edges:
        boxes = _adjacent_boxes(r, c, d)
        creates_three = False
        for br, bc in boxes:
            cnt = _box_side_count(br, bc, horizontal, vertical)
            if cnt == 2:  # after we draw, it would become 3
                creates_three = True
                break
        if not creates_three:
            safe_moves.append((r, c, d))

    if safe_moves:
        r, c, d = safe_moves[np.random.randint(len(safe_moves))]
        return f"{r},{c},{d}"

    # ------------------------------------------------------------
    # 4. No safe moves – we are forced to give a critical box.
    #    Pick any remaining edge.
    # ------------------------------------------------------------
    r, c, d = empty_edges[np.random.randint(len(empty_edges))]
    return f"{r},{c},{d}"
