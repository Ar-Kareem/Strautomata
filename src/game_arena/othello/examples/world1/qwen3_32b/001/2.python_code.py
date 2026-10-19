
import numpy as np

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    position_weights = [
        [ 100, -10,  10,   5,   5,  10, -10, 100 ],
        [ -10, -20,  -5,  -5,  -5,  -5, -20, -10 ],
        [  10,  -5,   4,   2,   2,   4,  -5,  10 ],
        [   5,  -5,   2,   1,   1,   2,  -5,   5 ],
        [   5,  -5,   2,   1,   1,   2,  -5,   5 ],
        [  10,  -5,   4,   2,   2,   4,  -5,  10 ],
        [ -10, -20,  -5,  -5,  -5,  -5, -20, -10 ],
        [ 100, -10,  10,   5,   5,  10, -10, 100 ]
    ]
    
    def get_flipped_count(r, c):
        directions = [(-1, -1), (-1, 0), (-1, 1),
                      (0, -1),          (0, 1),
                      (1, -1),  (1, 0), (1, 1)]
        total_flips = 0
        for dx, dy in directions:
            x, y = r + dx, c + dy
            flips = 0
            if x < 0 or x >= 8 or y < 0 or y >= 8:
                continue
            if opponent[x][y] != 1:
                continue
            while True:
                flips += 1
                x += dx
                y += dy
                if x < 0 or x >= 8 or y < 0 or y >= 8:
                    break
                if you[x][y] == 1:
                    total_flips += flips
                    break
                if opponent[x][y] != 1:
                    break
        return total_flips
    
    legal_moves = []
    for r in range(8):
        for c in range(8):
            if you[r][c] == 0 and opponent[r][c] == 0:
                flipped = get_flipped_count(r, c)
                if flipped > 0:
                    pos_score = position_weights[r][c]
                    total_score = pos_score + flipped * 5
                    legal_moves.append((-total_score, -flipped, r, c))
    
    if not legal_moves:
        return "pass"
    
    legal_moves.sort()
    best_r, best_c = legal_moves[0][2], legal_moves[0][3]
    column = chr(ord('a') + best_c)
    row = best_r + 1
    return f"{column}{row}"
