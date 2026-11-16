
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Greedy-safe policy for Dots and Boxes on 4x4 grid.
    Always capture boxes when possible.
    Otherwise avoid creating 3-sided boxes.
    If unavoidable, minimize the number of 3-sided boxes created.
    """
    moves = []

    # Legal horizontal edges: row 0-4, col 0-3
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] == 0:
                moves.append((r, c, 'H'))

    # Legal vertical edges: row 0-3, col 0-4
    for r in range(4):
        for c in range(5):
            if vertical[r, c] == 0:
                moves.append((r, c, 'V'))

    # If no moves (shouldn't happen), return something legal-ish
    if not moves:
        return "0,0,H"

    def count_box_sides(br, bc):
        # Count sides of box (br, bc)
        return int(horizontal[br, bc] != 0) + int(horizontal[br + 1, bc] != 0) + \
               int(vertical[br, bc] != 0) + int(vertical[br, bc + 1] != 0)

    def adjacent_boxes(move):
        r, c, d = move
        boxes = []
        if d == 'H':
            if r > 0:  # box above
                boxes.append((r - 1, c))
            if r < 4:  # box below
                boxes.append((r, c))
        else:  # 'V'
            if c > 0:  # box left
                boxes.append((r, c - 1))
            if c < 4:  # box right
                boxes.append((r, c))
        return boxes

    evaluated = []
    for move in moves:
        r, c, d = move
        boxes = adjacent_boxes(move)
        captures = 0
        threes = 0
        for br, bc in boxes:
            before = count_box_sides(br, bc)
            after = before + 1  # this edge adds one side
            if after == 4:
                captures += 1
            elif after == 3:
                threes += 1
        evaluated.append((move, captures, threes))

    # Prioritize capturing moves
    capture_moves = [e for e in evaluated if e[1] > 0]
    if capture_moves:
        # Maximize captures, then minimize threes
        capture_moves.sort(key=lambda x: (-x[1], x[2]))
        best_move = capture_moves[0][0]
        return f"{best_move[0]},{best_move[1]},{best_move[2]}"

    # No capture moves: choose safe move (no new 3-sided boxes)
    safe_moves = [e for e in evaluated if e[2] == 0]
    if safe_moves:
        # If multiple safe moves, choose first (deterministic)
        best_move = safe_moves[0][0]
        return f"{best_move[0]},{best_move[1]},{best_move[2]}"

    # No safe moves: minimize number of new 3-sided boxes
    evaluated.sort(key=lambda x: x[2])
    best_move = evaluated[0][0]
    return f"{best_move[0]},{best_move[1]},{best_move[2]}"
