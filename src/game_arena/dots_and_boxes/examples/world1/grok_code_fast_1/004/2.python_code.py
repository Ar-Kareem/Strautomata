
import numpy as np
import random

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    def get_legal_moves(hor, ver):
        moves = []
        for r in range(5):
            for c in range(5):
                if hor[r, c] == 0:
                    moves.append((r, c, 'H'))
                if ver[r, c] == 0:
                    moves.append((r, c, 'V'))
        return moves

    def check_if_completes(hor, ver, cap, r, c, dir):
        h = hor.copy()
        v = ver.copy()
        if dir == 'H':
            h[r, c] = 1
        else:
            v[r, c] = 1
        completes = False
        for i in range(4):
            for j in range(4):
                if cap[i, j] == 0:
                    edges = [h[i, j], h[i + 1, j], v[i, j], v[i, j + 1]]
                    if all(x != 0 for x in edges):
                        completes = True
                        break
            if completes:
                break
        return completes

    def is_safe_after_move(hor, ver, cap, r, c, dir):
        h = hor.copy()
        v = ver.copy()
        if dir == 'H':
            h[r, c] = 1
        else:
            v[r, c] = 1
        for i in range(4):
            for j in range(4):
                if cap[i, j] == 0:
                    edges = [h[i, j], h[i + 1, j], v[i, j], v[i, j + 1]]
                    filled_edges = sum(1 for x in edges if x != 0)
                    if filled_edges == 3:
                        return False
        return True

    legal_moves = get_legal_moves(horizontal, vertical)
    capturing_moves = [move for move in legal_moves if check_if_completes(horizontal, vertical, capture, *move)]
    if capturing_moves:
        return ','.join(str(x) for x in random.choice(capturing_moves))

    safe_moves = [move for move in legal_moves if is_safe_after_move(horizontal, vertical, capture, *move)]
    if safe_moves:
        return ','.join(str(x) for x in random.choice(safe_moves))

    # If no safe or capturing moves, pick any legal move
    return ','.join(str(x) for x in random.choice(legal_moves))
