
import numpy as np

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    directions = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),          (0, 1),
        ( 1, -1), ( 1, 0), ( 1, 1)
    ]

    moves = []

    for r in range(8):
        for c in range(8):
            if you[r, c] or opponent[r, c]:
                continue  # Skip occupied cells.

            flips = 0
            for dr, dc in directions:
                tr, tc = r + dr, c + dc
                if tr < 0 or tr >= 8 or tc < 0 or tc >= 8:
                    continue
                if you[tr, tc] == 1:
                    continue  # Skip own disc.
                if opponent[tr][tc] == 0:
                    continue  # Empty cell.

                count = 0
                path = []
                valid = False
                while True:
                    path.append((tr, tc))
                    tr += dr
                    tc += dc

                    if not (0 <= tr < 8 and 0 <= tc < 8):
                        break

                    if you[tr, tc] == 1 and opponent[tr, tc] == 0:
                        # Found my own disc: valid sequence
                        if len(path) > 0:
                            flips += len(path)
                        break
                    elif you[tr, tc] == 0 and opponent[tr, tc] == 0:
                        break

            if flips > 0:
                moves.append((r, c, flips))

    if not moves:
        return "pass"

    max_flips = max(move[2] for move in moves)
    candidates = [(r, c) for r, c, f in moves if f == max_flips]

    # Prioritize corners: (0,0), (0,7), (7,0), (7,7)
    corner_order = [(0, 0), (0, 7), (7, 0), (7, 7)]
    for corner in corner_order:
        if corner in candidates:
            selected_r, selected_c = corner
            break
    else:
        # No corner move available
        selected_r, selected_c = candidates[0]

    return chr(ord('a') + selected_c) + str(selected_r + 1)
