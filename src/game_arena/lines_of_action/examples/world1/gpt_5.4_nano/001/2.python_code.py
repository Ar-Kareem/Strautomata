
import random
from collections import deque

def policy(board):
    # Board: 8x8 list of lists with 0 empty, 1 self, -1 opponent.
    N = 8
    me = 1
    opp = -1
    b = board

    # --- Utilities ---
    def inb(r, c):
        return 0 <= r < N and 0 <= c < N

    def get(r, c):
        return b[r][c]

    def count_on_line_through(r, c, dr, dc):
        # Count total pieces (both colors) along the full line (row/col/diag) determined by (r,c) and (dr,dc)
        # dr,dc must be one of 8 directions with step -1/0/1.
        # We extend to the ends and count.
        rr, cc = r, c
        while inb(rr - dr, cc - dc):
            rr -= dr
            cc -= dc
        total = 0
        while inb(rr, cc):
            if b[rr][cc] != 0:
                total += 1
            rr += dr
            cc += dc
        return total

    def can_jump_without_crossing_enemy(fr, fc, tr, tc):
        # Moving in straight/diag direction; check intermediate squares:
        # can jump over friendly but not over enemy.
        dr = (tr - fr)
        dc = (tc - fc)
        steps = max(abs(dr), abs(dc))
        dr = 0 if steps == 0 else dr // steps
        dc = 0 if steps == 0 else dc // steps
        rr, cc = fr + dr, fc + dc
        while (rr, cc) != (tr, tc):
            if b[rr][cc] == opp:
                return False
            rr += dr
            cc += dc
        return True

    def connected_components_size():
        # Return size of largest 8-neighbor component for current player (me)
        seen = [[False]*N for _ in range(N)]
        best = 0

        dirs8 = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
        for r in range(N):
            for c in range(N):
                if b[r][c] == me and not seen[r][c]:
                    q = deque([(r,c)])
                    seen[r][c] = True
                    sz = 0
                    while q:
                        x,y = q.popleft()
                        sz += 1
                        for dx,dy in dirs8:
                            nx, ny = x+dx, y+dy
                            if inb(nx, ny) and not seen[nx][ny] and b[nx][ny] == me:
                                seen[nx][ny] = True
                                q.append((nx, ny))
                    if sz > best:
                        best = sz
        return best

    def all_moves():
        moves = []
        # 8 directions but movement may have dr=0 or dc=0 etc.
        dirs = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
        # For each own piece, consider each direction; distance = total pieces on that line.
        for fr in range(N):
            for fc in range(N):
                if b[fr][fc] != me:
                    continue
                for dr, dc in dirs:
                    line_count = count_on_line_through(fr, fc, dr, dc)
                    if line_count <= 1:
                        continue
                    # move exactly line_count squares; direction step is (sign of dr, sign of dc)
                    step_r, step_c = dr, dc
                    tr = fr + step_r * line_count
                    tc = fc + step_c * line_count
                    if not inb(tr, tc):
                        continue
                    # Destination: can be empty or contain opponent; cannot contain own
                    if b[tr][tc] == me:
                        continue
                    # Jump rule: no jumping over enemy
                    if not can_jump_without_crossing_enemy(fr, fc, tr, tc):
                        continue
                    # Legal move
                    moves.append((fr, fc, tr, tc))
        return moves

    def apply_move(move):
        fr, fc, tr, tc = move
        nb = [row[:] for row in b]
        # Move piece, capture if opponent at destination
        nb[tr][tc] = me
        nb[fr][fc] = 0
        # captured piece removed automatically by overwrite
        return nb

    def score_position(nb):
        # Temporarily set b for scoring? We'll compute from nb.
        # Components for me on nb
        # Create simple helpers using nb directly:
        def inb2(r, c):
            return 0 <= r < N and 0 <= c < N

        dirs8 = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

        # largest component
        seen = [[False]*N for _ in range(N)]
        best = 0
        me_cells = []
        for r in range(N):
            for c in range(N):
                if nb[r][c] == me:
                    me_cells.append((r,c))
        for r in range(N):
            for c in range(N):
                if nb[r][c] == me and not seen[r][c]:
                    q = deque([(r,c)])
                    seen[r][c] = True
                    sz = 0
                    while q:
                        x,y = q.popleft()
                        sz += 1
                        for dx,dy in dirs8:
                            nx, ny = x+dx, y+dy
                            if inb2(nx, ny) and not seen[nx][ny] and nb[nx][ny] == me:
                                seen[nx][ny] = True
                                q.append((nx, ny))
                    best = max(best, sz)

        # spread heuristic: bounding box area (smaller is better)
        rows = [r for r,c in me_cells]
        cols = [c for r,c in me_cells]
        if me_cells:
            spread = (max(rows)-min(rows)) + (max(cols)-min(cols))
        else:
            spread = 99

        # centralization: closer to center better
        center = 3.5
        central = 0.0
        for r,c in me_cells:
            central += abs(r-center) + abs(c-center)
        # opponent interference: slight penalty if opponent has larger component (to avoid bad races)
        opp_best = 0
        if opp_cells := [(r,c) for r in range(N) for c in range(N) if nb[r][c] == opp]:
            seen2 = [[False]*N for _ in range(N)]
            for r in range(N):
                for c in range(N):
                    if nb[r][c] == opp and not seen2[r][c]:
                        q = deque([(r,c)])
                        seen2[r][c] = True
                        sz=0
                        while q:
                            x,y=q.popleft(); sz+=1
                            for dx,dy in dirs8:
                                nx, ny = x+dx, y+dy
                                if inb2(nx, ny) and not seen2[nx][ny] and nb[nx][ny] == opp:
                                    seen2[nx][ny]=True
                                    q.append((nx,ny))
                        opp_best=max(opp_best, sz)

        # Combine: maximize connectivity; minimize spread and central distance
        # weights tuned for short search
        total_pieces = len(me_cells)
        # If already fully connected, huge reward
        if best == total_pieces and total_pieces > 0:
            conn_reward = 10000
        else:
            conn_reward = 200 * best

        # fewer spread and central distance better
        return conn_reward - 3.0*spread - 0.8*central - 25*(opp_best)

    moves = all_moves()
    if not moves:
        # Fallback: attempt a random move from any adjacent? but must be legal.
        # Since moves should not be empty, just return a guaranteed legal if possible:
        # Try again deterministically by relaxing? Instead, brute recomputation already done.
        # We'll return a no-op format is not allowed. So we pick the first legal if exists.
        return "0,0:0,0"  # will likely be illegal; but should be unreachable.

    # Evaluate all moves
    best_move = None
    best_score = None

    # Deterministic tie-break order for reproducibility
    moves_sorted = sorted(moves, key=lambda m: (m[0], m[1], m[2], m[3]))
    for mv in moves_sorted:
        nb = apply_move(mv)
        sc = score_position(nb)
        if best_score is None or sc > best_score:
            best_score = sc
            best_move = mv

    fr, fc, tr, tc = best_move
    return f"{fr},{fc}:{tr},{tc}"
