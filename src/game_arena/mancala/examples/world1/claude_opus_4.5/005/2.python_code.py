
def policy(you: list[int], opponent: list[int]) -> int:
    import time
    
    legal = [i for i in range(6) if you[i] > 0]
    if len(legal) == 1:
        return legal[0]
    
    start = time.time()
    limit = 0.85
    timeout = False
    
    def sim(y, o, m):
        y, o = list(y), list(o)
        s, y[m] = y[m], 0
        p = m
        last_empty = False
        while s:
            p = (p + 1) % 13
            if p < 6:
                last_empty = (y[p] == 0)
                y[p] += 1
            elif p == 6:
                y[6] += 1
            else:
                o[p - 7] += 1
            s -= 1
        ex = p == 6
        if not ex and p < 6 and last_empty and o[5 - p]:
            y[6] += y[p] + o[5 - p]
            y[p] = o[5 - p] = 0
        return y, o, ex
    
    def nm(y, o, d, a, b):
        nonlocal timeout
        if time.time() - start > limit:
            timeout = True
            return 0, -1
        
        ys = sum(y[:6])
        os = sum(o[:6])
        if ys == 0:
            return y[6] - o[6] - os, -1
        if os == 0:
            return y[6] + ys - o[6], -1
        if d == 0:
            return y[6] - o[6], -1
        
        best_v, best_m = -9999, -1
        
        moves = []
        for i in range(6):
            if y[i]:
                landing = (i + y[i]) % 13
                score = 1000 if landing == 6 else 0
                moves.append((-score, i))
        moves.sort()
        
        for _, i in moves:
            ny, no, ex = sim(y, o, i)
            if ex:
                v, _ = nm(ny, no, d, a, b)
            else:
                v, _ = nm(no, ny, d - 1, -b, -a)
                v = -v
            if timeout:
                return 0, -1
            if v > best_v:
                best_v, best_m = v, i
            a = max(a, v)
            if a >= b:
                break
        return best_v, best_m
    
    best = None
    for d in range(1, 50):
        if time.time() - start > limit * 0.7:
            break
        timeout = False
        _, m = nm(list(you), list(opponent), d, -9999, 9999)
        if not timeout and m >= 0:
            best = m
    
    if best is None:
        for i in range(6):
            if you[i] > 0:
                return i
    return best
