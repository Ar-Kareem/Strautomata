
from collections import deque

N = 19

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    try:
        board = [[0]*N for _ in range(N)]
        for r, c in me:
            if 1 <= r <= 19 and 1 <= c <= 19:
                board[r-1][c-1] = 1
        for r, c in opponent:
            if 1 <= r <= 19 and 1 <= c <= 19:
                if board[r-1][c-1] == 0:
                    board[r-1][c-1] = 2

        empties = []
        for r in range(N):
            br = board[r]
            for c in range(N):
                if br[c] == 0:
                    empties.append((r, c))
        if not empties:
            return (0, 0)
        total = len(me) + len(opponent)

        # opening book: take corners / sides fast
        if total < 8:
            book = [(3,3),(15,15),(15,3),(3,15),(9,9),(3,9),(9,3),(9,15),(15,9),
                    (3,6),(6,3),(15,6),(6,15),(12,3),(3,12),(15,12),(12,15),
                    (6,6),(12,12),(12,6),(6,12)]
            occ = set((r-1,c-1) for r,c in me) | set((r-1,c-1) for r,c in opponent)
            for br, bc in book:
                if (br,bc) not in occ:
                    return (br+1, bc+1)
            # fallback to first empty
            r,c = empties[0]
            return (r+1, c+1)

        # build groups
        gid_board = [[-1]*N for _ in range(N)]
        groups = []  # list of dict color,size,libs(set int),stones(list)
        gid = 0
        for sr in range(N):
            for sc in range(N):
                if board[sr][sc] == 0 or gid_board[sr][sc] != -1:
                    continue
                color = board[sr][sc]
                q = deque()
                q.append((sr,sc))
                gid_board[sr][sc] = gid
                stones = []
                libs = set()
                while q:
                    r,c = q.popleft()
                    stones.append((r,c))
                    for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
                        nr, nc = r+dr, c+dc
                        if nr < 0 or nr >= N or nc < 0 or nc >= N:
                            continue
                        if board[nr][nc] == 0:
                            libs.add(nr*N+nc)
                        elif board[nr][nc] == color and gid_board[nr][nc] == -1:
                            gid_board[nr][nc] = gid
                            q.append((nr,nc))
                groups.append({'color': color, 'size': len(stones), 'libs': libs, 'stones': stones})
                gid += 1

        dirs = ((1,0),(-1,0),(0,1),(0,-1))
        best = None
        best_score = -1e18

        # precompute stone positions for window counts (use board directly)
        for er, ec in empties:
            # neighbor classification
            f_ids = set()
            o_ids = set()
            empty_adj = 0
            empty_nbs = []
            f_adj = 0
            o_adj = 0
            wall = 0
            friendly_orth = 0
            for dr, dc in dirs:
                nr, nc = er+dr, ec+dc
                if nr < 0 or nr >= N or nc < 0 or nc >= N:
                    wall += 1
                    continue
                v = board[nr][nc]
                if v == 0:
                    empty_adj += 1
                    empty_nbs.append(nr*N+nc)
                elif v == 1:
                    f_adj += 1
                    friendly_orth += 1
                    f_ids.add(gid_board[nr][nc])
                else:
                    o_adj += 1
                    o_ids.add(gid_board[nr][nc])

            # captures
            captures = 0
            cap_ids = set()
            for g in o_ids:
                glibs = groups[g]['libs']
                # single liberty neighbor must be this point
                if len(glibs) == 1 and (er*N+ec) in glibs:
                    captures += groups[g]['size']
                    cap_ids.add(g)

            # suicide check
            if captures == 0 and empty_adj == 0:
                if not f_ids:
                    continue  # suicide, no friendly, surrounded by opp
                suicide = True
                for g in f_ids:
                    if len(groups[g]['libs']) > 1:
                        suicide = False
                        break
                if suicide:
                    continue

            # own size at risk
            own_size = 1
            for g in f_ids:
                own_size += groups[g]['size']

            # new liberties estimate
            union_libs = set()
            for g in f_ids:
                union_libs |= groups[g]['libs']
            union_libs.discard(er*N+ec)
            for code in empty_nbs:
                union_libs.add(code)
            # captured adjacent stones become liberties
            if cap_ids:
                for dr, dc in dirs:
                    nr, nc = er+dr, ec+dc
                    if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == 2:
                        gg = gid_board[nr][nc]
                        if gg in cap_ids:
                            union_libs.add(nr*N+nc)
            new_libs = len(union_libs)
            if captures == 0 and new_libs == 0:
                continue  # illegal

            score = 0.0

            if captures > 0:
                score += 1000 + 150 * captures

            # save / defend
            save_bonus = 0
            for g in f_ids:
                l = len(groups[g]['libs'])
                sz = groups[g]['size']
                if l == 1:
                    save_bonus += 800 + 100 * sz
                elif l == 2:
                    save_bonus += 25 + 6 * sz
                elif l == 3:
                    save_bonus += 5 + 1 * sz
            score += save_bonus

            # attack
            atk = 0
            for g in o_ids:
                if g in cap_ids:
                    continue
                l = len(groups[g]['libs'])
                sz = groups[g]['size']
                if l == 2:
                    atk += 130 + 35 * sz
                elif l == 3:
                    atk += 12 + 2 * sz
                elif l == 4:
                    atk += 4
            score += atk

            # connectivity / contact
            score += f_adj * 8 + o_adj * 4
            score += empty_adj * 2.5
            score += new_libs * 1.2

            # edge penalties
            if er == 0 or er == 18 or ec == 0 or ec == 18:
                score -= 14 if captures == 0 else 4
            elif er == 1 or er == 17 or ec == 1 or ec == 17:
                score -= 4 if captures == 0 else 1
            else:
                # small bonus for 3rd/4th line
                if er in (2,3,15,16) or ec in (2,3,15,16):
                    score += 2

            # eye fill penalty: all orth friendly/wall
            if friendly_orth + wall == 4 and captures == 0:
                # need to check if really eye (no capture) -> heavy
                score -= 900
            elif empty_adj == 0 and captures == 0 and f_adj > 0 and o_adj == 0:
                score -= 500

            # self-atari / snapback
            if new_libs == 1:
                if captures > 0:
                    # risk losing own_size to recapture
                    score -= 200 * own_size
                else:
                    score -= 200 * own_size + 100
            elif new_libs == 2:
                # slight danger, reduce if no compensating tactic
                if captures == 0 and save_bonus == 0 and atk == 0:
                    score -= 30
                elif captures == 0 and save_bonus == 0:
                    score -= 15

            # influence window 5x5
            f_win = 0
            o_win = 0
            r0 = er-2 if er-2 > 0 else 0
            r1 = er+2 if er+2 < 18 else 18
            c0 = ec-2 if ec-2 > 0 else 0
            c1 = ec+2 if ec+2 < 18 else 18
            for rr in range(r0, r1+1):
                brow = board[rr]
                for cc in range(c0, c1+1):
                    if rr == er and cc == ec:
                        continue
                    v = brow[cc]
                    if v == 1:
                        f_win += 1
                    elif v == 2:
                        o_win += 1
            if total < 60:
                # spread own, approach opp
                score += min(o_win, 6) * 3.0 - min(f_win, 6) * 2.0
            else:
                score += min(f_win, 5) * 0.8 + min(o_win, 5) * 1.2

            # tiny tie-breaker deterministic
            score += ((er * 19 + ec) % 7) * 0.1

            if score > best_score:
                best_score = score
                best = (er, ec)

        if best is None:
            return (0, 0)
        # pass if only bad moves remain (avoid filling eyes)
        if best_score < 0:
            return (0, 0)
        return (best[0]+1, best[1]+1)
    except Exception:
        try:
            occ = set(me) | set(opponent)
            for r in range(1, 20):
                for c in range(1, 20):
                    if (r, c) not in occ:
                        return (r, c)
        except Exception:
            pass
        return (0, 0)
