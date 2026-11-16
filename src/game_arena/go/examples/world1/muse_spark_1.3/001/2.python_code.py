
from collections import deque
import random

N = 19
DIRS = [(-1,0),(1,0),(0,-1),(0,1)]

def _in(r,c):
    return 0 <= r < N and 0 <= c < N

def _group_and_libs(board, sr, sc):
    color = board[sr][sc]
    q = deque([(sr,sc)])
    seen = {(sr,sc)}
    stones = []
    libs = set()
    while q:
        r,c = q.popleft()
        stones.append((r,c))
        for dr,dc in DIRS:
            nr, nc = r+dr, c+dc
            if not _in(nr,nc):
                continue
            v = board[nr][nc]
            if v == 0:
                libs.add((nr,nc))
            elif v == color and (nr,nc) not in seen:
                seen.add((nr,nc))
                q.append((nr,nc))
    return stones, libs

def _all_groups(board, color):
    visited = [[False]*N for _ in range(N)]
    groups = []
    for r in range(N):
        for c in range(N):
            if board[r][c]==color and not visited[r][c]:
                q = deque([(r,c)])
                visited[r][c]=True
                stones=[]
                libs=set()
                while q:
                    cr,cc = q.popleft()
                    stones.append((cr,cc))
                    for dr,dc in DIRS:
                        nr,nc = cr+dr, cc+dc
                        if not _in(nr,nc):
                            continue
                        v=board[nr][nc]
                        if v==0:
                            libs.add((nr,nc))
                        elif v==color and not visited[nr][nc]:
                            visited[nr][nc]=True
                            q.append((nr,nc))
                groups.append((stones, libs))
    return groups

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    try:
        board = [[0]*N for _ in range(N)]
        for r,c in me:
            try:
                if 1<=r<=19 and 1<=c<=19:
                    board[r-1][c-1]=1
            except: pass
        for r,c in opponent:
            try:
                if 1<=r<=19 and 1<=c<=19:
                    if board[r-1][c-1]==0:
                        board[r-1][c-1]=2
            except: pass

        empties = [(r,c) for r in range(N) for c in range(N) if board[r][c]==0]
        if not empties:
            return (0,0)
        empty_set = set(empties)
        total = len(me)+len(opponent)

        # Opening book for very early game
        if total < 6:
            pref = [(3,3),(15,15),(3,15),(15,3),(9,9),(3,9),(9,3),(15,9),(9,15),(5,3),(3,5)]
            for r,c in pref:
                if board[r][c]==0:
                    return (r+1,c+1)
            # fallback continue

        # Find atari groups
        opp_groups = _all_groups(board, 2)
        own_groups = _all_groups(board, 1)

        # 1. Winning captures: opponent groups with 1 liberty
        cap_map = {}
        for stones, libs in opp_groups:
            if len(libs)==1:
                lib = next(iter(libs))
                cap_map[lib] = cap_map.get(lib,0)+len(stones)
        if cap_map:
            # play largest capture; verify legality (capture is always legal)
            best = max(cap_map.items(), key=lambda x: x[1])[0]
            return (best[0]+1, best[1]+1)

        # 2. Save own groups in atari
        # sort largest first
        own_atari = [(stones,libs) for stones,libs in own_groups if len(libs)==1]
        own_atari.sort(key=lambda x: -len(x[0]))
        for stones, libs in own_atari:
            lib = next(iter(libs))
            # simulate to check suicide / legality
            lr,lc = lib
            # quick sim
            nb = [row[:] for row in board]
            nb[lr][lc]=1
            # remove captured neighbors
            seen_g = set()
            cap = 0
            for dr,dc in DIRS:
                nr,nc = lr+dr, lc+dc
                if _in(nr,nc) and nb[nr][nc]==2:
                    # find group if not processed
                    # simple BFS to check libs
                    g_stones, g_libs = _group_and_libs(nb, nr, nc)
                    if len(g_libs)==0:
                        cap += len(g_stones)
                        for sr,sc in g_stones:
                            nb[sr][sc]=0
            _, my_libs = _group_and_libs(nb, lr, lc)
            if len(my_libs)>0:
                return (lr+1, lc+1)
            # else illegal, try next

        # Candidate generation: empties near stones
        if total < 30:
            # include star points + near stones
            cands = set()
            for r,c in empties:
                # near any stone within 2?
                found=False
                for dr in range(-2,3):
                    for dc in range(-2,3):
                        nr,nc=r+dr,c+dc
                        if _in(nr,nc) and board[nr][nc]!=0:
                            found=True
                            break
                    if found: break
                if found:
                    cands.add((r,c))
            # add opening points if empty
            for r,c in [(3,3),(3,15),(15,3),(15,15),(9,9),(3,9),(9,3),(15,9),(9,15),(6,3),(3,6)]:
                if board[r][c]==0:
                    cands.add((r,c))
            if not cands:
                cands=set(empties)
        else:
            cands = set()
            for r,c in empties:
                found=False
                for dr,dc in DIRS:
                    nr,nc=r+dr,c+dc
                    if _in(nr,nc) and board[nr][nc]!=0:
                        found=True
                        break
                    # distance 2
                    nr2,nc2=r+2*dr,c+2*dc
                    if _in(nr2,nc2) and board[nr2][nc2]!=0:
                        found=True
                        break
                # diagonal adjacency also
                if not found:
                    for dr,dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:
                        nr,nc=r+dr,c+dc
                        if _in(nr,nc) and board[nr][nc]!=0:
                            found=True
                            break
                if found:
                    cands.add((r,c))
            if not cands:
                # board almost full or isolated: consider all
                cands=set(empties)
                if len(cands)>250:
                    # pass if only dame? play center-ish empty
                    # pick first near center
                    cands_sorted = sorted(cands, key=lambda x: abs(x[0]-9)+abs(x[1]-9))
                    cands=set(cands_sorted[:120])

        # limit candidates for speed
        if len(cands)>220:
            # keep those closest to stones / center balanced: sample
            # prioritize near opponent
            def _pri(x):
                r,c=x
                s=0
                for dr in range(-2,3):
                    for dc in range(-2,3):
                        nr,nc=r+dr,c+dc
                        if _in(nr,nc) and board[nr][nc]==2:
                            s+=1
                        if _in(nr,nc) and board[nr][nc]==1:
                            s+=0.5
                return -s
            cands = set(sorted(cands, key=_pri)[:220])

        best_score = -10**9
        best_move = None

        # Precompute for eye detection helper: need fast
        for (r,c) in cands:
            # simulate
            nb = [row[:] for row in board]
            nb[r][c]=1
            captured=0
            # capture neighbors, avoid double processing same group
            done=set()
            for dr,dc in DIRS:
                nr,nc=r+dr,c+dc
                if _in(nr,nc) and nb[nr][nc]==2 and (nr,nc) not in done:
                    g_stones,g_libs=_group_and_libs(nb,nr,nc)
                    for s in g_stones:
                        done.add(s)
                    if len(g_libs)==0:
                        captured+=len(g_stones)
                        for sr,sc in g_stones:
                            nb[sr][sc]=0
            my_stones, my_libs = _group_and_libs(nb,r,c)
            my_lib_count=len(my_libs)
            if my_lib_count==0:
                continue  # suicide illegal
            my_size=len(my_stones)

            score=0
            # captures
            score+=captured*120

            # liberties of new group
            score+=my_lib_count*4
            if my_lib_count>=6:
                score+=6

            # neighbor counts on original board
            f_orth=0; o_orth=0; f_diag=0; o_diag=0; e_orth=0
            for dr,dc in DIRS:
                nr,nc=r+dr,c+dc
                if not _in(nr,nc):
                    continue
                v=board[nr][nc]
                if v==1: f_orth+=1
                elif v==2: o_orth+=1
                else: e_orth+=1
            for dr,dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:
                nr,nc=r+dr,c+dc
                if _in(nr,nc):
                    if board[nr][nc]==1: f_diag+=1
                    elif board[nr][nc]==2: o_diag+=1
            score+=f_orth*14
            score+=o_orth*9
            score+=f_diag*3
            # empty surroundings = potential
            score+=e_orth*1.5

            # attack: neighboring opp groups after move
            seen2=set()
            for dr,dc in DIRS:
                nr,nc=r+dr,c+dc
                if _in(nr,nc) and nb[nr][nc]==2 and (nr,nc) not in seen2:
                    gs,gl=_group_and_libs(nb,nr,nc)
                    for s in gs: seen2.add(s)
                    if len(gl)==1:
                        score+=70+len(gs)*12
                    elif len(gl)==2:
                        score+=18+len(gs)*2
                    elif len(gl)==3:
                        score+=4
            # defense: neighboring friendly groups (excluding new group) that were in trouble?
            # check friendly neighbors' groups liberty counts after move
            seen3=set()
            seen3.add((r,c))
            # mark new group stones to skip
            for s in my_stones:
                seen3.add(s)
            for dr,dc in DIRS:
                nr,nc=r+dr,c+dc
                if _in(nr,nc) and nb[nr][nc]==1 and (nr,nc) not in seen3:
                    gs,gl=_group_and_libs(nb,nr,nc)
                    for s in gs: seen3.add(s)
                    if len(gl)==1:
                        score-=90  # still leaves a group in atari
                    elif len(gl)==2:
                        score-=8

            # self-atari penalty
            if my_lib_count==1:
                if captured>0:
                    score-=40
                else:
                    score-=260
            elif my_lib_count==2:
                if captured==0 and f_orth==0:
                    score-=12

            # eye fill detection (own eye)
            # orthogonal all friendly/offboard
            orth_ok=True
            for dr,dc in DIRS:
                nr,nc=r+dr,c+dc
                if not _in(nr,nc):
                    continue
                if nb[nr][nc]!=1:
                    orth_ok=False
                    break
            if orth_ok:
                # count diagonal friendly/offboard
                diag_ok=0
                diag_total=0
                for dr,dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:
                    nr,nc=r+dr,c+dc
                    if not _in(nr,nc):
                        diag_ok+=1
                        diag_total+=1
                    else:
                        diag_total+=1
                        if nb[nr][nc]==1:
                            diag_ok+=1
                # corner/edge needs fewer
                on_edge = (r==0 or r==N-1 or c==0 or c==N-1)
                need = 3 if not on_edge else 2
                # actually need adjustment for corner: 1?
                if (r==0 or r==N-1) and (c==0 or c==N-1):
                    need=1
                if diag_ok>=need:
                    if captured==0:
                        score-=600
                    else:
                        score-=150

            # edge penalty
            rr=r+1; cc=c+1
            line=min(rr,20-rr,cc,20-cc)
            if line==1:
                score+=-80 if captured==0 else -10
            elif line==2:
                score+=-14 if captured==0 else 0
            elif line==3 or line==4:
                score+=8
            # slight center bias midgame
            dist=abs(r-9)+abs(c-9)
            score+=-dist*0.25

            # connection bonus: playing between two friends (cut prevention)
            # already via f_orth, add extra for 2+ friends
            if f_orth>=2:
                score+=10
            if o_orth>=2:
                score+=8  # cut

            # tiny deterministic tiebreak
            score+=((r*19+c)%11)*0.15

            if score>best_score:
                best_score=score
                best_move=(r,c)

        if best_move is None:
            # all suicides? pass
            return (0,0)
        # pass if only terrible eye-filling moves remain and board is crowded
        if best_score < -300 and total > 60:
            return (0,0)
        # also if board very full and best is very bad, pass
        if len(empties)<10 and best_score<-100:
            return (0,0)
        return (best_move[0]+1, best_move[1]+1)
    except Exception:
        try:
            for r in range(19):
                for c in range(19):
                    ok=True
                    for s in me:
                        if s==(r+1,c+1):
                            ok=False
                            break
                    if not ok: continue
                    for s in opponent:
                        if s==(r+1,c+1):
                            ok=False
                            break
                    if ok:
                        return (r+1,c+1)
        except:
            pass
        return (0,0)
