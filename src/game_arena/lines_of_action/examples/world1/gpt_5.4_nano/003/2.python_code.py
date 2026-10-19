
import random
from collections import deque

def policy(board) -> str:
    """
    board: 8x8 list of lists with 0 empty, 1 our pieces, -1 opponent pieces.
    Returns a legal move string: "fr,fc:tr,tc".
    """
    N = 8
    # Determine side to move: assume policy is called for player whose pieces are 1.
    me = 1
    opp = -1

    # Convert to simple access
    b = board

    def in_bounds(r, c):
        return 0 <= r < N and 0 <= c < N

    def count_pieces_in_line(r, c, dr, dc):
        """Count total pieces (both colors) on the line through (r,c) in direction dr,dc."""
        rr, cc = r, c
        # walk to one end
        while in_bounds(rr - dr, cc - dc):
            rr -= dr
            cc -= dc
        total = 0
        # walk to other end
        while in_bounds(rr, cc):
            if b[rr][cc] != 0:
                total += 1
            rr += dr
            cc += dc
        return total

    def is_jump_blocked(fr, fc, tr, tc):
        """Rules: may not jump over opponent pieces. Friendly can be jumped."""
        dr = tr - fr
        dc = tc - fc
        step_r = 0 if dr == 0 else (1 if dr > 0 else -1)
        step_c = 0 if dc == 0 else (1 if dc > 0 else -1)
        # must be aligned already
        rr, cc = fr + step_r, fc + step_c
        while (rr, cc) != (tr, tc):
            if b[rr][cc] == opp:
                return True
            rr += step_r
            cc += step_c
        return False

    def neighbors8_component_count(grid):
        """Compute # connected components among our pieces using 8-neighbor connectivity."""
        visited = [[False]*N for _ in range(N)]
        comps = 0
        sizes = []

        for r in range(N):
            for c in range(N):
                if grid[r][c] == me and not visited[r][c]:
                    comps += 1
                    q = deque([(r, c)])
                    visited[r][c] = True
                    size = 0
                    while q:
                        cr, cc = q.popleft()
                        size += 1
                        for dr in (-1, 0, 1):
                            for dc in (-1, 0, 1):
                                if dr == 0 and dc == 0:
                                    continue
                                nr, nc = cr + dr, cc + dc
                                if in_bounds(nr, nc) and not visited[nr][nc] and grid[nr][nc] == me:
                                    visited[nr][nc] = True
                                    q.append((nr, nc))
                    sizes.append(size)
        return comps, (max(sizes) if sizes else 0), sizes

    def apply_move(fr, fc, tr, tc):
        """Return new grid after applying move (assumes move is legal)."""
        newb = [row[:] for row in b]
        newb[tr][tc] = me
        newb[fr][fc] = 0
        if b[tr][tc] == opp:
            # captured: just overwritten above
            pass
        return newb

    def generate_legal_moves():
        dirs = [(1,0), (-1,0), (0,1), (0,-1), (1,1), (1,-1), (-1,1), (-1,-1)]
        moves = []
        # list our pieces
        pieces = [(r, c) for r in range(N) for c in range(N) if b[r][c] == me]
        if not pieces:
            return moves

        for fr, fc in pieces:
            for dr, dc in dirs:
                # Count total pieces on that line
                L = count_pieces_in_line(fr, fc, dr, dc)
                if L <= 1:
                    continue
                step_r, step_c = dr, dc
                # L squares moved => destination is L-1 steps in that direction from start
                tr, tc = fr + step_r * (L - 1), fc + step_c * (L - 1)
                if not in_bounds(tr, tc):
                    continue
                if b[tr][tc] == me:
                    continue
                # Must also ensure movement is along same line already, satisfied by construction.
                # Check no opponent pieces are jumped over.
                if is_jump_blocked(fr, fc, tr, tc):
                    continue
                moves.append((fr, fc, tr, tc))
        return moves

    legal_moves = generate_legal_moves()
    if not legal_moves:
        # Fallback: no legal moves found (unexpected). Return any safe string format.
        return "0,0:0,0"

    # Heuristic scoring
    def move_score(fr, fc, tr, tc):
        newgrid = apply_move(fr, fc, tr, tc)
        comps, largest, sizes = neighbors8_component_count(newgrid)

        # Primary objective: reduce components and increase largest component.
        # Perfect: comps == 1
        score = 0.0
        score += (10.0 * largest)  # reward biggest component
        score -= (50.0 * comps)     # strong penalty for more components
        if comps == 1:
            score += 10000.0

        # Reward captures
        if b[tr][tc] == opp:
            score += 200.0

        # Additional light preference: keep pieces somewhat centralized to avoid drift
        center = 3.5
        old_dist = abs(fc - center) + abs(fr - center)
        new_dist = abs(tc - center) + abs(tr - center)
        score -= 2.0 * (new_dist - old_dist)

        # Penalize moves that reduce our mobility too much (optional)
        # Approx: count legal moves for us after move (fast enough for 1 ply)
        # Keep it small to fit time.
        saved = b
        nonlocal_b = newgrid  # can't rebind outer used by helper; do direct count with local helpers

        # We'll just estimate mobility by counting available moves from moved position only (cheap)
        # to avoid full regeneration.
        # Compute whether moved piece can connect: if landing on/near our pieces.
        near = 0
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = tr + dr, tc + dc
                if in_bounds(nr, nc) and newgrid[nr][nc] == me:
                    near += 1
        score += 10.0 * near

        return score

    # Evaluate and pick best; add tiny randomness to avoid ties always same
    best = None
    best_s = None
    for mv in legal_moves:
        fr, fc, tr, tc = mv
        s = move_score(fr, fc, tr, tc) + random.random() * 1e-6
        if best is None or s > best_s:
            best = mv
            best_s = s

    fr, fc, tr, tc = best
    return f"{fr},{fc}:{tr},{tc}"
