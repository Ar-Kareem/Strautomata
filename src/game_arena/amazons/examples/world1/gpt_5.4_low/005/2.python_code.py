
import numpy as np
import time

DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)]

INF = 10**9


def in_bounds(r, c):
    return 0 <= r < 6 and 0 <= c < 6


def reachable_squares(board, r, c):
    out = []
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while in_bounds(nr, nc) and board[nr, nc] == 0:
            out.append((nr, nc))
            nr += dr
            nc += dc
    return out


def mobility_count(board, player):
    total = 0
    positions = np.argwhere(board == player)
    for r, c in positions:
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while in_bounds(nr, nc) and board[nr, nc] == 0:
                total += 1
                nr += dr
                nc += dc
    return total


def local_liberties(board, player):
    total = 0
    positions = np.argwhere(board == player)
    for r, c in positions:
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc) and board[nr, nc] == 0:
                total += 1
    return total


def center_score(board, player):
    # Prefer squares nearer the center of the 6x6 board.
    total = 0.0
    positions = np.argwhere(board == player)
    for r, c in positions:
        total -= abs(r - 2.5) + abs(c - 2.5)
    return total


def evaluate(board):
    my_mob = mobility_count(board, 1)
    opp_mob = mobility_count(board, 2)

    if opp_mob == 0 and my_mob > 0:
        return INF // 2
    if my_mob == 0 and opp_mob > 0:
        return -INF // 2

    my_lib = local_liberties(board, 1)
    opp_lib = local_liberties(board, 2)

    my_ctr = center_score(board, 1)
    opp_ctr = center_score(board, 2)

    return (
        10 * (my_mob - opp_mob)
        + 2 * (my_lib - opp_lib)
        + 0.5 * (my_ctr - opp_ctr)
    )


def apply_move(board, move, player):
    fr, fc, tr, tc, ar, ac = move
    nb = board.copy()
    nb[fr, fc] = 0
    nb[tr, tc] = player
    nb[ar, ac] = -1
    return nb


def gen_moves(board, player):
    positions = np.argwhere(board == player)
    for fr, fc in positions:
        dests = reachable_squares(board, fr, fc)
        if not dests:
            continue

        # Make a temporary board with the amazon moved once per destination.
        for tr, tc in dests:
            tmp = board.copy()
            tmp[fr, fc] = 0
            tmp[tr, tc] = player

            for ar, ac in reachable_squares(tmp, tr, tc):
                yield (int(fr), int(fc), int(tr), int(tc), int(ar), int(ac))


def has_any_move(board, player):
    positions = np.argwhere(board == player)
    for r, c in positions:
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc) and board[nr, nc] == 0:
                return True
    return False


def move_to_str(move):
    fr, fc, tr, tc, ar, ac = move
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"


def quick_rank_moves(board, player, deadline, limit=None):
    scored = []
    fallback = None

    for mv in gen_moves(board, player):
        if fallback is None:
            fallback = mv
        if time.perf_counter() > deadline:
            break

        nb = apply_move(board, mv, player)

        if player == 1:
            score = evaluate(nb)
        else:
            # Opponent move: still evaluate from our perspective.
            score = evaluate(nb)

        # Strong terminal preference.
        if not has_any_move(nb, 3 - player):
            score = INF // 3 if player == 1 else -INF // 3

        scored.append((score, mv, nb))

    if not scored:
        return [], fallback

    reverse = (player == 1)
    scored.sort(key=lambda x: x[0], reverse=reverse)

    if limit is not None and len(scored) > limit:
        scored = scored[:limit]

    return scored, fallback


def policy(board) -> str:
    board = np.asarray(board)
    start = time.perf_counter()
    deadline = start + 0.92

    # Generate and rank our moves quickly.
    my_scored, fallback = quick_rank_moves(board, 1, deadline, limit=None)

    if fallback is None:
        # Should not happen in normal play, but remain robust.
        # Try to fabricate nothing impossible; return a harmless string format.
        return "0,0:0,0:0,0"

    if not my_scored:
        return move_to_str(fallback)

    # Immediate winning move?
    for score, mv, nb in my_scored:
        if time.perf_counter() > deadline:
            return move_to_str(mv)
        if not has_any_move(nb, 2):
            return move_to_str(mv)

    # Candidate pruning for deeper look.
    top_my = my_scored[:12]

    best_move = top_my[0][1]
    best_value = -INF

    for my_score, mv, nb in top_my:
        if time.perf_counter() > deadline:
            break

        # Opponent replies, minimizing our evaluation.
        opp_scored, _ = quick_rank_moves(nb, 2, deadline, limit=12)

        if not opp_scored:
            return move_to_str(mv)

        worst_value = INF

        for _, opp_mv, nb2 in opp_scored:
            if time.perf_counter() > deadline:
                break

            val = evaluate(nb2)

            # Small bonus for positions where we still have moves and opponent has less.
            if not has_any_move(nb2, 1):
                val = -INF // 4
            elif not has_any_move(nb2, 2):
                val = INF // 4

            if val < worst_value:
                worst_value = val

        # If time cut inside opp loop, at least use what we got.
        if worst_value == INF:
            worst_value = my_score

        if worst_value > best_value:
            best_value = worst_value
            best_move = mv

    return move_to_str(best_move)
