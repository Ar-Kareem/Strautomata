
import random
from functools import lru_cache

def _winner(t):
    # t is tuple of 9 ints, row-major
    for r in range(3):
        s = t[r*3] + t[r*3+1] + t[r*3+2]
        if s == 3:
            return 1
        if s == -3:
            return -1
    for c in range(3):
        s = t[c] + t[c+3] + t[c+6]
        if s == 3:
            return 1
        if s == -3:
            return -1
    s = t[0] + t[4] + t[8]
    if s == 3:
        return 1
    if s == -3:
        return -1
    s = t[2] + t[4] + t[6]
    if s == 3:
        return 1
    if s == -3:
        return -1
    return 0

@lru_cache(maxsize=None)
def _mm(t, p):
    # minimax value from perspective of player 1 (us): 1 win, 0 draw, -1 loss
    # p is player to move: 1 or -1
    w = _winner(t)
    if w != 0:
        return w
    # find empties
    has_empty = False
    for v in t:
        if v == 0:
            has_empty = True
            break
    if not has_empty:
        return 0
    if p == 1:
        best = -2
        for i, v in enumerate(t):
            if v == 0:
                lst = list(t)
                lst[i] = 1
                nt = tuple(lst)
                val = _mm(nt, -1)
                if val > best:
                    best = val
                    if best == 1:
                        break
        return best
    else:
        best = 2
        for i, v in enumerate(t):
            if v == 0:
                lst = list(t)
                lst[i] = -1
                nt = tuple(lst)
                val = _mm(nt, 1)
                if val < best:
                    best = val
                    if best == -1:
                        break
        return best

@lru_cache(maxsize=None)
def _ex(t, p):
    # expected value vs random opponent, we play optimally (max mm, then max ex)
    w = _winner(t)
    if w != 0:
        return float(w)
    empties = [i for i, v in enumerate(t) if v == 0]
    if not empties:
        return 0.0
    if p == 1:
        children = []
        best_mm = -2
        for i in empties:
            lst = list(t)
            lst[i] = 1
            nt = tuple(lst)
            v = _mm(nt, -1)
            children.append((nt, v))
            if v > best_mm:
                best_mm = v
        best_e = -2.0
        for nt, v in children:
            if v == best_mm:
                e = _ex(nt, -1)
                if e > best_e:
                    best_e = e
        return best_e
    else:
        total = 0.0
        for i in empties:
            lst = list(t)
            lst[i] = -1
            nt = tuple(lst)
            total += _ex(nt, 1)
        return total / len(empties)

def policy(board: list[list[int]]) -> tuple[int, int]:
    try:
        t = tuple(board[r][c] for r in range(3) for c in range(3))
        empties_idx = [i for i, v in enumerate(t) if v == 0]
        if not empties_idx:
            return (0, 0)
        if len(empties_idx) == 1:
            i = empties_idx[0]
            return (i // 3, i % 3)
        # random order for tie-breaking variety
        order = empties_idx[:]
        random.shuffle(order)
        best_move = order[0]
        best_mm = -10
        best_ex = -10.0
        for i in order:
            lst = list(t)
            lst[i] = 1
            nt = tuple(lst)
            mm = _mm(nt, -1)
            ex = _ex(nt, -1)
            if mm > best_mm or (mm == best_mm and ex > best_ex):
                best_mm = mm
                best_ex = ex
                best_move = i
                if best_mm == 1 and best_ex == 1.0:
                    break
        return (best_move // 3, best_move % 3)
    except Exception:
        try:
            for r in range(3):
                for c in range(3):
                    if board[r][c] == 0:
                        return (r, c)
        except Exception:
            pass
        return (0, 0)
