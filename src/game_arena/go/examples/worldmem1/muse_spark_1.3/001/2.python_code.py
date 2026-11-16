
DIRS = [(1,0),(-1,0),(0,1),(0,-1)]
DIAG = [(1,1),(1,-1),(-1,1),(-1,-1)]
N = 19

OPENING = [
 (4,4),(16,16),(4,16),(16,4),
 (10,10),
 (4,10),(10,4),(16,10),(10,16),
 (7,4),(4,7),(7,16),(16,7),(13,4),(4,13),(13,16),(16,13),(4,15),(15,4),(4,5),(5,4),
 (16,5),(5,16),(16,15),(15,16),
 (7,7),(7,13),(13,7),(13,13),
 (10,7),(7,10),(10,13),(13,10),
 (6,4),(4,6),(6,16),(16,6),(14,4),(4,14),(14,16),(16,14),
 (10,4),(4,10),
 (3,4),(4,3),(3,16),(16,3),(16,17),(17,16),(3,3),(3,17),(17,3),(17,17),
]

def _neighbors(r,c):
    if r>1: yield (r-1,c)
    if r<19: yield (r+1,c)
    if c>1: yield (r,c-1)
    if c<19: yield (r,c+1)

def _compute_groups(stones_set, occupied):
    groups = []
    visited = set()
    for s in stones_set:
        if s in visited:
            continue
        # bfs
        stack = [s]
        visited.add(s)
        stones = []
        libs = set()
        idx = 0
        while idx < len(stack):
            x,y = stack[idx]
            idx+=1
            stones.append((x,y))
            for nb in _neighbors(x,y):
                if nb in stones_set:
                    if nb not in visited:
                        visited.add(nb)
                        stack.append(nb)
                elif nb not in occupied:
                    libs.add(nb)
        groups.append((stones, libs))
    return groups

def _simulate(board_me, board_opp, occupied, r, c):
    # board_me/opp are sets, occupied set
    # place me at r,c, return (legal, captured_list, new_me_group_libs, new_opp_groups_libs_min, new_me_set, new_opp_set)
    # assumes (r,c) empty
    new_me = board_me | {(r,c)}
    # find opponent neighbor groups to capture
    # need opp groups; compute only adjacent
    captured = set()
    # find opp groups adjacent
    seen_opp = set()
    for nb in _neighbors(r,c):
        if nb in board_opp and nb not in seen_opp:
            # bfs opp group
            stack = [nb]
            seen_opp.add(nb)
            grp = [nb]
            libs = set()
            qi=0
            while qi < len(stack):
                x,y = stack[qi]; qi+=1
                for nn in _neighbors(x,y):
                    if nn == (r,c):
                        continue
                    if nn in board_opp:
                        if nn not in seen_opp:
                            seen_opp.add(nn)
                            stack.append(nn)
                            grp.append(nn)
                    elif nn not in occupied:
                        libs.add(nn)
                    # if nn == (r,c) it's now occupied, not lib
            # libs computed without (r,c); if empty -> captured
            if len(libs)==0:
                for st in grp:
                    captured.add(st)
    new_opp = board_opp - captured
    new_occupied = (occupied | {(r,c)}) - captured
    # compute liberties of new own group at (r,c)
    stack=[(r,c)]
    vis={(r,c)}
    libs=set()
    qi=0
    while qi<len(stack):
        x,y=stack[qi]; qi+=1
        for nn in _neighbors(x,y):
            if nn in captured:
                libs.add(nn)
            elif nn in new_me:
                if nn not in vis:
                    vis.add(nn)
                    stack.append(nn)
            elif nn not in new_occupied:
                libs.add(nn)
    if len(libs)==0:
        return (False, captured, 0, new_me, new_opp)
    return (True, captured, len(libs), new_me, new_opp)

