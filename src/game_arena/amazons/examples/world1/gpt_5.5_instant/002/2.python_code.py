
import numpy as np
import random
import time

DIRS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)

N = 6


def _inside(r, c):
    return 0 <= r < N and 0 <= c < N


def _ray_squares(b, r, c):
    """All empty squares reachable by queen move from (r,c) on board b."""
    res = []
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while 0 <= nr < N and 0 <= nc < N and b[nr, nc] == 0:
            res.append((nr, nc))
            nr += dr
            nc += dc
    return res


def _mobility_from(b, r, c):
    cnt = 0
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while 0 <= nr < N and 0 <= nc < N and b[nr, nc] == 0:
            cnt += 1
            nr += dr
            nc += dc
    return cnt


def _all_moves(board):
    """Return legal moves as tuples: (fr,fc,tr,tc,ar,ac)."""
    moves = []
    amazons = np.argwhere(board == 1)
    for fr, fc in amazons:
        fr = int(fr)
        fc = int(fc)

        for tr, tc in _ray_squares(board, fr, fc):
            # Temporarily move amazon for arrow generation.
            board[fr, fc] = 0
            board[tr, tc] = 1

            for ar, ac in _ray_squares(board, tr, tc):
                moves.append((fr, fc, tr, tc, ar, ac))

            board[tr, tc] = 0
            board[fr, fc] = 1

    return moves


def _apply_move(board, mv):
    fr, fc, tr, tc, ar, ac = mv
    b = board.copy()
    b[fr, fc] = 0
    b[tr, tc] = 1
    b[ar, ac] = -1
    return b


def _count_moves_for_player(board, player, cap=None):
    """Counts full legal moves for player. Optional cap for speed."""
    cnt = 0
    amazons = np.argwhere(board == player)
    for fr, fc in amazons:
        fr = int(fr)
        fc = int(fc)

        # Generate destinations while treating this amazon as moving.
        for tr, tc in _ray_squares(board, fr, fc):
            board[fr, fc] = 0
            board[tr, tc] = player

            arrows = _mobility_from(board, tr, tc)
            cnt += arrows

            board[tr, tc] = 0
            board[fr, fc] = player

            if cap is not None and cnt >= cap:
                return cnt
    return cnt


def _simple_mobility(board, player):
    total = 0
    for r, c in np.argwhere(board == player):
        total += _mobility_from(board, int(r), int(c))
    return total


def _queen_distance_map(board, player):
    """
    Minimum queen-move distance from any amazon of player to each empty cell.
    Uses BFS over queen rays.
    """
    inf = 99
    dist = np.full((N, N), inf, dtype=np.int16)
    q = []
    head = 0

    for r, c in np.argwhere(board == player):
        r = int(r)
        c = int(c)
        dist[r, c] = 0
        q.append((r, c))

    while head < len(q):
        r, c = q[head]
        head += 1
        nd = int(dist[r, c]) + 1

        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < N and 0 <= nc < N:
                # Own starting amazons are allowed only as BFS sources, not pass-through.
                if board[nr, nc] != 0:
                    break
                if nd < dist[nr, nc]:
                    dist[nr, nc] = nd
                    q.append((nr, nc))
                nr += dr
                nc += dc

    return dist


def _territory_score(board):
    d1 = _queen_distance_map(board, 1)
    d2 = _queen_distance_map(board, 2)

    score = 0.0
    for r in range(N):
        for c in range(N):
            if board[r, c] == 0:
                a = d1[r, c]
                o = d2[r, c]
                if a < o:
                    score += 1.0
                    score += 0.12 * max(0, o - a)
                elif o < a:
                    score -= 1.0
                    score -= 0.12 * max(0, a - o)
                elif a < 99:
                    score += 0.05
    return score


def _center_bonus(move):
    _, _, tr, tc, ar, ac = move
    # Prefer amazon landing near center, arrow not too self-trapping.
    center = 2.5
    land = -((tr - center) ** 2 + (tc - center) ** 2)
    arrow = ((ar - center) ** 2 + (ac - center) ** 2) * 0.05
    return 0.15 * land + arrow


def _score_move(board, mv):
    b = _apply_move(board, mv)

    # Immediate win: opponent has no move.
    opp_moves = _count_moves_for_player(b, 2, cap=1)
    if opp_moves == 0:
        return 1e9

    my_simple = _simple_mobility(b, 1)
    opp_simple = _simple_mobility(b, 2)

    # Full move counts are more expensive but powerful on 6x6.
    my_full = _count_moves_for_player(b, 1, cap=300)
    opp_full = _count_moves_for_player(b, 2, cap=300)

    terr = _territory_score(b)

    # Arrow tactical effect: occupying arrow square should reduce opponent access.
    fr, fc, tr, tc, ar, ac = mv
    arrow_near_opp = 0
    for orow, ocol in np.argwhere(b == 2):
        d = max(abs(int(orow) - ar), abs(int(ocol) - ac))
        if d <= 2:
            arrow_near_opp += (3 - d)

    return (
        4.5 * terr
        + 2.2 * (my_simple - opp_simple)
        + 0.45 * (my_full - opp_full)
        + 1.0 * arrow_near_opp
        + _center_bonus(mv)
    )


def _move_to_string(mv):
    fr, fc, tr, tc, ar, ac = mv
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"


def policy(board) -> str:
    """
    Main arena API. Returns a legal Amazons move string.
    """
    start = time.time()

    try:
        b = np.array(board, copy=True)
        moves = _all_moves(b)

        # Robust terminal fallback. Environment should not call in this case.
        if not moves:
            amazons = np.argwhere(b == 1)
            if len(amazons) > 0:
                r, c = map(int, amazons[0])
                return f"{r},{c}:{r},{c}:{r},{c}"
            return "0,0:0,0:0,0"

        best = moves[0]
        best_score = -1e100

        # Move ordering: examine tactically promising moves first.
        # On 6x6 this is usually still all moves within time.
        random_seedless_noise = 0.000001

        for i, mv in enumerate(moves):
            if time.time() - start > 0.92:
                break

            s = _score_move(b, mv)

            # Tiny deterministic tie breaker to avoid predictable bad equalities.
            s += random_seedless_noise * ((mv[2] * 37 + mv[3] * 17 + mv[4] * 7 + mv[5]) % 13)

            if s > best_score:
                best_score = s
                best = mv

        return _move_to_string(best)

    except Exception:
        # Absolute safety: recompute the first legal move simply.
        try:
            b = np.array(board, copy=True)
            moves = _all_moves(b)
            if moves:
                return _move_to_string(moves[0])
        except Exception:
            pass

        return "0,0:0,0:0,0"
