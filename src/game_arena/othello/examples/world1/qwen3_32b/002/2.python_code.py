
import numpy as np

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    def is_legal_move(r, c):
        directions = [(-1, -1), (-1, 0), (-1, 1),
                      (0, -1),           (0, 1),
                      (1, -1),  (1, 0), (1, 1)]
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < 8 and 0 <= nc < 8):
                continue
            if opponent[nr][nc] != 1:
                continue
            found = False
            while True:
                nr += dr
                nc += dc
                if not (0 <= nr < 8 and 0 <= nc < 8):
                    break
                if you[nr][nc] == 1:
                    found = True
                    break
                if opponent[nr][nc] != 1:
                    break
            if found:
                return True
        return False

    def count_flips(r, c):
        directions = [(-1, -1), (-1, 0), (-1, 1),
                      (0, -1),           (0, 1),
                      (1, -1),  (1, 0), (1, 1)]
        total = 0
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < 8 and 0 <= nc < 8):
                continue
            if opponent[nr][nc] != 1:
                continue
            count = 1  # First opponent disc
            while True:
                nr += dr
                nc += dc
                if not (0 <= nr < 8 and 0 <= nc < 8):
                    break
                if you[nr][nc] == 1:
                    total += count
                    break
                if opponent[nr][nc] != 1:
                    break
                count += 1
        return total

    legal_moves = []
    for r in range(8):
        for c in range(8):
            if you[r][c] == 0 and opponent[r][c] == 0:
                if is_legal_move(r, c):
                    legal_moves.append((r, c))
    if not legal_moves:
        return "pass"
    corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
    for move in legal_moves:
        if move in corners:
            col = chr(ord('a') + move[1])
            row = str(move[0] + 1)
            return col + row
    best_move = None
    max_flips = -1
    for (r, c) in legal_moves:
        flips = count_flips(r, c)
        if flips > max_flips:
            max_flips = flips
            best_move = (r, c)
    col = chr(ord('a') + best_move[1])
    row = str(best_move[0] + 1)
    return col + row
