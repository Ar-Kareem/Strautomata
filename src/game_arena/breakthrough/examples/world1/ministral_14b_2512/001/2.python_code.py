
import numpy as np
from collections import deque

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    # Convert to numpy arrays for easier manipulation
    my_pieces = np.array(me)
    opp_pieces = np.array(opp)

    # Determine direction: +1 for white (moving up), -1 for black (moving down)
    direction = 1 if color == 'w' else -1
    my_home_row = 0 if color == 'b' else 7
    opp_home_row = 7 if color == 'b' else 0

    # Generate all legal moves
    legal_moves = generate_legal_moves(my_pieces, opp_pieces, direction)

    # If any move leads to immediate win, take it
    for move in legal_moves:
        new_me = move_piece(my_pieces, move, direction)
        if any(new_me[:, 0] == opp_home_row):
            return move

    # Evaluate all legal moves using minimax with alpha-beta pruning
    best_move = None
    best_score = -float('inf')
    alpha = -float('inf')
    beta = float('inf')

    for move in legal_moves:
        new_me = move_piece(my_pieces, move, direction)
        new_opp = remove_captured(opp_pieces, move, direction)
        score = minimax(new_me, new_opp, direction, opp_home_row, alpha, beta, depth=3, is_maximizing=False)
        if score > best_score:
            best_score = score
            best_move = move
        alpha = max(alpha, score)
        if beta <= alpha:
            break

    return best_move

def generate_legal_moves(my_pieces, opp_pieces, direction):
    legal_moves = []
    for (r, c) in my_pieces:
        # Forward move (straight)
        new_r = r + direction
        if 0 <= new_r < 8 and (new_r, c) not in opp_pieces:
            legal_moves.append(((r, c), (new_r, c)))

        # Diagonal captures
        for dc in [-1, 1]:
            new_r = r + direction
            new_c = c + dc
            if 0 <= new_r < 8 and 0 <= new_c < 8 and (new_r, new_c) in opp_pieces:
                legal_moves.append(((r, c), (new_r, new_c)))

        # Diagonal non-captures (if adjacent)
        for dc in [-1, 1]:
            new_r = r + direction
            new_c = c + dc
            if 0 <= new_r < 8 and 0 <= new_c < 8 and (new_r, new_c) not in opp_pieces and (new_r, new_c) not in my_pieces:
                legal_moves.append(((r, c), (new_r, new_c)))

    return legal_moves

def move_piece(pieces, move, direction):
    from_r, from_c = move[0]
    to_r, to_c = move[1]
    new_pieces = pieces.copy()
    idx = np.where((new_pieces[:, 0] == from_r) & (new_pieces[:, 1] == from_c))[0]
    if len(idx) > 0:
        new_pieces[idx[0]] = (to_r, to_c)
    return new_pieces

def remove_captured(pieces, move, direction):
    from_r, from_c = move[0]
    to_r, to_c = move[1]
    if to_r != from_r + direction or to_c != from_c + 1 or to_c != from_c - 1:
        return pieces  # Not a capture
    return pieces[~((pieces[:, 0] == to_r) & (pieces[:, 1] == to_c))]

def evaluate(my_pieces, opp_pieces, direction, opp_home_row):
    score = 0

    # Material: prefer fewer opponent pieces
    score += len(my_pieces) * 10
    score -= len(opp_pieces) * 10

    # King potential: pieces closer to opponent's home row are stronger
    for (r, c) in my_pieces:
        distance = abs(r - opp_home_row)
        score += (8 - distance) * 2  # Higher weight for pieces near promotion

    # Mobility: more legal moves = better
    legal_moves = generate_legal_moves(my_pieces, opp_pieces, direction)
    score += len(legal_moves) * 0.5

    # Center control: pieces in columns 3-4 are more valuable
    for (r, c) in my_pieces:
        if 3 <= c <= 4:
            score += 3

    return score

def minimax(my_pieces, opp_pieces, direction, opp_home_row, alpha, beta, depth, is_maximizing):
    if depth == 0 or len(opp_pieces) == 0:
        return evaluate(my_pieces, opp_pieces, direction, opp_home_row)

    legal_moves = generate_legal_moves(my_pieces, opp_pieces, direction)
    if not legal_moves:
        return -float('inf') if is_maximizing else float('inf')

    if is_maximizing:
        max_eval = -float('inf')
        for move in legal_moves:
            new_me = move_piece(my_pieces, move, direction)
            new_opp = remove_captured(opp_pieces, move, direction)
            eval = minimax(new_me, new_opp, direction, opp_home_row, alpha, beta, depth - 1, False)
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in generate_legal_moves(opp_pieces, my_pieces, -direction):
            new_opp = move_piece(opp_pieces, move, -direction)
            new_me = remove_captured(my_pieces, move, -direction)
            eval = minimax(new_me, new_opp, direction, opp_home_row, alpha, beta, depth - 1, True)
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval
