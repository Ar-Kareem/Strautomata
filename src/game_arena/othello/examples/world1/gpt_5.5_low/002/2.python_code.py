
import numpy as np
import time

DIRS = [(-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)]

POS_W = np.array([
    [120, -25,  20,   5,   5,  20, -25, 120],
    [-25, -45,  -5,  -5,  -5,  -5, -45, -25],
    [ 20,  -5,  15,   3,   3,  15,  -5,  20],
    [  5,  -5,   3,   3,   3,   3,  -5,   5],
    [  5,  -5,   3,   3,   3,   3,  -5,   5],
    [ 20,  -5,  15,   3,   3,  15,  -5,  20],
    [-25, -45,  -5,  -5,  -5,  -5, -45, -25],
    [120, -25,  20,   5,   5,  20, -25, 120]
], dtype=np.int16)

CORNERS = [(0, 0), (0, 7), (7, 0), (7, 7)]

ADJACENT_TO_CORNER = {
    (0, 0): [(0, 1), (1, 0), (1, 1)],
    (0, 7): [(0, 6), (1, 7), (1, 6)],
    (7, 0): [(6, 0), (7, 1), (6, 1)],
    (7, 7): [(6, 7), (7, 6), (6, 6)]
}

_deadline = 0.0


class Timeout(Exception):
    pass


def inside(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def legal_moves(board, side):
    moves = []
    opp = -side

    for r in range(8):
        for c in range(8):
            if board[r, c] != 0:
                continue

            flips_total = []
            for dr, dc in DIRS:
                rr, cc = r + dr, c + dc
                flips = []

                while inside(rr, cc) and board[rr, cc] == opp:
                    flips.append((rr, cc))
                    rr += dr
                    cc += dc

                if flips and inside(rr, cc) and board[rr, cc] == side:
                    flips_total.extend(flips)

            if flips_total:
                moves.append((r, c, flips_total))

    return moves


def make_move(board, move, side):
    r, c, flips = move
    nb = board.copy()
    nb[r, c] = side
    for rr, cc in flips:
        nb[rr, cc] = side
    return nb


def frontier_count(board, side):
    count = 0
    for r in range(8):
        for c in range(8):
            if board[r, c] != side:
                continue
            for dr, dc in DIRS:
                rr, cc = r + dr, c + dc
                if inside(rr, cc) and board[rr, cc] == 0:
                    count += 1
                    break
    return count


def evaluate(board, side):
    opp = -side
    empty = np.count_nonzero(board == 0)

    my_discs = np.count_nonzero(board == side)
    op_discs = np.count_nonzero(board == opp)

    if empty == 0:
        return 100000 * (my_discs - op_discs)

    positional = int(np.sum(POS_W[board == side]) - np.sum(POS_W[board == opp]))

    my_corners = 0
    op_corners = 0
    corner_danger = 0

    for cr, cc in CORNERS:
        if board[cr, cc] == side:
            my_corners += 1
        elif board[cr, cc] == opp:
            op_corners += 1
        else:
            for ar, ac in ADJACENT_TO_CORNER[(cr, cc)]:
                if board[ar, ac] == side:
                    corner_danger -= 35
                elif board[ar, ac] == opp:
                    corner_danger += 35

    corner_score = 800 * (my_corners - op_corners)

    my_mob = len(legal_moves(board, side))
    op_mob = len(legal_moves(board, opp))
    mobility_score = 0
    if my_mob + op_mob:
        mobility_score = 120 * (my_mob - op_mob) / (my_mob + op_mob)

    my_frontier = frontier_count(board, side)
    op_frontier = frontier_count(board, opp)
    frontier_score = -18 * (my_frontier - op_frontier)

    disc_score = 0
    if empty < 18:
        disc_score = 12 * (my_discs - op_discs)
    else:
        disc_score = -2 * (my_discs - op_discs)

    return int(positional + corner_score + corner_danger +
               mobility_score + frontier_score + disc_score)


def terminal_score(board, side):
    my_discs = np.count_nonzero(board == side)
    op_discs = np.count_nonzero(board == -side)
    diff = my_discs - op_discs

    if diff > 0:
        return 1000000 + diff
    if diff < 0:
        return -1000000 + diff
    return 0


def move_order_key(move):
    r, c, flips = move

    if (r, c) in CORNERS:
        return 10000 + len(flips)

    score = POS_W[r, c] + 4 * len(flips)

    for corner, adj in ADJACENT_TO_CORNER.items():
        if (r, c) in adj:
            score -= 200

    return int(score)


def negamax(board, side, depth, alpha, beta):
    if time.time() > _deadline:
        raise Timeout()

    moves = legal_moves(board, side)

    if not moves:
        opp_moves = legal_moves(board, -side)
        if not opp_moves:
            return terminal_score(board, side)
        return -negamax(board, -side, depth, -beta, -alpha)

    if depth <= 0:
        return evaluate(board, side)

    moves.sort(key=move_order_key, reverse=True)

    best = -10**12

    for mv in moves:
        nb = make_move(board, mv, side)
        val = -negamax(nb, -side, depth - 1, -beta, -alpha)

        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    return best


def coord(move):
    r, c, _ = move
    return chr(ord('a') + c) + str(r + 1)


def choose_max_depth(empty):
    if empty <= 10:
        return empty
    if empty <= 14:
        return 10
    if empty <= 20:
        return 8
    if empty <= 36:
        return 6
    if empty <= 52:
        return 5
    return 4


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    global _deadline

    board = np.zeros((8, 8), dtype=np.int8)
    board[you == 1] = 1
    board[opponent == 1] = -1

    moves = legal_moves(board, 1)

    if not moves:
        return "pass"

    moves.sort(key=move_order_key, reverse=True)
    best_move = moves[0]

    empty = int(np.count_nonzero(board == 0))
    max_depth = choose_max_depth(empty)

    _deadline = time.time() + 0.92

    try:
        for depth in range(1, max_depth + 1):
            current_best = best_move
            current_score = -10**12
            alpha = -10**12
            beta = 10**12

            ordered = moves[:]
            ordered.sort(key=move_order_key, reverse=True)

            for mv in ordered:
                if time.time() > _deadline:
                    raise Timeout()

                nb = make_move(board, mv, 1)
                score = -negamax(nb, -1, depth - 1, -beta, -alpha)

                if score > current_score:
                    current_score = score
                    current_best = mv

                if score > alpha:
                    alpha = score

            best_move = current_best

    except Timeout:
        pass

    return coord(best_move)
