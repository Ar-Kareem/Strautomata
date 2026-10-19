
import numpy as np

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    def is_valid(r, c):
        directions = [(-1, -1), (-1, 0), (-1, 1),
                      (0, -1),          (0, 1),
                      (1, -1),  (1, 0), (1, 1)]
        if you[r][c] != 0 or opponent[r][c] != 0:
            return False
        for dr, dc in directions:
            current_r, current_c = r + dr, c + dc
            has_opponent = False
            while 0 <= current_r < 8 and 0 <= current_c < 8:
                if opponent[current_r][current_c] == 1:
                    has_opponent = True
                    current_r += dr
                    current_c += dc
                elif you[current_r][current_c] == 1:
                    if has_opponent:
                        return True
                    else:
                        break
                else:
                    break
        return False

    def count_flips(r, c):
        directions = [(-1, -1), (-1, 0), (-1, 1),
                      (0, -1),          (0, 1),
                      (1, -1),  (1, 0), (1, 1)]
        total = 0
        for dr, dc in directions:
            current_r, current_c = r + dr, c + dc
            flipped = 0
            while 0 <= current_r < 8 and 0 <= current_c < 8:
                if opponent[current_r][current_c] == 1:
                    flipped += 1
                    current_r += dr
                    current_c += dc
                else:
                    break
            if 0 <= current_r < 8 and 0 <= current_c < 8 and you[current_r][current_c] == 1:
                total += flipped
        return total

    legal_moves = []
    for r in range(8):
        for c in range(8):
            if you[r][c] == 0 and opponent[r][c] == 0:
                if is_valid(r, c):
                    legal_moves.append((r, c))
    if not legal_moves:
        return "pass"

    position_values = np.array([
        [ 20,  -3,  11,   8,   8,  11,  -3,  20],
        [-3, -7, -4,  1,  1, -4, -7, -3],
        [11, -4,  2,  2,  2,  2, -4, 11],
        [ 8,  1,  2, -3, -3,  2,  1,  8],
        [ 8,  1,  2, -3, -3,  2,  1,  8],
        [11, -4,  2,  2,  2,  2, -4, 11],
        [-3, -7, -4,  1,  1, -4, -7, -3],
        [ 20,  -3,  11,   8,   8,  11,  -3,  20],
    ])

    best_move = None
    best_score = -float('inf')
    for r, c in legal_moves:
        flips = count_flips(r, c)
        score = flips * 10 + position_values[r][c]
        if score > best_score:
            best_score = score
            best_move = (r, c)

    r, c = best_move
    col = chr(ord('a') + c)
    row = str(r + 1)
    return col + row
