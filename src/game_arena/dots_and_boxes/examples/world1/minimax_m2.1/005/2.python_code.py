
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Generate all legal moves
    moves = []
    # Horizontal moves: i in [0,4], j in [0,3]
    for i in range(5):
        for j in range(4):
            if horizontal[i, j] == 0:
                moves.append((i, j, 'H'))
    # Vertical moves: i in [0,3], j in [0,4]
    for i in range(4):
        for j in range(5):
            if vertical[i, j] == 0:
                moves.append((i, j, 'V'))

    # Helper functions
    def get_boxes_for_horizontal_edge(i, j):
        boxes = []
        # Box above
        if i > 0:
            box_i = i-1
            box_j = j
            if 0 <= box_i < 4 and 0 <= box_j < 4:
                boxes.append((box_i, box_j))
        # Box below
        if i < 4:
            box_i = i
            box_j = j
            if 0 <= box_i < 4 and 0 <= box_j < 4:
                boxes.append((box_i, box_j))
        return boxes

    def get_boxes_for_vertical_edge(i, j):
        boxes = []
        # Box to the left
        if j > 0:
            box_i = i
            box_j = j-1
            if 0 <= box_i < 4 and 0 <= box_j < 4:
                boxes.append((box_i, box_j))
        # Box to the right
        if j < 4:
            box_i = i
            box_j = j
            if 0 <= box_i < 4 and 0 <= box_j < 4:
                boxes.append((box_i, box_j))
        return boxes

    def simulate_move(move):
        i, j, dir = move
        h = horizontal.copy()
        v = vertical.copy()
        c = capture.copy()
        captured_boxes = []
        three_sided_boxes = []

        if dir == 'H':
            if h[i, j] != 0:
                return None
            h[i, j] = 1
            boxes = get_boxes_for_horizontal_edge(i, j)
        else:
            if v[i, j] != 0:
                return None
            v[i, j] = 1
            boxes = get_boxes_for_vertical_edge(i, j)

        for (box_i, box_j) in boxes:
            if c[box_i, box_j] != 0:
                continue
            count = 0
            # Top edge
            if h[box_i, box_j] != 0:
                count += 1
            # Bottom edge
            if h[box_i+1, box_j] != 0:
                count += 1
            # Left edge
            if v[box_i, box_j] != 0:
                count += 1
            # Right edge
            if v[box_i, box_j+1] != 0:
                count += 1

            if count == 4:
                captured_boxes.append((box_i, box_j))
                c[box_i, box_j] = 1
            elif count == 3:
                three_sided_boxes.append((box_i, box_j))

        return {
            'captured': captured_boxes,
            'three_sided': three_sided_boxes
        }

    def compute_degree(box):
        i, j = box
        deg = 0
        if i > 0:
            if capture[i-1, j] == 0:
                deg += 1
        if i < 3:
            if capture[i+1, j] == 0:
                deg += 1
        if j > 0:
            if capture[i, j-1] == 0:
                deg += 1
        if j < 3:
            if capture[i, j+1] == 0:
                deg += 1
        return deg

    candidate1 = []
    candidate2 = []
    candidate3 = []

    for move in moves:
        sim = simulate_move(move)
        if sim is None:
            continue
        num_captured = len(sim['captured'])
        num_three_sided = len(sim['three_sided'])

        if num_captured > 0:
            candidate1.append( (move, num_captured, num_three_sided) )
        elif num_three_sided == 0:
            candidate2.append(move)
        else:
            max_degree = -1
            for box in sim['three_sided']:
                deg = compute_degree(box)
                if deg > max_degree:
                    max_degree = deg
            candidate3.append( (move, max_degree, num_three_sided) )

    if candidate1:
        candidate1.sort(key=lambda x: (-x[1], x[2]))
        move = candidate1[0][0]
        return f"{move[0]},{move[1]},{move[2]}"
    elif candidate2:
        move = candidate2[0]
        return f"{move[0]},{move[1]},{move[2]}"
    else:
        candidate3.sort(key=lambda x: (x[1], x[2]))
        move = candidate3[0][0]
        return f"{move[0]},{move[1]},{move[2]}"
