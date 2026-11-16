
import random

N = 10
SHIPS = [5, 4, 3, 3, 2]


def _compute_scores(board, target_mode):
    score = [[0.0] * N for _ in range(N)]
    for L in SHIPS:
        for r in range(N):
            for c in range(N):
                for dr, dc in ((0, 1), (1, 0)):
                    er = r + dr * (L - 1)
                    ec = c + dc * (L - 1)
                    if er >= N or ec >= N:
                        continue
                    ok = True
                    h = 0
                    cells = []
                    for i in range(L):
                        rr = r + dr * i
                        cc = c + dc * i
                        v = board[rr][cc]
                        if v == -1:
                            ok = False
                            break
                        if v == 1:
                            h += 1
                        else:
                            cells.append((rr, cc))
                    if not ok:
                        continue
                    if target_mode and h == 0:
                        continue
                    if not cells:
                        continue
                    w = 5.0 ** h
                    for rr, cc in cells:
                        score[rr][cc] += w
    return score


def _best_cell(board, score, parity_boost=False):
    best = -1.0
    cands = []
    for r in range(N):
        for c in range(N):
            if board[r][c] != 0:
                continue
            s = score[r][c]
            if parity_boost and (r + c) % 2 == 0:
                s *= 1.05
            if s > best + 1e-9:
                best = s
                cands = [(r, c)]
            elif abs(s - best) <= 1e-9:
                cands.append((r, c))
    if best <= 0 or not cands:
        return None
    return random.choice(cands)


def policy(board):
    try:
        # Determine whether there are "live" hits (with an unknown neighbor)
        active = False
        for r in range(N):
            for c in range(N):
                if board[r][c] == 1:
                    for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0)):
                        rr, cc = r + dr, c + dc
                        if 0 <= rr < N and 0 <= cc < N and board[rr][cc] == 0:
                            active = True
                            break
                if active:
                    break

        move = None
        if active:
            score = _compute_scores(board, True)
            move = _best_cell(board, score, parity_boost=False)
        if move is None:
            score = _compute_scores(board, False)
            move = _best_cell(board, score, parity_boost=True)
        if move is not None:
            return (int(move[0]), int(move[1]))
    except Exception:
        pass

    # Fallback: any legal unknown cell
    unknown = [(r, c) for r in range(N) for c in range(N) if board[r][c] == 0]
    if unknown:
        # prefer parity cells first
        par = [x for x in unknown if (x[0] + x[1]) % 2 == 0]
        pick = random.choice(par) if par else random.choice(unknown)
        return (int(pick[0]), int(pick[1]))
    return (0, 0)
