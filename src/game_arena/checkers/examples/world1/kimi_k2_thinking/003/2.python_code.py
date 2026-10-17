
import itertools
import time
from typing import List, Tuple, Set

# ----------------------------------------------------------------------
# Helper functions for board manipulation and move generation
# ----------------------------------------------------------------------
def in_board(pos: Tuple[int, int]) -> bool:
    r, c = pos
    return 0 <= r < 8 and 0 <= c < 8

def is_promotion_row(pos: Tuple[int, int], color: str) -> bool:
    r = pos[0]
    if color == 'b':
        return r == 0
    else:
        return r == 7

def get_directions(piece_type: str, color: str) -> List[Tuple[int, int]]:
    if piece_type == 'man':
        dr = -1 if color == 'b' else 1
        return [(dr, -1), (dr, 1)]
    else:  # king
        return [(-1, -1), (-1, 1), (1, -1), (1, 1)]

def get_pieces(board_state: Tuple[Set, Set, Set, Set], color: str):
    b_men, b_kings, w_men, w_kings = board_state
    if color == 'b':
        return b_men, b_kings, w_men, w_kings
    else:
        return w_men, w_kings, b_men, b_kings

def generate_jumps_for_piece(
    start_pos: Tuple[int, int],
    piece_type: str,
    board_state: Tuple[Set, Set, Set, Set],
    color: str
) -> List[Tuple[Tuple[int, int], Tuple[int, int], Set]]:
    my_men, my_kings, opp_men, opp_kings = get_pieces(board_state, color)
    opp_pieces = opp_men | opp_kings
    directions = get_directions(piece_type, color)
    moves = []

    def recurse(cur_pos, cur_type, captured_set):
        for dr, dc in directions:
            adj = (cur_pos[0] + dr, cur_pos[1] + dc)
            if not in_board(adj):
                continue
            if adj not in opp_pieces:
                continue
            if adj in captured_set:
                continue
            landing = (cur_pos[0] + 2 * dr, cur_pos[1] + 2 * dc)
            if not in_board(landing):
                continue
            # landing must be empty
            if landing in my_men or landing in my_kings or landing in opp_men or landing in opp_kings:
                continue
            new_captured = captured_set | {adj}
            new_type = cur_type
            if cur_type == 'man' and is_promotion_row(landing, color):
                new_type = 'king'
            moves.append((start_pos, landing, new_captured))
            recurse(landing, new_type, new_captured)

    recurse(start_pos, piece_type, set())
    return moves

def generate_non_capture_moves_for_piece(
    start_pos: Tuple[int, int],
    piece_type: str,
    board_state: Tuple[Set, Set, Set, Set],
    color: str
) -> List[Tuple[Tuple[int, int], Tuple[int, int], Set]]:
    my_men, my_kings, opp_men, opp_kings = get_pieces(board_state, color)
    all_pieces = my_men | my_kings | opp_men | opp_kings
    directions = get_directions(piece_type, color)
    moves = []
    for dr, dc in directions:
        landing = (start_pos[0] + dr, start_pos[1] + dc)
        if not in_board(landing):
            continue
        if landing in all_pieces:
            continue
        moves.append((start_pos, landing, set()))
    return moves

def generate_moves(
    board_state: Tuple[Set, Set, Set, Set],
    color: str
) -> List[Tuple[Tuple[int, int], Tuple[int, int], Set]]:
    my_men, my_kings, opp_men, opp_kings = get_pieces(board_state, color)
    capture_moves = []
    for pos in my_men:
        capture_moves.extend(generate_jumps_for_piece(pos, 'man', board_state, color))
    for pos in my_kings:
        capture_moves.extend(generate_jumps_for_piece(pos, 'king', board_state, color))
    if capture_moves:
        return capture_moves
    # non‑capture moves
    non_capture = []
    for pos in my_men:
        non_capture.extend(generate_non_capture_moves_for_piece(pos, 'man', board_state, color))
    for pos in my_kings:
        non_capture.extend(generate_non_capture_moves_for_piece(pos, 'king', board_state, color))
    return non_capture

