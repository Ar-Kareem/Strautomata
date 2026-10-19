
import numpy as np
from collections import deque

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    # Convert pieces to sets for faster lookups
    my_pieces = set(me)
    opp_pieces = set(opp)

    # Determine direction based on color
    direction = 1 if color == 'w' else -1
    opponent_home_row = 7 if color == 'w' else 0

    # Generate all legal moves
    legal_moves = generate_legal_moves(my_pieces, opp_pieces, direction)

    if not legal_moves:
        # Should not happen in Breakthrough, but return a dummy move if no moves
        return ((0, 0), (0, 0))

    # Evaluate each move using minimax with alpha-beta pruning
    best_move = None
    best_score = -float('inf')
    alpha = -float('inf')
    beta = float('inf')

    # Order moves to prioritize captures, promotions, and center control
    ordered_moves = order_moves(legal_moves, my_pieces, opp_pieces, direction, opponent_home_row)

    for move in ordered_moves:
        from_row, from_col = move[0]
        to_row, to_col = move[1]

        # Simulate the move
        new_my_pieces = my_pieces.copy()
        new_my_pieces.remove((from_row, from_col))
        new_my_pieces.add((to_row, to_col))

        new_opp_pieces = opp_pieces.copy()
        if (to_row, to_col) in opp_pieces:
            new_opp_pieces.remove((to_row, to_col))

        # Evaluate the new position
        score = -minimax(
            new_opp_pieces, new_my_pieces, color, -beta, -alpha, depth=3, direction=direction,
            opponent_home_row=opponent_home_row
        )

        if score > best_score:
            best_score = score
            best_move = move
            alpha = max(alpha, score)

    return best_move

def generate_legal_moves(my_pieces, opp_pieces, direction):
    legal_moves = []
    for (row, col) in my_pieces:
        # Forward move (straight)
        new_row = row + direction
        if 0 <= new_row < 8 and (new_row, col) not in my_pieces and (new_row, col) not in opp_pieces:
            legal_moves.append(((row, col), (new_row, col)))

        # Diagonal captures
        for dc in [-1, 1]:
            new_row = row + direction
            new_col = col + dc
            if 0 <= new_row < 8 and 0 <= new_col < 8 and (new_row, new_col) in opp_pieces:
                legal_moves.append(((row, col), (new_row, new_col)))

        # Diagonal non-captures (if allowed)
        for dc in [-1, 1]:
            new_row = row + direction
            new_col = col + dc
            if 0 <= new_row < 8 and 0 <= new_col < 8 and (new_row, new_col) not in my_pieces and (new_row, new_col) not in opp_pieces:
                legal_moves.append(((row, col), (new_row, new_col)))

    return legal_moves

def order_moves(moves, my_pieces, opp_pieces, direction, opponent_home_row):
    # Prioritize captures, promotions, and center control
    ordered = []
    captures = []
    promotions = []
    others = []

    for move in moves:
        from_row, from_col = move[0]
        to_row, to_col = move[1]

        # Check if it's a capture
        if (to_row, to_col) in opp_pieces:
            captures.append(move)
        # Check if it's a promotion
        elif to_row == opponent_home_row:
            promotions.append(move)
        else:
            others.append(move)

    # Order captures by how many opponent pieces are adjacent (to reduce opponent mobility)
    captures.sort(key=lambda m: -len(get_adjacent_opp_pieces(m[1], opp_pieces, direction)))
    promotions.sort(key=lambda m: -abs(m[1][1] - 3.5))  # Prefer center promotions
    others.sort(key=lambda m: -abs(m[1][1] - 3.5))  # Prefer center moves

    return captures + promotions + others

def get_adjacent_opp_pieces(pos, opp_pieces, direction):
    row, col = pos
    adjacent = []
    for dr, dc in [(direction, -1), (direction, 1), (0, -1), (0, 1)]:
        new_row = row + dr
        new_col = col + dc
        if 0 <= new_row < 8 and 0 <= new_col < 8 and (new_row, new_col) in opp_pieces:
            adjacent.append((new_row, new_col))
    return adjacent

def minimax(opp_pieces, my_pieces, color, alpha, beta, depth, direction, opponent_home_row):
    if depth == 0 or is_terminal(my_pieces, opp_pieces, opponent_home_row):
        return evaluate_position(my_pieces, opp_pieces, direction, opponent_home_row)

    legal_moves = generate_legal_moves(my_pieces, opp_pieces, direction)
    if not legal_moves:
        return evaluate_position(my_pieces, opp_pieces, direction, opponent_home_row)

    # Order moves for alpha-beta pruning
    ordered_moves = order_moves(legal_moves, my_pieces, opp_pieces, direction, opponent_home_row)

    if color == 'w':
        value = -float('inf')
        for move in ordered_moves:
            from_row, from_col = move[0]
            to_row, to_col = move[1]

            new_my_pieces = my_pieces.copy()
            new_my_pieces.remove((from_row, from_col))
            new_my_pieces.add((to_row, to_col))

            new_opp_pieces = opp_pieces.copy()
            if (to_row, to_col) in opp_pieces:
                new_opp_pieces.remove((to_row, to_col))

            value = max(value, minimax(new_opp_pieces, new_my_pieces, 'b', alpha, beta, depth - 1, direction, opponent_home_row))
            alpha = max(alpha, value)
            if beta <= alpha:
                break
        return value
    else:
        value = float('inf')
        for move in ordered_moves:
            from_row, from_col = move[0]
            to_row, to_col = move[1]

            new_opp_pieces = opp_pieces.copy()
            new_opp_pieces.remove((from_row, from_col))
            new_opp_pieces.add((to_row, to_col))

            new_my_pieces = my_pieces.copy()
            if (to_row, to_col) in my_pieces:
                new_my_pieces.remove((to_row, to_col))

            value = min(value, minimax(new_my_pieces, new_opp_pieces, 'w', alpha, beta, depth - 1, -direction, opponent_home_row))
            beta = min(beta, value)
            if beta <= alpha:
                break
        return value

def evaluate_position(my_pieces, opp_pieces, direction, opponent_home_row):
    score = 0

    # Piece value: closer to opponent's home row is better
    for (row, col) in my_pieces:
        distance = abs(row - opponent_home_row)
        score += 1 + (7 - distance) / 7  # Bonus for pieces closer to promotion

    for (row, col) in opp_pieces:
        distance = abs(row - opponent_home_row)
        score -= 1 + (7 - distance) / 7

    # Mobility: more legal moves is better
    my_mobility = len(generate_legal_moves(my_pieces, opp_pieces, direction))
    opp_mobility = len(generate_legal_moves(opp_pieces, my_pieces, -direction))
    score += 0.1 * (my_mobility - opp_mobility)

    # Center control: prefer pieces in columns 3-4
    for (row, col) in my_pieces:
        center_bonus = 1 - abs(col - 3.5) / 3.5
        score += 0.2 * center_bonus

    for (row, col) in opp_pieces:
        center_bonus = 1 - abs(col - 3.5) / 3.5
        score -= 0.2 * center_bonus

    return score

def is_terminal(my_pieces, opp_pieces, opponent_home_row):
    # Check if any of my pieces reached opponent's home row
    for (row, col) in my_pieces:
        if row == opponent_home_row:
            return True

    # Check if opponent has no pieces left
    if not opp_pieces:
        return True

    return False
