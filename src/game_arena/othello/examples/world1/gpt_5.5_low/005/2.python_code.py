
import numpy as np
import time

# 8 directions for Othello flips
DIRS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)

# Positional square table. Corners are excellent; squares adjacent to
# empty corners are dangerous; edges are generally good.
PST = np.array([
    [120, -25,  20,   5,   5,  20, -25, 120],
    [-25, -60, -10, -10, -10, -10, -60, -25],
    [ 20, -10,  15,   3,   3,  15, -10,  20],
    [  5, -10,   3,   3,   3,   3, -10,   5],
    [  5, -10,   3,   3,   3,   3, -10,   5],
    [ 20, -10,  15,   3,   3,  15, -10,  20],
    [-25, -60, -10, -10, -10, -10, -60, -25],
    [120, -25,  20,   5,   5,  20, -25, 120],
], dtype=np.int32)

CORNERS = ((0, 0), (0, 7), (7, 0), (7, 7))
CORNER_ADJ = {
    (0, 0): ((0, 1), (1, 0), (1, 1)),
    (0, 7): ((0, 6), (1, 7), (1, 6)),
    (7, 0): ((7, 1), (6, 0), (6, 1)),
    (7, 7): ((7, 6), (6, 7), (6, 6)),
}


class TimeUp(Exception):
    pass


