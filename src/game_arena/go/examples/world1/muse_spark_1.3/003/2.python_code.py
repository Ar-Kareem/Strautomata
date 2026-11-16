
import random
from collections import deque

N = 19
_rng = random.Random(12345)
ZOBRIST = [[[0,0,0] for _ in range(19)] for _ in range(19)]
for r in range(19):
    for c in range(19):
        for k in (1,2):
            ZOBRIST[r][c][k] = _rng.getrandbits(64)

POS = [[0]*19 for _ in range(19)]
for r in range(19):
    for c in range(19):
        d = min(r, 18-r, c, 18-c)
        if d == 0:
            v = -15
        elif d == 1:
            v = 5
        elif d == 2:
            v = 12
        elif d == 3:
            v = 8
        elif d == 4:
            v = 4
        else:
            v = 0
        POS[r][c] = v

OPENING = [
    (4,4),(16,16),(4,16),(16,4),
    (10,4),(10,16),(4,10),(16,10),
    (7,4),(13,4),(4,7),(4,13),
    (16,7),(16,13),(7,16),(13,16),
    (10,10),(7,7),(13,13),(7,13),(13,7),
    (3,4),(4,3),(16,3),(3,16),(16,17),(17,16),(17,4),(4,17),
    (10,7),(7,10),(13,10),(10,13)
]

_seen_hashes = set()

