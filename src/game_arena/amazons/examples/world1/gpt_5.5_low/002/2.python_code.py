
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


def _move_to_str(m):
    fr, fc, tr, tc, ar, ac = m
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"


def _apply_move(board, move, player):
    fr, fc, tr, tc, ar, ac = move
    nb = board.copy()
    nb[fr, fc] = 0
    nb[tr, tc] = player
    nb[ar, ac] = -1
    return nb


def _generate_moves(board, player, limit=None):
    """
    Generate legal moves for player.
    If limit is given, stops after that many moves. Used for fast terminal/mobility checks.
    """
    moves = []
    pieces = np.argwhere(board == player)

    for fr, fc in pieces:
        fr = int(fr)
        fc = int(fc)

        for dr, dc in DIRS:
            tr, tc = fr + dr, fc + dc

            while _inside(tr, tc) and board[tr, tc] == 0:
                # Temporarily move amazon: from is vacated, to is occupied.
                for adr, adc in DIRS:
                    ar, ac = tr + adr, tc + adc

                    while _inside(ar, ac):
                        if ar == fr and ac == fc:
                            # The arrow may land/pass through the vacated from-square.
                            moves.append((fr, fc, tr, tc, ar, ac))
                        elif board[ar, ac] == 0:
                            moves.append((fr, fc, tr, tc, ar, ac))
                        else:
                            break

                        if limit is not None and len(moves) >= limit:
                            return moves

                        ar += adr
                        ac += adc

                tr += dr
                tc += dc

    return moves


def _has_move(board, player):
    return len(_generate_moves(board, player, limit=1)) > 0


def _queen_reach_count(board, player):
    total = 0
    for r, c in np.argwhere(board == player):
        r = int(r)
        c = int(c)
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while _inside(nr, nc) and board[nr, nc] == 0:
                total += 1
                nr += dr
                nc += dc
    return total


def _action_count_limited(board, player, cap=500):
    return len(_generate_moves(board, player, limit=cap))


def _distance_map(board, player):
    """
    Queen-move distance map from all amazons of player to empty cells.
    Other occupied cells block rays.
    """
    dist = [[99] * N for _ in range(N)]
    queue = []

    for r, c in np.argwhere(board == player):
        r = int(r)
        c = int(c)
        dist[r][c] = 0
        queue.append((r, c))

    head = 0
    while head < len(queue):
        r, c = queue[head]
        head += 1
        nd = dist[r][c] + 1

        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while _inside(nr, nc):
                if board[nr, nc] != 0:
                    break
                if nd < dist[nr][nc]:
                    dist[nr][nc] = nd
                    queue.append((nr, nc))
                nr += dr
                nc += dc

    return dist


def _territory_score(board):
    d1 = _distance_map(board, 1)
    d2 = _distance_map(board, 2)

    score = 0.0
    for r in range(N):
        for c in range(N):
            if board[r, c] == 0:
                a = d1[r][c]
                b = d2[r][c]

                if a < b:
                    score += 3.0
                    score += min(2.0, (b - a) * 0.25)
                elif b < a:
                    score -= 3.0
                    score -= min(2.0, (a - b) * 0.25)
                elif a < 99:
                    score += 0.15
    return score


def _evaluate(board):
    """
    Positive is good for us, negative is good for opponent.
    """
    our_has = _has_move(board, 1)
    opp_has = _has_move(board, 2)

    if not opp_has and our_has:
        return 100000.0
    if not our_has and opp_has:
        return -100000.0
    if not our_has and not opp_has:
        return 0.0

    our_reach = _queen_reach_count(board, 1)
    opp_reach = _queen_reach_count(board, 2)

    our_actions = _action_count_limited(board, 1, 700)
    opp_actions = _action_count_limited(board, 2, 700)

    territory = _territory_score(board)

    return (
        1.25 * (our_reach - opp_reach)
        + 0.07 * (our_actions - opp_actions)
        + 2.2 * territory
    )


def _quick_move_score(board, move, player):
    """
    Cheap ordering heuristic.
    For our moves, larger is better.
    For opponent moves, from our perspective larger is still better for us,
    so opponent ordering uses the negative of this value.
    """
    nb = _apply_move(board, move, player)

    if player == 1:
        if not _has_move(nb, 2):
            return 1000000.0
        return _evaluate(nb)
    else:
        if not _has_move(nb, 1):
            return -1000000.0
        return _evaluate(nb)


def policy(board) -> str:
    start = time.time()
    deadline = start + 0.92

    try:
        b = np.asarray(board).astype(int, copy=False)
    except Exception:
        b = board

    legal = _generate_moves(b, 1)
    if not legal:
        # Should not be called in this state. No legal string can truly exist.
        return "0,0:0,0:0,0"

    # Baseline: always keep a legal fallback.
    best_move = legal[0]
    best_score = -float("inf")

    # Order our candidate moves.
    scored = []
    for m in legal:
        if time.time() > deadline:
            break
        s = _quick_move_score(b, m, 1)
        scored.append((s, m))
        if s > best_score:
            best_score = s
            best_move = m

    if not scored:
        return _move_to_str(best_move)

    scored.sort(reverse=True, key=lambda x: x[0])

    # On 6x6, full move generation can be large. Search strongest candidates first.
    our_candidates = [m for _, m in scored[:70]]

    for m in our_candidates:
        if time.time() > deadline:
            break

        nb = _apply_move(b, m, 1)

        # Immediate win.
        opp_moves = _generate_moves(nb, 2)
        if not opp_moves:
            return _move_to_str(m)

        # Order opponent replies. Opponent wants to minimize our evaluation.
        opp_scored = []
        for om in opp_moves:
            if time.time() > deadline:
                break
            os = _quick_move_score(nb, om, 2)
            opp_scored.append((os, om))

        if not opp_scored:
            return _move_to_str(m)

        opp_scored.sort(key=lambda x: x[0])
        opp_candidates = [om for _, om in opp_scored[:45]]

        worst = float("inf")

        for om in opp_candidates:
            if time.time() > deadline:
                break

            nb2 = _apply_move(nb, om, 2)

            # If opponent move leaves us no move, terrible.
            if not _has_move(nb2, 1):
                val = -100000.0
            else:
                # Shallow one-ply lookahead bonus: estimate our next best tactical option.
                val = _evaluate(nb2)

                if time.time() < deadline:
                    replies = _generate_moves(nb2, 1, limit=90)
                    if replies:
                        local_best = -float("inf")
                        for rm in replies[:90]:
                            if time.time() > deadline:
                                break
                            rb = _apply_move(nb2, rm, 1)
                            rs = _evaluate(rb)
                            if rs > local_best:
                                local_best = rs
                        if local_best > -float("inf"):
                            val = 0.65 * val + 0.35 * local_best

            if val < worst:
                worst = val

            # Alpha-style pruning against current best.
            if worst <= best_score:
                break

        if worst > best_score:
            best_score = worst
            best_move = m

    return _move_to_str(best_move)
