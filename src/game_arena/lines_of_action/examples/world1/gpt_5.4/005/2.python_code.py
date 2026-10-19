
import math
import time
from collections import deque

DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)]

ORTHO_DIAG_DIRS = [
    (-1, 0), (1, 0), (0, -1), (0, 1),
    (-1, -1), (-1, 1), (1, -1), (1, 1)
]


def in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def copy_board(board):
    return [row[:] for row in board]


def format_move(m):
    fr, fc, tr, tc = m
    return f"{fr},{fc}:{tr},{tc}"


def apply_move(board, move):
    fr, fc, tr, tc = move
    nb = [row[:] for row in board]
    nb[tr][tc] = nb[fr][fc]
    nb[fr][fc] = 0
    return nb


def count_line_pieces(board, r, c, dr, dc):
    total = 1
    rr, cc = r + dr, c + dc
    while in_bounds(rr, cc):
        if board[rr][cc] != 0:
            total += 1
        rr += dr
        cc += dc
    rr, cc = r - dr, c - dc
    while in_bounds(rr, cc):
        if board[rr][cc] != 0:
            total += 1
        rr -= dr
        cc -= dc
    return total


def legal_moves(board, player=1):
    moves = []
    for r in range(8):
        for c in range(8):
            if board[r][c] != player:
                continue
            for dr, dc in ORTHO_DIAG_DIRS:
                dist = count_line_pieces(board, r, c, dr, dc)
                tr, tc = r + dr * dist, c + dc * dist
                if not in_bounds(tr, tc):
                    continue

                blocked = False
                rr, cc = r + dr, c + dc
                for _ in range(dist - 1):
                    if board[rr][cc] == -player:
                        blocked = True
                        break
                    rr += dr
                    cc += dc
                if blocked:
                    continue

                if board[tr][tc] == player:
                    continue

                moves.append((r, c, tr, tc))
    return moves


def rotate(board):
    return [[-board[r][c] for c in range(8)] for r in range(8)]


def player_positions(board, player=1):
    out = []
    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                out.append((r, c))
    return out


def components_and_largest(board, player=1):
    pos = set(player_positions(board, player))
    if not pos:
        return 0, 0
    seen = set()
    comps = 0
    largest = 0
    for p in pos:
        if p in seen:
            continue
        comps += 1
        q = [p]
        seen.add(p)
        sz = 0
        while q:
            r, c = q.pop()
            sz += 1
            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                if (nr, nc) in pos and (nr, nc) not in seen:
                    seen.add((nr, nc))
                    q.append((nr, nc))
        if sz > largest:
            largest = sz
    return comps, largest


def is_connected(board, player=1):
    pos = player_positions(board, player)
    n = len(pos)
    if n <= 1:
        return True
    s = set(pos)
    seen = set([pos[0]])
    stack = [pos[0]]
    while stack:
        r, c = stack.pop()
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if (nr, nc) in s and (nr, nc) not in seen:
                seen.add((nr, nc))
                stack.append((nr, nc))
    return len(seen) == n


def min_pairwise_chebyshev_sum(board, player=1):
    pos = player_positions(board, player)
    n = len(pos)
    if n <= 1:
        return 0
    total = 0
    for i in range(n):
        best = 99
        r1, c1 = pos[i]
        for j in range(n):
            if i == j:
                continue
            r2, c2 = pos[j]
            d = max(abs(r1 - r2), abs(c1 - c2))
            if d < best:
                best = d
        total += best
    return total


def centralization(board, player=1):
    pos = player_positions(board, player)
    if not pos:
        return -100
    score = 0.0
    for r, c in pos:
        score -= (abs(r - 3.5) + abs(c - 3.5))
    return score


def mobility(board, player=1):
    return len(legal_moves(board, player))


def immediate_winning_moves(board, player=1):
    wins = []
    for m in legal_moves(board, player):
        nb = apply_move(board, m)
        if is_connected(nb, player):
            wins.append(m)
    return wins


