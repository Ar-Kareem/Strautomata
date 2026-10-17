
import math
import time
from collections import deque

DIRS = [
    (-1, 0), (1, 0), (0, -1), (0, 1),
    (-1, -1), (-1, 1), (1, -1), (1, 1)
]

INF = 10**18


def in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def copy_board(board):
    return [row[:] for row in board]


def piece_positions(board, player):
    out = []
    for r in range(8):
        row = board[r]
        for c in range(8):
            if row[c] == player:
                out.append((r, c))
    return out


def count_components(board, player):
    pieces = piece_positions(board, player)
    if not pieces:
        return 0, 0
    piece_set = set(pieces)
    seen = set()
    comps = 0
    largest = 0
    for p in pieces:
        if p in seen:
            continue
        comps += 1
        q = [p]
        seen.add(p)
        size = 0
        while q:
            r, c = q.pop()
            size += 1
            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                if (nr, nc) in piece_set and (nr, nc) not in seen:
                    seen.add((nr, nc))
                    q.append((nr, nc))
        if size > largest:
            largest = size
    return comps, largest


def is_connected(board, player):
    count = sum(1 for r in range(8) for c in range(8) if board[r][c] == player)
    if count <= 1:
        return True
    comps, _ = count_components(board, player)
    return comps == 1


def line_count(board, r, c, dr, dc):
    # Count pieces on the full line through (r,c) in direction (dr,dc)
    cnt = 1  # include self
    nr, nc = r + dr, c + dc
    while in_bounds(nr, nc):
        if board[nr][nc] != 0:
            cnt += 1
        nr += dr
        nc += dc
    nr, nc = r - dr, c - dc
    while in_bounds(nr, nc):
        if board[nr][nc] != 0:
            cnt += 1
        nr -= dr
        nc -= dc
    return cnt


def legal_moves(board, player=1):
    moves = []
    for r in range(8):
        for c in range(8):
            if board[r][c] != player:
                continue
            for dr, dc in DIRS:
                dist = line_count(board, r, c, dr, dc)
                tr, tc = r + dr * dist, c + dc * dist
                if not in_bounds(tr, tc):
                    continue
                if board[tr][tc] == player:
                    continue

                # Path may jump over friendly pieces but not enemy pieces.
                ok = True
                nr, nc = r + dr, c + dc
                while (nr, nc) != (tr, tc):
                    if board[nr][nc] == -player:
                        ok = False
                        break
                    nr += dr
                    nc += dc
                if not ok:
                    continue

                moves.append((r, c, tr, tc))
    return moves


def apply_move(board, move, player=1):
    r, c, tr, tc = move
    nb = copy_board(board)
    nb[r][c] = 0
    nb[tr][tc] = player
    return nb


def flip_board(board):
    return [[-board[r][c] for c in range(8)] for r in range(8)]


def canonical_after_move(board, move):
    # After our move, opponent to move. Flip perspective so side-to-move is always +1.
    nb = apply_move(board, move, 1)
    return flip_board(nb)


def center_score(pieces):
    # Higher is better: closer to center
    score = 0.0
    for r, c in pieces:
        score += 7.0 - ((r - 3.5) ** 2 + (c - 3.5) ** 2) ** 0.5
    return score


def compactness_score(pieces):
    if not pieces:
        return -1000.0
    n = len(pieces)
    cr = sum(r for r, _ in pieces) / n
    cc = sum(c for _, c in pieces) / n
    s = 0.0
    for r, c in pieces:
        s -= abs(r - cr) + abs(c - cc)
    return s


def edge_penalty(pieces):
    pen = 0
    for r, c in pieces:
        if r == 0 or r == 7:
            pen += 1
        if c == 0 or c == 7:
            pen += 1
    return pen


def evaluate(board):
    # board is from side-to-move perspective: +1 us, -1 opponent
    my_connected = is_connected(board, 1)
    opp_connected = is_connected(board, -1)

    if my_connected and opp_connected:
        # In LOA, player who just moved wins immediately upon connecting.
        # Since it's our turn now, if both connected, previous player likely just connected.
        return -INF // 2
    if my_connected:
        return INF // 2
    if opp_connected:
        return -INF // 2

    my_pieces = piece_positions(board, 1)
    opp_pieces = piece_positions(board, -1)

    my_comps, my_largest = count_components(board, 1)
    opp_comps, opp_largest = count_components(board, -1)

    my_mob = len(legal_moves(board, 1))
    opp_mob = len(legal_moves(flip_board(board), 1))

    score = 0.0

    score += 600 * (opp_comps - my_comps)
    score += 80 * (my_largest - opp_largest)
    score += 18 * (center_score(my_pieces) - center_score(opp_pieces))
    score += 10 * (compactness_score(my_pieces) - compactness_score(opp_pieces))
    score += 12 * (len(my_pieces) - len(opp_pieces))
    score += 4 * (my_mob - opp_mob)
    score += 15 * (edge_penalty(opp_pieces) - edge_penalty(my_pieces))

    # Mild bonus for adjacency among own pieces
    my_adj = 0
    my_set = set(my_pieces)
    for r, c in my_pieces:
        for dr, dc in DIRS:
            if (r + dr, c + dc) in my_set:
                my_adj += 1
    opp_adj = 0
    opp_set = set(opp_pieces)
    for r, c in opp_pieces:
        for dr, dc in DIRS:
            if (r + dr, c + dc) in opp_set:
                opp_adj += 1
    score += 6 * (my_adj - opp_adj)

    return score


