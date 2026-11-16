
import numpy as np
import math
import time

# Directions for scanning flips
_DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1),
               (0, -1),          (0, 1),
               (1, -1),  (1, 0), (1, 1)]

# Positional weights (classical heuristic)
_WEIGHTS = np.array([
    [120, -20,  20,   5,   5,  20, -20, 120],
    [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
    [20,   -5,  15,   3,   3,  15,  -5,  20],
    [5,    -5,   3,   3,   3,   3,  -5,   5],
    [5,    -5,   3,   3,   3,   3,  -5,   5],
    [20,   -5,  15,   3,   3,  15,  -5,  20],
    [-20, -40,  -5,  -5,  -5,  -5, -40, -20],
    [120, -20,  20,   5,   5,  20, -20, 120]
], dtype=float)

_CORNERS = [(0,0),(0,7),(7,0),(7,7)]

# Time safety: ensure we don't exceed ~0.9s (if needed)
_TIME_LIMIT = 0.90

def _coords_to_move(r, c):
    return chr(ord('a') + c) + str(r + 1)

def _in_bounds(r, c):
    return 0 <= r < 8 and 0 <= c < 8

def _flips_for_move(player, opp, r, c):
    # player and opp are numpy arrays 8x8 with 0/1
    if player[r, c] or opp[r, c]:
        return []  # occupied
    flips = []
    for dr, dc in _DIRECTIONS:
        rr, cc = r + dr, c + dc
        seq = []
        while _in_bounds(rr, cc) and opp[rr, cc] == 1:
            seq.append((rr, cc))
            rr += dr
            cc += dc
        if seq and _in_bounds(rr, cc) and player[rr, cc] == 1:
            flips.extend(seq)
    return flips

def _get_legal_moves(player, opp):
    moves = {}
    # iterate empties
    # using numpy where might be slightly faster
    empties = np.where((player == 0) & (opp == 0))
    for r, c in zip(empties[0], empties[1]):
        flips = _flips_for_move(player, opp, r, c)
        if flips:
            moves[(r, c)] = flips
    return moves

def _apply_move(player, opp, move, flips):
    # returns new_player, new_opp (copies)
    r, c = move
    new_player = player.copy()
    new_opp = opp.copy()
    new_player[r, c] = 1
    for (fr, fc) in flips:
        new_player[fr, fc] = 1
        new_opp[fr, fc] = 0
    return new_player, new_opp

def _game_over(you, opp):
    return (len(_get_legal_moves(you, opp)) == 0) and (len(_get_legal_moves(opp, you)) == 0)

def _evaluate(you, opp):
    # If game over, return large value favoring winner
    you_count = int(you.sum())
    opp_count = int(opp.sum())
    empties = 64 - you_count - opp_count
    if _game_over(you, opp):
        # final outcome decisive
        return (you_count - opp_count) * 10000

    # Corner occupancy
    corner_score = 0
    for (r, c) in _CORNERS:
        if you[r, c]:
            corner_score += 1
        elif opp[r, c]:
            corner_score -= 1

    # Mobility
    my_moves = len(_get_legal_moves(you, opp))
    opp_moves = len(_get_legal_moves(opp, you))
    mobility = 0
    if my_moves + opp_moves > 0:
        mobility = 100 * (my_moves - opp_moves) / (my_moves + opp_moves)

    # Positional weight sum
    pos = float(((_WEIGHTS * you).sum()) - ((_WEIGHTS * opp).sum()))

    # Disc difference (more relevant in endgame)
    disc_diff = you_count - opp_count

    # In early/midgame prioritize position and mobility; in endgame prioritize disc count
    if empties <= 12:
        score = 1000 * disc_diff + 500 * corner_score + pos * 1.0 + mobility * 1.0
    else:
        score = pos + 800 * corner_score + mobility * 1.5 + 10 * disc_diff

    return score

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    start_time = time.time()

    you = you.astype(np.int8)
    opponent = opponent.astype(np.int8)

    legal_moves = _get_legal_moves(you, opponent)
    if not legal_moves:
        return "pass"

    # Choose search depth based on empties (adaptive)
    you_count = int(you.sum())
    opp_count = int(opponent.sum())
    empties = 64 - you_count - opp_count

    if empties > 48:
        max_depth = 3
    elif empties > 30:
        max_depth = 4
    elif empties > 15:
        max_depth = 5
    else:
        max_depth = 8  # deeper in endgame where branching is lower

    # global best_move storage
    best_move = None
    best_score = -1e20

    # Move ordering helper: prefer corners, then high positional weight, then flip count
    def _move_sort_key(m):
        (r, c) = m
        key = 0
        if (r, c) in _CORNERS:
            key += 100000
        key += _WEIGHTS[r, c] * 10
        key += len(legal_moves[(r, c)]) * 1
        return -key  # negative for descending

    ordered_moves = sorted(legal_moves.keys(), key=_move_sort_key)

    # Alpha-beta with swapping roles; maximizing indicates it's "you" to move when True
    nodes_searched = 0

    def alphabeta(you_board, opp_board, depth, alpha, beta, maximizing, passed):
        nonlocal nodes_searched, start_time
        nodes_searched += 1

        # Time cutoff safeguard
        if time.time() - start_time > _TIME_LIMIT:
            # fallback: evaluate current position
            return _evaluate(you_board, opp_board)

        if depth == 0 or _game_over(you_board, opp_board):
            return _evaluate(you_board, opp_board)

        if maximizing:
            moves = _get_legal_moves(you_board, opp_board)
        else:
            moves = _get_legal_moves(opp_board, you_board)

        if not moves:
            if passed:
                # both passed -> game over
                return _evaluate(you_board, opp_board)
            # pass turn
            return alphabeta(you_board, opp_board, depth, alpha, beta, not maximizing, True)

        # order moves (local ordering)
        move_list = sorted(moves.keys(), key=lambda m: -(_WEIGHTS[m] * 10 + len(moves[m])))

        if maximizing:
            value = -1e20
            for m in move_list:
                flips = moves[m]
                new_you, new_opp = _apply_move(you_board, opp_board, m, flips)
                val = alphabeta(new_you, new_opp, depth - 1, alpha, beta, False, False)
                if val > value:
                    value = val
                if value > alpha:
                    alpha = value
                if alpha >= beta:
                    break
            return value
        else:
            value = 1e20
            for m in move_list:
                flips = moves[m]
                # apply move for opponent; apply on (opp_board, you_board)
                moved_opp, moved_you = _apply_move(opp_board, you_board, m, flips)
                # moved_you and moved_opp correspond to our new you_board and opp_board
                val = alphabeta(moved_you, moved_opp, depth - 1, alpha, beta, True, False)
                if val < value:
                    value = val
                if value < beta:
                    beta = value
                if alpha >= beta:
                    break
            return value

    # Iterative deepening to get a best move quickly and improve as time allows
    current_depth = 1
    final_depth = max_depth
    while current_depth <= final_depth:
        # For top-level ordering, re-evaluate legal moves each depth
        legal_moves = _get_legal_moves(you, opponent)
        if not legal_moves:
            return "pass"

        ordered = sorted(legal_moves.keys(), key=_move_sort_key)
        local_best_move = None
        local_best_score = -1e20
        alpha = -1e20
        beta = 1e20

        for m in ordered:
            flips = legal_moves[m]
            new_you, new_opp = _apply_move(you, opponent, m, flips)
            score = alphabeta(new_you, new_opp, current_depth - 1, alpha, beta, False, False)
            if score > local_best_score or local_best_move is None:
                local_best_score = score
                local_best_move = m
            if score > alpha:
                alpha = score
            # time cutoff
            if time.time() - start_time > _TIME_LIMIT:
                break

        # adopt local best if we have one
        if local_best_move is not None:
            best_move = local_best_move
            best_score = local_best_score

        # break if out of time
        if time.time() - start_time > _TIME_LIMIT:
            break

        current_depth += 1

    # Fallback if nothing found (shouldn't happen because we checked legal moves)
    if best_move is None:
        best_move = ordered_moves[0]

    r, c = best_move
    return _coords_to_move(r, c)
