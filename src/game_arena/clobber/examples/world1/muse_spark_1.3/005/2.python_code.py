
import time
import random
import sys
sys.setrecursionlimit(10000)
try:
    import numpy as _NP
except Exception:
    _NP = None

# neighbour masks for 5x6 board, idx = r*6+c
_NEIGH_MASK = [0]*30
for _r in range(5):
    for _c in range(6):
        _i = _r*6+_c
        _m = 0
        if _r > 0:
            _m |= 1 << ((_r-1)*6+_c)
        if _r < 4:
            _m |= 1 << ((_r+1)*6+_c)
        if _c > 0:
            _m |= 1 << (_r*6+_c-1)
        if _c < 5:
            _m |= 1 << (_r*6+_c+1)
        _NEIGH_MASK[_i] = _m

try:
    _tmp = (1).bit_count()
    def _pop(x):
        return x.bit_count()
except Exception:
    def _pop(x):
        return bin(x).count("1")

class _Timeout(Exception):
    pass

def _to_mask(b):
    if _NP is not None:
        try:
            a = _NP.asarray(b, dtype=int).ravel()
            m = 0
            n = int(a.size)
            if n > 30:
                n = 30
            for i in range(n):
                if int(a[i]):
                    m |= 1 << i
            return m
        except Exception:
            pass
    m = 0
    try:
        for r in range(5):
            row = b[r]
            for c in range(6):
                try:
                    v = row[c]
                except Exception:
                    v = 0
                if v:
                    m |= 1 << (r*6+c)
        return m
    except Exception:
        pass
    try:
        L = len(b)
        for i in range(L if L < 30 else 30):
            if b[i]:
                m |= 1 << i
    except Exception:
        pass
    return m

def _gen_list(cur, other):
    res = []
    c = cur
    NM = _NEIGH_MASK
    while c:
        lsb = c & -c
        src = lsb.bit_length() - 1
        c ^= lsb
        inter = NM[src] & other
        while inter:
            lsb2 = inter & -inter
            dst = lsb2.bit_length() - 1
            inter ^= lsb2
            res.append((src << 5) | dst)
    return res

def _count(cur, other):
    tot = 0
    c = cur
    NM = _NEIGH_MASK
    while c:
        lsb = c & -c
        src = lsb.bit_length() - 1
        c ^= lsb
        tot += _pop(NM[src] & other)
    return tot

def _dir_of(src, dst):
    sr = src // 6
    sc = src % 6
    dr = dst // 6
    dc = dst % 6
    if dr == sr - 1:
        return 'U'
    if dr == sr + 1:
        return 'D'
    if dc == sc + 1:
        return 'R'
    return 'L'

def _move_to_str(code):
    src = code >> 5
    dst = code & 31
    return f"{src//6},{src%6},{_dir_of(src,dst)}"

def _first_legal_fallback(you, opponent):
    try:
        for r in range(5):
            for c in range(6):
                try:
                    v = you[r][c]
                except Exception:
                    try:
                        v = you[r, c]
                    except Exception:
                        v = 0
                if v:
                    if r > 0:
                        try:
                            w = opponent[r-1][c]
                        except Exception:
                            try:
                                w = opponent[r-1, c]
                            except Exception:
                                w = 0
                        if w:
                            return f"{r},{c},U"
                    if r < 4:
                        try:
                            w = opponent[r+1][c]
                        except Exception:
                            try:
                                w = opponent[r+1, c]
                            except Exception:
                                w = 0
                        if w:
                            return f"{r},{c},D"
                    if c > 0:
                        try:
                            w = opponent[r][c-1]
                        except Exception:
                            try:
                                w = opponent[r, c-1]
                            except Exception:
                                w = 0
                        if w:
                            return f"{r},{c},L"
                    if c < 5:
                        try:
                            w = opponent[r][c+1]
                        except Exception:
                            try:
                                w = opponent[r, c+1]
                            except Exception:
                                w = 0
                        if w:
                            return f"{r},{c},R"
    except Exception:
        pass
    return "0,0,U"

