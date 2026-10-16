
import time
import numpy as np

DIRS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)

N = 6


def policy(board) -> str:
    """
    Return a legal move string for 6x6 Amazons.

    board values:
      0  empty
      1  our amazon
      2  opponent amazon
     -1  arrow / blocked
    """
    start_time = time.time()
    TIME_LIMIT = 0.90

    b = np.array(board, copy=True)

    def in_bounds(r, c):
        return 0 <= r < N and 0 <= c < N

    def generate_moves(side):
        moves = []
        amazons = np.argwhere(b == side)

        for fr, fc in amazons:
            fr = int(fr)
            fc = int(fc)

            for dr, dc in DIRS:
                tr, tc = fr + dr, fc + dc
                while in_bounds(tr, tc) and b[tr, tc] == 0:
                    # Temporarily move amazon so arrow may pass through from-square.
                    b[fr, fc] = 0
                    b[tr, tc] = side

                    for adr, adc in DIRS:
                        ar, ac = tr + adr, tc + adc
                        while in_bounds(ar, ac) and b[ar, ac] == 0:
                            moves.append((fr, fc, tr, tc, ar, ac))
                            ar += adr
                            ac += adc

                    b[tr, tc] = 0
                    b[fr, fc] = side

                    tr += dr
                    tc += dc

        return moves

    def apply_move(m, side):
        fr, fc, tr, tc, ar, ac = m
        b[fr, fc] = 0
        b[tr, tc] = side
        b[ar, ac] = -1

    def undo_move(m, side):
        fr, fc, tr, tc, ar, ac = m
        b[ar, ac] = 0
        b[tr, tc] = 0
        b[fr, fc] = side

    def queen_reach_count(side):
        total = 0
        for r, c in np.argwhere(b == side):
            r = int(r)
            c = int(c)
            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                while in_bounds(nr, nc) and b[nr, nc] == 0:
                    total += 1
                    nr += dr
                    nc += dc
        return total

    def queen_distances(side):
        """
        Small-board territory estimate.
        Distance is minimum number of queen-like moves from any amazon of side
        to each empty square, moving only through empty squares.
        """
        dist = [[99] * N for _ in range(N)]
        frontier = []

        for r, c in np.argwhere(b == side):
            r = int(r)
            c = int(c)
            dist[r][c] = 0
            frontier.append((r, c))

        head = 0
        while head < len(frontier):
            r, c = frontier[head]
            head += 1
            nd = dist[r][c] + 1

            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                while in_bounds(nr, nc) and b[nr, nc] == 0:
                    if nd < dist[nr][nc]:
                        dist[nr][nc] = nd
                        frontier.append((nr, nc))
                    nr += dr
                    nc += dc

        return dist

    def has_any_move(side):
        for fr, fc in np.argwhere(b == side):
            fr = int(fr)
            fc = int(fc)
            for dr, dc in DIRS:
                tr, tc = fr + dr, fc + dc
                if in_bounds(tr, tc) and b[tr, tc] == 0:
                    return True
        return False

    def evaluate():
        # Terminal checks.
        our_can = has_any_move(1)
        opp_can = has_any_move(2)

        if not opp_can:
            return 1_000_000
        if not our_can:
            return -1_000_000

        our_mob = queen_reach_count(1)
        opp_mob = queen_reach_count(2)

        d1 = queen_distances(1)
        d2 = queen_distances(2)

        territory = 0
        reach_bonus = 0

        for r in range(N):
            for c in range(N):
                if b[r, c] == 0:
                    a = d1[r][c]
                    o = d2[r][c]

                    if a < o:
                        territory += 1
                    elif o < a:
                        territory -= 1

                    if a < 99:
                        reach_bonus += 1
                    if o < 99:
                        reach_bonus -= 1

        # Mobility is very important in Amazons, especially on a 6x6 board.
        return (
            10 * (our_mob - opp_mob)
            + 18 * territory
            + 4 * reach_bonus
        )

    def move_to_str(m):
        fr, fc, tr, tc, ar, ac = m
        return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"

    root_moves = generate_moves(1)

    # Robust fallback. The environment should not call us with no legal moves,
    # but return syntactically valid text anyway.
    if not root_moves:
        return "0,0:0,0:0,0"

    # First static ordering.
    scored_roots = []
    best_move = root_moves[0]
    best_static = -10**18

    for m in root_moves:
        apply_move(m, 1)
        val = evaluate()
        undo_move(m, 1)

        scored_roots.append((val, m))
        if val > best_static:
            best_static = val
            best_move = m

        if time.time() - start_time > TIME_LIMIT * 0.35:
            break

    scored_roots.sort(reverse=True, key=lambda x: x[0])

    # Keep enough candidate moves for quality, but avoid timeout.
    candidate_moves = [m for _, m in scored_roots[:90]]
    if best_move not in candidate_moves:
        candidate_moves.append(best_move)

    best_value = -10**18

    for m in candidate_moves:
        if time.time() - start_time > TIME_LIMIT:
            break

        apply_move(m, 1)

        # If opponent has no move, this is immediately winning.
        if not has_any_move(2):
            undo_move(m, 1)
            return move_to_str(m)

        opp_moves = generate_moves(2)

        # If somehow no opponent moves were generated, also winning.
        if not opp_moves:
            value = 1_000_000
        else:
            # Order opponent replies by how bad they are for us.
            opp_scored = []
            for om in opp_moves:
                apply_move(om, 2)
                v = evaluate()
                undo_move(om, 2)
                opp_scored.append((v, om))

                if time.time() - start_time > TIME_LIMIT:
                    break

            opp_scored.sort(key=lambda x: x[0])

            # Search the most dangerous opponent replies.
            value = 10**18
            for _, om in opp_scored[:70]:
                if time.time() - start_time > TIME_LIMIT:
                    break

                apply_move(om, 2)

                if not has_any_move(1):
                    child_val = -1_000_000
                else:
                    child_val = evaluate()

                undo_move(om, 2)

                if child_val < value:
                    value = child_val

                # Alpha-style pruning at root.
                if value <= best_value:
                    break

        undo_move(m, 1)

        if value > best_value:
            best_value = value
            best_move = m

    return move_to_str(best_move)
