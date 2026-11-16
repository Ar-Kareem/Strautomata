
def _winner_flat(f):
    # f is tuple of 9 ints row-major
    # rows
    for r in range(3):
        s = f[r*3] + f[r*3+1] + f[r*3+2]
        if s == 3:
            return 1
        if s == -3:
            return -1
    for c in range(3):
        s = f[c] + f[3+c] + f[6+c]
        if s == 3:
            return 1
        if s == -3:
            return -1
    s = f[0] + f[4] + f[8]
    if s == 3:
        return 1
    if s == -3:
        return -1
    s = f[2] + f[4] + f[6]
    if s == 3:
        return 1
    if s == -3:
        return -1
    return 0

def policy(board: list[list[int]]) -> tuple[int, int]:
    try:
        empties = [(r, c) for r in range(3) for c in range(3) if board[r][c] == 0]
        if not empties:
            return (0, 0)
        if len(empties) == 9:
            return (0, 0)

        # flatten
        flat = (board[0][0], board[0][1], board[0][2],
                board[1][0], board[1][1], board[1][2],
                board[2][0], board[2][1], board[2][2])

        cache = {}

        def minimax(f, turn):
            key = (f, turn)
            v = cache.get(key)
            if v is not None:
                return v
            w = _winner_flat(f)
            if w == 1:
                # more empties left = faster win = better
                sc = 100 + f.count(0)
                cache[key] = sc
                return sc
            if w == -1:
                sc = -100 - f.count(0)
                cache[key] = sc
                return sc
            # count empties
            has_empty = False
            for x in f:
                if x == 0:
                    has_empty = True
                    break
            if not has_empty:
                cache[key] = 0
                return 0
            if turn == 1:
                best = -10000
                # try all
                lst = list(f)
                for i in range(9):
                    if lst[i] == 0:
                        lst[i] = 1
                        s = minimax(tuple(lst), -1)
                        lst[i] = 0
                        if s > best:
                            best = s
                            # early exit on fastest possible win
                            # max possible is 100 + (empties-1)
                            # can't prune safely without bound, keep simple
                cache[key] = best
                return best
            else:
                best = 10000
                lst = list(f)
                for i in range(9):
                    if lst[i] == 0:
                        lst[i] = -1
                        s = minimax(tuple(lst), 1)
                        lst[i] = 0
                        if s < best:
                            best = s
                cache[key] = best
                return best

        # evaluate all our moves
        scored = []
        for (r, c) in empties:
            idx = r * 3 + c
            lst = list(flat)
            lst[idx] = 1
            f2 = tuple(lst)
            # if immediate win, minimax returns win value directly
            s = minimax(f2, -1) if _winner_flat(f2) == 0 and 0 in f2 else (
                (100 + f2.count(0)) if _winner_flat(f2) == 1 else (
                (-100 - f2.count(0)) if _winner_flat(f2) == -1 else 0
                ) if _winner_flat(f2) != 0 or 0 not in f2 else minimax(f2, -1)
            )
            # simpler: just call minimax (it handles terminal)
            # recompute correctly to avoid logic error:
            s = minimax(f2, -1)
            # minimax with turn -1 on terminal still returns terminal value, so above is fine
            scored.append((s, r, c, f2))

        best_score = max(s for s, _, _, _ in scored)
        candidates = [(r, c, f2) for s, r, c, f2 in scored if s == best_score]

        if len(candidates) == 1:
            return (candidates[0][0], candidates[0][1])

        # trap maximization: maximize total opponent error magnitude
        def trap_value(f2):
            w = _winner_flat(f2)
            if w != 0:
                # game already over (we won) - best possible
                return 10000
            # list opponent moves
            empt2 = [i for i in range(9) if f2[i] == 0]
            if not empt2:
                return 0
            total = 0
            # best_score is min over opponent replies (opponent minimizes)
            for oi in empt2:
                lst = list(f2)
                lst[oi] = -1
                f3 = tuple(lst)
                s_opp = minimax(f3, 1)
                if s_opp > best_score:
                    total += (s_opp - best_score)
            return total

        best_trap = None
        best_move = candidates[0]
        # preference order for final tie-break: corners > center > edges
        def pref(r, c):
            if (r, c) in ((0, 0), (0, 2), (2, 0), (2, 2)):
                return 0
            if (r, c) == (1, 1):
                return 1
            return 2

        # sort by pref to have deterministic tie-break
        candidates_sorted = sorted(candidates, key=lambda x: pref(x[0], x[1]))
        best_trap = -1
        best_pick = candidates_sorted[0]
        for (r, c, f2) in candidates_sorted:
            t = trap_value(f2)
            if t > best_trap:
                best_trap = t
                best_pick = (r, c, f2)
        return (best_pick[0], best_pick[1])
    except Exception:
        # guaranteed legal fallback
        try:
            for r in range(3):
                for c in range(3):
                    if board[r][c] == 0:
                        return (r, c)
        except Exception:
            pass
        return (0, 0)