DIRS = ((1,0),(-1,0),(0,1),(0,-1))

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    global _seen_hashes
    try:
        board = [[0]*19 for _ in range(19)]
        for (r,c) in me:
            try:
                if 1 <= r <= 19 and 1 <= c <= 19:
                    board[r-1][c-1] = 1
            except: pass
        for (r,c) in opponent:
            try:
                if 1 <= r <= 19 and 1 <= c <= 19:
                    if board[r-1][c-1] == 0:
                        board[r-1][c-1] = 2
            except: pass

        empties = [(r,c) for r in range(19) for c in range(19) if board[r][c]==0]
        if not empties:
            return (0,0)

        total = 0
        for r in range(19):
            for c in range(19):
                if board[r][c] != 0:
                    total += 1

        cur_hash = 0
        for r in range(19):
            row = board[r]
            for c in range(19):
                v = row[c]
                if v:
                    cur_hash ^= ZOBRIST[r][c][v]

        # groups
        gid_board = [[-1]*19 for _ in range(19)]
        groups = []  # dict color, stones, libs(set int), lib, size
        gid = 0
        for r in range(19):
            for c in range(19):
                if board[r][c] != 0 and gid_board[r][c] == -1:
                    color = board[r][c]
                    q = deque()
                    q.append((r,c))
                    gid_board[r][c] = gid
                    stones = [(r,c)]
                    libs = set()
                    qi = 0
                    # BFS using deque
                    while q:
                        cr,cc = q.popleft()
                        for dr,dc in DIRS:
                            nr, nc = cr+dr, cc+dc
                            if 0 <= nr < 19 and 0 <= nc < 19:
                                v = board[nr][nc]
                                if v == 0:
                                    libs.add(nr*19+nc)
                                elif v == color and gid_board[nr][nc] == -1:
                                    gid_board[nr][nc] = gid
                                    q.append((nr,nc))
                                    stones.append((nr,nc))
                    groups.append({'color':color,'stones':stones,'libs':libs,'lib':len(libs),'size':len(stones)})
                    gid += 1

        def quick_legal(r,c, own_ids, opp_ids, empty_nbs_list, cap_gids):
            # compute liberties after
            lib_set = set(empty_nbs_list)
            for gidd in own_ids:
                g = groups[gidd]
                # union without move point
                mv = r*19+c
                for L in g['libs']:
                    if L != mv:
                        lib_set.add(L)
            # captured adjacent liberties
            if cap_gids:
                # build quick set of connected positions for adjacency check
                # connected = new point + own stones? check via gid membership
                # for each captured stone, if neighbor is new point or belongs to own_ids group -> liberty
                for gidd in cap_gids:
                    g = groups[gidd]
                    for (sx,sy) in g['stones']:
                        # check 4 neighbours
                        is_lib = False
                        if abs(sx-r)+abs(sy-c)==1:
                            is_lib = True
                        else:
                            for dr,dc in DIRS:
                                nr, nc = sx+dr, sy+dc
                                if 0 <= nr < 19 and 0 <= nc < 19:
                                    if nr==r and nc==c:
                                        is_lib=True
                                        break
                                    if board[nr][nc]==1 and gid_board[nr][nc] in own_ids:
                                        is_lib=True
                                        break
                        if is_lib:
                            lib_set.add(sx*19+sy)
                            # one liberty per captured group is enough to be >0,
                            # but collect all for better count; break early if many?
                            # continue to count more accurately but limit
                            if len(lib_set) > 10:
                                pass
            return len(lib_set), lib_set

        # opening: play first free opening point if very early
        if total < 8:
            for (or1,oc1) in OPENING:
                rr, cc = or1-1, oc1-1
                if board[rr][cc] != 0:
                    continue
                # quick legality: empty board always legal, but check near edge case
                own_ids=set(); opp_ids=set(); empty_nbs=[]
                for dr,dc in DIRS:
                    nr,nc=rr+dr,cc+dc
                    if 0 <= nr < 19 and 0 <= nc < 19:
                        v=board[nr][nc]
                        if v==0:
                            empty_nbs.append(nr*19+nc)
                        elif v==1:
                            own_ids.add(gid_board[nr][nc])
                        else:
                            opp_ids.add(gid_board[nr][nc])
                cap_gids=[g for g in opp_ids if groups[g]['lib']==1] if opp_ids else []
                la,_ = quick_legal(rr,cc,own_ids,opp_ids,empty_nbs,cap_gids)
                if not cap_gids and la==0:
                    continue
                return (or1,oc1)

        # candidate generation: points within chebyshev 2 of any stone
        candidates = []
        if total < 40:
            star_set = set((r-1,c-1) for (r,c) in OPENING)
            for (r,c) in empties:
                found=False
                # 5x5 scan
                r0=max(0,r-2); r1=min(18,r+2)
                c0=max(0,c-2); c1=min(18,c+2)
                for nr in range(r0,r1+1):
                    brow=board[nr]
                    for nc in range(c0,c1+1):
                        if brow[nc]!=0:
                            found=True
                            break
                    if found:
                        break
                if found or (r,c) in star_set:
                    candidates.append((r,c))
            if not candidates:
                candidates = empties[:60]
        else:
            for (r,c) in empties:
                r0=max(0,r-2); r1=min(18,r+2)
                c0=max(0,c-2); c1=min(18,c+2)
                found=False
                for nr in range(r0,r1+1):
                    brow=board[nr]
                    for nc in range(c0,c1+1):
                        if brow[nc]!=0:
                            found=True
                            break
                    if found:
                        break
                if found:
                    candidates.append((r,c))
            if not candidates:
                candidates = empties

        # cap candidates for time safety (should rarely trigger)
        if len(candidates) > 360:
            candidates = candidates[:360]

        best_score = -10**18
        best_move = None
        best_res_hash = None
        # tie-break random
        rnd = random.random

        for (r,c) in candidates:
            own_ids=set()
            opp_ids=set()
            empty_nbs=[]
            empty_cnt=0
            for dr,dc in DIRS:
                nr,nc=r+dr,c+dc
                if 0 <= nr < 19 and 0 <= nc < 19:
                    v=board[nr][nc]
                    if v==0:
                        empty_cnt+=1
                        empty_nbs.append(nr*19+nc)
                    elif v==1:
                        own_ids.add(gid_board[nr][nc])
                    else:
                        opp_ids.add(gid_board[nr][nc])
            cap_gids=[]
            cap_size=0
            for gidd in opp_ids:
                g=groups[gidd]
                if g['lib']==1:
                    # ensure its liberty is this point (adjacent guarantees it)
                    cap_gids.append(gidd)
                    cap_size+=g['size']
            save_size=0
            for gidd in own_ids:
                g=groups[gidd]
                if g['lib']==1:
                    save_size+=g['size']

            lib_after,_libset = quick_legal(r,c,own_ids,opp_ids,empty_nbs,cap_gids)
            if not cap_gids and lib_after==0:
                continue  # suicide illegal

            # base score
            if cap_size>0 or save_size>0:
                score = 9000 + (cap_size+save_size)*500
            else:
                score = 0

            # atari / defence bonuses
            for gidd in opp_ids:
                if gidd in cap_gids:
                    continue
                lb=groups[gidd]['lib']
                if lb==2:
                    score+=400
                elif lb==3:
                    score+=100
                elif lb==4:
                    score+=30
                elif lb==5:
                    score+=10
            for gidd in own_ids:
                lb=groups[gidd]['lib']
                if lb==2:
                    score+=250
                elif lb==3:
                    score+=60
                elif lb==4:
                    score+=15

            if len(own_ids)>=2:
                score+=300 + len(own_ids)*50
            elif len(own_ids)==1:
                score+=10
            if len(opp_ids)>=2:
                score+=200 + len(opp_ids)*30

            score+=empty_cnt*10
            score+=POS[r][c]

            if lib_after==1:
                score-=1500
            elif lib_after==2:
                score-=80

            if empty_cnt==0:
                # eye-like
                if own_ids and not opp_ids:
                    if save_size==0:
                        score-=3000
                    else:
                        score-=500
                elif opp_ids and not own_ids:
                    if cap_size>0:
                        score+=2000
                    else:
                        score-=3000
                else:
                    score-=200

            if (r==0 or r==18 or c==0 or c==18) and cap_size==0 and save_size==0:
                score-=120
            if (r==1 or r==17 or c==1 or c==17) and cap_size==0 and save_size==0:
                score-=20

            # ko / superko avoidance via hash
            res_hash = cur_hash ^ ZOBRIST[r][c][1]
            for gidd in cap_gids:
                for (sx,sy) in groups[gidd]['stones']:
                    res_hash ^= ZOBRIST[sx][sy][2]
            if res_hash in _seen_hashes:
                score-=8000

            score+=rnd()*6

            if score>best_score:
                best_score=score
                best_move=(r,c)
                best_res_hash=res_hash

        _seen_hashes.add(cur_hash)
        if len(_seen_hashes)>8000:
            # prevent unbounded growth: clear half (keep recent not tracked precisely, acceptable)
            _seen_hashes.clear()
            _seen_hashes.add(cur_hash)

        if best_move is None:
            return (0,0)
        if best_score < -500:
            return (0,0)
        if best_res_hash is not None:
            _seen_hashes.add(best_res_hash)
        return (best_move[0]+1, best_move[1]+1)
    except Exception:
        try:
            for (r,c) in me:
                pass
            # fallback: first empty
            occ=set(me)|set(opponent)
            for rr in range(1,20):
                for cc in range(1,20):
                    if (rr,cc) not in occ:
                        return (rr,cc)
            return (0,0)
        except:
            return (0,0)
