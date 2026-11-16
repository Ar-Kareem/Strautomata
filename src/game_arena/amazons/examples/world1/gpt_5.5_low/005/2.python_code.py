
import time
from collections import deque
import numpy as np

DIRS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)

N = 6


def _inside(r, c):
    return 0 <= r < N and 0 <= c < N


def _pieces(board, player):
    return list(zip(*np.where(board == player)))


def _destinations(board, r, c):
    out = []
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while _inside(nr, nc) and board[nr, nc] == 0:
            out.append((nr, nc))
            nr += dr
            nc += dc
    return out


def _arrow_squares(board, fr, fc, tr, tc):
    """
    Arrow is fired after amazon has moved from (fr,fc) to (tr,tc).
    Original from-square is considered empty.
    Landing square is considered occupied.
    """
    out = []
    for dr, dc in DIRS:
        nr, nc = tr + dr, tc + dc
        while _inside(nr, nc):
            if nr == fr and nc == fc:
                out.append((nr, nc))
            elif board[nr, nc] == 0:
                out.append((nr, nc))
            else:
                break
            nr += dr
            nc += dc
    return out


def _generate_moves(board, player):
    moves = []
    for fr, fc in _pieces(board, player):
        for tr, tc in _destinations(board, fr, fc):
            for ar, ac in _arrow_squares(board, fr, fc, tr, tc):
                moves.append((fr, fc, tr, tc, ar, ac))
    return moves


def _has_any_move(board, player):
    for r, c in _pieces(board, player):
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if _inside(nr, nc) and board[nr, nc] == 0:
                return True
    return False


def _apply_move(board, move, player):
    fr, fc, tr, tc, ar, ac = move
    b = board.copy()
    b[fr, fc] = 0
    b[tr, tc] = player
    b[ar, ac] = -1
    return b


def _mobility(board, player):
    total = 0
    for r, c in _pieces(board, player):
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while _inside(nr, nc) and board[nr, nc] == 0:
                total += 1
                nr += dr
                nc += dc
    return total


def _queen_distances(board, player):
    """
    Multi-source queen-move distance from all amazons of `player`.
    Blocked cells and occupied cells are not traversable.
    Sources have distance 0.
    """
    dist = [[99] * N for _ in range(N)]
    q = deque()

    for r, c in _pieces(board, player):
        dist[r][c] = 0
        q.append((r, c))

    while q:
        r, c = q.popleft()
        nd = dist[r][c] + 1

        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while _inside(nr, nc):
                if board[nr, nc] != 0:
                    break
                if dist[nr][nc] < nd:
                    break
                if dist[nr][nc] == 99:
                    dist[nr][nc] = nd
                    q.append((nr, nc))
                nr += dr
                nc += dc

    return dist


def _territory_score(board):
    d1 = _queen_distances(board, 1)
    d2 = _queen_distances(board, 2)

    score = 0
    for r in range(N):
        for c in range(N):
            if board[r, c] == 0:
                if d1[r][c] < d2[r][c]:
                    score += 1
                elif d2[r][c] < d1[r][c]:
                    score -= 1
                elif d1[r][c] != 99:
                    score += 0
    return score


def _chamber_score(board):
    """
    Small bonus for isolating regions where we have more amazons than opponent.
    Useful in late game when the board splits into chambers.
    """
    seen = [[False] * N for _ in range(N)]
    score = 0

    for sr in range(N):
        for sc in range(N):
            if seen[sr][sc] or board[sr, sc] == -1:
                continue

            q = deque([(sr, sc)])
            seen[sr][sc] = True
            empties = 0
            mine = 0
            opp = 0

            while q:
                r, c = q.popleft()
                if board[r, c] == 0:
                    empties += 1
                elif board[r, c] == 1:
                    mine += 1
                elif board[r, c] == 2:
                    opp += 1

                for dr, dc in DIRS:
                    nr, nc = r + dr, c + dc
                    if _inside(nr, nc) and not seen[nr][nc] and board[nr, nc] != -1:
                        seen[nr][nc] = True
                        q.append((nr, nc))

            if mine and not opp:
                score += empties * 2
            elif opp and not mine:
                score -= empties * 2
            else:
                score += (mine - opp) * 2

    return score


def _evaluate(board):
    if not _has_any_move(board, 2):
        return 100000
    if not _has_any_move(board, 1):
        return -100000

    my_mob = _mobility(board, 1)
    op_mob = _mobility(board, 2)
    terr = _territory_score(board)
    chamber = _chamber_score(board)

    return 9.0 * terr + 3.0 * (my_mob - op_mob) + 1.5 * chamber


def _move_to_str(m):
    fr, fc, tr, tc, ar, ac = m
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"


def policy(board) -> str:
    start = time.time()
    limit = 0.92

    board = np.asarray(board)
    moves = _generate_moves(board, 1)

    if not moves:
        # The environment should not call us here. This is only a robustness fallback.
        return "0,0:0,0:0,0"

    fallback = moves[0]

    # First pass: static ordering of our legal moves.
    scored = []
    for m in moves:
        b = _apply_move(board, m, 1)
        s = _evaluate(b)
        scored.append((s, m))

    scored.sort(reverse=True, key=lambda x: x[0])

    # If there are many moves, search only the most promising ones.
    candidate_limit = 90
    candidates = scored[:candidate_limit]

    best_score = -10**18
    best_move = scored[0][1]

    for base_score, m in candidates:
        if time.time() - start > limit:
            break

        b1 = _apply_move(board, m, 1)

        # Immediate win: opponent has no move.
        if not _has_any_move(b1, 2):
            return _move_to_str(m)

        opp_moves = _generate_moves(b1, 2)

        if not opp_moves:
            reply_score = 100000
        else:
            # Order opponent replies by how bad they are for us.
            opp_scored = []
            for om in opp_moves:
                if time.time() - start > limit:
                    break
                b2 = _apply_move(b1, om, 2)
                opp_scored.append((_evaluate(b2), om))

            if not opp_scored:
                reply_score = base_score
            else:
                opp_scored.sort(key=lambda x: x[0])

                # Consider a limited number of strongest opponent replies.
                worst = 10**18
                for _, om in opp_scored[:45]:
                    if time.time() - start > limit:
                        break
                    b2 = _apply_move(b1, om, 2)
                    val = _evaluate(b2)
                    if val < worst:
                        worst = val
                        if worst < best_score - 200:
                            break
                reply_score = worst

        if reply_score > best_score:
            best_score = reply_score
            best_move = m

    return _move_to_str(best_move if best_move else fallback)
