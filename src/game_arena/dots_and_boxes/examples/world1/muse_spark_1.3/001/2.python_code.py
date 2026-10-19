
import numpy as np
import time

# 40 real edges: 0-19 H(r 0-4,c 0-3), 20-39 V(r 0-3,c 0-4)
_IDX_TO_MOVE = []
for _r in range(5):
    for _c in range(4):
        _IDX_TO_MOVE.append((_r, _c, 'H'))
for _r in range(4):
    for _c in range(5):
        _IDX_TO_MOVE.append((_r, _c, 'V'))

_BOX_MASKS = []
_ADJ = [[] for _ in range(40)]
for _br in range(4):
    for _bc in range(4):
        _top = _br*4+_bc
        _bot = (_br+1)*4+_bc
        _lef = 20+_br*5+_bc
        _rig = 20+_br*5+_bc+1
        _m = (1 << _top) | (1 << _bot) | (1 << _lef) | (1 << _rig)
        _bidx = _br*4+_bc
        _BOX_MASKS.append(_m)
        _ADJ[_top].append(_bidx)
        _ADJ[_bot].append(_bidx)
        _ADJ[_lef].append(_bidx)
        _ADJ[_rig].append(_bidx)
_FULL_MASK = (1 << 40) - 1
_MEMO = {}

def _mask_from_board(h, v):
    m = 0
    for i, (r, c, d) in enumerate(_IDX_TO_MOVE):
        if d == 'H':
            if h[r, c] != 0:
                m |= (1 << i)
        else:
            if v[r, c] != 0:
                m |= (1 << i)
    return m

def _get_sides(h, v):
    s = np.zeros((4, 4), dtype=int)
    for br in range(4):
        for bc in range(4):
            cnt = 0
            if h[br, bc] != 0:
                cnt += 1
            if h[br+1, bc] != 0:
                cnt += 1
            if v[br, bc] != 0:
                cnt += 1
            if v[br, bc+1] != 0:
                cnt += 1
            s[br, bc] = cnt
    return s

def _first_legal(h, v):
    try:
        for r in range(5):
            for c in range(4):
                if h[r, c] == 0:
                    return f"{r},{c},H"
        for r in range(4):
            for c in range(5):
                if v[r, c] == 0:
                    return f"{r},{c},V"
        for r in range(5):
            for c in range(5):
                if h[r, c] == 0:
                    return f"{r},{c},H"
                if v[r, c] == 0:
                    return f"{r},{c},V"
    except Exception:
        pass
    return "0,0,H"

