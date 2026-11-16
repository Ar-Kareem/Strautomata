
import time
from collections import deque

DIRS = [
    (-1, 0), (1, 0), (0, -1), (0, 1),
    (-1, -1), (-1, 1), (1, -1), (1, 1)
]

WIN_SCORE = 10**8
TIME_LIMIT = 0.92  # keep a safety margin under 1 second


def inside(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def board_key(board):
    return tuple(tuple(row) for row in board)


def count_line(board, r, c, dr, dc):
    cnt = 1
    rr, cc = r + dr, c + dc
    while inside(rr, cc):
        if board[rr][cc] != 0:
            cnt += 1
        rr += dr
        cc += dc
    rr, cc = r - dr, c - dc
    while inside(rr, cc):
        if board[rr][cc] != 0:
            cnt += 1
        rr -= dr
        cc -= dc
    return cnt


def generate_moves(board):
    moves = []
    for r in range(8):
        for c in range(8):
            if board[r][c] != 1:
                continue
            for dr, dc in DIRS:
                dist = count_line(board, r, c, dr, dc)
                tr, tc = r + dr * dist, c + dc * dist
                if not inside(tr, tc):
                    continue
                if board[tr][tc] == 1:
                    continue

                # Cannot jump over enemy pieces
                ok = True
                rr, cc = r + dr, c + dc
                for _ in range(dist - 1):
                    if board[rr][cc] == -1:
                        ok = False
                        break
                    rr += dr
                    cc += dc
                if not ok:
                    continue

                moves.append((r, c, tr, tc))
    return moves


def make_move(board, move):
    r, c, tr, tc = move
    nb = [row[:] for row in board]
    nb[tr][tc] = nb[r][c]
    nb[r][c] = 0
    return nb


def piece_positions(board, player):
    out = []
    for r in range(8):
        for c in range(8):
            if board[r][c] == player:
                out.append((r, c))
    return out


def connected(board, player):
    pos = piece_positions(board, player)
    if len(pos) <= 1:
        return True
    seen = set()
    q = deque([pos[0]])
    seen.add(pos[0])
    while q:
        r, c = q.popleft()
        for dr, dc in DIRS:
            rr, cc = r + dr, c + dc
            if inside(rr, cc) and board[rr][cc] == player and (rr, cc) not in seen:
                seen.add((rr, cc))
                q.append((rr, cc))
    return len(seen) == len(pos)


def components_info(board, player):
    pos = piece_positions(board, player)
    if not pos:
        return 0, 0
    seen = set()
    comps = 0
    largest = 0
    for start in pos:
        if start in seen:
            continue
        comps += 1
        q = deque([start])
        seen.add(start)
        sz = 0
        while q:
            r, c = q.popleft()
            sz += 1
            for dr, dc in DIRS:
                rr, cc = r + dr, c + dc
                if inside(rr, cc) and board[rr][cc] == player and (rr, cc) not in seen:
                    seen.add((rr, cc))
                    q.append((rr, cc))
        if sz > largest:
            largest = sz
    return comps, largest


def concentration_score(positions):
    if not positions:
        return 0.0
    cr = sum(r for r, _ in positions) / len(positions)
    cc = sum(c for _, c in positions) / len(positions)
    # smaller is better
    return sum(max(abs(r - cr), abs(c - cc)) for r, c in positions)


def centralization_score(positions):
    # smaller is better
    return sum(abs(r - 3.5) + abs(c - 3.5) for r, c in positions)


_eval_cache = {}


def evaluate(board):
    key = board_key(board)
    if key in _eval_cache:
        return _eval_cache[key]

    if connected(board, 1):
        _eval_cache[key] = WIN_SCORE
        return WIN_SCORE
    if connected(board, -1):
        _eval_cache[key] = -WIN_SCORE
        return -WIN_SCORE

    my_pos = piece_positions(board, 1)
    op_pos = piece_positions(board, -1)

    my_comps, my_largest = components_info(board, 1)
    op_comps, op_largest = components_info(board, -1)

    my_conc = concentration_score(my_pos)
    op_conc = concentration_score(op_pos)

    my_cent = centralization_score(my_pos)
    op_cent = centralization_score(op_pos)

    my_mob = len(generate_moves(board))
    # Mobility for opponent in their perspective
    opp_board = [[-x for x in row] for row in board]
    op_mob = len(generate_moves(opp_board))

    score = 0.0
    score += 700 * (op_comps - my_comps)
    score += 120 * (my_largest - op_largest)
    score += 18 * (op_conc - my_conc)
    score += 4 * (op_cent - my_cent)
    score += 2 * (my_mob - op_mob)
    score += 25 * (len(my_pos) - len(op_pos))

    val = int(score)
    _eval_cache[key] = val
    return val


def quick_move_score(board, move):
    r, c, tr, tc = move
    score = 0
    if board[tr][tc] == -1:
        score += 200
    # prefer central destinations
    score -= int(10 * (abs(tr - 3.5) + abs(tc - 3.5)))
    # prefer moves that reduce distance to board center from source
    score += int(5 * ((abs(r - 3.5) + abs(c - 3.5)) - (abs(tr - 3.5) + abs(tc - 3.5))))
    return score


def ordered_moves(board):
    moves = generate_moves(board)
    if not moves:
        return moves

    scored = []
    for mv in moves:
        nb = make_move(board, mv)
        if connected(nb, 1):
            s = WIN_SCORE
        else:
            s = quick_move_score(board, mv)
        scored.append((s, mv))
    scored.sort(reverse=True, key=lambda x: x[0])
    return [mv for _, mv in scored]


class SearchTimeout(Exception):
    pass


def negamax(board, depth, alpha, beta, start_time):
    if time.time() - start_time > TIME_LIMIT:
        raise SearchTimeout

    if connected(board, 1):
        return WIN_SCORE
    if connected(board, -1):
        return -WIN_SCORE

    if depth == 0:
        return evaluate(board)

    moves = ordered_moves(board)
    if not moves:
        return evaluate(board)

    best = -10**18
    for mv in moves:
        nb = make_move(board, mv)

        # Immediate win for side to move
        if connected(nb, 1):
            score = WIN_SCORE - (4 - depth)
        else:
            # Switch perspective
            nb2 = [[-x for x in row] for row in nb]
            score = -negamax(nb2, depth - 1, -beta, -alpha, start_time)

        if score > best:
            best = score
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    return best


def move_to_str(move):
    r, c, tr, tc = move
    return f"{r},{c}:{tr},{tc}"


def policy(board) -> str:
    global _eval_cache
    _eval_cache = {}

    start_time = time.time()
    moves = generate_moves(board)

    # Should not happen in normal LOA, but remain safe.
    if not moves:
        return "0,0:0,0"

    # Legal fallback
    best_move = moves[0]

    # Immediate winning move
    for mv in moves:
        if connected(make_move(board, mv), 1):
            return move_to_str(mv)

    # Fast tactical filter: avoid moves that allow immediate opponent win if possible
    safe_moves = []
    for mv in moves:
        nb = make_move(board, mv)
        opp_board = [[-x for x in row] for row in nb]
        opp_moves = generate_moves(opp_board)
        opp_can_win = False
        for omv in opp_moves:
            if connected(make_move(opp_board, omv), 1):
                opp_can_win = True
                break
        if not opp_can_win:
            safe_moves.append(mv)

    root_moves = safe_moves if safe_moves else moves
    root_moves = sorted(root_moves, key=lambda mv: quick_move_score(board, mv), reverse=True)
    best_move = root_moves[0]

    # Iterative deepening
    max_depth = 4
    if len(root_moves) <= 12:
        max_depth = 5
    if len(root_moves) <= 6:
        max_depth = 6

    try:
        for depth in range(1, max_depth + 1):
            current_best = None
            current_best_score = -10**18
            alpha = -10**18
            beta = 10**18

            for mv in root_moves:
                if time.time() - start_time > TIME_LIMIT:
                    raise SearchTimeout

                nb = make_move(board, mv)
                if connected(nb, 1):
                    return move_to_str(mv)

                nb2 = [[-x for x in row] for row in nb]
                score = -negamax(nb2, depth - 1, -beta, -alpha, start_time)

                # small tie-break using quick move quality
                score += quick_move_score(board, mv) // 20

                if score > current_best_score:
                    current_best_score = score
                    current_best = mv
                if score > alpha:
                    alpha = score

            if current_best is not None:
                best_move = current_best

            # Reorder root moves by results for next iteration
            root_moves = sorted(
                root_moves,
                key=lambda mv: (mv == best_move, quick_move_score(board, mv)),
                reverse=True
            )

    except SearchTimeout:
        pass

    return move_to_str(best_move)
