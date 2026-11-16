
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Generate all legal moves
    legal_moves = []
    for r in range(5):
        for c in range(5):
            if horizontal[r][c] == 0:
                legal_moves.append((r, c, 'H'))
            if vertical[r][c] == 0:
                legal_moves.append((r, c, 'V'))

    # Helper function to check completed boxes for a move
    def get_completed_boxes(r, c, dir):
        boxes = []
        if dir == 'H':
            for (box_r, box_c) in [(r, c), (r - 1, c)]:
                if 0 <= box_r <= 3 and 0 <= box_c <= 3:
                    top = horizontal[box_r][box_c]
                    bottom = horizontal[box_r + 1][box_c]
                    left = vertical[box_r][box_c]
                    right = vertical[box_r][box_c + 1]
                    top_val = 1 if (box_r == r and box_c == c) else top
                    filled = sum([top_val != 0, bottom != 0, left != 0, right != 0])
                    if filled == 4:
                        boxes.append((box_r, box_c))
        else:  # vertical
            for (box_r, box_c) in [(r, c - 1), (r, c)]:
                if 0 <= box_r <= 3 and 0 <= box_c <= 3:
                    top = horizontal[box_r][box_c]
                    bottom = horizontal[box_r + 1][box_c]
                    left_val = 1 if (box_r == r and box_c == c) else vertical[box_r][box_c]
                    right_val = 1 if (box_r == r and box_c + 1 == c) else vertical[box_r][box_c + 1]
                    filled = sum([top != 0, bottom != 0, left_val != 0, right_val != 0])
                    if filled == 4:
                        boxes.append((box_r, box_c))
        return boxes

    # Check for moves that complete boxes
    capture_moves = []
    for move in legal_moves:
        r, c, dir = move
        boxes = get_completed_boxes(r, c, dir)
        if boxes:
            capture_moves.append((move, len(boxes)))

    if capture_moves:
        # Prioritize moves that complete the most boxes
        capture_moves.sort(key=lambda x: -x[1])
        return f"{capture_moves[0][0][0]},{capture_moves[0][0][1]},{capture_moves[0][0][2]}"

    # Otherwise, minimize opponent scoring threats by checking 3-edge boxes
    min_threat = float('inf')
    best_moves = []
    for move in legal_moves:
        r, c, dir = move
        # Simulate the move
        temp_h = horizontal.copy()
        temp_v = vertical.copy()
        if dir == 'H':
            temp_h[r][c] = 1
        else:
            temp_v[r][c] = 1

        # Count boxes with exactly three edges filled after the move
        threat = 0
        for box_r in range(4):
            for box_c in range(4):
                top = temp_h[box_r][box_c]
                bottom = temp_h[box_r + 1][box_c]
                left = temp_v[box_r][box_c]
                right = temp_v[box_r][box_c + 1]
                filled = sum([top != 0, bottom != 0, left != 0, right != 0])
                if filled == 3:
                    threat += 1

        if threat < min_threat:
            min_threat = threat
            best_moves = [move]
        elif threat == min_threat:
            best_moves.append(move)

    # Select the first move with minimal threat
    return f"{best_moves[0][0]},{best_moves[0][1]},{best_moves[0][2]}"