def _exact_best_move(start_mask, time_limit=0.85):
    # return edge idx 0..39 best, or None
    rem = bin(_FULL_MASK ^ start_mask).count("1")
    if rem == 0:
        return None
    # collect empties
    empties = []
    tmp = _FULL_MASK ^ start_mask
    # tmp has 1 where empty (since start has 1 where full, restricted to 40 bits)
    # Actually _FULL ^ start = complement within 40 bits
    b = tmp
    while b:
        lsb = b & -b
        i = (lsb.bit_length() - 1)
        empties.append(i)
        b ^= lsb
    if not empties:
        return None
    t0 = time.time()
    counter = [0]

    # local refs for speed
    box_masks = _BOX_MASKS
    adj = _ADJ
    memo = _MEMO
    full = _FULL_MASK

    import sys
    sys.setrecursionlimit(10000)

    def dp(mask):
        v = memo.get(mask)
        if v is not None:
            return v
        counter[0] += 1
        if (counter[0] & 2047) == 0 and (time.time() - t0) > time_limit:
            raise TimeoutError()
        if mask == full:
            memo[mask] = 0
            return 0
        # count unclaimed for early exit
        # iterate empty bits
        remain = full ^ mask
        best = -1000
        # we need unclaimed count for pruning: compute quickly
        # number of boxes not full
        unclaimed = 0
        for bm in box_masks:
            if (mask & bm) != bm:
                unclaimed += 1
        m = remain
        while m:
            lsb = m & -m
            i = (lsb.bit_length() - 1)
            m ^= lsb
            nmask = mask | lsb
            k = 0
            for bb in adj[i]:
                if (nmask & box_masks[bb]) == box_masks[bb]:
                    k += 1
            if k > 0:
                val = k + dp(nmask)
            else:
                val = -dp(nmask)
            if val > best:
                best = val
                if best == unclaimed:
                    break
        memo[mask] = best
        return best

    try:
        best_val = -1000
        best_i = empties[0]
        for i in empties:
            nmask = start_mask | (1 << i)
            k = 0
            for bb in adj[i]:
                if (nmask & box_masks[bb]) == box_masks[bb]:
                    k += 1
            if k > 0:
                val = k + dp(nmask)
            else:
                val = -dp(nmask)
            if val > best_val:
                best_val = val
                best_i = i
            if (time.time() - t0) > time_limit:
                break
        return best_i
    except TimeoutError:
        return None
    except RecursionError:
        return None

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    try:
        h = horizontal
        v = vertical
        t_start = time.time()

        # legal real moves
        legal = []
        for r in range(5):
            for c in range(4):
                try:
                    if h[r, c] == 0:
                        legal.append((r, c, 'H'))
                except Exception:
                    pass
        for r in range(4):
            for c in range(5):
                try:
                    if v[r, c] == 0:
                        legal.append((r, c, 'V'))
                except Exception:
                    pass
        if not legal:
            return _first_legal(h, v)

        if len(legal) == 1:
            r, c, d = legal[0]
            return f"{r},{c},{d}"

        sides = _get_sides(h, v)

        # helper to get k for a move (adjacent 3-sided count)
        def move_k(r, c, d):
            if d == 'H':
                boxes = []
                if r - 1 >= 0 and r - 1 < 4 and c < 4:
                    boxes.append((r-1, c))
                if r >= 0 and r < 4 and c < 4:
                    boxes.append((r, c))
            else:
                boxes = []
                if c - 1 >= 0 and c - 1 < 4 and r < 4:
                    boxes.append((r, c-1))
                if c >= 0 and c < 4 and r < 4:
                    boxes.append((r, c))
            k = 0
            for br, bc in boxes:
                if sides[br, bc] == 3:
                    k += 1
            return k, boxes

        # capturing moves
        cap_moves = []
        for (r, c, d) in legal:
            k, boxes = move_k(r, c, d)
            if k > 0:
                cap_moves.append((r, c, d, k, boxes))

        remaining = len(legal)

        # exact search in endgame
        def try_exact(limit=0.8):
            try:
                sm = _mask_from_board(h, v)
                # time left
                elapsed = time.time() - t_start
                tl = max(0.05, limit - elapsed)
                bi = _exact_best_move(sm, time_limit=tl)
                if bi is not None:
                    r, c, d = _IDX_TO_MOVE[bi]
                    # verify legal
                    if d == 'H':
                        if h[r, c] == 0:
                            return f"{r},{c},{d}"
                    else:
                        if v[r, c] == 0:
                            return f"{r},{c},{d}"
            except Exception:
                pass
            return None

        if cap_moves:
            if remaining <= 14:
                em = try_exact(0.85)
                if em is not None:
                    return em
            # greedy: max k, then most remaining 3s, then least 2s
            best = None
            best_key = None
            for (r, c, d, k, boxes) in cap_moves:
                # simulate new sides
                # new sides = sides +1 for adjacent boxes
                n2 = 0
                rem3 = 0
                tot = 0
                # compute quickly
                adj_set = set(boxes)
                for br in range(4):
                    for bc in range(4):
                        ns = int(sides[br, bc]) + (1 if (br, bc) in adj_set else 0)
                        # if this box is newly completed (was 3 ->4) it is 4, ignore for rem3/n2
                        if ns == 4 and (br, bc) in adj_set and sides[br, bc] == 3:
                            tot += ns
                            continue
                        if ns == 3:
                            rem3 += 1
                        if ns == 2:
                            n2 += 1
                        tot += ns
                key = (k, rem3, -n2, -tot)
                if best_key is None or key > best_key:
                    best_key = key
                    best = (r, c, d)
            r, c, d = best
            return f"{r},{c},{d}"

        # no captures: find safe moves
        safe = []
        danger_info = {}
        for (r, c, d) in legal:
            k, boxes = move_k(r, c, d)
            # k==0 here
            adj_set = set(boxes)
            has3 = False
            n2 = 0
            tot = 0
            for br in range(4):
                for bc in range(4):
                    ns = int(sides[br, bc]) + (1 if (br, bc) in adj_set else 0)
                    tot += ns
                    if ns == 3:
                        has3 = True
                    if ns == 2:
                        n2 += 1
            danger_info[(r, c, d)] = (n2, tot)
            if not has3:
                safe.append((r, c, d))

        if safe:
            if remaining <= 14:
                em = try_exact(0.85)
                if em is not None:
                    return em
            # pick safest: min n2, min tot, prefer border (single-box moves)
            best = None
            best_key = None
            for (r, c, d) in safe:
                n2, tot = danger_info[(r, c, d)]
                # border bonus: moves touching 1 box better than 2?
                if d == 'H':
                    nb = 1
                    if r > 0 and r < 4:
                        # touches 2 boxes (if c<4 always)
                        nb = 2
                    # top/bottom row touches 1
                else:
                    nb = 1
                    if c > 0 and c < 4:
                        nb = 2
                # key to minimize: (n2, tot, nb)
                key = (n2, tot, nb)
                if best_key is None or key < best_key:
                    best_key = key
                    best = (r, c, d)
            r, c, d = best
            return f"{r},{c},{d}"

        # loony: no safe, no capture -> must give away
        if remaining <= 14:
            em = try_exact(0.85)
            if em is not None:
                return em

        # minimal loot heuristic
        best = legal[0]
        best_key = None
        for (r, c, d) in legal:
            # simulate loot
            try:
                h2 = np.array(h, copy=True)
                v2 = np.array(v, copy=True)
                if d == 'H':
                    h2[r, c] = 1
                else:
                    v2[r, c] = 1
                loot = 0
                # greedy take loop
                for _ in range(20):
                    s2 = _get_sides(h2, v2)
                    found = None
                    for br in range(4):
                        for bc in range(4):
                            if s2[br, bc] == 3:
                                found = (br, bc)
                                break
                        if found is not None:
                            break
                    if found is None:
                        break
                    br, bc = found
                    if h2[br, bc] == 0:
                        h2[br, bc] = 1
                    elif h2[br+1, bc] == 0:
                        h2[br+1, bc] = 1
                    elif v2[br, bc] == 0:
                        v2[br, bc] = 1
                    elif v2[br, bc+1] == 0:
                        v2[br, bc+1] = 1
                    else:
                        break
                    loot += 1
                s2 = _get_sides(h2, v2)
                n2 = int(np.sum(s2 == 2))
                tot = int(np.sum(s2))
                key = (loot, n2, tot)
            except Exception:
                key = (99, 99, 99)
            if best_key is None or key < best_key:
                best_key = key
                best = (r, c, d)
        r, c, d = best
        return f"{r},{c},{d}"
    except Exception:
        try:
            return _first_legal(horizontal, vertical)
        except Exception:
            return "0,0,H"
