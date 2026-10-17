
import random

def policy(me, opponent):
    N = 19
    B = [[0]*(N+2) for _ in range(N+2)]
    for r,c in me: B[r][c] = 1
    for r,c in opponent: B[r][c] = 2

    def nbrs(r,c):
        res=[]
        if r>1: res.append((r-1,c))
        if r<N: res.append((r+1,c))
        if c>1: res.append((r,c-1))
        if c<N: res.append((r,c+1))
        return res

    def group_liberties(r,c,b):
        color = b[r][c]
        seen = {(r,c)}
        stack = [(r,c)]
        libs = set()
        while stack:
            x,y = stack.pop()
            for nx,ny in nbrs(x,y):
                v = b[nx][ny]
                if v == 0:
                    libs.add((nx,ny))
                elif v == color and (nx,ny) not in seen:
                    seen.add((nx,ny))
                    stack.append((nx,ny))
        return seen, libs

    def simulate(r,c,color,b):
        if b[r][c] != 0: return None
        b[r][c] = color
        opp = 3-color
        captured = []
        for nr,nc in nbrs(r,c):
            if b[nr][nc] == opp:
                g, libs = group_liberties(nr,nc,b)
                if not libs:
                    for gr,gc in g:
                        if b[gr][gc] == opp:
                            b[gr][gc] = 0
                            captured.append((gr,gc))
        g, libs = group_liberties(r,c,b)
        if not libs:
            b[r][c] = 0
            for gr,gc in captured:
                b[gr][gc] = opp
            return None
        return captured

    def undo(r,c,color,b,captured):
        b[r][c] = 0
        opp = 3-color
        for gr,gc in captured:
            b[gr][gc] = opp

    def is_own_eye(r,c,color,b):
        for nr,nc in nbrs(r,c):
            if b[nr][nc] != color:
                return False
        diag_opp = 0
        edge = False
        for dr,dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:
            nr,nc = r+dr, c+dc
            if not (1<=nr<=N and 1<=nc<=N):
                edge = True
                continue
            if b[nr][nc] == 3-color:
                diag_opp += 1
        if edge:
            return diag_opp == 0
        return diag_opp <= 1

    if not me and not opponent:
        return (16,16)

    candidates = set()
    all_stones = me + opponent
    for r,c in all_stones:
        for dr in range(-2,3):
            for dc in range(-2,3):
                nr,nc = r+dr, c+dc
                if 1<=nr<=N and 1<=nc<=N and B[nr][nc]==0:
                    candidates.add((nr,nc))

    if len(all_stones) < 8:
        for pt in [(4,4),(4,10),(4,16),(10,4),(10,10),(10,16),(16,4),(16,10),(16,16),
                   (4,17),(17,4),(17,17),(4,3),(3,4),(16,17),(17,16),(3,16),(16,3)]:
            if 1<=pt[0]<=N and 1<=pt[1]<=N and B[pt[0]][pt[1]]==0:
                candidates.add(pt)

    best = None
    best_score = -1e18

    for r,c in candidates:
        if is_own_eye(r,c,1,B):
            continue

        save_stones = 0
        seen_f = set()
        for nr,nc in nbrs(r,c):
            if B[nr][nc] == 1:
                og, olibs = group_liberties(nr,nc,B)
                key = frozenset(og)
                if key in seen_f: continue
                seen_f.add(key)
                if len(olibs) == 1:
                    save_stones += len(og)

        captured = simulate(r,c,1,B)
        if captured is None:
            continue

        score = 0.0
        score += len(captured) * 25

        g, libs = group_liberties(r,c,1,B)
        my_libs = len(libs)

        if my_libs == 1:
            score -= 50
        elif my_libs == 2:
            score -= 2

        if save_stones > 0 and my_libs >= 2:
            score += save_stones * 15

        seen_og = set()
        for nr,nc in nbrs(r,c):
            if B[nr][nc] == 2:
                og, olibs = group_liberties(nr,nc,B)
                key = frozenset(og)
                if key in seen_og: continue
                seen_og.add(key)
                if len(olibs) == 1:
                    score += 10 * len(og)
                elif len(olibs) == 2:
                    score += 3 * len(og)

        dist_edge = min(r-1, N-r, c-1, N-c)
        if dist_edge == 0:
            score -= 10
        elif dist_edge == 1:
            score -= 4
        elif dist_edge == 2:
            score += 1
        elif dist_edge == 3:
            score += 2

        min_d = 99
        for fr,fc in all_stones:
            d = max(abs(fr-r), abs(fc-c))
            if d < min_d: min_d = d

        if min_d >= 4:
            score -= 3
        elif min_d == 1:
            score += 1

        score += random.random() * 0.1

        undo(r,c,1,B,captured)

        if score > best_score:
            best_score = score
            best = (r,c)

    if best is None:
        return (0,0)
    return best
