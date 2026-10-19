
import random
from collections import deque

def policy(board):
    """
    Returns a legal Lines of Action move string: "r1,c1:r2,c2"
    """
    B = board
    me = 1
    opp = -1

    # Directions for 8-neighbor connectivity
    conn_dirs = [(-1, -1), (-1, 0), (-1, 1),
                 (0, -1),           (0, 1),
                 (1, -1),  (1, 0),  (1, 1)]

    def in_bounds(r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def count_pieces_in_line(r, c, dr, dc):
        """Count all pieces (both players) along the full line through (r,c) in direction dr,dc."""
        # Determine the line id by walking to the start
        rr, cc = r, c
        while in_bounds(rr - dr, cc - dc):
            rr -= dr
            cc -= dc
        # Walk to end and count
        cnt = 0
        while in_bounds(rr, cc):
            if B[rr][cc] != 0:
                cnt += 1
            rr += dr
            cc += dc
        return cnt

    def can_jump_and_land(r1, c1, r2, c2):
        """Check line-of-action movement legality including jump rules."""
        dr = r2 - r1
        dc = c2 - c1
        # Normalize direction
        if dr == 0 and dc == 0:
            return False
        step_r = 0 if dr == 0 else (1 if dr > 0 else -1)
        step_c = 0 if dc == 0 else (1 if dc > 0 else -1)
        # Must be horizontal/vertical/diagonal
        if not (step_r == 0 or step_c == 0 or abs(dr) == abs(dc)):
            return False

        # Exact distance rule: move exactly as many squares as total pieces on that line
        total_on_line = count_pieces_in_line(r1, c1, step_r, step_c)
        dist = abs(dr) + abs(dc)
        # dist is number of squares moved: for horizontal/vertical it's abs(dc) or abs(dr),
        # for diagonal it's abs(dr)=abs(dc). We'll compute as max(abs(dr),abs(dc)).
        moved = max(abs(dr), abs(dc))
        if moved != total_on_line:
            return False

        # Check path: may jump friendly but NOT over enemies; landing can capture
        rr, cc = r1 + step_r, c1 + step_c
        # Need to traverse intermediate squares only
        # Landing square is (r2,c2)
        while (rr, cc) != (r2, c2):
            if not in_bounds(rr, cc):
                return False
            if B[rr][cc] == opp:
                return False
            rr += step_r
            cc += step_c

        # Landing: must be empty or enemy
        if B[r2][c2] == me:
            return False
        return True

    def generate_legal_moves():
        moves = []
        # Consider 8 directions for movement; distance is determined by piece count on line.
        dirs = [(-1, -1), (-1, 0), (-1, 1),
                (0, -1),          (0, 1),
                (1, -1),  (1, 0), (1, 1)]
        for r in range(8):
            for c in range(8):
                if B[r][c] != me:
                    continue
                for dr, dc in dirs:
                    # Determine target by exact distance = total pieces in the line
                    total_on_line = count_pieces_in_line(r, c, dr, dc)
                    if total_on_line == 0:
                        continue
                    tr = r + dr * total_on_line
                    tc = c + dc * total_on_line
                    if in_bounds(tr, tc):
                        if can_jump_and_land(r, c, tr, tc):
                            moves.append((r, c, tr, tc))
        return moves

    def apply_move(r1, c1, r2, c2):
        """Return new board after performing capture if any."""
        nb = [row[:] for row in B]
        nb[r2][c2] = me
        nb[r1][c1] = 0
        # captured enemy removed by overwrite
        return nb

    def largest_component_score(nb):
        """Compute largest 8-neighbor component size for current player, and #components."""
        visited = [[False]*8 for _ in range(8)]
        comps = 0
        largest = 0

        for r in range(8):
            for c in range(8):
                if nb[r][c] == me and not visited[r][c]:
                    comps += 1
                    q = deque([(r, c)])
                    visited[r][c] = True
                    size = 0
                    while q:
                        cr, cc = q.popleft()
                        size += 1
                        for dr, dc in conn_dirs:
                            nr, nc = cr + dr, cc + dc
                            if in_bounds(nr, nc) and not visited[nr][nc] and nb[nr][nc] == me:
                                visited[nr][nc] = True
                                q.append((nr, nc))
                    if size > largest:
                        largest = size
        # Higher largest is better, fewer components is better.
        return largest, comps

    # Generate moves
    legal = generate_legal_moves()
    if not legal:
        # Shouldn't happen in normal LoA, but ensure we return something legal-like:
        # fall back to any capture/empty diagonal step could be illegal though.
        # We'll just return a deterministic placeholder (still should be legal if generator is correct).
        return "0,0:0,0"

    best = None
    best_score = None

    # Precompute our total pieces
    my_total = sum(1 for r in range(8) for c in range(8) if B[r][c] == me)

    for (r1, c1, r2, c2) in legal:
        captured = (B[r2][c2] == opp)
        nb = apply_move(r1, c1, r2, c2)
        largest, comps = largest_component_score(nb)

        # Core score terms
        # - Prefer max connectivity: make largest component bigger.
        # - Prefer fewer components.
        # - Captures slightly improve score because they can reduce enemy obstacles.
        # - Add a small incentive to reduce "spread" by preferring moves that don't drastically
        #   reduce largest component (implicit).
        if my_total > 0:
            connectivity_frac = largest / my_total
        else:
            connectivity_frac = 0.0

        score = 0.0
        score += 1000.0 * connectivity_frac
        score += -50.0 * (comps - 1)  # components=1 best -> 0 penalty
        if captured:
            score += 8.0

        # Tie-break: slight randomness but deterministic-ish by using move coords
        score += 0.001 * (r1*8 + c1)  # tiny bias
        score += random.random() * 1e-6

        if best_score is None or score > best_score:
            best_score = score
            best = (r1, c1, r2, c2)

    r1, c1, r2, c2 = best
    return f"{r1},{c1}:{r2},{c2}"