def policy(me, opponent, memory):
    import time
    t0 = time.time()
    try:
        me_set = set(me) if me else set()
        opp_set = set(opponent) if opponent else set()
        occupied = me_set | opp_set

        if not isinstance(memory, dict):
            memory = {}
        if "seen" not in memory:
            memory["seen"] = set()
        seen = memory["seen"]
        # hash current
        try:
            cur_hash = (frozenset(me_set), frozenset(opp_set))
            seen.add(cur_hash)
            # cap size
            if len(seen) > 2000:
                # keep recent
                seen.clear()
                seen.add(cur_hash)
        except:
            pass

        # helper to find any legal fallback
        def first_legal():
            for r in range(1,20):
                for c in range(1,20):
                    if (r,c) not in occupied:
                        ok, cap, libs, nm, no = _simulate(me_set, opp_set, occupied, r, c)
                        if ok:
                            try:
                                h=(frozenset(nm),frozenset(no))
                                if h in seen:
                                    continue
                            except: pass
                            return (r,c)
            return (0,0)

        empties = [(r,c) for r in range(1,20) for c in range(1,20) if (r,c) not in occupied]
        if not empties:
            memory["prev_opp"] = set(opp_set)
            memory["prev_me"] = set(me_set)
            return ((0,0), memory)

        # detect last opp move via memory
        last_opp = None
        try:
            prev_opp = memory.get("prev_opp", None)
            if prev_opp is not None:
                diff = opp_set - set(prev_opp)
                if len(diff)==1:
                    last_opp = next(iter(diff))
                elif len(diff)>1:
                    # pick one closest to our stones? just pick arbitrary
                    last_opp = next(iter(diff))
        except:
            pass

        total = len(me_set)+len(opp_set)

        # compute groups
        try:
            my_groups = _compute_groups(me_set, occupied)
            opp_groups = _compute_groups(opp_set, occupied)
        except:
            mv = first_legal()
            memory["prev_opp"]=set(opp_set); memory["prev_me"]=set(me_set)
            return (mv, memory)

        # map liberty -> capture value
        cap_moves = {}  # move -> total captured
        for stones, libs in opp_groups:
            if len(libs)==1:
                mv = next(iter(libs))
                cap_moves[mv] = cap_moves.get(mv,0)+len(stones)

        save_moves = {} # move -> max group size to save
        for stones, libs in my_groups:
            if len(libs)==1:
                mv = next(iter(libs))
                sz = len(stones)
                if mv not in save_moves or sz>save_moves[mv]:
                    save_moves[mv]=sz

        # helper legality check with ko
        def is_legal_move(r,c):
            if (r,c) in occupied:
                return False
            ok, cap, libs, nm, no = _simulate(me_set, opp_set, occupied, r, c)
            if not ok:
                return False
            try:
                h=(frozenset(nm),frozenset(no))
                if h in seen:
                    return False
            except: pass
            return True

        # 1) winning captures
        if cap_moves:
            # sort by captured size desc
            ordered = sorted(cap_moves.items(), key=lambda x: -x[1])
            for mv, sz in ordered:
                r,c = mv
                if (r,c) in occupied:
                    continue
                ok, cap, libs, nm, no = _simulate(me_set, opp_set, occupied, r, c)
                if not ok:
                    continue
                try:
                    h=(frozenset(nm),frozenset(no))
                    if h in seen:
                        continue
                except: pass
                memory["prev_opp"]=set(opp_set); memory["prev_me"]=set(me_set)|(set([mv]))
                try: seen.add(h)
                except: pass
                return (mv, memory)
            # if all captures ko-illegal, fall through

        # 2) must save own group in atari
        if save_moves:
            ordered = sorted(save_moves.items(), key=lambda x: -x[1])
            for mv, sz in ordered:
                r,c = mv
                if (r,c) in occupied:
                    continue
                ok, cap, libs, nm, no = _simulate(me_set, opp_set, occupied, r, c)
                if not ok:
                    continue
                try:
                    h=(frozenset(nm),frozenset(no))
                    if h in seen:
                        continue
                except: pass
                # require that it actually lives (libs>1) or captures
                if libs<=1 and len(cap)==0:
                    continue
                memory["prev_opp"]=set(opp_set); memory["prev_me"]=set(me_set)|(set([mv]))
                try: seen.add(h)
                except: pass
                return (mv, memory)

        # 3) opening book
        if total < 12:
            for mv in OPENING:
                if mv in occupied:
                    continue
                # distance to opponent: prefer not adjacent to opponent in very first moves? allow
                # check legal
                r,c = mv
                ok, cap, libs, nm, no = _simulate(me_set, opp_set, occupied, r, c)
                if not ok:
                    continue
                try:
                    h=(frozenset(nm),frozenset(no))
                    if h in seen:
                        continue
                except: pass
                # avoid playing too close to opponent stone (distance 1) in empty board? still ok
                memory["prev_opp"]=set(opp_set); memory["prev_me"]=set(me_set)|(set([mv]))
                try: seen.add(h)
                except: pass
                return (mv, memory)

        # Build quick lookup: stone -> group libs len and size
        # For scoring
        opp_lib_map = {}  # stone -> (libs_len, size)
        for stones, libs in opp_groups:
            L=len(libs); S=len(stones)
            for s in stones:
                opp_lib_map[s]= (L,S)
        my_lib_map = {}
        for stones, libs in my_groups:
            L=len(libs); S=len(stones)
            for s in stones:
                my_lib_map[s]=(L,S)

        # score empties quickly
        scored = []
        for (r,c) in empties:
            # time guard
            # edge counts
            f_n=0; o_n=0; e_n=0
            atari_opp_bonus=0
            threat_size=0
            defend_bonus=0
            # orthogonal neighbors
            # manually
            for nb in _neighbors(r,c):
                if nb in me_set:
                    f_n+=1
                    info = my_lib_map.get(nb)
                    if info:
                        L,S = info
                        if L==2:
                            defend_bonus += 20 + S*5
                        elif L==3:
                            defend_bonus += 5
                elif nb in opp_set:
                    o_n+=1
                    info = opp_lib_map.get(nb)
                    if info:
                        L,S = info
                        if L==2:
                            atari_opp_bonus += 60 + S*15
                            threat_size+=S
                        elif L==3:
                            atari_opp_bonus += 10 + S*2
                        elif L==1:
                            # should have been capture, but keep
                            atari_opp_bonus += 5000
                else:
                    e_n+=1
            # eye fill detection: all neighbors friendly or edge, no opponent neighbor
            edge=0
            if r==1 or r==19: edge+=1
            if c==1 or c==19: edge+=1
            # number of orthogonal positions = 4 - edge? Actually corners have 2, edges 3
            # eye-like if o_n==0 and f_n+edge==4? For corner f_n==2+edge2 => eye. For edge f_n==3+edge1
            is_eye_like = False
            if o_n==0 and (f_n+edge==4):
                # check diagonals: if opponent controls diagonals, not eye
                o_diag=0
                f_diag=0
                for dr,dc in DIAG:
                    nr=r+dr; nc=c+dc
                    if 1<=nr<=19 and 1<=nc<=19:
                        if (nr,nc) in opp_set: o_diag+=1
                        elif (nr,nc) in me_set: f_diag+=1
                # if many opponent diags, it's not solid eye, less penalty
                if o_diag==0:
                    is_eye_like=True
                elif o_diag==1 and total>40:
                    is_eye_like=True
            # line penalty
            line_pen=0
            if r==1 or r==19 or c==1 or c==19:
                line_pen=-30
            elif r==2 or r==19-1 or c==2 or c==19-1:
                line_pen=-12
            elif r in (3,4,16,17) or c in (3,4,16,17):
                line_pen=4
            # proximity to last move
            prox=0
            if last_opp is not None:
                d = abs(r-last_opp[0])+abs(c-last_opp[1])
                if d==1: prox=25
                elif d==2: prox=15
                elif d==3: prox=6
                elif d==4: prox=2
            # connection bonus
            conn = f_n*6 + o_n*5
            # avoid isolated far moves in midgame: if f_n==0 and o_n==0 penalize unless empty area large
            isolated_pen=0
            if f_n==0 and o_n==0:
                # check 2-step neighborhood has any stone? if none, very isolated
                has_near=False
                for dr in range(-2,3):
                    for dc in range(-2,3):
                        if dr==0 and dc==0: continue
                        nr=r+dr; nc=c+dc
                        if 1<=nr<=19 and 1<=nc<=19:
                            if (nr,nc) in occupied:
                                has_near=True
                                break
                    if has_near: break
                if not has_near:
                    isolated_pen=-15 if total>30 else 0
            # center control small
            dist_center = abs(r-10)+abs(c-10)
            center_bonus = -dist_center*0.3

            s = 0
            s += conn + atari_opp_bonus + defend_bonus + line_pen + prox + isolated_pen + center_bonus
            if is_eye_like:
                # huge penalty, but allow if defending? saves already handled, so penalize
                s -= 5000
            scored.append((s,(r,c),f_n,o_n,atari_opp_bonus,defend_bonus))

        scored.sort(key=lambda x: -x[0])
        # take top K and simulate
        K = 30
        if len(scored)<K: K=len(scored)
        best=None
        best_s=-1e18
        # if best quick score is eye-fill only (very negative), consider pass
        # simulate top K
        for i in range(K):
            s,(r,c),f_n,o_n,at_bonus,def_bonus = scored[i]
            # early time abort
            if time.time()-t0>0.85:
                break
            ok, cap, libs, nm, no = _simulate(me_set, opp_set, occupied, r, c)
            if not ok:
                continue
            try:
                h=(frozenset(nm),frozenset(no))
                if h in seen:
                    continue
            except:
                h=None
            # adjust
            adj = s
            if len(cap)>0:
                adj += 5000 + len(cap)*100
            if libs==1:
                adj -= 600  # self atari
                # if atari gives capture threat? check if libs==1 but threatens? still bad
            elif libs==2:
                adj -= 25
            elif libs>=3:
                adj += libs*2
            # liberty count of adjacent opp after move: compute quickly
            # we can approximate: for each neighbor opp stone not captured, its libs -1 (since we filled one) + maybe?
            # Use full recompute for neighbors only if adj promising? skip detailed, use at_bonus already
            # penalize filling second eye? already
            # bonus for capturing string with net gain? done
            # prefer larger libs
            if adj>best_s:
                best_s=adj
                best=((r,c),h,nm)

        # pass threshold: if best is very bad (all eye fills) -> pass
        if best is None:
            memory["prev_opp"]=set(opp_set); memory["prev_me"]=set(me_set)
            return ((0,0), memory)
        # if best score extremely low, pass rather than fill eye
        # eye moves scored -5000, so threshold -1000
        if best_s < -1000:
            memory["prev_opp"]=set(opp_set); memory["prev_me"]=set(me_set)
            return ((0,0), memory)
        # late game: if board fairly full and best is isolated dame with low score, maybe pass? 
        # if empties small and best_s < 0, pass to avoid filling territory
        if total>200 and best_s < -5:
            # check if any capture/atari available? none (handled). So pass.
            memory["prev_opp"]=set(opp_set); memory["prev_me"]=set(me_set)
            return ((0,0), memory)

        mv,h,nm = best
        memory["prev_opp"]=set(opp_set); memory["prev_me"]=set(me_set)|(set([mv]))
        try:
            if h is not None: seen.add(h)
        except: pass
        return (mv, memory)
    except Exception:
        try:
            me_set = set(me) if me else set()
            occ = me_set | set(opponent if opponent else [])
            for r in range(1,20):
                for c in range(1,20):
                    if (r,c) not in occ:
                        return ((r,c), memory if isinstance(memory,dict) else {})
            return ((0,0), memory if isinstance(memory,dict) else {})
        except:
            return ((0,0), {})

