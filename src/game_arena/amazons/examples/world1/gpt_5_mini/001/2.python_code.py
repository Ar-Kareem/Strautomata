
import numpy as np

def policy(board) -> str:
    """
    Return a legal Amazons move for the player with pieces marked '1' on a 6x6 board.
    Move format: "from_row,from_col:to_row,to_col:arrow_row,arrow_col"
    """
    # Ensure we have a numpy array copy to safely index
    b = np.asarray(board)
    H, W = b.shape
    assert H == 6 and W == 6, "Expected 6x6 board"

    # 8 queen directions
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1),
                  (-1, -1), (-1, 1), (1, -1), (1, 1)]

    def sliding_positions(grid, r, c):
        """Yield all empty positions reachable from (r,c) by queen moves (no stepping on non-zero)."""
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            while 0 <= nr < H and 0 <= nc < W and grid[nr, nc] == 0:
                yield (nr, nc)
                nr += dr
                nc += dc

    # Find our amazons
    our_positions = list(zip(*np.where(b == 1)))
    # Iterate through each amazon, reachable destinations, and arrow targets.
    for fr, fc in our_positions:
        # For each possible move destination
        for tr, tc in sliding_positions(b, fr, fc):
            # Simulate the move: vacate from, place amazon at to
            b2 = b.copy()
            b2[fr, fc] = 0
            b2[tr, tc] = 1
            # From the landing square, find all arrow targets (sliding on b2)
            for ar, ac in sliding_positions(b2, tr, tc):
                # Found a legal move triple
                return f"{int(fr)},{int(fc)}:{int(tr)},{int(tc)}:{int(ar)},{int(ac)}"

    # If we reach here, no legal move was found.
    # The environment is guaranteed not to call us in that terminal case,
    # but to be robust, try fallback: attempt any adjacent step and arrow if possible.
    # Try brute-force: any from,to,arrow triple that satisfies rules checked explicitly.
    coords = [(r, c) for r in range(H) for c in range(W)]
    for fr, fc in coords:
        if b[fr, fc] != 1:
            continue
        for tr, tc in coords:
            # to must be empty initially
            if b[tr, tc] != 0:
                continue
            # check that tr,tc is reachable from fr,fc by queen move without crossing obstacles
            dr = tr - fr
            dc = tc - fc
            if dr == 0 and dc == 0:
                continue
            step_r = 0 if dr == 0 else (1 if dr > 0 else -1)
            step_c = 0 if dc == 0 else (1 if dc > 0 else -1)
            if step_r != 0 and step_c != 0 and abs(dr) != abs(dc):
                continue  # not on same diagonal
            if step_r == 0 and step_c == 0:
                continue
            # walk the path
            r, c = fr + step_r, fc + step_c
            blocked = False
            while (r, c) != (tr, tc):
                if b[r, c] != 0:
                    blocked = True
                    break
                r += step_r
                c += step_c
            if blocked:
                continue
            # simulate
            b2 = b.copy()
            b2[fr, fc] = 0
            b2[tr, tc] = 1
            for ar, ac in coords:
                if b2[ar, ac] != 0:
                    continue
                # check arrow reachable from tr,tc to ar,ac in queen move
                dr2 = ar - tr
                dc2 = ac - tc
                if dr2 == 0 and dc2 == 0:
                    continue
                step_r2 = 0 if dr2 == 0 else (1 if dr2 > 0 else -1)
                step_c2 = 0 if dc2 == 0 else (1 if dc2 > 0 else -1)
                if step_r2 != 0 and step_c2 != 0 and abs(dr2) != abs(dc2):
                    continue
                r2, c2 = tr + step_r2, tc + step_c2
                blocked2 = False
                while (r2, c2) != (ar, ac):
                    if not (0 <= r2 < H and 0 <= c2 < W) or b2[r2, c2] != 0:
                        blocked2 = True
                        break
                    r2 += step_r2
                    c2 += step_c2
                if blocked2:
                    continue
                # Found fallback legal move
                return f"{int(fr)},{int(fc)}:{int(tr)},{int(tc)}:{int(ar)},{int(ac)}"

    # As a last resort (should not happen in valid non-terminal calls), return a dummy
    # This is unlikely to be legal; environment should not call in terminal positions.
    return "0,0:0,0:0,0"
