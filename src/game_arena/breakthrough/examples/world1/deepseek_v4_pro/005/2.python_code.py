
import time

PIECE_VALUE = 100
INF = 1000000

# Piece-square tables for White (row 0 is home, row 7 is opponent's home)
WHITE_PST = [
    [  0,  0,  0,  0,  0,  0,  0,  0],
    [ 10, 15, 20, 20, 20, 20, 15, 10],
    [ 20, 25, 30, 35, 35, 30, 25, 20],
    [ 30, 35, 40, 45, 45, 40, 35, 30],
    [ 40, 45, 50, 55, 55, 50, 45, 40],
    [ 50, 55, 60, 65, 65, 60, 55, 50],
    [ 60, 65, 70, 75, 75, 70, 65, 60],
    [  0,  0,  0,  0,  0,  0,  0,  0]
]

BLACK_PST = [WHITE_PST[7 - r] for r in range(8)]

def opponent_color(color):
    return 'b' if color == 'w' else 'w'

def generate_moves(me_set, opp_set, my_color):
    moves = []
    dr = -1 if my_color == 'b' else 1
    for (r, c) in me_set:
        nr = r + dr
        if not (0 <= nr <= 7):
            continue
        # straight forward
        target = (nr, c)
        if target not in me_set and target not in opp_set:
            moves.append(((r, c), target))
        # diagonals
        for dc in (-1, 1):
            nc = c + dc
            if 0 <= nc <= 7:
                target = (nr, nc)
                if target in opp_set:
                    moves.append(((r, c), target))
                elif target not in me_set:
                    moves.append(((r, c), target))
    return moves

def is_win(me_set, my_color):
    win_row = 7 if my_color == 'w' else 0
    for (r, c) in me_set:
        if r == win_row:
            return True
    return False

def apply_move(me_set, opp_set, move):
    (fr, fc), (tr, tc) = move
    new_me = set(me_set)
    new_me.remove((fr, fc))
    new_me.add((tr, tc))
    new_opp = set(opp_set)
    new_opp.discard((tr, tc))
    return new_me, new_opp

def evaluate(me_set, opp_set, my_color):
    score = 0
    if my_color == 'w':
        for (r, c) in me_set:
            score += PIECE_VALUE + WHITE_PST[r][c]
        for (r, c) in opp_set:
            score -= PIECE_VALUE + BLACK_PST[r][c]
    else:
        for (r, c) in me_set:
            score += PIECE_VALUE + BLACK_PST[r][c]
        for (r, c) in opp_set:
            score -= PIECE_VALUE + WHITE_PST[r][c]
    return score

def move_priority(move, opp_set, my_color):
    (fr, fc), (tr, tc) = move
    win_row = 7 if my_color == 'w' else 0
    if tr == win_row:
        return 100000
    prio = 0
    if (tr, tc) in opp_set:
        prio += 500  # capture bonus
    if my_color == 'w':
        prio += tr * 10
    else:
        prio += (7 - tr) * 10
    # slight center preference
    prio += 4 - abs(tc - 3.5)
    return prio

class TimeoutException(Exception):
    pass

def alphabeta(me_set, opp_set, my_color, depth, alpha, beta, start_time, time_limit):
    if time.perf_counter() - start_time > time_limit:
        raise TimeoutException()
    if depth == 0:
        return evaluate(me_set, opp_set, my_color)
    moves = generate_moves(me_set, opp_set, my_color)
    if not moves:
        return -INF + (10 - depth)  # lose, prefer later
    moves.sort(key=lambda m: move_priority(m, opp_set, my_color), reverse=True)
    for move in moves:
        new_me, new_opp = apply_move(me_set, opp_set, move)
        if is_win(new_me, my_color) or not new_opp:
            score = INF - (10 - depth)
        else:
            score = -alphabeta(new_opp, new_me, opponent_color(my_color), depth - 1, -beta, -alpha, start_time, time_limit)
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break
    return alpha

def policy(me, opp, color):
    me_set = set(me)
    opp_set = set(opp)
    start_time = time.perf_counter()
    time_limit = 0.95

    moves = generate_moves(me_set, opp_set, color)
    if not moves:
        # fallback (should never happen)
        return ((0, 0), (0, 0))

    # If only one move, return it immediately
    if len(moves) == 1:
        return moves[0]

    # Check for immediate win
    for move in moves:
        new_me, new_opp = apply_move(me_set, opp_set, move)
        if is_win(new_me, color) or not new_opp:
            return move

    best_move = moves[0]

    max_depth = 10
    for depth in range(1, max_depth + 1):
        if time.perf_counter() - start_time > time_limit:
            break
        current_best = best_move
        alpha = -INF
        beta = INF
        moves.sort(key=lambda m: move_priority(m, opp_set, color), reverse=True)
        try:
            for move in moves:
                if time.perf_counter() - start_time > time_limit:
                    break
                new_me, new_opp = apply_move(me_set, opp_set, move)
                if is_win(new_me, color) or not new_opp:
                    score = INF
                else:
                    score = -alphabeta(new_opp, new_me, opponent_color(color), depth - 1, -beta, -alpha, start_time, time_limit)
                if score > alpha:
                    alpha = score
                    current_best = move
                if alpha >= beta:
                    break
            # Update best_move only if we completed the depth without timeout
            if time.perf_counter() - start_time <= time_limit:
                best_move = current_best
            else:
                break
        except TimeoutException:
            break

    return best_move
