
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # helper to check how many sides of box (r, c) are filled
    def count_sides(r, c):
        count = 0
        if horizontal[r, c] != 0: count += 1
        if horizontal[r + 1, c] != 0: count += 1
        if vertical[r, c] != 0: count += 1
        if vertical[r, c + 1] != 0: count += 1
        return count

    possible_h = []
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] == 0:
                possible_h.append((r, c))

    possible_v = []
    for r in range(4):
        for c in range(5):
            if vertical[r, c] == 0:
                possible_v.append((r, c))

    # 1. Capture moves (filling the 4th side)
    for r, c in possible_h:
        # Check box above and box below
        if (r > 0 and count_sides(r - 1, c) == 3) or (r < 4 and count_sides(r, c) == 3):
            return f"{r},{c},H"
    
    for r, c in possible_v:
        # Check box left and box right
        if (c > 0 and count_sides(r, c - 1) == 3) or (c < 4 and count_sides(r, c) == 3):
            return f"{r},{c},V"

    # 2. Safe moves (avoiding creating a 3rd side)
    safe_h = []
    for r, c in possible_h:
        is_safe = True
        if r > 0 and count_sides(r - 1, c) == 2:
            is_safe = False
        if r < 4 and count_sides(r, c) == 2:
            is_safe = False
        if is_safe:
            safe_h.append((r, c))

    safe_v = []
    for r, c in possible_v:
        is_safe = True
        if c > 0 and count_sides(r, c - 1) == 2:
            is_safe = False
        if c < 4 and count_sides(r, c) == 2:
            is_safe = False
        if is_safe:
            safe_v.append((r, c))

    if safe_h:
        r, c = safe_h[0]
        return f"{r},{c},H"
    if safe_v:
        r, c = safe_v[0]
        return f"{r},{c},V"

    # 3. Fallback: Take any move (usually sacrifices)
    if possible_h:
        r, c = possible_h[0]
        return f"{r},{c},H"
    if possible_v:
        r, c = possible_v[0]
        return f"{r},{c},V"

    return "0,0,H" # Should never reach here in a valid game state
