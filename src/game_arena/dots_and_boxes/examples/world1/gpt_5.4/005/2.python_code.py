
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    N = 4  # 4x4 boxes, arrays are 5x5

    def box_sides_after(h, v, r, c):
        return (
            1 if h[r, c] != 0 else 0
        ) + (
            1 if h[r + 1, c] != 0 else 0
        ) + (
            1 if v[r, c] != 0 else 0
        ) + (
            1 if v[r, c + 1] != 0 else 0
        )

    def adjacent_boxes(move):
        r, c, d = move
        boxes = []
        if d == 'H':
            if r > 0 and c < N:
                boxes.append((r - 1, c))
            if r < N and c < N:
                boxes.append((r, c))
        else:  # 'V'
            if c > 0 and r < N:
                boxes.append((r, c - 1))
            if c < N and r < N:
                boxes.append((r, c))
        return boxes

    def simulate_move(move):
        r, c, d = move
        h = horizontal.copy()
        v = vertical.copy()

        if d == 'H':
            h[r, c] = 1
        else:
            v[r, c] = 1

        completed = 0
        made_threes = 0
        side_sum = 0

        for br, bc in adjacent_boxes(move):
            if capture[br, bc] != 0:
                continue
            sides = box_sides_after(h, v, br, bc)
            side_sum += sides
            if sides == 4:
                completed += 1
            elif sides == 3:
                made_threes += 1

        return completed, made_threes, side_sum

    legal_moves = []

    # Horizontal edges that exist in play: rows 0..4, cols 0..3
    for r in range(N + 1):
        for c in range(N):
            if horizontal[r, c] == 0:
                legal_moves.append((r, c, 'H'))

    # Vertical edges that exist in play: rows 0..3, cols 0..4
    for r in range(N):
        for c in range(N + 1):
            if vertical[r, c] == 0:
                legal_moves.append((r, c, 'V'))

    # Absolute fallback: scan all provided cells in case arena uses a looser encoding.
    if not legal_moves:
        for r in range(horizontal.shape[0]):
            for c in range(horizontal.shape[1]):
                if horizontal[r, c] == 0:
                    return f"{r},{c},H"
        for r in range(vertical.shape[0]):
            for c in range(vertical.shape[1]):
                if vertical[r, c] == 0:
                    return f"{r},{c},V"
        return "0,0,H"

    scored = []
    for mv in legal_moves:
        completed, made_threes, side_sum = simulate_move(mv)
        scored.append((mv, completed, made_threes, side_sum))

    # 1. Take captures immediately, preferring bigger captures.
    capturing = [x for x in scored if x[1] > 0]
    if capturing:
        # Maximize boxes completed, then minimize new 3-siders, then prefer larger local fill.
        capturing.sort(key=lambda x: (-x[1], x[2], -x[3], x[0][2], x[0][0], x[0][1]))
        r, c, d = capturing[0][0]
        return f"{r},{c},{d}"

    # 2. Prefer safe moves that do not create any 3-sided box.
    safe = [x for x in scored if x[2] == 0]
    if safe:
        # Among safe moves, prefer lower side_sum (less advancement toward dangerous boxes).
        safe.sort(key=lambda x: (x[3], x[0][2], x[0][0], x[0][1]))
        r, c, d = safe[0][0]
        return f"{r},{c},{d}"

    # 3. If forced, minimize number of 3-sided boxes created.
    scored.sort(key=lambda x: (x[2], x[3], x[0][2], x[0][0], x[0][1]))
    r, c, d = scored[0][0]
    return f"{r},{c},{d}"
