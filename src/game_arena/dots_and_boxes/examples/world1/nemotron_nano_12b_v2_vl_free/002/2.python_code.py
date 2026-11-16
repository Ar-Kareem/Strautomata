
import numpy as np

def policy(horizontal, vertical, capture):
    def get_adjacent_boxes(row, col, direction):
        boxes = []
        if direction == 'H':
            if row < 4:
                boxes.append((row, col))
            if row > 0:
                boxes.append((row - 1, col))
        else:
            if c > 0:
                boxes.append((row, c - 1))
            if c <= 3:
                boxes.append((row, c))
        return boxes

    possible_moves = []
    for r in range(5):
        for c in range(5):
            if horizontal[r, c] == 0:
                possible_moves.append((r, c, 'H'))
    for r in range(5):
        for c in range(5):
            if vertical[r, c] == 0:
                possible_moves.append((r, c, 'V'))

    captures = {}
    three_edge = {}
    for move in possible_moves:
        r, c, d = move
        boxes = get_adjacent_boxes(r, c, d)
        captured = 0
        three_edges_count = 0
        for (i, j) in boxes:
            sum_before = 0
            # Check top edge (box's top edge is horizontal[i][j])
            if not (d == 'H' and r == i and c == j):
                sum_before += horizontal[i, j] != 0
            # Check right edge (box's right edge is vertical[i][j+1])
            if not (d == 'V' and r == i and c == j + 1):
                sum_before += vertical[i, j + 1] != 0
            # Check bottom edge (box's bottom edge is horizontal[i+1][j])
            if not (d == 'H' and r == i + 1 and c == j):
                sum_before += horizontal[i + 1, j] != 0
            # Check left edge (box's left edge is vertical[i][j])
            if not (d == 'V' and r == i and c == j):
                sum_before += vertical[i, j] != 0
            # Determine if this move completes the box or creates a three-edge box
            if sum_before == 3:
                captured += 1
            if sum_before == 2:
                three_edges_count += 1
        # Update dictionaries
        captures[move] = captured
        three_edge[move] = three_edges_count

    # Determine capturing moves and select best move
    capturing_moves = [m for m in possible_moves if captures[m] > 0]
    if capturing_moves:
        max_caps = max(captures.values())
        candidates = [m for m in possible_moves if captures[m] == max_caps]
        candidates.sort(key=lambda m: (m[0], m[1], m[2] == 'V'))
        return f"{candidates[0][0]},{candidates[0][1]},{candidates[0][2]}"
    else:
        # Find move with minimum three-edge boxes created
        min_three = min(three_edge.values())
        candidates = [m for m in possible_moves if three_edge[m] == min_three]
        candidates.sort(key=lambda m: (m[0], m[1], m[2] == 'V'))
        return f"{candidates[0][0]},{candidates[0][1]},{candidates[0][2]}"