def apply_move(
    board_state: Tuple[Set, Set, Set, Set],
    color: str,
    move: Tuple[Tuple[int, int], Tuple[int, int], Set]
) -> Tuple[Set, Set, Set, Set]:
    b_men, b_kings, w_men, w_kings = board_state
    from_pos, to_pos, captured = move
    if color == 'b':
        my_men, my_kings, opp_men, opp_kings = b_men, b_kings, w_men, w_kings
    else:
        my_men, my_kings, opp_men, opp_kings = w_men, w_kings, b_men, b_kings

    # remove moving piece
    if from_pos in my_men:
        piece_type = 'man'
        my_men = my_men - {from_pos}
    else:
        piece_type = 'king'
        my_kings = my_kings - {from_pos}

    # remove captured opponent pieces
    for cap in captured:
        if cap in opp_men:
            opp_men = opp_men - {cap}
        else:
            opp_kings = opp_kings - {cap}

    # promotion
    new_type = piece_type
    if piece_type == 'man' and is_promotion_row(to_pos, color):
        new_type = 'king'

    # place piece at destination
    if new_type == 'man':
        my_men = my_men | {to_pos}
    else:
        my_kings = my_kings | {to_pos}

    # re‑assemble board tuple
    if color == 'b':
        return (my_men, my_kings, opp_men, opp_kings)
    else:
        return (opp_men, opp_kings, my_men, my_kings)

def evaluate(board_state: Tuple[Set, Set, Set, Set], color: str) -> float:
    b_men, b_kings, w_men, w_kings = board_state
    if color == 'b':
        my_men, my_kings, opp_men, opp_kings = b_men, b_kings, w_men, w_kings
    else:
        my_men, my_kings, opp_men, opp_kings = w_men, w_kings, b_men, b_kings

    # material
    score = (len(my_men) - len(opp_men)) + 3 * (len(my_kings) - len(opp_kings))

    # central squares bonus
    central = {(3, 3), (3, 4), (4, 3), (4, 4)}
    central_bonus = 0.0
    for sq in my_men | my_kings:
        if sq in central:
            central_bonus += 0.1
    for sq in opp_men | opp_kings:
        if sq in central:
            central_bonus -= 0.1

    # advancement bonus
    advancement = 0.0
    if color == 'b':
        for r, c in my_men:
            advancement += (7 - r) * 0.01
        for r, c in opp_men:
            advancement -= (7 - r) * 0.01
    else:
        for r, c in my_men:
            advancement += r * 0.01
        for r, c in opp_men:
            advancement -= r * 0.01

    return score + central_bonus + advancement

def negamax(
    board_state: Tuple[Set, Set, Set, Set],
    color: str,
    depth: int,
    alpha: float,
    beta: float
) -> float:
    if depth == 0:
        return evaluate(board_state, color)
    moves = generate_moves(board_state, color)
    if not moves:
        return -1e6  # loss
    for move in moves:
        new_board = apply_move(board_state, color, move)
        opp_color = 'w' if color == 'b' else 'b'
        score = -negamax(new_board, opp_color, depth - 1, -beta, -alpha)
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break
    return alpha

# ----------------------------------------------------------------------
# Policy API
# ----------------------------------------------------------------------
def policy(my_men, my_kings, opp_men, opp_kings, color) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    # Convert input lists to sets of tuples
    my_men_set = set(map(tuple, my_men))
    my_kings_set = set(map(tuple, my_kings))
    opp_men_set = set(map(tuple, opp_men))
    opp_kings_set = set(map(tuple, opp_kings))

    # Board state as (b_men, b_kings, w_men, w_kings)
    if color == 'b':
        board_state = (my_men_set, my_kings_set, opp_men_set, opp_kings_set)
    else:
        board_state = (opp_men_set, opp_kings_set, my_men_set, my_kings_set)

    moves = generate_moves(board_state, color)
    if not moves:
        # Should never happen under normal play, but return a dummy move to satisfy API.
        return ((0, 0), (0, 0))

    best_move = None
    best_val = -float('inf')
    search_depth = 6

    for move in moves:
        new_board = apply_move(board_state, color, move)
        opp_color = 'w' if color == 'b' else 'b'
        val = -negamax(new_board, opp_color, search_depth - 1, -float('inf'), float('inf'))
        if val > best_val:
            best_val = val
            best_move = move

    # If no best move was selected (unlikely), fall back to first available move.
    if best_move is None:
        best_move = moves[0]

    # Return (from_square, to_square)
    return (best_move[0], best_move[1])
