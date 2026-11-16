
import time

DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1),
        (-1, -1), (1, 1), (-1, 1), (1, -1)]
PAIR_DIRS = [(1, 0), (0, 1), (1, 1), (1, -1)]

WIN = 1_000_000
INF = 10**9


def board_key(board):
    return bytes([cell + 1 for row in board for cell in row])


def centrality(r, c):
    return 7 - abs(2 * r - 7) - abs(2 * c - 7)


def compute_line_counts(board):
    rows = [0] * 8
    cols = [0] * 8
    d1 = [0] * 15  # r-c+7
    d2 = [0] * 15  # r+c
    for r in range(8):
        row = board[r]
        for c in range(8):
            if row[c] != 0:
                rows[r] += 1
                cols[c] += 1
                d1[r - c + 7] += 1
                d2[r + c] += 1
    return rows, cols, d1, d2


def legal_moves(board):
    rows, cols, d1, d2 = compute_line_counts(board)
    moves = []

    for r in range(8):
        row = board[r]
        for c in range(8):
            if row[c] != 1:
                continue

            for dr, dc in DIRS:
                if dr == 0:
                    n = rows[r]
                elif dc == 0:
                    n = cols[c]
                elif dr == dc:
                    n = d1[r - c + 7]
                else:
                    n = d2[r + c]

                tr = r + dr * n
                tc = c + dc * n

                if not (0 <= tr < 8 and 0 <= tc < 8):
                    continue
                if board[tr][tc] == 1:
                    continue

                ok = True
                for k in range(1, n):
                    rr = r + dr * k
                    cc = c + dc * k
                    if board[rr][cc] == -1:
                        ok = False
                        break

                if ok:
                    moves.append((r, c, tr, tc))

    return moves


def neighbor_count(board, r, c, val, exclude=None):
    exr = exc = -1
    if exclude is not None:
        exr, exc = exclude
    cnt = 0
    for dr, dc in DIRS:
        rr = r + dr
        cc = c + dc
        if 0 <= rr < 8 and 0 <= cc < 8 and not (rr == exr and cc == exc):
            if board[rr][cc] == val:
                cnt += 1
    return cnt


def is_connected(board, val):
    first = None
    total = 0

    for r in range(8):
        row = board[r]
        for c in range(8):
            if row[c] == val:
                total += 1
                if first is None:
                    first = (r, c)

    if total <= 1:
        return True

    seen = [[False] * 8 for _ in range(8)]
    stack = [first]
    seen[first[0]][first[1]] = True
    visited = 1

    while stack:
        r, c = stack.pop()
        for dr, dc in DIRS:
            rr = r + dr
            cc = c + dc
            if 0 <= rr < 8 and 0 <= cc < 8 and not seen[rr][cc] and board[rr][cc] == val:
                seen[rr][cc] = True
                visited += 1
                if visited == total:
                    return True
                stack.append((rr, cc))

    return visited == total


def piece_stats(board, val):
    positions = []
    minr = 8
    minc = 8
    maxr = -1
    maxc = -1
    sumr = 0
    sumc = 0

    for r in range(8):
        row = board[r]
        for c in range(8):
            if row[c] == val:
                positions.append((r, c))
                sumr += r
                sumc += c
                if r < minr:
                    minr = r
                if r > maxr:
                    maxr = r
                if c < minc:
                    minc = c
                if c > maxc:
                    maxc = c

    n = len(positions)
    if n == 0:
        return (0, 0, 0, 0.0, 0, 0, 0)

    seen = [[False] * 8 for _ in range(8)]
    comps = 0
    largest = 0

    for r, c in positions:
        if seen[r][c]:
            continue
        comps += 1
        size = 0
        stack = [(r, c)]
        seen[r][c] = True
        while stack:
            rr, cc = stack.pop()
            size += 1
            for dr, dc in DIRS:
                nr = rr + dr
                nc = cc + dc
                if 0 <= nr < 8 and 0 <= nc < 8 and not seen[nr][nc] and board[nr][nc] == val:
                    seen[nr][nc] = True
                    stack.append((nr, nc))
        if size > largest:
            largest = size

    bbox = (maxr - minr + 1) * (maxc - minc + 1)

    cr = sumr / n
    cc = sumc / n
    spread = 0.0
    cent = 0
    adj = 0

    for r, c in positions:
        dr = r - cr
        dc = c - cc
        spread += dr * dr + dc * dc
        cent += centrality(r, c)
        for pr, pc in PAIR_DIRS:
            rr = r + pr
            cc2 = c + pc
            if 0 <= rr < 8 and 0 <= cc2 < 8 and board[rr][cc2] == val:
                adj += 1

    return (comps, largest, bbox, spread, cent, adj, n)


