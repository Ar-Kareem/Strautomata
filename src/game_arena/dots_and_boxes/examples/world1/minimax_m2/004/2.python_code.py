
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Collect legal moves
    legal_moves = []
    for r in range(5):
        for c in range(5):
            if horizontal[r, c] == 0:
                legal_moves.append((r, c, 'H'))
            if vertical[r, c] == 0:
                legal_moves.append((r, c, 'V'))

    best_score = -10**9
    best_move = None

    for r, c, d in legal_moves:
        # Create copies
        h = horizontal.copy()
        v = vertical.copy()
        cap = capture.copy()

        # Set the edge
        if d == 'H':
            h[r, c] = 1
        else:
            v[r, c] = 1

        # Determine the boxes adjacent to the new edge
        boxes = []
        if d == 'H':
            if r - 1 >= 0:
                boxes.append((r-1, c))
            if r < 4:
                boxes.append((r, c))
        else:  # 'V'
            if c - 1 >= 0:
                boxes.append((r, c-1))
            if c < 4:
                boxes.append((r, c))

        # Check for completed boxes
        for i, j in boxes:
            if cap[i, j] == 0:
                # Check if all four edges are drawn
                if h[i, j] != 0 and h[i+1, j] != 0 and v[i, j] != 0 and v[i, j+1] != 0:
                    cap[i, j] = 1

        # Count captures
        captures = 0
        for i in range(4):
            for j in range(4):
                if capture[i, j] == 0 and cap[i, j] == 1:
                    captures += 1

        # Count three-sided boxes
        three = 0
        for i in range(4):
            for j in range(4):
                if cap[i, j] == 0:
                    drawn = 0
                    if h[i, j] != 0:
                        drawn += 1
                    if h[i+1, j] != 0:
                        drawn += 1
                    if v[i, j] != 0:
                        drawn += 1
                    if v[i, j+1] != 0:
                        drawn += 1
                    if drawn == 3:
                        three += 1

        score = captures - three

        if score > best_score:
            best_score = score
            best_move = (r, c, d)

    # Format the move
    return f"{best_move[0]},{best_move[1]},{best_move[2]}"
