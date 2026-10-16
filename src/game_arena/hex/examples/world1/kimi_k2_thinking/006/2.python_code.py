
from collections import deque
import random

def policy(me, opp, color):
    # ------------------------------------------------------------
    # board geometry
    N = 11
    # neighbour offsets for a hex board (pointy‑top orientation)
    NEIGH = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]

    # ------------------------------------------------------------
    # helper: all cells of the board
    def all_cells():
        for r in range(N):
            for c in range(N):
                yield (r, c)

    # ------------------------------------------------------------
    # helper: neighbours of a cell that stay inside the board
    def neighbours(cell):
        r, c = cell
        for dr, dc in NEIGH:
            nr, nc = r + dr, c + dc
            if 0 <= nr < N and 0 <= nc < N:
                yield (nr, nc)

    # ------------------------------------------------------------
    # BFS that returns a dict {cell : distance} starting from
    # any of the start cells, walking only through passable cells.
    def bfs(start_cells, passable):
        dist = {}
        q = deque()
        for s in start_cells:
            if s in passable:
                dist[s] = 0
                q.append(s)
        while q:
            cur = q.popleft()
            d = dist[cur]
            for nb in neighbours(cur):
                if nb in passable and nb not in dist:
                    dist[nb] = d + 1
                    q.append(nb)
        return dist

    # ------------------------------------------------------------
    # does the player `color` with the given set of stones already
    # connect his two sides ?
    def is_win(stones, color):
        stones = set(stones)
        if color == 'b':          # Black: top‑bottom
            src = [c for c in stones if c[0] == 0]
            if not src:
                return False
            target_row = 10
            # BFS on the player's own stones only
            seen = set(src)
            q = deque(src)
            while q:
                r, c = q.popleft()
                if r == target_row:
                    return True
                for nb in neighbours((r, c)):
                    if nb in stones and nb not in seen:
                        seen.add(nb)
                        q.append(nb)
            return False
        else:                     # White: left‑right
            src = [c for c in stones if c[1] == 0]
            if not src:
                return False
            target_col = 10
            seen = set(src)
            q = deque(src)
            while q:
                r, c = q.popleft()
                if c == target_col:
                    return True
                for nb in neighbours((r, c)):
                    if nb in stones and nb not in seen:
                        seen.add(nb)
                        q.append(nb)
            return False

    # ------------------------------------------------------------
    # immediate win for us
    empty = [c for c in all_cells() if c not in me and c not in opp]
    for mv in empty:
        if is_win(me + [mv], color):
            return mv

    # ------------------------------------------------------------
    # immediate win for the opponent → block it
    opp_color = 'w' if color == 'b' else 'b'
    for mv in empty:
        if is_win(opp + [mv], opp_color):
            return mv

    # ------------------------------------------------------------
    # otherwise: build a shortest‑path based heuristic
    my_passable = set(all_cells()) - set(opp)          # my stones + empties
    opp_passable = set(all_cells()) - set(me)          # opponent stones + empties

    # edges for each colour
    if color == 'b':
        my_src = [(0, c) for c in range(N) if (0, c) in my_passable]
        my_tgt = [(10, c) for c in range(N) if (10, c) in my_passable]
    else:  # white
        my_src = [(r, 0) for r in range(N) if (r, 0) in my_passable]
        my_tgt = [(r, 10) for r in range(N) if (r, 10) in my_passable]

    # distances for us
    d_top = bfs(my_src, my_passable)
    d_bottom = bfs(my_tgt, my_passable)
    INF = 10 ** 9
    L = INF
    my_cands = set()
    for c in my_passable:
        dt = d_top.get(c)
        db = d_bottom.get(c)
        if dt is not None and db is not None:
            total = dt + db
            if total < L:
                L = total
                my_cands = {c}
            elif total == L:
                my_cands.add(c)
    # keep only empty cells
    my_cands = [c for c in my_cands if c in empty]

    # edges for opponent
    if opp_color == 'b':
        opp_src = [(0, c) for c in range(N) if (0, c) in opp_passable]
        opp_tgt = [(10, c) for c in range(N) if (10, c) in opp_passable]
    else:
        opp_src = [(r, 0) for r in range(N) if (r, 0) in opp_passable]
        opp_tgt = [(r, 10) for r in range(N) if (r, 10) in opp_passable]

    # distances for opponent
    d_left = bfs(opp_src, opp_passable)
    d_right = bfs(opp_tgt, opp_passable)
    O = INF
    opp_cands = set()
    for c in opp_passable:
        dl = d_left.get(c)
        dr = d_right.get(c)
        if dl is not None and dr is not None:
            total = dl + dr
            if total < O:
                O = total
                opp_cands = {c}
            elif total == O:
                opp_cands.add(c)
    opp_cands = [c for c in opp_cands if c in empty]

    # ------------------------------------------------------------
    # decide the move
    # a) cell that is both offensive and defensive
    common = [c for c in empty if c in my_cands and c in opp_cands]
    if common:
        common.sort(key=lambda x: abs(x[0] - 5) + abs(x[1] - 5))
        return common[0]

    # b) if opponent is at least as close, block
    if O <= L + 1:
        if opp_cands:
            opp_cands.sort(key=lambda x: abs(x[0] - 5) + abs(x[1] - 5))
            return opp_cands[0]
        # fallback – continue to offensive
    # c) otherwise build our own path
    if my_cands:
        my_cands.sort(key=lambda x: abs(x[0] - 5) + abs(x[1] - 5))
        return my_cands[0]

    # ------------------------------------------------------------
    # no clear path – expand next to our own stones, prefer central cells
    adj_to_me = []
    for c in empty:
        for nb in neighbours(c):
            if nb in me:
                adj_to_me.append(c)
                break
    if adj_to_me:
        adj_to_me.sort(key=lambda x: abs(x[0] - 5) + abs(x[1] - 5))
        return adj_to_me[0]

    # last resort – most central empty cell
    empty.sort(key=lambda x: abs(x[0] - 5) + abs(x[1] - 5))
    return empty[0]