def policy(you, opponent):
    try:
        cur = _to_mask(you)
        other = _to_mask(opponent)
        moves = _gen_list(cur, other)
        if not moves:
            return _first_legal_fallback(you, opponent)
        if len(moves) == 1:
            return _move_to_str(moves[0])

        t0 = time.perf_counter()
        TIME_LIMIT = 0.93

        infos = []
        for code in moves:
            src = code >> 5
            dst = code & 31
            nc = other ^ (1 << dst)
            no = (cur ^ (1 << src)) | (1 << dst)
            m = _count(nc, no)
            infos.append([m, src, dst, nc, no])
        infos.sort(key=lambda x: x[0])

        if infos[0][0] == 0:
            s = infos[0][1]
            d = infos[0][2]
            return f"{s//6},{s%6},{_dir_of(s,d)}"

        # exact win search with small budget
        exact_budget = 0.28
        try:
            memo = {}
            nodes = [0]
            NM = _NEIGH_MASK

            def win(c, o):
                nodes[0] += 1
                if (nodes[0] & 1023) == 0:
                    if time.perf_counter() - t0 > exact_budget:
                        raise _Timeout()
                key = (c, o) if c <= o else (o, c)
                v = memo.get(key)
                if v is not None:
                    return v
                # generate
                cc = c
                ml = []
                while cc:
                    lsb = cc & -cc
                    src2 = lsb.bit_length() - 1
                    cc ^= lsb
                    inter = NM[src2] & o
                    while inter:
                        lsb2 = inter & -inter
                        dst2 = lsb2.bit_length() - 1
                        inter ^= lsb2
                        ml.append((src2 << 5) | dst2)
                if not ml:
                    memo[key] = False
                    return False
                for cd in ml:
                    s2 = cd >> 5
                    d2 = cd & 31
                    nc2 = o ^ (1 << d2)
                    no2 = (c ^ (1 << s2)) | (1 << d2)
                    if not win(nc2, no2):
                        memo[key] = True
                        return True
                memo[key] = False
                return False

            for inf in infos:
                nc0, no0 = inf[3], inf[4]
                if not win(nc0, no0):
                    s = inf[1]
                    d = inf[2]
                    return f"{s//6},{s%6},{_dir_of(s,d)}"
        except _Timeout:
            pass
        except Exception:
            pass

        # Monte-Carlo refinement
        now = time.perf_counter()
        remain = (t0 + TIME_LIMIT) - now
        if remain < 0.05:
            s = infos[0][1]
            d = infos[0][2]
            return f"{s//6},{s%6},{_dir_of(s,d)}"

        n = len(infos)
        wins = [0]*n
        tots = [0]*n
        randrange = random.randrange
        gen_local = _gen_list
        deadline = t0 + TIME_LIMIT

        # round robin playouts
        while True:
            if time.perf_counter() >= deadline:
                break
            broke = False
            for i in range(n):
                if time.perf_counter() >= deadline:
                    broke = True
                    break
                nc0 = infos[i][3]
                no0 = infos[i][4]
                c = nc0
                o = no0
                ply = 0
                while True:
                    ml = gen_local(c, o)
                    if not ml:
                        break
                    cd = ml[randrange(len(ml))]
                    s2 = cd >> 5
                    d2 = cd & 31
                    nc2 = o ^ (1 << d2)
                    no2 = (c ^ (1 << s2)) | (1 << d2)
                    c, o = nc2, no2
                    ply += 1
                    if ply > 60:
                        break
                our_win = 1 if (ply & 1) == 0 else 0
                wins[i] += our_win
                tots[i] += 1
            if broke:
                break

        best_i = -1
        best_key = None
        for i in range(n):
            if tots[i] == 0:
                continue
            rate = wins[i] / tots[i]
            key = (rate, -infos[i][0])
            if best_key is None or key > best_key:
                best_key = key
                best_i = i
        if best_i >= 0:
            s = infos[best_i][1]
            d = infos[best_i][2]
            return f"{s//6},{s%6},{_dir_of(s,d)}"
        s = infos[0][1]
        d = infos[0][2]
        return f"{s//6},{s%6},{_dir_of(s,d)}"
    except Exception:
        try:
            return _first_legal_fallback(you, opponent)
        except Exception:
            return "0,0,U"
