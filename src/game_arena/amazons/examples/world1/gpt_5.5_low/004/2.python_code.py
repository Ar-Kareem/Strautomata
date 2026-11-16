
import time
import math
import numpy as np

DIRS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)

N = 6


def _inside(r, c):
    return 0 <= r < N and 0 <= c < N


def _reachable_squares(b, r, c):
    out = []
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while 0 <= nr < N and 0 <= nc < N and b[nr, nc] == 0:
            out.append((nr, nc))
            nr += dr
            nc += dc
    return out


def _reachable_count(b, r, c):
    cnt = 0
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while 0 <= nr < N and 0 <= nc < N and b[nr, nc] == 0:
            cnt += 1
            nr += dr
            nc += dc
    return cnt


def _generate_moves(b, player=1):
    """Yield legal moves as (fr,fc,tr,tc,ar,ac)."""
    pieces = np.argwhere(b == player)
    for fr, fc in pieces:
        fr = int(fr)
        fc = int(fc)
        for tr, tc in _reachable_squares(b, fr, fc):
            # Temporarily move amazon so the arrow may pass through the vacated square.
            b[fr, fc] = 0
            b[tr, tc] = player
            arrows = _reachable_squares(b, tr, tc)
            for ar, ac in arrows:
                yield (fr, fc, tr, tc, ar, ac)
            b[tr, tc] = 0
            b[fr, fc] = player


def _count_actions(b, player=1, cap=1000000):
    total = 0
    pieces = np.argwhere(b == player)
    for fr, fc in pieces:
        fr = int(fr)
        fc = int(fc)
        for tr, tc in _reachable_squares(b, fr, fc):
            b[fr, fc] = 0
            b[tr, tc] = player
            total += _reachable_count(b, tr, tc)
            b[tr, tc] = 0
            b[fr, fc] = player
            if total >= cap:
                return total
    return total


def _count_destinations(b, player=1):
    total = 0
    for r, c in np.argwhere(b == player):
        total += _reachable_count(b, int(r), int(c))
    return total


def _apply_move(b, mv, player):
    fr, fc, tr, tc, ar, ac = mv
    nb = b.copy()
    nb[fr, fc] = 0
    nb[tr, tc] = player
    nb[ar, ac] = -1
    return nb


def _queen_distance_map(b, player):
    """Small-board BFS where queen rays are graph edges."""
    dist = [[99] * N for _ in range(N)]
    q = []
    for r, c in np.argwhere(b == player):
        r = int(r)
        c = int(c)
        dist[r][c] = 0
        q.append((r, c))

    head = 0
    while head < len(q):
        r, c = q[head]
        head += 1
        nd = dist[r][c] + 1
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < N and 0 <= nc < N:
                # Own/opponent amazons and arrows are blockers, except source amazons
                # are already in the queue and do not need to be crossed.
                if b[nr, nc] != 0:
                    break
                if nd < dist[nr][nc]:
                    dist[nr][nc] = nd
                    q.append((nr, nc))
                nr += dr
                nc += dc
    return dist


def _territory_score(b):
    myd = _queen_distance_map(b, 1)
    opd = _queen_distance_map(b, 2)

    score = 0.0
    for r in range(N):
        for c in range(N):
            if b[r, c] != 0:
                continue
            a = myd[r][c]
            o = opd[r][c]
            if a < o:
                score += 4.0 if o < 99 else 5.0
                score += max(0.0, 0.25 * (o - a))
            elif o < a:
                score -= 4.0 if a < 99 else 5.0
                score -= max(0.0, 0.25 * (a - o))
    return score


def _static_eval(b):
    # Immediate terminal / near-terminal checks.
    my_actions = _count_actions(b, 1, cap=3000)
    op_actions = _count_actions(b, 2, cap=3000)

    if op_actions == 0:
        return 100000.0 + my_actions
    if my_actions == 0:
        return -100000.0 - op_actions

    my_dest = _count_destinations(b, 1)
    op_dest = _count_destinations(b, 2)

    terr = _territory_score(b)

    # Action mobility is important in Amazons; destination mobility is a cheaper
    # positional proxy. Territory dominates as the board fills.
    return (
        terr
        + 0.10 * (my_actions - op_actions)
        + 0.75 * (my_dest - op_dest)
    )


def _move_to_string(mv):
    fr, fc, tr, tc, ar, ac = mv
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"


def policy(board) -> str:
    start = time.time()
    limit = 0.92

    b = np.array(board, copy=True)

    # Generate all legal moves. If somehow no move exists, return a syntactically
    # valid dummy; the environment says policy should not be called then.
    moves = list(_generate_moves(b, 1))
    if not moves:
        return "0,0:0,0:0,0"

    best_move = moves[0]
    best_score = -1e100

    # First pass: static evaluation of all moves.
    scored = []
    for mv in moves:
        nb = _apply_move(b, mv, 1)

        # Prefer arrows that reduce opponent mobility and preserve ours.
        s = _static_eval(nb)

        # Tiny tie-breaker: arrows near opponent pieces are often restrictive.
        ar, ac = mv[4], mv[5]
        near_opp = 0
        for orow, ocol in np.argwhere(nb == 2):
            d = max(abs(ar - int(orow)), abs(ac - int(ocol)))
            if d <= 2:
                near_opp += (3 - d)
        s += 0.15 * near_opp

        scored.append((s, mv, nb))
        if s > best_score:
            best_score = s
            best_move = mv

        if time.time() - start > limit * 0.55:
            break

    scored.sort(key=lambda x: x[0], reverse=True)

    # If there is little time, trust static choice.
    if time.time() - start > limit * 0.65:
        return _move_to_string(best_move)

    # Second pass: shallow adversarial search on the strongest candidates.
    # On 6x6 this is usually enough to spot immediate traps and avoid blunders.
    top_k = min(28, len(scored))
    for static_s, mv, nb in scored[:top_k]:
        if time.time() - start > limit:
            break

        opp_moves = []
        for omv in _generate_moves(nb, 2):
            ob = _apply_move(nb, omv, 2)
            # Evaluation remains from our perspective.
            os = _static_eval(ob)
            opp_moves.append((os, omv, ob))
            if len(opp_moves) >= 70 or time.time() - start > limit:
                break

        if not opp_moves:
            score = 1000000.0 + static_s
        else:
            # Opponent chooses the move minimizing our evaluation.
            # Examine the most dangerous replies first.
            opp_moves.sort(key=lambda x: x[0])
            worst = 1e100
            reply_cap = min(24, len(opp_moves))
            for os, omv, ob in opp_moves[:reply_cap]:
                if os < worst:
                    worst = os
                if time.time() - start > limit:
                    break

            # Blend minimax safety with static promise so good positional moves
            # are not over-penalized by a noisy one-ply heuristic.
            score = 0.82 * worst + 0.18 * static_s

        if score > best_score:
            best_score = score
            best_move = mv

    return _move_to_string(best_move)
