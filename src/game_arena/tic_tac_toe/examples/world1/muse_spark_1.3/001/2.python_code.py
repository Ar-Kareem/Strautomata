
from functools import lru_cache

WIN_LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
)

def _winner(t):
    for a, b, c in WIN_LINES:
        s = t[a] + t[b] + t[c]
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0

@lru_cache(maxsize=None)
def _minimax(t, turn):
    w = _winner(t)
    if w != 0:
        return w
    if 0 not in t:
        return 0
    if turn == 1:
        best = -2
        for i in range(9):
            if t[i] == 0:
                lst = list(t)
                lst[i] = 1
                v = _minimax(tuple(lst), -1)
                if v > best:
                    best = v
                    if best == 1:
                        break
        return best
    else:
        best = 2
        for i in range(9):
            if t[i] == 0:
                lst = list(t)
                lst[i] = -1
                v = _minimax(tuple(lst), 1)
                if v < best:
                    best = v
                    if best == -1:
                        break
        return best

@lru_cache(maxsize=None)
def _expval(t, turn):
    w = _winner(t)
    if w == 1:
        return 1.0
    if w == -1:
        return -1.0
    if 0 not in t:
        return 0.0
    if turn == 1:
        best = -2.0
        for i in range(9):
            if t[i] == 0:
                lst = list(t)
                lst[i] = 1
                v = _expval(tuple(lst), -1)
                if v > best:
                    best = v
                    if best == 1.0:
                        break
        return best
    else:
        s = 0.0
        n = 0
        for i in range(9):
            if t[i] == 0:
                lst = list(t)
                lst[i] = -1
                s += _expval(tuple(lst), 1)
                n += 1
        return s / n if n else 0.0

def _to_tuple(board):
    return (board[0][0], board[0][1], board[0][2],
            board[1][0], board[1][1], board[1][2],
            board[2][0], board[2][1], board[2][2])

def policy(board: list[list[int]]) -> tuple[int, int]:
    try:
        empties = [(r, c) for r in range(3) for c in range(3) if board[r][c] == 0]
        if not empties:
            return (0, 0)
        if len(empties) == 1:
            return empties[0]

        t = _to_tuple(board)

        # immediate win
        for r, c in empties:
            i = r * 3 + c
            lst = list(t)
            lst[i] = 1
            nt = tuple(lst)
            if _winner(nt) == 1:
                return (r, c)

        # immediate block (opponent about to win -> must block)
        # check if opponent has winning threat now (after our non-block move they'd win)
        # handled by minimax, but do fast check:
        threats = []
        for r, c in empties:
            i = r * 3 + c
            lst = list(t)
            lst[i] = -1
            if _winner(tuple(lst)) == -1:
                threats.append((r, c))
        # if opponent has immediate win threat, we must block one of them
        # (minimax will do it, but shortcut saves time)

        best_score = -10
        best_exp = -10.0
        best_move = empties[0]
        # static preference for final tie-break: center > corner > edge
        pref = {(1, 1): 3, (0, 0): 2, (0, 2): 2, (2, 0): 2, (2, 2): 2,
                (0, 1): 1, (1, 0): 1, (1, 2): 1, (2, 1): 1}
        best_pref = -1

        for r, c in empties:
            i = r * 3 + c
            lst = list(t)
            lst[i] = 1
            nt = tuple(lst)
            # game-theoretic value from our perspective after our move
            # if we already won, score 1
            w = _winner(nt)
            if w == 1:
                return (r, c)
            score = _minimax(nt, -1)
            expv = _expval(nt, -1)
            p = pref.get((r, c), 0)
            if score > best_score or (score == best_score and (expv > best_exp + 1e-9 or (abs(expv - best_exp) < 1e-9 and p > best_pref))):
                best_score = score
                best_exp = expv
                best_pref = p
                best_move = (r, c)
                if best_score == 1 and best_exp == 1.0:
                    break
        return best_move
    except Exception:
        try:
            for r in range(3):
                for c in range(3):
                    if board[r][c] == 0:
                        return (r, c)
        except Exception:
            pass
        return (0, 0)
