
import numpy as np
import time
import sys
sys.setrecursionlimit(10000)

class _Timeout(Exception):
    pass

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    t0 = time.perf_counter()
    deadline = t0 + 0.85

    try:
        h0 = np.array(horizontal, copy=True)
        v0 = np.array(vertical, copy=True)
        c0 = np.array(capture, copy=True)

        # ---------- helpers ----------
        def valid_legal(h, v):
            mv = []
            # H: row 0..4 col 0..3
            for r in range(5):
                for cc in range(4):
                    try:
                        if h[r, cc] == 0:
                            mv.append((r, cc, 'H'))
                    except Exception:
                        pass
            for r in range(4):
                for cc in range(5):
                    try:
                        if v[r, cc] == 0:
                            mv.append((r, cc, 'V'))
                    except Exception:
                        pass
            return mv

        def adj_boxes(move):
            r, cc, d = move
            boxes = []
            if d == 'H':
                if r < 4 and 0 <= cc < 4:
                    boxes.append((r, cc))
                if r - 1 >= 0 and r - 1 < 4 and 0 <= cc < 4:
                    boxes.append((r - 1, cc))
            else:
                if r < 4 and cc < 4 and r >= 0 and cc >= 0:
                    boxes.append((r, cc))
                if r < 4 and cc - 1 >= 0 and cc - 1 < 4:
                    boxes.append((r, cc - 1))
            # filter valid 0..3
            out = []
            for br, bc in boxes:
                if 0 <= br < 4 and 0 <= bc < 4:
                    out.append((br, bc))
            return out

        def filled_of(br, bc, h, v):
            try:
                t = 0 if h[br, bc] == 0 else 1
                b = 0 if h[br + 1, bc] == 0 else 1
                l = 0 if v[br, bc] == 0 else 1
                rr = 0 if v[br, bc + 1] == 0 else 1
                return t + b + l + rr
            except Exception:
                return 4

        def is_capture_move(h, v, c, move):
            for br, bc in adj_boxes(move):
                try:
                    if c[br, bc] != 0:
                        continue
                except Exception:
                    continue
                if filled_of(br, bc, h, v) == 3:
                    return True
            return False

        def creates_danger(h, v, c, move):
            # True if any adjacent unclaimed box has exactly 2 sides
            for br, bc in adj_boxes(move):
                try:
                    if c[br, bc] != 0:
                        continue
                except Exception:
                    continue
                if filled_of(br, bc, h, v) == 2:
                    return True
            return False

        def count_completed(h, v, c, move):
            k = 0
            for br, bc in adj_boxes(move):
                try:
                    if c[br, bc] != 0:
                        continue
                except Exception:
                    continue
                if filled_of(br, bc, h, v) == 3:
                    k += 1
            return k

        def apply_move(h, v, c, move, turn):
            h2 = h.copy()
            v2 = v.copy()
            c2 = c.copy()
            r, cc, d = move
            if d == 'H':
                h2[r, cc] = turn
            else:
                v2[r, cc] = turn
            cap = 0
            for br, bc in adj_boxes(move):
                try:
                    if c2[br, bc] != 0:
                        continue
                except Exception:
                    continue
                # check now full
                try:
                    full = (h2[br, bc] != 0 and h2[br + 1, bc] != 0 and v2[br, bc] != 0 and v2[br, bc + 1] != 0)
                except Exception:
                    full = False
                if full:
                    c2[br, bc] = turn
                    cap += 1
            return h2, v2, c2, cap

        def score_diff(c):
            try:
                # only 4x4 core
                sub = c[0:4, 0:4]
                return int(np.sum(sub))
            except Exception:
                return 0

        def any_safe_exists(h, v, c, legal, caps_set=None):
            for m in legal:
                if caps_set is not None and m in caps_set:
                    continue
                # need non-capture and not danger
                if is_capture_move(h, v, c, m):
                    continue
                if not creates_danger(h, v, c, m):
                    return True
            return False

        legal0 = valid_legal(h0, v0)
        if len(legal0) == 0:
            # fallback to any zero including dummies
            try:
                for r in range(5):
                    for cc in range(5):
                        if h0[r, cc] == 0:
                            return f"{r},{cc},H"
                        if v0[r, cc] == 0:
                            return f"{r},{cc},V"
            except Exception:
                pass
            return "0,0,H"

        # quick classification
        caps0 = [m for m in legal0 if is_capture_move(h0, v0, c0, m)]

        # ---------- exact search ----------
        SEARCH_THRESH = 13
        memo = {}
        node_cnt = [0]

        def get_candidates(h, v, c, legal):
            caps = [m for m in legal if is_capture_move(h, v, c, m)]
            if caps:
                # if safe move exists elsewhere, must take
                has_safe = False
                for m in legal:
                    if m in caps:
                        continue
                    # safe = not danger (non-capture)
                    # creates_danger check
                    danger = False
                    for br, bc in adj_boxes(m):
                        try:
                            if c[br, bc] != 0:
                                continue
                        except Exception:
                            continue
                        if filled_of(br, bc, h, v) == 2:
                            danger = True
                            break
                    if not danger:
                        has_safe = True
                        break
                if has_safe:
                    # order by completions desc
                    caps.sort(key=lambda m: count_completed(h, v, c, m), reverse=True)
                    return caps
                else:
                    # chain endgame: all moves allowed (for control)
                    # order captures first
                    caps_set = set(caps)
                    rest = [m for m in legal if m not in caps_set]
                    caps.sort(key=lambda m: count_completed(h, v, c, m), reverse=True)
                    return caps + rest
            else:
                safes = []
                for m in legal:
                    danger = False
                    for br, bc in adj_boxes(m):
                        try:
                            if c[br, bc] != 0:
                                continue
                        except Exception:
                            continue
                        if filled_of(br, bc, h, v) == 2:
                            danger = True
                            break
                    if not danger:
                        safes.append(m)
                if safes:
                    return safes
                else:
                    return legal

        def minimax(h, v, c, turn, alpha, beta):
            node_cnt[0] += 1
            if (node_cnt[0] & 255) == 0 and time.perf_counter() > deadline:
                raise _Timeout()
            legal = valid_legal(h, v)
            if not legal:
                return score_diff(c)
            cands = get_candidates(h, v, c, legal)
            # order for pruning
            if turn == 1:
                best = -10**9
                for m in cands:
                    h2, v2, c2, cap = apply_move(h, v, c, m, turn)
                    nt = turn if cap > 0 else -turn
                    val = minimax(h2, v2, c2, nt, alpha, beta)
                    if val > best:
                        best = val
                    if best > alpha:
                        alpha = best
                    if alpha >= beta:
                        break
                return best
            else:
                best = 10**9
                for m in cands:
                    h2, v2, c2, cap = apply_move(h, v, c, m, turn)
                    nt = turn if cap > 0 else -turn
                    val = minimax(h2, v2, c2, nt, alpha, beta)
                    if val < best:
                        best = val
                    if best < beta:
                        beta = best
                    if alpha >= beta:
                        break
                return best

        def exact_pick():
            legal = valid_legal(h0, v0)
            cands = get_candidates(h0, v0, c0, legal)
            # order root: captures with more boxes first
            if caps0:
                cands.sort(key=lambda m: count_completed(h0, v0, c0, m), reverse=True)
            best_val = -10**9
            best_m = cands[0]
            alpha = -10**9
            beta = 10**9
            for m in cands:
                h2, v2, c2, cap = apply_move(h0, v0, c0, m, 1)
                nt = 1 if cap > 0 else -1
                val = minimax(h2, v2, c2, nt, alpha, beta)
                if val > best_val:
                    best_val = val
                    best_m = m
                if val > alpha:
                    alpha = val
                if alpha >= beta:
                    break
                if time.perf_counter() > deadline:
                    raise _Timeout()
            return best_m

        # ---------- heuristic helpers ----------
        def heuristic_safe_pick(safes, h, v, c):
            best = None
            best_score = 10**9
            for m in safes:
                s = 0
                for br, bc in adj_boxes(m):
                    try:
                        if c[br, bc] != 0:
                            continue
                    except Exception:
                        continue
                    f = filled_of(br, bc, h, v)
                    s += (f + 1)  # after move
                # prefer fewer adjacent (edge) already reflected; tie by position
                if s < best_score:
                    best_score = s
                    best = m
            return best if best is not None else safes[0]

        def closure_give(h, v, c, move):
            # simulate we play move (turn=1), then opponent takes all chains
            h2 = h.copy(); v2 = v.copy(); c2 = c.copy()
            r, cc, d = move
            if d == 'H':
                h2[r, cc] = 1
            else:
                v2[r, cc] = 1
            # no capture expected (caller ensures) but handle generally
            # now opponent closure
            opp = 0
            # helper to find a 3-sided box
            while True:
                found = None
                found_edge = None
                for br in range(4):
                    for bc in range(4):
                        try:
                            if c2[br, bc] != 0:
                                continue
                        except Exception:
                            continue
                        f = filled_of(br, bc, h2, v2)
                        if f == 3:
                            found = (br, bc)
                            break
                    if found is not None:
                        break
                if found is None:
                    break
                br, bc = found
                # find empty edge
                try:
                    if h2[br, bc] == 0:
                        h2[br, bc] = -1
                        edge = (br, bc, 'H')
                    elif h2[br + 1, bc] == 0:
                        h2[br + 1, bc] = -1
                        edge = (br + 1, bc, 'H')
                    elif v2[br, bc] == 0:
                        v2[br, bc] = -1
                        edge = (br, bc, 'V')
                    elif v2[br, bc + 1] == 0:
                        v2[br, bc + 1] = -1
                        edge = (br, bc + 1, 'V')
                    else:
                        break
                except Exception:
                    break
                # claim any newly completed boxes adjacent to edge
                for ar, ac in adj_boxes(edge):
                    try:
                        if c2[ar, ac] != 0:
                            continue
                    except Exception:
                        continue
                    try:
                        full = (h2[ar, ac] != 0 and h2[ar + 1, ac] != 0 and v2[ar, ac] != 0 and v2[ar, ac + 1] != 0)
                    except Exception:
                        full = False
                    if full:
                        c2[ar, ac] = -1
                        opp += 1
                # safety: avoid infinite loop
                if opp > 16:
                    break
            return opp

        # ---------- main decision ----------
        if caps0:
            if len(legal0) <= SEARCH_THRESH:
                try:
                    bm = exact_pick()
                    return f"{bm[0]},{bm[1]},{bm[2]}"
                except _Timeout:
                    pass
                except Exception:
                    pass
            # greedy take: max completions
            best = max(caps0, key=lambda m: count_completed(h0, v0, c0, m))
            # tie among max: pick first deterministically with smallest closure? keep simple
            maxc = count_completed(h0, v0, c0, best)
            tied = [m for m in caps0 if count_completed(h0, v0, c0, m) == maxc]
            if len(tied) > 1:
                # prefer move that keeps more options (smaller immediate chain? take small first)
                # evaluate closure size quickly, pick smallest
                try:
                    tied.sort(key=lambda m: closure_give(h0, v0, c0, m))
                    best = tied[0]
                except Exception:
                    best = tied[0]
            return f"{best[0]},{best[1]},{best[2]}"
        else:
            # no captures
            safes0 = [m for m in legal0 if not creates_danger(h0, v0, c0, m)]
            if safes0:
                if len(legal0) <= SEARCH_THRESH:
                    try:
                        bm = exact_pick()
                        return f"{bm[0]},{bm[1]},{bm[2]}"
                    except _Timeout:
                        pass
                    except Exception:
                        pass
                best = heuristic_safe_pick(safes0, h0, v0, c0)
                return f"{best[0]},{best[1]},{best[2]}"
            else:
                # loony: must give
                if len(legal0) <= SEARCH_THRESH:
                    try:
                        bm = exact_pick()
                        return f"{bm[0]},{bm[1]},{bm[2]}"
                    except _Timeout:
                        pass
                    except Exception:
                        pass
                # minimize opponent immediate take
                best_m = legal0[0]
                best_give = 10**9
                best_sec = 10**9
                for m in legal0:
                    try:
                        g = closure_give(h0, v0, c0, m)
                    except Exception:
                        g = 10
                    # secondary: sum fill after
                    s = 0
                    for br, bc in adj_boxes(m):
                        try:
                            if c0[br, bc] != 0:
                                continue
                        except Exception:
                            continue
                        s += filled_of(br, bc, h0, v0) + 1
                    if g < best_give or (g == best_give and s < best_sec):
                        best_give = g
                        best_sec = s
                        best_m = m
                    if time.perf_counter() > deadline - 0.05:
                        break
                return f"{best_m[0]},{best_m[1]},{best_m[2]}"
    except Exception:
        pass
    # ultimate fallback: any legal
    try:
        h = np.array(horizontal)
        v = np.array(vertical)
        for r in range(5):
            for cc in range(4):
                if h[r, cc] == 0:
                    return f"{r},{cc},H"
        for r in range(4):
            for cc in range(5):
                if v[r, cc] == 0:
                    return f"{r},{cc},V"
        for r in range(5):
            for cc in range(5):
                try:
                    if h[r, cc] == 0:
                        return f"{r},{cc},H"
                except Exception:
                    pass
                try:
                    if v[r, cc] == 0:
                        return f"{r},{cc},V"
                except Exception:
                    pass
    except Exception:
        pass
    return "0,0,H"
