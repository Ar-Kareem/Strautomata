
def policy(me, opponent):
    try:
        N = 19
        DIRS = ((1,0),(-1,0),(0,1),(0,-1))
        # board 0 empty 1 me 2 opp
        board = [[0]*N for _ in range(N)]
        for r,c in me:
            if 1 <= r <= 19 and 1 <= c <= 19:
                board[r-1][c-1] = 1
        for r,c in opponent:
            if 1 <= r <= 19 and 1 <= c <= 19:
                if board[r-1][c-1] == 0:
                    board[r-1][c-1] = 2
        total = len(me) + len(opponent)
        if total == 0:
            return (4, 4)

        def bfs_group(bd, sr, sc, col):
            stones = []
            libs = set()
            stack = [(sr, sc)]
            seen = {(sr, sc)}
            while stack:
                r, c = stack.pop()
                stones.append((r, c))
                # unroll neighbours
                nr = r+1
                if nr < 19:
                    v = bd[nr][c]
                    if v == 0:
                        libs.add((nr, c))
                    elif v == col and (nr, c) not in seen:
                        seen.add((nr, c)); stack.append((nr, c))
                nr = r-1
                if nr >= 0:
                    v = bd[nr][c]
                    if v == 0:
                        libs.add((nr, c))
                    elif v == col and (nr, c) not in seen:
                        seen.add((nr, c)); stack.append((nr, c))
                nc = c+1
                if nc < 19:
                    v = bd[r][nc]
                    if v == 0:
                        libs.add((r, nc))
                    elif v == col and (r, nc) not in seen:
                        seen.add((r, nc)); stack.append((r, nc))
                nc = c-1
                if nc >= 0:
                    v = bd[r][nc]
                    if v == 0:
                        libs.add((r, nc))
                    elif v == col and (r, nc) not in seen:
                        seen.add((r, nc)); stack.append((r, nc))
            return stones, libs

        # label original groups once
        gid = [[-1]*N for _ in range(N)]
        gcolor = {}
        gsize = {}
        glibs = {}
        cur = 0
        any_atari = False
        for r in range(N):
            for c in range(N):
                if board[r][c] != 0 and gid[r][c] == -1:
                    st, li = bfs_group(board, r, c, board[r][c])
                    for sr, sc in st:
                        gid[sr][sc] = cur
                    gcolor[cur] = board[r][c]
                    gsize[cur] = len(st)
                    glibs[cur] = len(li)
                    if len(li) == 1:
                        any_atari = True
                    cur += 1

        # opening: if early and no atari, take far corner / side star
        if total < 30 and not any_atari:
            openings = [(4,4),(16,16),(16,4),(4,16),(10,10),
                        (4,10),(16,10),(10,4),(10,16),
                        (7,4),(13,4),(7,16),(13,16),(4,7),(4,13),
                        (16,7),(16,13),(7,10),(13,10),(10,7),(10,13)]
            opp_list = [(r-1,c-1) for r,c in opponent]
            best_o = None
            best_d = -1
            for orr, occ in openings:
                r0 = orr-1; c0 = occ-1
                if board[r0][c0] != 0:
                    continue
                if not opp_list:
                    return (orr, occ)
                d = min(abs(r0-br)+abs(c0-bc) for br,bc in opp_list)
                # slight preference for corners
                bonus = 2 if (orr in (4,16) and occ in (4,16)) else 0
                s = d + bonus*0.1
                if s > best_d:
                    best_d = s
                    best_o = (orr, occ)
            if best_o is not None:
                return best_o
            # else fall through to search

        # candidate generation: empty within chebyshev 2 of any stone
        near = [[False]*N for _ in range(N)]
        for r,c in me:
            r0=r-1; c0=c-1
            for dr in (-2,-1,0,1,2):
                nr=r0+dr
                if 0 <= nr < N:
                    row = near[nr]
                    for dc in (-2,-1,0,1,2):
                        nc=c0+dc
                        if 0 <= nc < N:
                            row[nc]=True
        for r,c in opponent:
            r0=r-1; c0=c-1
            for dr in (-2,-1,0,1,2):
                nr=r0+dr
                if 0 <= nr < N:
                    row = near[nr]
                    for dc in (-2,-1,0,1,2):
                        nc=c0+dc
                        if 0 <= nc < N:
                            row[nc]=True
        cands = []
        for r in range(N):
            br = board[r]
            nr = near[r]
            for c in range(N):
                if br[c]==0 and nr[c]:
                    cands.append((r,c))
        # if board sparse and near empty (should not happen), add openings
        if not cands:
            for r in range(N):
                for c in range(N):
                    if board[r][c]==0:
                        cands.append((r,c))
                        if len(cands)>40:
                            break
                if len(cands)>40:
                    break
            if not cands:
                return (0,0)

        # limit huge candidate set: keep atari liberties + neighbours distance1 first
        # collect must-play liberties of atari groups
        must = set()
        # we need lib positions; recover by scanning? approximate: liberties of atari groups
        # find via groups: need lib_set, we didn't store. Recompute only for atari groups (few)
        # Instead just keep all cands if <=180 else prune to distance1 + random subset
        if len(cands) > 180:
            # keep all distance-1 cands
            close = set()
            for r,c in me:
                r0=r-1; c0=c-1
                for dr,dc in DIRS:
                    nr=r0+dr; nc=c0+dc
                    if 0<=nr<N and 0<=nc<N and board[nr][nc]==0:
                        close.add((nr,nc))
            for r,c in opponent:
                r0=r-1; c0=c-1
                for dr,dc in DIRS:
                    nr=r0+dr; nc=c0+dc
                    if 0<=nr<N and 0<=nc<N and board[nr][nc]==0:
                        close.add((nr,nc))
            # keep close + first 80 of rest
            rest = [p for p in cands if p not in close]
            cands = list(close) + rest[:80]

        late = total > 150
        best_move = None
        best_score = -10**9
        # for pass decision need to know if any non-eye move exists
        found_non_eye = False

        for r,c in cands:
            # quick occupied check (already empty)
            # simulate
            # copy board (19 rows)
            # manual copy fast
            b2 = [row[:] for row in board]
            b2[r][c] = 1
            captured = 0
            # track visited opp stones to avoid duplicate bfs
            # use small set of gids for distinct neighbour groups (original gids)
            # but after placement groups may merge? opp groups stay distinct, use positions
            visited = set()
            opp_after = []  # (size, libs)
            # iterate 4 neighbours
            # neighbour 1
            if r+1 < 19 and b2[r+1][c]==2 and (r+1,c) not in visited:
                st, li = bfs_group(b2, r+1, c, 2)
                for s in st: visited.add(s)
                if len(li)==0:
                    captured += len(st)
                    for sr,sc in st: b2[sr][sc]=0
                else:
                    opp_after.append((len(st), len(li)))
            if r-1 >=0 and b2[r-1][c]==2 and (r-1,c) not in visited:
                st, li = bfs_group(b2, r-1, c, 2)
                for s in st: visited.add(s)
                if len(li)==0:
                    captured += len(st)
                    for sr,sc in st: b2[sr][sc]=0
                else:
                    opp_after.append((len(st), len(li)))
            if c+1 < 19 and b2[r][c+1]==2 and (r,c+1) not in visited:
                st, li = bfs_group(b2, r, c+1, 2)
                for s in st: visited.add(s)
                if len(li)==0:
                    captured += len(st)
                    for sr,sc in st: b2[sr][sc]=0
                else:
                    opp_after.append((len(st), len(li)))
            if c-1 >=0 and b2[r][c-1]==2 and (r,c-1) not in visited:
                st, li = bfs_group(b2, r, c-1, 2)
                for s in st: visited.add(s)
                if len(li)==0:
                    captured += len(st)
                    for sr,sc in st: b2[sr][sc]=0
                else:
                    opp_after.append((len(st), len(li)))

            own_st, own_li = bfs_group(b2, r, c, 1)
            if len(own_li)==0:
                continue  # suicide illegal
            own_size = len(own_st)
            own_libs = len(own_li)

            # eye filter: all orthogonal neighbours friendly or offboard and no capture
            if captured==0:
                is_eye = True
                if r+1 < 19 and board[r+1][c]!=1: is_eye=False
                if r-1 >=0 and board[r-1][c]!=1: is_eye=False
                if c+1 < 19 and board[r][c+1]!=1: is_eye=False
                if c-1 >=0 and board[r][c-1]!=1: is_eye=False
                # need at least one friendly neighbour (avoid empty board corner case)
                has_f = False
                if r+1<19 and board[r+1][c]==1: has_f=True
                if r-1>=0 and board[r-1][c]==1: has_f=True
                if c+1<19 and board[r][c+1]==1: has_f=True
                if c-1>=0 and board[r][c-1]==1: has_f=True
                if is_eye and has_f:
                    continue  # skip eye fill for now
            found_non_eye = True

            # ---- scoring ----
            score = 0.0
            # capture
            if captured>0:
                score += captured*30 + 12
            # friendly neighbour info (before)
            f_gids = set()
            o_gids = set()
            f_orth = 0
            o_orth = 0
            if r+1<19:
                v = board[r+1][c]
                if v==1:
                    f_orth+=1; f_gids.add(gid[r+1][c])
                elif v==2:
                    o_orth+=1; o_gids.add(gid[r+1][c])
            if r-1>=0:
                v = board[r-1][c]
                if v==1:
                    f_orth+=1; f_gids.add(gid[r-1][c])
                elif v==2:
                    o_orth+=1; o_gids.add(gid[r-1][c])
            if c+1<19:
                v = board[r][c+1]
                if v==1:
                    f_orth+=1; f_gids.add(gid[r][c+1])
                elif v==2:
                    o_orth+=1; o_gids.add(gid[r][c+1])
            if c-1>=0:
                v = board[r][c-1]
                if v==1:
                    f_orth+=1; f_gids.add(gid[r][c-1])
                elif v==2:
                    o_orth+=1; o_gids.add(gid[r][c-1])
            # save / defend
            for g in f_gids:
                if g==-1: continue
                lb = glibs.get(g, 5)
                sz = gsize.get(g, 1)
                if lb==1:
                    if own_libs>1:
                        score += sz*25 + 25
                    else:
                        score -= 10
                elif lb==2:
                    score += 6 + sz*0.8
                elif lb==3:
                    score += 1.5
            # attack
            for sz, lb in opp_after:
                if lb==1:
                    score += sz*12 + 16
                elif lb==2:
                    score += sz*2.0 + 3
                elif lb==3:
                    score += 1.0
            # connect / cut
            if len(f_gids)>=2:
                score += 10
            elif len(f_gids)==1:
                score += 2
            if len(o_gids)>=2:
                score += 9
            elif o_orth>0:
                score += 1.5
            # self-atari
            if own_libs==1:
                if captured>0:
                    score -= 25 + own_size*2
                else:
                    score -= 80 + own_size*4
            elif own_libs==2:
                score -= 2
            else:
                score += own_libs*0.4
            # positional: line from edge
            edge = r
            if 18-r < edge: edge = 18-r
            if c < edge: edge = c
            if 18-c < edge: edge = 18-c
            line = edge+1
            if not late:
                if line==1: score -= 10
                elif line==2: score -= 3
                elif line==3: score += 3
                elif line==4: score += 5
                elif line==5: score += 2
            else:
                if line==1: score -= 2
                elif line==2: score -= 1
                elif line==3: score += 1
                elif line==4: score += 1.5
            # over-concentration penalty
            if f_orth>=3:
                score -= 4
            # immediate recapture threat (own group in atari)
            if own_libs==1:
                score -= own_size*28
            # tiny deterministic tie-break to prefer centre-ish and corners
            score += ((r*19+c)%7)*0.05

            if score > best_score:
                best_score = score
                best_move = (r,c)

        if best_move is None:
            # all eye fills or no candidate: try any legal non-suicide, else pass
            if not found_non_eye:
                return (0,0)
            # fallback search for any legal
            for r in range(N):
                for c in range(N):
                    if board[r][c]!=0: continue
                    b2 = [row[:] for row in board]
                    b2[r][c]=1
                    cap=False
                    for dr,dc in DIRS:
                        nr=r+dr; nc=c+dc
                        if 0<=nr<N and 0<=nc<N and b2[nr][nc]==2:
                            st,li=bfs_group(b2,nr,nc,2)
                            if len(li)==0:
                                cap=True
                                break
                    if cap:
                        return (r+1,c+1)
                    # check suicide: any empty neighbour or friendly group with other lib
                    empt=False
                    for dr,dc in DIRS:
                        nr=r+dr; nc=c+dc
                        if 0<=nr<N and 0<=nc<N and b2[nr][nc]==0:
                            empt=True
                            break
                    if empt:
                        # need to ensure not eye? return it
                        return (r+1,c+1)
            return (0,0)

        # pass if clearly losing move in late game
        if best_score < -2 and total > 100:
            return (0,0)
        return (best_move[0]+1, best_move[1]+1)
    except Exception:
        try:
            occ=set(me)|set(opponent)
            for r in range(1,20):
                for c in range(1,20):
                    if (r,c) not in occ:
                        return (r,c)
        except Exception:
            pass
        return (0,0)