def move_heuristic(board, move):
    r, c, tr, tc = move
    score = 0.0
    # Capture bonus
    if board[tr][tc] == -1:
        score += 200
    # Move toward center
    before = ((r - 3.5) ** 2 + (c - 3.5) ** 2) ** 0.5
    after = ((tr - 3.5) ** 2 + (tc - 3.5) ** 2) ** 0.5
    score += 20 * (before - after)

    # Encourage joining own neighbors at destination
    neigh = 0
    for dr, dc in DIRS:
        nr, nc = tr + dr, tc + dc
        if in_bounds(nr, nc) and board[nr][nc] == 1 and not (nr == r and nc == c):
            neigh += 1
    score += 25 * neigh

    # Discourage leaving isolated region
    old_neigh = 0
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if in_bounds(nr, nc) and board[nr][nc] == 1 and not (nr == tr and nc == tc):
            old_neigh += 1
    score += 5 * (neigh - old_neigh)

    return score


def ordered_moves(board, player=1):
    moves = legal_moves(board, player)
    moves.sort(key=lambda m: move_heuristic(board, m), reverse=True)
    return moves


def immediate_winning_move(board):
    for m in ordered_moves(board, 1):
        nb = apply_move(board, m, 1)
        if is_connected(nb, 1):
            return m
    return None


def opponent_has_immediate_win(board_after_our_move_flipped):
    # board_after_our_move_flipped is from opponent-to-move perspective as +1
    for m in ordered_moves(board_after_our_move_flipped, 1):
        nb = apply_move(board_after_our_move_flipped, m, 1)
        if is_connected(nb, 1):
            return True
    return False


def negamax(board, depth, alpha, beta, end_time):
    if time.time() >= end_time:
        return evaluate(board), None

    if is_connected(board, 1):
        return INF // 2, None
    if is_connected(board, -1):
        return -INF // 2, None

    moves = ordered_moves(board, 1)
    if not moves:
        return evaluate(board), None

    if depth == 0:
        return evaluate(board), None

    best_move = moves[0]
    best_val = -INF

    for m in moves:
        if time.time() >= end_time:
            break
        child = canonical_after_move(board, m)
        val, _ = negamax(child, depth - 1, -beta, -alpha, end_time)
        val = -val
        if val > best_val:
            best_val = val
            best_move = m
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    return best_val, best_move


def move_to_str(m):
    r, c, tr, tc = m
    return f"{r},{c}:{tr},{tc}"


def policy(board) -> str:
    start = time.time()
    end_time = start + 0.92

    moves = legal_moves(board, 1)
    if not moves:
        # Should not happen in normal LOA, but return something safe-looking if arena misbehaves.
        return "0,0:0,0"

    # 1. Immediate win
    win_move = immediate_winning_move(board)
    if win_move is not None:
        return move_to_str(win_move)

    # 2. Filter out moves allowing immediate opponent win, if possible
    safe_moves = []
    for m in ordered_moves(board, 1):
        if time.time() >= end_time:
            break
        child = canonical_after_move(board, m)
        if not opponent_has_immediate_win(child):
            safe_moves.append(m)

    candidate_moves = safe_moves if safe_moves else ordered_moves(board, 1)

    # 3. Iterative deepening alpha-beta
    best_move = candidate_moves[0]
    # Narrow root to best candidates for speed if many moves
    root_moves = candidate_moves[:20] if len(candidate_moves) > 20 else candidate_moves

    depth = 1
    while depth <= 3 and time.time() < end_time:
        alpha = -INF
        beta = INF
        current_best = best_move
        current_best_val = -INF

        # Reorder root moves each iteration by quick eval
        scored = []
        for m in root_moves:
            child = canonical_after_move(board, m)
            scored.append((evaluate(child), m))
        scored.sort(reverse=True, key=lambda x: x[0])
        root_moves = [m for _, m in scored]

        for m in root_moves:
            if time.time() >= end_time:
                break
            child = canonical_after_move(board, m)
            val, _ = negamax(child, depth - 1, -beta, -alpha, end_time)
            val = -val
            if val > current_best_val:
                current_best_val = val
                current_best = m
            if val > alpha:
                alpha = val

        if time.time() < end_time:
            best_move = current_best
        depth += 1

    # 4. Guaranteed legal fallback
    if best_move not in moves:
        best_move = moves[0]

    return move_to_str(best_move)
