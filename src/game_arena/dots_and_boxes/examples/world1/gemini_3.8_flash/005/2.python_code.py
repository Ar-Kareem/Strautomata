
import numpy as np

def _get_box_edges(r: int, c: int):
    """Returns the four edges bounding box (r, c)."""
    return [
        (r, c, 'H'),      # top
        (r + 1, c, 'H'),  # bottom
        (r, c, 'V'),      # left
        (r, c + 1, 'V')   # right
    ]

def _is_edge_drawn(horizontal: np.ndarray, vertical: np.ndarray, r: int, c: int, orientation: str) -> bool:
    if orientation == 'H':
        return horizontal[r, c] != 0
    else:
        return vertical[r, c] != 0

def _get_boxes_for_edge(r: int, c: int, orientation: str):
    """Returns the coordinates of boxes adjacent to a given edge in a 4x4 grid."""
    boxes = []
    if orientation == 'H':
        if r > 0:
            boxes.append((r - 1, c))
        if r < 4:
            boxes.append((r, c))
    else:  # 'V'
        if c > 0:
            boxes.append((r, c - 1))
        if c < 4:
            boxes.append((r, c))
    return boxes

def _count_box_edges(horizontal: np.ndarray, vertical: np.ndarray, r: int, c: int) -> int:
    """Counts how many of the 4 edges of box (r, c) have been drawn."""
    count = 0
    if horizontal[r, c] != 0:
        count += 1
    if horizontal[r + 1, c] != 0:
        count += 1
    if vertical[r, c] != 0:
        count += 1
    if vertical[r, c + 1] != 0:
        count += 1
    return count

def _simulate_chain_length(h: np.ndarray, v: np.ndarray, start_move):
    """
    Simulates greedy capture sequence starting from a sacrifice move
    to estimate the number of boxes conceded to the opponent.
    """
    h_copy = h.copy()
    v_copy = v.copy()
    
    r, c, orient = start_move
    if orient == 'H':
        h_copy[r, c] = 1
    else:
        v_copy[r, c] = 1

    total_conceded = 0
    while True:
        found_box = False
        for br in range(4):
            for bc in range(4):
                if _count_box_edges(h_copy, v_copy, br, bc) == 3:
                    # Find missing edge and fill it
                    for er, ec, eo in _get_box_edges(br, bc):
                        if not _is_edge_drawn(h_copy, v_copy, er, ec, eo):
                            if eo == 'H':
                                h_copy[er, ec] = 1
                            else:
                                v_copy[er, ec] = 1
                            total_conceded += 1
                            found_box = True
                            break
                    if found_box:
                        break
            if found_box:
                break
        if not found_box:
            break

    return total_conceded

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Dots and Boxes policy for 4x4 box grid.
    Returns move formatted as 'row,col,dir'.
    """
    # 1. Identify all valid playable grid edges (5x4 horizontal, 4x5 vertical)
    legal_moves = []
    
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] == 0:
                legal_moves.append((r, c, 'H'))

    for r in range(4):
        for c in range(5):
            if vertical[r, c] == 0:
                legal_moves.append((r, c, 'V'))

    # Fallback to any remaining 0 in arrays if standard set is somehow empty
    if not legal_moves:
        for r in range(horizontal.shape[0]):
            for c in range(horizontal.shape[1]):
                if horizontal[r, c] == 0:
                    return f"{r},{c},H"
        for r in range(vertical.shape[0]):
            for c in range(vertical.shape[1]):
                if vertical[r, c] == 0:
                    return f"{r},{c},V"

    # 2. Priority 1: Captures (edges completing a 3-sided box)
    captures = []
    for move in legal_moves:
        r, c, orient = move
        adj_boxes = _get_boxes_for_edge(r, c, orient)
        boxes_completed = sum(1 for br, bc in adj_boxes if _count_box_edges(horizontal, vertical, br, bc) == 3)
        if boxes_completed > 0:
            captures.append((boxes_completed, move))

    if captures:
        # Prefer moves capturing 2 boxes simultaneously
        captures.sort(key=lambda x: x[0], reverse=True)
        best_move = captures[0][1]
        return f"{best_move[0]},{best_move[1]},{best_move[2]}"

    # 3. Priority 2: Safe Moves (moves that do not create any 3-sided box)
    safe_moves = []
    for move in legal_moves:
        r, c, orient = move
        adj_boxes = _get_boxes_for_edge(r, c, orient)
        # Safe if none of the adjacent boxes currently have 2 edges filled
        is_safe = all(_count_box_edges(horizontal, vertical, br, bc) < 2 for br, bc in adj_boxes)
        if is_safe:
            # Score safe moves: prefer edges bounded by boxes with 0 sides filled
            edge_score = sum(1 for br, bc in adj_boxes if _count_box_edges(horizontal, vertical, br, bc) == 0)
            safe_moves.append((edge_score, move))

    if safe_moves:
        safe_moves.sort(key=lambda x: x[0], reverse=True)
        best_move = safe_moves[0][1]
        return f"{best_move[0]},{best_move[1]},{best_move[2]}"

    # 4. Priority 3: Sacrifices (minimize boxes surrendered)
    best_move = None
    min_conceded = 999

    for move in legal_moves:
        conceded = _simulate_chain_length(horizontal, vertical, move)
        if conceded < min_conceded:
            min_conceded = conceded
            best_move = move

    if best_move is None:
        best_move = legal_moves[0]

    return f"{best_move[0]},{best_move[1]},{best_move[2]}"