def evaluate(board):
    if is_connected(board, 1):
        return 1000000
    if is_connected(board, -1):
        return -1000000

    my_comps, my_largest = components_and_largest(board, 1)
    op_comps, op_largest = components_and_largest(board, -1)

    my_pos = len(player_positions(board, 1))
    op_pos = len(player_positions(board, -1))

    score = 0.0
    score += -250 * my_comps
    score += 220 * op_comps
    score += 35 * my_largest
    score += -25 * op_largest

    score += -18 * min_pairwise_chebyshev_sum(board, 1)
    score += 14 * min_pairwise_chebyshev_sum(board, -1)

    score += 8 * centralization(board, 1)
    score += -6 * centralization(board, -1)

    my_mob = mobility(board, 1)
    op_mob = mobility(board, -1)
    score += 1.5 * (my_mob - op_mob)

    score += 12 * (my_pos - op_pos)

    # Reward contact opportunities / punish vulnerable fragmentation.
    for r in range(8):
        for c in range(8):
            if board[r][c] == 1:
                local = 0
                for dr, dc in DIRS:
                    nr, nc = r + dr, c + dc
                    if in_bounds(nr, nc) and board[nr][nc] == 1:
                        local += 1
                score += 4 * local
            elif board[r][c] == -1:
                local = 0
                for dr, dc in DIRS:
                    nr, nc = r + dr, c + dc
                    if in_bounds(nr, nc) and board[nr][nc] == -1:
                        local += 1
                score -= 3 * local

    return score


def ordered_moves(board, player=1):
    moves = legal_moves(board, player)
    scored = []
    for m in moves:
        nb = apply_move(board, m)
        tr, tc = m[2], m[3]
        capture_bonus = 50 if board[tr][tc] == -player else 0
        if player == 1:
            s = evaluate(nb) + capture_bonus
        else:
            s = -evaluate(rotate(nb)) + capture_bonus
        scored.append((s, m))
    scored.sort(reverse=True, key=lambda x: x[0])
    return [m for _, m in scored]


def negamax(board, depth, alpha, beta, end_time):
    if time.time() >= end_time:
        return evaluate(board), None

    if is_connected(board, 1):
        return 1000000 + depth, None
    if is_connected(board, -1):
        return -1000000 - depth, None

    moves = ordered_moves(board, 1)
    if not moves:
        return evaluate(board), None

    if depth == 0:
        return evaluate(board), None

    best_move = moves[0]
    best_score = -10**18

    for m in moves:
        if time.time() >= end_time:
            break
        nb = apply_move(board, m)
        rb = rotate(nb)
        score, _ = negamax(rb, depth - 1, -beta, -alpha, end_time)
        score = -score

        if score > best_score:
            best_score = score
            best_move = m

        if best_score > alpha:
            alpha = best_score
        if alpha >= beta:
            break

    return best_score, best_move


def choose_move(board):
    moves = legal_moves(board, 1)
    if not moves:
        return None

    # 1) Immediate win.
    wins = immediate_winning_moves(board, 1)
    if wins:
        return wins[0]

    # 2) Avoid giving opponent immediate win if possible.
    safe_moves = []
    for m in moves:
        nb = apply_move(board, m)
        opp_wins = immediate_winning_moves(rotate(nb), 1)
        if not opp_wins:
            safe_moves.append(m)

    candidate_moves = safe_moves if safe_moves else moves

    # 3) If small enough, search deeper on candidates by ordering.
    end_time = time.time() + 0.90

    # Good fallback from one-ply eval among candidates.
    best_fallback = candidate_moves[0]
    best_fallback_score = -10**18
    for m in candidate_moves:
        nb = apply_move(board, m)
        s = evaluate(nb)
        tr, tc = m[2], m[3]
        if board[tr][tc] == -1:
            s += 35
        if s > best_fallback_score:
            best_fallback_score = s
            best_fallback = m

    # Adaptive depth.
    b = len(candidate_moves)
    if b <= 8:
        depth = 3
    elif b <= 18:
        depth = 2
    else:
        depth = 1

    # Search from current board, but if candidate subset is smaller than all moves,
    # evaluate candidate subset manually to preserve the safety filter.
    if candidate_moves is not moves:
        best_move = best_fallback
        best_score = -10**18
        ordered = []
        for m in candidate_moves:
            nb = apply_move(board, m)
            ordered.append((evaluate(nb), m))
        ordered.sort(reverse=True, key=lambda x: x[0])

        alpha, beta = -10**18, 10**18
        for _, m in ordered:
            if time.time() >= end_time:
                break
            nb = apply_move(board, m)
            rb = rotate(nb)
            score, _ = negamax(rb, depth - 1, -beta, -alpha, end_time)
            score = -score
            if score > best_score:
                best_score = score
                best_move = m
            if score > alpha:
                alpha = score
        return best_move

    score, move = negamax(board, depth, -10**18, 10**18, end_time)
    if move is not None:
        return move

    return best_fallback


def policy(board) -> str:
    move = choose_move(board)
    if move is None:
        # Emergency fallback: scan for first legal move.
        moves = legal_moves(board, 1)
        if moves:
            return format_move(moves[0])
        # Should not happen in valid LOA games, but return a syntactically valid string.
        return "0,0:0,0"
    return format_move(move)
