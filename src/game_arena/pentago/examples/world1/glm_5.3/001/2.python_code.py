
import time

import numpy as np

# ---------------------------------------------------------------------------
# Pentago policy.
# Board: flat int8 array of 36 cells (0 empty, 1 = me, 2 = opponent).
# All move generation is exhaustive but vectorised with numpy: a "ply
# expansion" produces every legal (placement x quadrant-rotation) successor
# state in a handful of numpy calls.
# ---------------------------------------------------------------------------

_QBASE = ((0, 0), (0, 3), (3, 0), (3, 3))   # top-left corner of each quadrant
_BIG_WIN = 1000000        # value marker: forced win detected
_BIG_LOSS = -1000000000   # value marker: forced loss detected


def _build_perms():
    """_PERMS[2*q + d]: P[new] = old, i.e. the marble at position P[new]
    moves to position new when quadrant q is rotated
    (d = 0 -> 'L' anticlockwise, d = 1 -> 'R' clockwise)."""
    perms = []
    for q in range(4):
        r0, c0 = _QBASE[q]
        for d in range(2):
            P = np.arange(36)
            for a in range(3):
                for b in range(3):
                    newp = (r0 + a) * 6 + (c0 + b)
                    if d == 1:                      # clockwise
                        oldp = (r0 + 2 - b) * 6 + (c0 + a)
                    else:                           # anticlockwise
                        oldp = (r0 + b) * 6 + (c0 + 2 - a)
                    P[newp] = oldp
            perms.append(P)
    return perms


_PERMS = _build_perms()


def _build_windows():
    """All 32 five-in-a-row windows (rows, columns, both diagonal directions)."""
    W = []
    for r in range(6):
        for c in range(2):
            W.append([r * 6 + c + k for k in range(5)])
    for c in range(6):
        for r in range(2):
            W.append([(r + k) * 6 + c for k in range(5)])
    for r in range(2):
        for c in range(2):
            W.append([(r + k) * 6 + (c + k) for k in range(5)])
    for r in range(2):
        for c in range(4, 6):
            W.append([(r + k) * 6 + (c - k) for k in range(5)])
    return np.array(W, dtype=np.intp)


_WIDX = _build_windows()
_WW = np.array([0, 1, 6, 30, 300, 6000], dtype=np.int64)


def _expand(S, player):
    """Every successor of S for `player`: place a marble on each empty cell,
    then apply each of the 8 rotations.  Row i of the result corresponds to
    rotation k = i // n and empty cell empt[i % n]."""
    empt = np.flatnonzero(S == 0)
    n = empt.shape[0]
    if n == 0:
        return np.zeros((0, 36), dtype=np.int8), empt
    placed = np.tile(S, (n, 1))
    placed[np.arange(n), empt] = player
    return np.concatenate([placed[:, P] for P in _PERMS], axis=0), empt


def _classify(batch):
    """Vectorised win / threat / evaluation for a batch of states."""
    T = batch[:, _WIDX]                                   # (N, 32, 5)
    myc = (T == 1).sum(axis=2, dtype=np.int64)
    opc = (T == 2).sum(axis=2, dtype=np.int64)
    my5 = (myc == 5).any(axis=1)
    op5 = (opc == 5).any(axis=1)
    cheap_me = ((myc == 4) & (opc == 0)).any(axis=1)
    cheap_opp = ((opc == 4) & (myc == 0)).any(axis=1)
    ev = (np.where(opc == 0, _WW[myc], 0)
          - np.where(myc == 0, _WW[opc], 0)).sum(axis=1)
    return my5, op5, cheap_me, cheap_opp, ev


def _fmt(empt, i, n):
    k = i // n
    j = i - k * n
    pos = int(empt[j])
    return "{},{},{},{}".format(pos // 6 + 1, pos % 6 + 1, k // 2,
                                 "R" if (k & 1) else "L")