def inside(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def legal_moves(board, player):
    """
    Return a dictionary mapping (r,c) -> list of discs flipped.
    board values: 1 for current root player, -1 for opponent, 0 empty.
    player is either 1 or -1.
    """
    opp = -player
    moves = {}

    for r in range(8):
        for c in range(8):
            if board[r, c] != 0:
                continue

            all_flips = []
            for dr, dc in DIRS:
                rr, cc = r + dr, c + dc
                flips = []

                while inside(rr, cc) and board[rr, cc] == opp:
                    flips.append((rr, cc))
                    rr += dr
                    cc += dc

                if flips and inside(rr, cc) and board[rr, cc] == player:
                    all_flips.extend(flips)

            if all_flips:
                moves[(r, c)] = all_flips

    return moves


def make_move(board, move, flips, player):
    r, c = move
    board[r, c] = player
    for rr, cc in flips:
        board[rr, cc] = player


def undo_move(board, move, flips, player):
    r, c = move
    board[r, c] = 0
    opp = -player
    for rr, cc in flips:
        board[rr, cc] = opp


def frontier_count(board, player):
    count = 0
    for r in range(8):
        for c in range(8):
            if board[r, c] != player:
                continue
            for dr, dc in DIRS:
                rr, cc = r + dr, c + dc
                if inside(rr, cc) and board[rr, cc] == 0:
                    count += 1
                    break
    return count


def evaluate(board, player):
    """
    Evaluation from the perspective of 'player'.
    Positive means good for player.
    """
    occupied = int(np.count_nonzero(board))
    empties = 64 - occupied

    my_discs = int(np.sum(board == player))
    op_discs = int(np.sum(board == -player))

    # Terminal / near-terminal disc count becomes decisive.
    my_moves = legal_moves(board, player)
    op_moves = legal_moves(board, -player)

    if not my_moves and not op_moves:
        diff = my_discs - op_discs
        if diff > 0:
            return 100000 + diff
        if diff < 0:
            return -100000 + diff
        return 0

    # Positional score
    pos = int(np.sum(PST[board == player]) - np.sum(PST[board == -player]))

    # Mobility is one of the strongest midgame features.
    m1 = len(my_moves)
    m2 = len(op_moves)
    if m1 + m2:
        mobility = 100 * (m1 - m2) / (m1 + m2)
    else:
        mobility = 0

    # Corners are extremely important.
    corner_score = 0
    for r, c in CORNERS:
        if board[r, c] == player:
            corner_score += 1
        elif board[r, c] == -player:
            corner_score -= 1

    # Penalize discs adjacent to an empty corner.
    danger = 0
    for corner, adjacents in CORNER_ADJ.items():
        cr, cc = corner
        if board[cr, cc] == 0:
            for ar, ac in adjacents:
                if board[ar, ac] == player:
                    danger -= 1
                elif board[ar, ac] == -player:
                    danger += 1

    # Frontier discs are vulnerable; fewer is better.
    my_frontier = frontier_count(board, player)
    op_frontier = frontier_count(board, -player)
    frontier = op_frontier - my_frontier

    # Disc parity matters mostly in the endgame.
    disc_diff = my_discs - op_discs

    if empties > 44:
        return (
            2.0 * pos +
            8.0 * mobility +
            800.0 * corner_score +
            120.0 * danger +
            10.0 * frontier -
            1.0 * disc_diff
        )
    elif empties > 14:
        return (
            2.5 * pos +
            10.0 * mobility +
            900.0 * corner_score +
            140.0 * danger +
            8.0 * frontier +
            1.5 * disc_diff
        )
    else:
        return (
            1.0 * pos +
            4.0 * mobility +
            1200.0 * corner_score +
            100.0 * danger +
            3.0 * frontier +
            25.0 * disc_diff
        )


def move_order_score(board, move, flips, player):
    r, c = move
    score = int(PST[r, c]) + 2 * len(flips)

    if move in CORNERS:
        score += 10000

    # Avoid moving next to an empty corner.
    for corner, adjacents in CORNER_ADJ.items():
        cr, cc = corner
        if board[cr, cc] == 0 and move in adjacents:
            score -= 5000

    # Edge moves are often useful.
    if r == 0 or r == 7 or c == 0 or c == 7:
        score += 50

    return score


def negamax(board, player, depth, alpha, beta, deadline):
    if time.perf_counter() > deadline:
        raise TimeUp()

    moves = legal_moves(board, player)

    if depth == 0:
        return evaluate(board, player)

    if not moves:
        opp_moves = legal_moves(board, -player)
        if not opp_moves:
            return evaluate(board, player)
        return -negamax(board, -player, depth - 1, -beta, -alpha, deadline)

    ordered = sorted(
        moves.items(),
        key=lambda item: move_order_score(board, item[0], item[1], player),
        reverse=True
    )

    best = -10**18

    for move, flips in ordered:
        make_move(board, move, flips, player)
        val = -negamax(board, -player, depth - 1, -beta, -alpha, deadline)
        undo_move(board, move, flips, player)

        if val > best:
            best = val
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    return best


def exact_endgame_possible(empties):
    # Full-width endgame search is expensive; only attempt when safe.
    return empties <= 10


def coord_to_str(move):
    r, c = move
    return chr(ord('a') + c) + str(r + 1)


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Return a legal Othello move as algebraic notation, or "pass" if no legal move.
    """
    start = time.perf_counter()
    deadline = start + 0.88

    board = np.zeros((8, 8), dtype=np.int8)
    board[you == 1] = 1
    board[opponent == 1] = -1

    moves = legal_moves(board, 1)

    if not moves:
        return "pass"

    ordered = sorted(
        moves.items(),
        key=lambda item: move_order_score(board, item[0], item[1], 1),
        reverse=True
    )

    # Always keep a legal fallback.
    best_move = ordered[0][0]

    empties = int(np.sum(board == 0))

    # Choose a reasonable maximum depth. Iterative deepening will stop on time.
    if exact_endgame_possible(empties):
        max_depth = empties
    elif empties <= 16:
        max_depth = 8
    elif empties <= 28:
        max_depth = 6
    else:
        max_depth = 5

    # Iterative deepening: if time expires, use the best completed depth.
    try:
        for depth in range(1, max_depth + 1):
            if time.perf_counter() > deadline:
                break

            current_best = best_move
            current_score = -10**18
            alpha = -10**18
            beta = 10**18

            # Reorder root each iteration using static ordering.
            for move, flips in ordered:
                if time.perf_counter() > deadline:
                    raise TimeUp()

                make_move(board, move, flips, 1)
                score = -negamax(board, -1, depth - 1, -beta, -alpha, deadline)
                undo_move(board, move, flips, 1)

                if score > current_score:
                    current_score = score
                    current_best = move

                if score > alpha:
                    alpha = score

            best_move = current_best

            # Put the current best first for the next iteration.
            ordered.sort(
                key=lambda item: 1 if item[0] == best_move else 0,
                reverse=True
            )

    except TimeUp:
        pass
    except Exception:
        # Defensive fallback: never risk returning an illegal move.
        best_move = ordered[0][0]

    return coord_to_str(best_move)
