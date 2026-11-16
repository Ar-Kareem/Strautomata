
SIZE = 19

STAR_SET = {(3,3),(3,9),(3,15),(9,3),(9,9),(9,15),(15,3),(15,9),(15,15)}

def _neighbours(r,c):
    if r>0: yield (r-1,c)
    if r<18: yield (r+1,c)
    if c>0: yield (r,c-1)
    if c<18: yield (r,c+1)

def _diag(r,c):
    if r>0 and c>0: yield (r-1,c-1)
    if r>0 and c<18: yield (r-1,c+1)
    if r<18 and c>0: yield (r+1,c-1)
    if r<18 and c<18: yield (r+1,c+1)

def policy(me, opponent, memory):
    try:
        if not isinstance(memory, dict):
            memory = {}
        # convert to 0-indexed sets
        try:
            me_set = set((r-1,c-1) for (r,c) in me)
        except:
            me_set = set()
        try:
            opp_set = set((r-1,c-1) for (r,c) in opponent)
        except:
            opp_set = set()

        # board: 0 empty 1 me 2 opp
        board = [[0]*19 for _ in range(19)]
        for (r,c) in me_set:
            if 0 <= r < 19 and 0 <= c < 19:
                board[r][c] = 1
        for (r,c) in opp_set:
            if 0 <= r < 19 and 0 <= c < 19:
                if board[r][c]==0:
                    board[r][c]=2

        total = len(me_set)+len(opp_set)

        # empty opening instant
        if total==0:
            memory['prev_me'] = list(me_set)
            memory['prev_opp'] = list(opp_set)
            memory['seen'] = memory.get('seen', set())
            try:
                h = tuple(tuple(row) for row in board)
                memory['seen'].add(h)
            except: pass
            memory['move_num'] = memory.get('move_num',0)+1
            return ((4,4), memory)

        # history for ko / superko
        if 'seen' not in memory or not isinstance(memory['seen'], set):
            memory['seen'] = set()
        try:
            cur_hash = tuple(tuple(row) for row in board)
            memory['seen'].add(cur_hash)
        except:
            cur_hash = None

        # last opponent move detection
        last_opp = None
        try:
            prev_opp_list = memory.get('prev_opp', None)
            if prev_opp_list is not None:
                prev_opp_s = set(tuple(x) for x in prev_opp_list)
                diff = opp_set - prev_opp_s
                if len(diff)==1:
                    last_opp = next(iter(diff))
                elif len(diff)>1:
                    # pick one closest to center? just pick arbitrary
                    last_opp = next(iter(diff))
            # store for next time
        except:
            last_opp = None

        # ---- groups ----
        gid_map = [[-1]*19 for _ in range(19)]
        groups = {}  # gid -> {'stones':list, 'libs':set, 'color':int}
        gid = 0
        for sr in range(19):
            for sc in range(19):
                col = board[sr][sc]
                if col==0 or gid_map[sr][sc]!=-1:
                    continue
                # bfs
                stack = [(sr,sc)]
                gid_map[sr][sc]=gid
                stones = []
                libs = set()
                idx = 0
                # use list as stack
                while idx < len(stack):
                    r,c = stack[idx]; idx+=1
                    stones.append((r,c))
                    # neighbours
                    if r>0:
                        nr,nc = r-1,c
                        v = board[nr][nc]
                        if v==0:
                            libs.add((nr,nc))
                        elif v==col and gid_map[nr][nc]==-1:
                            gid_map[nr][nc]=gid
                            stack.append((nr,nc))
                    if r<18:
                        nr,nc = r+1,c
                        v = board[nr][nc]
                        if v==0:
                            libs.add((nr,nc))
                        elif v==col and gid_map[nr][nc]==-1:
                            gid_map[nr][nc]=gid
                            stack.append((nr,nc))
                    if c>0:
                        nr,nc = r,c-1
                        v = board[nr][nc]
                        if v==0:
                            libs.add((nr,nc))
                        elif v==col and gid_map[nr][nc]==-1:
                            gid_map[nr][nc]=gid
                            stack.append((nr,nc))
                    if c<18:
                        nr,nc = r,c+1
                        v = board[nr][nc]
                        if v==0:
                            libs.add((nr,nc))
                        elif v==col and gid_map[nr][nc]==-1:
                            gid_map[nr][nc]=gid
                            stack.append((nr,nc))
                groups[gid]={'stones':stones,'libs':libs,'color':col}
                gid+=1

        move_num = memory.get('move_num', total//2)
        # stage
        if total < 60:
            stage = 0 # opening
        elif total < 220:
            stage = 1 # middle
        else:
            stage = 2 # endgame

        best_score = -10**18
        best_move = None
        best_eye = False
        best_captures = 0
        best_save = 0

        # precompute for speed: board local refs
        # iterate empties
        for r in range(19):
            Brow = board[r]
            Grow = gid_map[r]
            for c in range(19):
                if Brow[c]!=0:
                    continue
                # neighbours collect
                friendly_ids = set()
                opp_ids = set()
                empty_orth = 0
                # for eye / counts we need lists; inline
                # gather orth neighbours
                # unrolled for speed
                if r>0:
                    v = board[r-1][c]
                    if v==0: empty_orth+=1
                    elif v==1: friendly_ids.add(gid_map[r-1][c])
                    else: opp_ids.add(gid_map[r-1][c])
                if r<18:
                    v = board[r+1][c]
                    if v==0: empty_orth+=1
                    elif v==1: friendly_ids.add(gid_map[r+1][c])
                    else: opp_ids.add(gid_map[r+1][c])
                if c>0:
                    v = board[r][c-1]
                    if v==0: empty_orth+=1
                    elif v==1: friendly_ids.add(gid_map[r][c-1])
                    else: opp_ids.add(gid_map[r][c-1])
                if c<18:
                    v = board[r][c+1]
                    if v==0: empty_orth+=1
                    elif v==1: friendly_ids.add(gid_map[r][c+1])
                    else: opp_ids.add(gid_map[r][c+1])

                captures = 0
                cap_adj = []
                for oid in opp_ids:
                    g = groups[oid]
                    if len(g['libs'])==1:
                        # liberty must be (r,c)
                        # verify quickly (almost always true)
                        # if (r,c) not in libs, then not captured (should not happen)
                        if (r,c) in g['libs']:
                            captures += len(g['stones'])
                            # adjacent captured positions for liberty calc
                            # only stones orth-adjacent to (r,c)
                            for (sr,sc) in g['stones']:
                                if abs(sr-r)+abs(sc-c)==1:
                                    cap_adj.append((sr,sc))
                                    break  # at least one; one is enough for non-zero, but collect all adj?
                            # collect all adj (group small usually)
                            # already broke after 1 to save time; that's enough to make libs_after>=1
                save_size = 0
                for fid in friendly_ids:
                    g = groups[fid]
                    if len(g['libs'])==1:
                        # must contain (r,c)
                        save_size += len(g['stones'])

                # liberties after
                # union
                if captures==0:
                    # quick suicide estimate
                    # libs = empty_orth + friendly libs minus (r,c)
                    # use set for accuracy when small
                    s = set()
                    if empty_orth>0:
                        if r>0 and board[r-1][c]==0: s.add((r-1,c))
                        if r<18 and board[r+1][c]==0: s.add((r+1,c))
                        if c>0 and board[r][c-1]==0: s.add((r,c-1))
                        if c<18 and board[r][c+1]==0: s.add((r,c+1))
                    for fid in friendly_ids:
                        # add libs except (r,c)
                        for lb in groups[fid]['libs']:
                            if lb!=(r,c):
                                s.add(lb)
                                if len(s)>4: # early break, we only need to know >2 for scoring except eye? keep full? break to save time
                                    pass
                    libs_after = len(s)
                    if libs_after==0:
                        continue  # suicide illegal
                else:
                    # capture gives liberty
                    s = set(cap_adj)
                    if empty_orth>0:
                        if r>0 and board[r-1][c]==0: s.add((r-1,c))
                        if r<18 and board[r+1][c]==0: s.add((r+1,c))
                        if c>0 and board[r][c-1]==0: s.add((r,c-1))
                        if c<18 and board[r][c+1]==0: s.add((r,c+1))
                    for fid in friendly_ids:
                        for lb in groups[fid]['libs']:
                            if lb!=(r,c):
                                s.add(lb)
                    libs_after = len(s)
                    if libs_after==0:
                        libs_after=1

                # ---- ko check for single capture (potential ko) ----
                if captures==1 and libs_after==1:
                    # simulate full board hash to check superko
                    try:
                        # build new board quickly: copy rows
                        # find captured group
                        cap_gid = None
                        for oid in opp_ids:
                            g2 = groups[oid]
                            if len(g2['libs'])==1 and (r,c) in g2['libs']:
                                cap_gid = oid
                                break
                        if cap_gid is not None:
                            # copy
                            nb = [row[:] for row in board]
                            # remove captured
                            for (sr,sc) in groups[cap_gid]['stones']:
                                nb[sr][sc]=0
                            nb[r][c]=1
                            nh = tuple(tuple(row) for row in nb)
                            if nh in memory['seen']:
                                continue
                    except:
                        pass

                # ---- positional value ----
                x = r if r<9 else 18-r
                y = c if c<9 else 18-c
                d = (x if x<y else y)+1  # 1 edge .. 10 center
                if stage==0:
                    if d==1: pos = -18
                    elif d==2: pos = 22
                    elif d==3: pos = 26
                    elif d==4: pos = 16
                    elif d==5: pos = 8
                    else: pos = 0
                    if (r,c) in STAR_SET:
                        pos += 28
                    # 3-4 points bonus
                    # small center penalty
                elif stage==1:
                    if d==1: pos = -12
                    elif d==2: pos = 12
                    elif d==3: pos = 12
                    elif d==4: pos = 8
                    else: pos = 2
                else:
                    if d==1: pos = 8
                    elif d==2: pos = 10
                    elif d==3: pos = 8
                    else: pos = 2
                    # endgame: prefer dame near stones, handled below

                score = float(pos)

                # contact / shape bonuses (count diag)
                f_orth = len(friendly_ids)  # distinct groups, use as proxy; also need stone count
                # count stones orth
                f_stone_orth = 0
                o_stone_orth = 0
                if r>0:
                    if board[r-1][c]==1: f_stone_orth+=1
                    elif board[r-1][c]==2: o_stone_orth+=1
                if r<18:
                    if board[r+1][c]==1: f_stone_orth+=1
                    elif board[r+1][c]==2: o_stone_orth+=1
                if c>0:
                    if board[r][c-1]==1: f_stone_orth+=1
                    elif board[r][c-1]==2: o_stone_orth+=1
                if c<18:
                    if board[r][c+1]==1: f_stone_orth+=1
                    elif board[r][c+1]==2: o_stone_orth+=1

                score += 9*f_stone_orth + 7*o_stone_orth

                # diagonal support (eye shape / connection)
                f_diag = 0
                o_diag = 0
                if r>0 and c>0:
                    if board[r-1][c-1]==1: f_diag+=1
                    elif board[r-1][c-1]==2: o_diag+=1
                if r>0 and c<18:
                    if board[r-1][c+1]==1: f_diag+=1
                    elif board[r-1][c+1]==2: o_diag+=1
                if r<18 and c>0:
                    if board[r+1][c-1]==1: f_diag+=1
                    elif board[r+1][c-1]==2: o_diag+=1
                if r<18 and c<18:
                    if board[r+1][c+1]==1: f_diag+=1
                    elif board[r+1][c+1]==2: o_diag+=1
                score += 2*f_diag + 1*o_diag

                # captures / saves
                if captures>0:
                    score += 1000 + 180*captures
                    if captures>1:
                        score += 250*captures
                if save_size>0:
                    if libs_after>1:
                        score += 850 + 110*save_size
                    else:
                        score += 450 + 60*save_size

                # attack: put opp in atari / reduce libs
                if captures==0:
                    for oid in opp_ids:
                        g = groups[oid]
                        ll = len(g['libs'])
                        sz = len(g['stones'])
                        if ll==2:
                            score += 170 + 25*sz
                            if sz>=3:
                                score += 80
                        elif ll==3:
                            score += 35 + 6*sz
                        elif ll==4:
                            score += 12 + 2*sz
                        elif ll==1:
                            # should have been capture, but if (r,c) not in libs (weird adjacency via other gid?) ignore
                            pass
                else:
                    # still bonus for reducing other groups
                    for oid in opp_ids:
                        g = groups[oid]
                        if len(g['libs'])!=1:
                            ll = len(g['libs'])
                            sz = len(g['stones'])
                            if ll==2:
                                score += 60 + 10*sz

                # self-atari penalty
                if libs_after==1:
                    if captures==0 and save_size==0:
                        score -= 600
                    elif captures>0:
                        score -= 80
                    else:
                        score -= 250
                elif libs_after==2:
                    # slight penalty if heavily surrounded
                    if o_stone_orth>=2 and f_stone_orth==0:
                        score -= 40
                    else:
                        score -= 12

                # eye fill detection (only if no capture)
                is_eye = False
                if captures==0 and f_stone_orth + (4 - (empty_orth+f_stone_orth+o_stone_orth) ) == 4:
                    # all orth are friendly or off-board, and no opp orth
                    # check: number of on-board orth neighbours == f_stone_orth (i.e. o==0 and empty==0)
                    if empty_orth==0 and o_stone_orth==0:
                        # potential eye, check diagonals
                        # count off-board diags as friendly
                        total_diag = 0
                        friendly_diag = 0
                        # enumerate
                        for (dr,dc) in ((-1,-1),(-1,1),(1,-1),(1,1)):
                            nr,nc = r+dr, c+dc
                            if nr<0 or nr>18 or nc<0 or nc>18:
                                friendly_diag+=1
                                total_diag+=1
                            else:
                                total_diag+=1
                                if board[nr][nc]==1:
                                    friendly_diag+=1
                                elif board[nr][nc]==2:
                                    # opponent controls diagonal -> not solid eye, reduce penalty?
                                    pass
                        # corner: 1 diag, edge: 2 diags, center: 4
                        # eye if all or all-but-one controlled
                        if total_diag==4:
                            if friendly_diag>=3:
                                is_eye=True
                        elif total_diag==2:  # edge? actually edge has 2? wait 19x19 edge non-corner has 2 diags on board +? Let's just require all
                            if friendly_diag>=2:
                                is_eye=True
                        else: # corner 1 diag
                            if friendly_diag>=1:
                                is_eye=True
                        if is_eye:
                            # don't fill own eye unless saving
                            if save_size==0:
                                score -= 900
                            else:
                                score -= 200
                # proximity to last opp move: respond locally
                if last_opp is not None:
                    lr,lc = last_opp
                    cheb = abs(r-lr) if abs(r-lr)>abs(c-lc) else abs(c-lc)
                    if cheb<=2:
                        score += (3-cheb)*18
                    elif cheb<=4:
                        score += 8
                    # manhattan bonus for direct adjacency already covered

                # isolation handling
                # if far from everything and not opening star, penalize in middle game
                if stage!=0 and f_stone_orth==0 and o_stone_orth==0 and f_diag==0 and o_diag==0:
                    # check wider 5x5? approximate: if no stones within 2, it's tenuki - allow but slight penalty in middle
                    # quick scan 5x5
                    found=False
                    for dr in (-2,-1,1,2):
                        nr=r+dr
                        if nr<0 or nr>18: continue
                        for dc in (-2,-1,0,1,2):
                            nc=c+dc
                            if nc<0 or nc>18: continue
                            if abs(dr)<=1 and abs(dc)<=1: continue # already checked
                            if board[nr][nc]!=0:
                                found=True
                                break
                        if found: break
                    if not found:
                        if stage==1:
                            score -= 12
                        elif stage==2:
                            score -= 25  # don't play isolated in endgame

                # endgame dame bonus: prefer moves with empty neighbours? Actually dame has empty neighbours
                if stage==2:
                    score += empty_orth*2

                # tiny deterministic tie-break to prefer center-ish and avoid patterns + small hash jitter
                score += ((r*19+c)%7)*0.3

                if score > best_score:
                    best_score = score
                    best_move = (r,c)
                    best_eye = is_eye
                    best_captures = captures
                    best_save = save_size

        # update memory
        try:
            memory['prev_me'] = list(me_set)
            memory['prev_opp'] = list(opp_set)
            memory['move_num'] = move_num+1
            memory['last_move'] = best_move
        except: pass

        if best_move is None:
            return ((0,0), memory)
        # pass if only eye-filling left or very bad
        if best_eye and best_captures==0 and best_save==0:
            return ((0,0), memory)
        if best_score < -300:
            return ((0,0), memory)
        # late game pass if score very low (no useful dame)
        if stage==2 and best_score < 2 and total>280:
            # check if board almost full?
            pass

        # final legality double-check: must be empty
        br,bc = best_move
        if board[br][bc]!=0:
            # fallback search first empty
            for r in range(19):
                for c in range(19):
                    if board[r][c]==0:
                        return ((r+1,c+1), memory)
            return ((0,0), memory)
        # record resulting hash for ko (approx without full capture sim except single handled; add optimistic)
        try:
            # simulate quickly for best move to add to seen
            nb = [row[:] for row in board]
            # remove captured groups adjacent in atari
            for oid in set():
                pass
            # find captured gids
            for oid in [gid_map[br-1][bc] if br>0 and board[br-1][bc]==2 else -1,
                        gid_map[br+1][bc] if br<18 and board[br+1][bc]==2 else -1,
                        gid_map[br][bc-1] if bc>0 and board[br][bc-1]==2 else -1,
                        gid_map[br][bc+1] if bc<18 and board[br][bc+1]==2 else -1]:
                if oid is not None and oid!=-1 and oid in groups:
                    g = groups[oid]
                    if len(g['libs'])==1 and (br,bc) in g['libs']:
                        for (sr,sc) in g['stones']:
                            nb[sr][sc]=0
            nb[br][bc]=1
            nh = tuple(tuple(row) for row in nb)
            memory['seen'].add(nh)
        except: pass

        return ((br+1,bc+1), memory)
    except Exception:
        # ultimate fallback: first empty
        try:
            occ = set(me).union(set(opponent))
            for r in range(1,20):
                for c in range(1,20):
                    if (r,c) not in occ:
                        return ((r,c), memory)
        except: pass
        try:
            return ((0,0), memory)
        except:
            return ((0,0), {})
