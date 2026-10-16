
import random
from collections import deque

N = 19
DIRS = [(-1,0),(1,0),(0,-1),(0,1)]

CORNER_STARS = {(4,4),(4,16),(16,4),(16,16)}
SIDE_STARS = {(4,10),(10,4),(10,16),(16,10)}
CENTER_STAR = (10,10)

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    try:
        if memory is None:
            memory = {}
        # board 0 empty, 1 me, 2 opp, 0-indexed internal
        board = [[0]*N for _ in range(N)]
        for r,c in me:
            if 1 <= r <= 19 and 1 <= c <= 19:
                board[r-1][c-1] = 1
        for r,c in opponent:
            if 1 <= r <= 19 and 1 <= c <= 19:
                # don't overwrite in case of duplicate (should not happen)
                if board[r-1][c-1] == 0:
                    board[r-1][c-1] = 2

        total_stones = len(me) + len(opponent)

        # ---- compute groups ----
        gid_board = [[-1]*N for _ in range(N)]
        groups = []  # list of dict(color,size,stones,libs)
        visited = [[False]*N for _ in range(N)]
        for sr in range(N):
            for sc in range(N):
                if board[sr][sc] == 0 or visited[sr][sc]:
                    continue
                color = board[sr][sc]
                q = deque()
                q.append((sr,sc))
                visited[sr][sc] = True
                stones = []
                libs = set()
                while q:
                    r,c = q.popleft()
                    stones.append((r,c))
                    for dr,dc in DIRS:
                        nr, nc = r+dr, c+dc
                        if nr < 0 or nr >= N or nc < 0 or nc >= N:
                            continue
                        if board[nr][nc] == 0:
                            libs.add((nr,nc))
                        elif board[nr][nc] == color and not visited[nr][nc]:
                            visited[nr][nc] = True
                            q.append((nr,nc))
                gid = len(groups)
                for r,c in stones:
                    gid_board[r][c] = gid
                groups.append({'color': color, 'size': len(stones), 'stones': stones, 'libs': libs})

        empties = [(r,c) for r in range(N) for c in range(N) if board[r][c]==0]
        if not empties:
            return ((0,0), memory)

        # fast opening: first move corner
        if total_stones == 0:
            if board[3][3]==0:
                return ((4,4), memory)

        best_move = None
        best_score = -1e18
        best_newlibs = 99

        # precompute for speed: group libs len and size
        glen = [len(g['libs']) for g in groups]
        gsize = [g['size'] for g in groups]
        gcolor = [g['color'] for g in groups]

        for r,c in empties:
            # adjacency
            empty_nb = 0
            adj_f = []
            adj_o = []
            for dr,dc in DIRS:
                nr, nc = r+dr, c+dc
                if nr < 0 or nr >= N or nc < 0 or nc >= N:
                    continue
                v = board[nr][nc]
                if v == 0:
                    empty_nb += 1
                elif v == 1:
                    adj_f.append(gid_board[nr][nc])
                else:
                    adj_o.append(gid_board[nr][nc])
            # dedup
            if adj_f:
                adj_f = list(set(adj_f))
            if adj_o:
                adj_o = list(set(adj_o))

            # capture detection: adjacent opp group with 1 liberty (must be this point)
            cap_groups = []
            cap_size = 0
            for gid in adj_o:
                if glen[gid]==1:
                    # verify (r,c) is the liberty; if adjacent and len 1 it must be
                    # but check to be safe
                    if (r,c) in groups[gid]['libs']:
                        cap_groups.append(gid)
                        cap_size += gsize[gid]

            # legality
            legal = False
            if empty_nb > 0:
                legal = True
            elif cap_size > 0:
                legal = True
            else:
                for gid in adj_f:
                    if glen[gid] > 1:
                        legal = True
                        break
            if not legal:
                continue

            # build captured positions set for liberty BFS
            if cap_groups:
                cap_set = set()
                for gid in cap_groups:
                    # add stones
                    for pos in groups[gid]['stones']:
                        cap_set.add(pos)
            else:
                cap_set = None

            # exact new liberties of own merged group via BFS limited to friendly
            # BFS from (r,c) over color 1
            libs_set = set()
            seen = set()
            seen.add((r,c))
            stack = [(r,c)]
            # iterative
            while stack:
                cr, cc = stack.pop()
                for dr,dc in DIRS:
                    nr, nc = cr+dr, cc+dc
                    if nr < 0 or nr >= N or nc < 0 or nc >= N:
                        continue
                    if cap_set is not None and (nr,nc) in cap_set:
                        libs_set.add((nr,nc))
                        continue
                    bv = board[nr][nc]
                    if bv == 0:
                        libs_set.add((nr,nc))
                    elif bv == 1:
                        if (nr,nc) not in seen:
                            seen.add((nr,nc))
                            stack.append((nr,nc))
                    else:
                        pass
            new_libs = len(libs_set)

            # ---- scoring ----
            score = 0.0

            # capture bonus (scale with size)
            if cap_size > 0:
                score += cap_size * 30.0 + 20.0
                if new_libs == 1:
                    score -= 25.0  # still in atari after capture, risky
                elif new_libs == 2:
                    score -= 3.0

            # defense bonus for adjacent friendly low-lib groups
            for gid in adj_f:
                ol = glen[gid]
                sz = gsize[gid]
                if ol == 1:
                    score += 32.0 + sz * 6.0
                elif ol == 2:
                    score += 9.0 + sz * 1.2
                elif ol == 3:
                    score += 2.5
                elif ol == 4:
                    score += 0.8

            # attack bonus: reduce opp to 1 or 2 libs
            for gid in adj_o:
                if gid in cap_groups:
                    continue
                ol = glen[gid]
                # new libs = ol -1 because (r,c) was a liberty (if it was)
                if (r,c) in groups[gid]['libs']:
                    nol = ol - 1
                else:
                    nol = ol
                sz = gsize[gid]
                if nol == 1:
                    score += 13.0 + sz * 2.5
                elif nol == 2:
                    score += 4.5 + sz * 0.3
                elif nol == 3:
                    score += 1.0

            # self atari penalty
            if cap_size == 0:
                if new_libs == 0:
                    # should not happen (illegal) but skip
                    score -= 1000.0
                elif new_libs == 1:
                    score -= 38.0
                elif new_libs == 2:
                    score -= 3.5
                else:
                    score += min(new_libs, 6) * 0.5
            else:
                if new_libs >= 3:
                    score += min(new_libs, 6) * 0.5

            # connectivity: connect distinct friendly groups
            if len(adj_f) >= 2:
                score += 7.0 + 2.0 * len(adj_f)

            # contact bonus
            score += empty_nb * 1.0
            # fight bonus: near opponent
            if adj_o:
                score += len(adj_o) * 0.7
            if adj_f:
                score += len(adj_f) * 0.5

            # edge penalty (first line bad, second line slightly bad)
            if r==0 or r==N-1 or c==0 or c==N-1:
                if cap_size==0:
                    # check if saving: don't penalize saving much
                    saving = any(glen[g]==1 for g in adj_f)
                    if not saving:
                        score -= 7.0
                    else:
                        score -= 2.0
            elif r==1 or r==N-2 or c==1 or c==N-2:
                if cap_size==0:
                    score -= 2.0

            # eye-fill penalty: surrounded only by own (no empty, no opp, no capture)
            if empty_nb==0 and cap_size==0 and len(adj_o)==0 and len(adj_f)>0:
                score -= 55.0
            # throwing inside strong opp territory: no friendly, no empty, no capture
            # already illegal in many cases, but if legal via friendly with other lib? that case has friendly.
            # suicidal inside: all neighbours opp and new_libs small
            if len(adj_f)==0 and empty_nb==0 and cap_size==0:
                score -= 20.0
            if len(adj_f)==0 and empty_nb==0 and cap_size>0:
                pass  # killing inside, good

            # opening bonuses
            if total_stones < 30:
                pos1 = (r+1,c+1)
                if pos1 in CORNER_STARS:
                    # only if not too close to fight? always good early
                    score += 15.0
                elif pos1 in SIDE_STARS:
                    score += 9.0
                elif pos1 == CENTER_STAR:
                    score += 6.0
                else:
                    # 3rd/4th line bonus
                    de = min(r, N-1-r, c, N-1-c)
                    if de==2 or de==3:
                        score += 2.5
                    elif de==0:
                        score -= 1.0
                # avoid playing too close to existing stone in very early opening? prefer spread
                # small penalty for contact in first moves unless fight
                if total_stones < 6 and (adj_f or adj_o):
                    # contact play early is unusual, slight penalty unless capture
                    if cap_size==0:
                        score -= 3.0
            else:
                # midgame: slight bonus for moves near last opponent stones? proxied by adjacency already
                pass

            # random tie break
            score += random.random()*2.0

            if score > best_score:
                best_score = score
                best_move = (r,c)
                best_newlibs = new_libs

        if best_move is None:
            return ((0,0), memory)

        # pass decision: don't fill eyes / suicide late
        if best_score < -8.0:
            return ((0,0), memory)
        if total_stones > 80 and best_score < 0.5 and best_newlibs <= 1:
            return ((0,0), memory)

        # return 1-indexed
        return (((best_move[0]+1, best_move[1]+1)), memory)

    except Exception:
        # fallback: find any legal empty (non-suicide approx) else pass
        try:
            occ = set(me) | set(opponent)
            for r in range(1,20):
                for c in range(1,20):
                    if (r,c) not in occ:
                        return ((r,c), memory)
            return ((0,0), memory)
        except Exception:
            return ((0,0), {})