def evaluate_features(board):
    myc, mylargest, mybox, myspread, mycent, myadj, _ = piece_stats(board, 1)
    opc, oplargest, opbox, opspread, opcent, opadj, _ = piece_stats(board, -1)

    score = 0
    score += 260 * (opc - myc)
    score += 35 * (mylargest - oplargest)
    score += 8 * (myadj - opadj)
    score += 5 * (opbox - mybox)
    score += int(4 * (opspread - myspread))
    score += 3 * (mycent - opcent)
    return score


def order_moves(board, moves, pv_move=None):
    scored = []

    for m in moves:
        fr, fc, tr, tc = m
        score = 0

        if pv_move is not None and m == pv_move:
            score += 100000

        if board[tr][tc] == -1:
            score += 500

        src_cent = centrality(fr, fc)
        dst_cent = centrality(tr, tc)
        score += 12 * (dst_cent - src_cent)
        score += 4 * dst_cent

        src_nei = neighbor_count(board, fr, fc, 1)
        dst_nei = neighbor_count(board, tr, tc, 1, exclude=(fr, fc))
        score += 20 * (dst_nei - src_nei)

        if src_nei == 0:
            score += 15

        scored.append((score, m))

    scored.sort(reverse=True)
    return [m for _, m in scored]


def make_board_after_move(board, move):
    fr, fc, tr, tc = move
    nb = [row[:] for row in board]
    nb[fr][fc] = 0
    nb[tr][tc] = 1
    return nb


def swap_perspective(board):
    return [[-cell for cell in row] for row in board]


def negamax(board, depth, alpha, beta, deadline, tt_exact, tt_move, nodes, ply):
    nodes[0] += 1
    if (nodes[0] & 255) == 0 and time.perf_counter() >= deadline:
        raise TimeoutError

    # Opponent already connected => loss for side to move.
    if is_connected(board, -1):
        return -WIN + ply
    # Rare/improper state, but keep it well-defined.
    if is_connected(board, 1):
        return WIN - ply

    if depth == 0:
        return evaluate_features(board)

    key = board_key(board)
    entry = tt_exact.get(key)
    if entry is not None and entry[0] >= depth:
        return entry[1]

    moves = legal_moves(board)
    if not moves:
        return -WIN + ply

    pv = tt_move.get(key)
    moves = order_moves(board, moves, pv)

    best = -INF
    best_move = moves[0]
    cutoff = False

    for m in moves:
        nb = make_board_after_move(board, m)

        if is_connected(nb, 1):
            score = WIN - ply - 1
        else:
            child = swap_perspective(nb)
            score = -negamax(child, depth - 1, -beta, -alpha,
                             deadline, tt_exact, tt_move, nodes, ply + 1)

        if score > best:
            best = score
            best_move = m

        if best > alpha:
            alpha = best
        if alpha >= beta:
            cutoff = True
            break

    tt_move[key] = best_move
    if not cutoff:
        tt_exact[key] = (depth, best)

    return best


def search_root(board, moves, depth, deadline, tt_exact, tt_move):
    key = board_key(board)
    pv = tt_move.get(key)
    ordered = order_moves(board, moves, pv)

    best_move = ordered[0]
    best_score = -INF
    alpha = -INF
    nodes = [0]

    for m in ordered:
        if (nodes[0] & 63) == 0 and time.perf_counter() >= deadline:
            raise TimeoutError

        nb = make_board_after_move(board, m)

        if is_connected(nb, 1):
            score = WIN - 1
        else:
            child = swap_perspective(nb)
            score = -negamax(child, depth - 1, -INF, -alpha,
                             deadline, tt_exact, tt_move, nodes, 1)

        if score > best_score:
            best_score = score
            best_move = m

        if score > alpha:
            alpha = score

    tt_move[key] = best_move
    tt_exact[key] = (depth, best_score)
    return best_move, best_score


def move_to_string(move):
    fr, fc, tr, tc = move
    return f"{fr},{fc}:{tr},{tc}"


def policy(board) -> str:
    board = [list(row) for row in board]
    moves = legal_moves(board)

    # Extremely rare fallback if there are no legal moves.
    # LOA positions should normally have a move.
    if not moves:
        return "0,0:0,0"

    if len(moves) == 1:
        return move_to_string(moves[0])

    # Immediate win check.
    for m in moves:
        nb = make_board_after_move(board, m)
        if is_connected(nb, 1):
            return move_to_string(m)

    moves = order_moves(board, moves, None)
    best_move = moves[0]

    total_pieces = sum(1 for r in range(8) for c in range(8) if board[r][c] != 0)
    if total_pieces <= 8:
        max_depth = 7
    elif total_pieces <= 12 or len(moves) <= 12:
        max_depth = 6
    elif len(moves) <= 22:
        max_depth = 5
    else:
        max_depth = 4

    deadline = time.perf_counter() + 0.92
    tt_exact = {}
    tt_move = {}

    for depth in range(1, max_depth + 1):
        try:
            mv, score = search_root(board, moves, depth, deadline, tt_exact, tt_move)
            best_move = mv
            if score >= WIN - 20:
                break
        except TimeoutError:
            break

    return move_to_string(best_move)