def _search(B, t_start):
    TL = 0.45            # overall soft time budget (seconds)
    P2_CAP = 0.32        # cap for the full two-ply scan

    root_batch, root_empt = _expand(B, 1)
    n_e = int(root_empt.shape[0])
    if n_e == 0 or root_batch.shape[0] == 0:
        return None

    my5, op5, _cm, _co, root_ev = _classify(root_batch)

    # ---- 1) exact immediate win -------------------------------------------
    win_mask = my5 & ~op5
    if win_mask.any():
        return _fmt(root_empt, int(np.argmax(win_mask)), n_e)
    draw_mask = my5 & op5
    cont_idx = np.flatnonzero(~(my5 | op5))

    entries = []
    analyzed = np.zeros(root_batch.shape[0], dtype=bool)

    def analyze(i):
        # full set of opponent replies after my move i
        rb, _ = _expand(root_batch[i], 2)
        if rb.shape[0] == 0:
            # my move filled the board and nobody has 5: game is a draw
            return (i, True, 0, 0, 0, None, None, None)
        rmy5, rop5, rcme, _rco, rev = _classify(rb)
        opp_win = rop5 & ~rmy5      # opponent wins immediately with this reply
        i_win = rmy5 & ~rop5        # opponent's reply completes MY line
        draw_r = rmy5 & rop5        # opponent's reply draws the game
        v = rev.copy()
        v[i_win | rcme] = _BIG_WIN  # I own a guaranteed winning move
        v[draw_r] = 0
        v[opp_win] = _BIG_LOSS
        return (i, not bool(opp_win.any()), int(v.min()),
                int((i_win | rcme).sum()), int(opp_win.sum()),
                rb, v, draw_r)

    done_all = True
    for ii in cont_idx:
        i = int(ii)
        if time.time() - t_start > P2_CAP:
            done_all = False
            break
        entries.append(analyze(i))
        analyzed[i] = True

    safe_entries = [e for e in entries if e[1]]

    # if nothing safe was found yet but the first time slice ran out,
    # keep scanning with the remaining budget
    if (not safe_entries) and entries and (not done_all):
        for ii in cont_idx:
            i = int(ii)
            if analyzed[i]:
                continue
            if time.time() - t_start > TL - 0.05:
                break
            entries.append(analyze(i))
            analyzed[i] = True
        safe_entries = [e for e in entries if e[1]]

    if not entries:
        if draw_mask.any():
            return _fmt(root_empt, int(np.argmax(draw_mask)), n_e)
        if cont_idx.shape[0] > 0:
            b = int(cont_idx[int(np.argmax(root_ev[cont_idx]))])
            return _fmt(root_empt, b, n_e)
        return _fmt(root_empt, 0, n_e)

    if not safe_entries:
        # every analysed move loses next ply: prefer an immediate draw,
        # otherwise make the opponent's win as hard as possible
        if draw_mask.any():
            return _fmt(root_empt, int(np.argmax(draw_mask)), n_e)
        best = min(entries, key=lambda e: (e[4], -e[2], -e[3]))
        return _fmt(root_empt, int(best[0]), n_e)

    # ---- 2) forced win through unstoppable (cheap) threats -----------------
    for e in safe_entries:
        if e[2] >= _BIG_WIN:
            return _fmt(root_empt, int(e[0]), n_e)

    safe_entries.sort(key=lambda e: (e[2], e[3]), reverse=True)
    vals = [e[2] for e in safe_entries]

    def refine(e, best_val):
        """Depth-3 value of my move e: min over replies of my best answer."""
        rb = e[5]
        if rb is None:
            return 0, True
        v = e[6]
        draw_r = e[7]
        v3 = None
        cnt = 0
        for jj in np.argsort(v):
            j = int(jj)
            cnt += 1
            if (cnt & 15) == 0 and time.time() - t_start > TL:
                return None, False
            vj = int(v[j])
            if vj >= _BIG_WIN or vj <= _BIG_LOSS:
                pass                          # already-decided marker
            elif draw_r[j]:
                vj = 0
            else:
                m2b, _ = _expand(rb[j], 1)    # all of my answers
                if m2b.shape[0] == 0:
                    vj = 0
                else:
                    m5, o5, _cme, cop, mev = _classify(m2b)
                    if (m5 & ~o5).any():
                        vj = _BIG_WIN         # a winning answer exists
                    else:
                        drawrows = m5 & o5
                        loserows = o5 & ~m5
                        if loserows.all():
                            vj = _BIG_LOSS
                        else:
                            # opponent moves at the leaf: their 4-in-window
                            # with the last cell empty is a guaranteed win
                            lv = np.where(cop, _BIG_LOSS, mev)
                            lv[drawrows] = 0
                            vj = int(lv[~loserows].max())
            if v3 is None or vj < v3:
                v3 = vj
                if v3 < best_val:             # cannot beat incumbent
                    return v3, True
        return v3, True

    cur_best = None
    for idx in range(len(safe_entries)):
        if idx >= 14 or time.time() - t_start > TL:
            break
        e = safe_entries[idx]
        v3, _done = refine(e, cur_best if cur_best is not None else -(10 ** 18))
        if v3 is not None:
            vals[idx] = v3
            if v3 >= _BIG_WIN:
                return _fmt(root_empt, int(e[0]), n_e)
            if cur_best is None or v3 > cur_best:
                cur_best = v3

    best_idx = 0
    for ti in range(1, len(safe_entries)):
        if (vals[ti], safe_entries[ti][3]) > (vals[best_idx],
                                              safe_entries[best_idx][3]):
            best_idx = ti
    if vals[best_idx] <= -100000000 and draw_mask.any():
        # everything detectable is lost: take the draw
        return _fmt(root_empt, int(np.argmax(draw_mask)), n_e)
    return _fmt(root_empt, int(safe_entries[best_idx][0]), n_e)


def policy(you, opponent):
    t_start = time.time()
    B = np.zeros(36, dtype=np.int8)
    ok = True
    try:
        for r in range(6):
            ry = you[r]
            ro = opponent[r]
            for c in range(6):
                if int(ry[c]):
                    B[r * 6 + c] = 1
                elif int(ro[c]):
                    B[r * 6 + c] = 2
    except Exception:
        ok = False
    if not ok:
        return "1,1,0,L"
    empt = np.flatnonzero(B == 0)
    if empt.shape[0] == 0:
        return "1,1,0,L"
    p0 = int(empt[0])
    fallback = "{},{},{},{}".format(p0 // 6 + 1, p0 % 6 + 1, 0, "L")
    try:
        mv = _search(B, t_start)
        if mv:
            return mv
    except Exception:
        pass
    return fallback
