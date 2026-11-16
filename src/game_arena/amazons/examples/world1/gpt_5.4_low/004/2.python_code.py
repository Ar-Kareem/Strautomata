
import numpy as np
from collections import deque
import time

DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)]

N = 6


def in_bounds(r, c):
    return 0 <= r < N and 0 <= c < N


def queen_targets(board, r, c):
    """All empty squares reachable by queen move from (r,c)."""
    out = []
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while 0 <= nr < N and 0 <= nc < N and board[nr, nc] == 0:
            out.append((nr, nc))
            nr += dr
            nc += dc
    return out


def count_move_targets(board, player):
    """Count movement destinations (not full move+arrow count)."""
    total = 0
    pos = np.argwhere(board == player)
    for r, c in pos:
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < N and 0 <= nc < N and board[nr, nc] == 0:
                total += 1
                nr += dr
                nc += dc
    return total


def adjacent_empty_count(board, player):
    total = 0
    pos = np.argwhere(board == player)
    for r, c in pos:
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < N and 0 <= nc < N and board[nr, nc] == 0:
                total += 1
    return total


def component_territory(board):
    """
    Approximate territory:
    For each empty-space connected component (8-neighbor),
    assign it if only one side borders it.
    """
    seen = np.zeros((N, N), dtype=bool)
    score = 0

    for r in range(N):
        for c in range(N):
            if board[r, c] != 0 or seen[r, c]:
                continue

            q = deque()
            q.append((r, c))
            seen[r, c] = True
            comp = []
            touch1 = False
            touch2 = False

            while q:
                x, y = q.popleft()
                comp.append((x, y))
                for dr, dc in DIRS:
                    nx, ny = x + dr, y + dc
                    if not in_bounds(nx, ny):
                        continue
                    v = board[nx, ny]
                    if v == 0 and not seen[nx, ny]:
                        seen[nx, ny] = True
                        q.append((nx, ny))
                    elif v == 1:
                        touch1 = True
                    elif v == 2:
                        touch2 = True

            size = len(comp)
            if touch1 and not touch2:
                score += size
            elif touch2 and not touch1:
                score -= size

    return score


def static_eval(board):
    """
    Evaluation from our perspective (player 1).
    """
    my_targets = count_move_targets(board, 1)
    opp_targets = count_move_targets(board, 2)

    my_adj = adjacent_empty_count(board, 1)
    opp_adj = adjacent_empty_count(board, 2)

    terr = component_territory(board)

    # Mobility dominates; territory becomes important in cramped positions.
    return 1.6 * (my_targets - opp_targets) + 0.35 * (my_adj - opp_adj) + 3.0 * terr


def apply_move(board, move, player):
    fr, fc, tr, tc, ar, ac = move
    b = board.copy()
    b[fr, fc] = 0
    b[tr, tc] = player
    b[ar, ac] = -1
    return b


def quick_move_score(board, move, player):
    """
    Fast ordering heuristic.
    """
    fr, fc, tr, tc, ar, ac = move

    # Centrality of landing square
    center_bias = -((tr - 2.5) ** 2 + (tc - 2.5) ** 2)

    # Temporarily move piece to estimate local freedom
    b = board.copy()
    b[fr, fc] = 0
    b[tr, tc] = player

    landing_freedom = 0
    for dr, dc in DIRS:
        nr, nc = tr + dr, tc + dc
        while 0 <= nr < N and 0 <= nc < N and b[nr, nc] == 0:
            landing_freedom += 1
            nr += dr
            nc += dc

    # Arrow near opponent is often useful
    opp = 2 if player == 1 else 1
    arrow_pressure = 0
    for dr, dc in DIRS:
        nr, nc = ar + dr, ac + dc
        if 0 <= nr < N and 0 <= nc < N and b[nr, nc] == opp:
            arrow_pressure += 1

    # Arrow next to our own moved amazon can self-trap, mild penalty
    self_trap = 1 if max(abs(ar - tr), abs(ac - tc)) == 1 else 0

    return 0.8 * landing_freedom + 0.6 * arrow_pressure + 0.12 * center_bias - 0.35 * self_trap


def generate_moves(board, player, limit=None):
    """
    Generate legal full moves: (fr,fc,tr,tc,ar,ac)
    Optionally return only top `limit` by quick ordering.
    """
    moves = []
    pos = np.argwhere(board == player)

    for fr, fc in pos:
        move_targets = queen_targets(board, fr, fc)
        if not move_targets:
            continue

        for tr, tc in move_targets:
            b = board.copy()
            b[fr, fc] = 0
            b[tr, tc] = player

            for ar, ac in queen_targets(b, tr, tc):
                mv = (int(fr), int(fc), int(tr), int(tc), int(ar), int(ac))
                if limit is None:
                    moves.append(mv)
                else:
                    moves.append((quick_move_score(board, mv, player), mv))

    if limit is None:
        return moves

    if not moves:
        return []

    moves.sort(key=lambda x: x[0], reverse=True)
    return [mv for _, mv in moves[:limit]]


def move_to_string(move):
    fr, fc, tr, tc, ar, ac = move
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"


def policy(board) -> str:
    board = np.asarray(board)
    start = time.time()
    time_limit = 0.92

    # Generate all our legal moves. This guarantees we can always return a legal action.
    all_moves = generate_moves(board, 1, limit=None)
    if not all_moves:
        # Robust fallback; environment should not call us here.
        return "0,0:0,0:0,0"

    if len(all_moves) == 1:
        return move_to_string(all_moves[0])

    # Quick ordering for all moves
    scored = [(quick_move_score(board, mv, 1), mv) for mv in all_moves]
    scored.sort(key=lambda x: x[0], reverse=True)
    ordered_moves = [mv for _, mv in scored]

    best_move = ordered_moves[0]
    best_val = -10**18

    # Search parameters adapted to branching factor
    top_main = 14 if len(ordered_moves) > 40 else min(len(ordered_moves), 24)
    reply_cap = 10

    for idx, mv in enumerate(ordered_moves):
        if time.time() - start > time_limit:
            break

        child = apply_move(board, mv, 1)

        # Immediate terminal win if opponent has no moves
        opp_candidates = generate_moves(child, 2, limit=reply_cap if idx < top_main else 0)

        if idx < top_main:
            if not opp_candidates:
                val = 10**9
            else:
                worst = 10**18
                # Opponent best reply among promising replies
                for omv in opp_candidates:
                    if time.time() - start > time_limit:
                        break
                    grand = apply_move(child, omv, 2)
                    ev = static_eval(grand)
                    if ev < worst:
                        worst = ev

                # Also include immediate-position heuristic so limited reply search is safer
                val = 0.45 * static_eval(child) + 0.55 * worst
        else:
            val = static_eval(child)

        # Small bonus for earlier / better-ordered moves
        val += 0.03 * scored[idx][0]

        if val > best_val:
            best_val = val
            best_move = mv

    return move_to_string(best_move)
