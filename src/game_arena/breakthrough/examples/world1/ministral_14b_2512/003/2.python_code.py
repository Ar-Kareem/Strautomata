
import numpy as np
from collections import deque

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    Policy for Breakthrough using depth-limited minimax with alpha-beta pruning.
    """
    # Convert pieces to sets for faster lookups
    my_pieces = set(me)
    opp_pieces = set(opp)

    # Determine direction based on color
    direction = 1 if color == 'w' else -1
    opponent_home_row = 0 if color == 'w' else 7

    # Generate all legal moves
    legal_moves = generate_legal_moves(my_pieces, opp_pieces, direction)

    if not legal_moves:
        # Should not happen per problem statement, but handle gracefully
        return ((0, 0), (0, 0))

    # Evaluate all legal moves using minimax with alpha-beta pruning
    best_move = None
    best_score = -float('inf')
    alpha = -float('inf')
    beta = float('inf')

    # Sort moves to prioritize captures and promotions
    legal_moves_sorted = sort_moves(legal_moves, my_pieces, opp_pieces, direction, opponent_home_row)

    for move in legal_moves_sorted:
        from_row, from_col = move[0]
        to_row, to_col = move[1]

        # Simulate the move
        new_my_pieces = my_pieces.copy()
        new_opp_pieces = opp_pieces.copy()
        new_my_pieces.remove((from_row, from_col))
        new_my_pieces.add((to_row, to_col))

        # Check if it's a capture
        if (to_row, to_col) in opp_pieces:
            new_opp_pieces.remove((to_row, to_col))

        # Evaluate the new position
        score = minimax(
            new_my_pieces, new_opp_pieces, direction, opponent_home_row,
            alpha, beta, depth=3, is_maximizing=False
        )

        # Update best move
        if score > best_score:
            best_score = score
            best_move = move
            alpha = max(alpha, score)

    return best_move

def generate_legal_moves(my_pieces, opp_pieces, direction):
    """Generate all legal moves for the current position."""
    legal_moves = []

    for (row, col) in my_pieces:
        # Forward move (straight)
        forward_row = row + direction
        if 0 <= forward_row < 8 and (forward_row, col) not in my_pieces and (forward_row, col) not in opp_pieces:
            legal_moves.append(((row, col), (forward_row, col)))

        # Diagonal moves (left and right)
        for dc in [-1, 1]:
            diag_row = row + direction
            diag_col = col + dc
            if 0 <= diag_row < 8 and 0 <= diag_col < 8:
                target = (diag_row, diag_col)
                if target not in my_pieces:
                    if target in opp_pieces:
                        # Capture
                        legal_moves.append(((row, col), target))
                    else:
                        # Diagonal move
                        legal_moves.append(((row, col), target))

    return legal_moves

def sort_moves(moves, my_pieces, opp_pieces, direction, opponent_home_row):
    """Sort moves by priority: captures, promotions, mobility, central control."""
    def move_key(move):
        from_row, from_col = move[0]
        to_row, to_col = move[1]

        # Priority 1: Captures
        if (to_row, to_col) in opp_pieces:
            return (0, 0)  # Higher priority

        # Priority 2: Promotions
        if to_row == opponent_home_row:
            return (1, 0)

        # Priority 3: Mobility (how many new moves this creates)
        mobility_gain = 0
        for (r, c) in my_pieces:
            if (r, c) == (from_row, from_col):
                continue
            # Check if the new position enables new moves for other pieces
            # (Simplified: just count potential moves from the new position)
            pass  # Placeholder for mobility calculation

        # Priority 4: Central control (prefer moves toward center)
        center_score = abs(to_col - 3.5) + abs(to_row - 3.5)
        return (2, center_score)

    return sorted(moves, key=move_key)

def minimax(my_pieces, opp_pieces, direction, opponent_home_row, alpha, beta, depth, is_maximizing):
    """Minimax with alpha-beta pruning."""
    if depth == 0 or is_game_over(my_pieces, opp_pieces, direction, opponent_home_row):
        return evaluate_position(my_pieces, opp_pieces, direction, opponent_home_row)

    if is_maximizing:
        max_eval = -float('inf')
        for move in generate_legal_moves(my_pieces, opp_pieces, direction):
            new_my_pieces = my_pieces.copy()
            new_opp_pieces = opp_pieces.copy()
            from_row, from_col = move[0]
            to_row, to_col = move[1]
            new_my_pieces.remove((from_row, from_col))
            new_my_pieces.add((to_row, to_col))
            if (to_row, to_col) in opp_pieces:
                new_opp_pieces.remove((to_row, to_col))
            eval = minimax(new_my_pieces, new_opp_pieces, direction, opponent_home_row, alpha, beta, depth - 1, False)
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in generate_legal_moves(opp_pieces, my_pieces, -direction):
            new_my_pieces = my_pieces.copy()
            new_opp_pieces = opp_pieces.copy()
            from_row, from_col = move[0]
            to_row, to_col = move[1]
            new_opp_pieces.remove((from_row, from_col))
            new_opp_pieces.add((to_row, to_col))
            if (to_row, to_col) in my_pieces:
                new_my_pieces.remove((to_row, to_col))
            eval = minimax(new_my_pieces, new_opp_pieces, direction, opponent_home_row, alpha, beta, depth - 1, True)
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval

def evaluate_position(my_pieces, opp_pieces, direction, opponent_home_row):
    """Evaluate the position using heuristics."""
    score = 0

    # Promoted pieces
    for (row, col) in my_pieces:
        if row == opponent_home_row:
            score += 1000
    for (row, col) in opp_pieces:
        if row == opponent_home_row:
            score -= 1000

    # Mobility (number of legal moves)
    score += len(generate_legal_moves(my_pieces, opp_pieces, direction))
    score -= len(generate_legal_moves(opp_pieces, my_pieces, -direction))

    # Central control
    for (row, col) in my_pieces:
        center_score = abs(col - 3.5) + abs(row - 3.5)
        score += (4 - center_score) * 0.5  # Prefer center
    for (row, col) in opp_pieces:
        center_score = abs(col - 3.5) + abs(row - 3.5)
        score -= (4 - center_score) * 0.5

    # Threat to opponent pieces
    for (row, col) in my_pieces:
        for dc in [-1, 1]:
            diag_row = row + direction
            diag_col = col + dc
            if 0 <= diag_row < 8 and 0 <= diag_col < 8 and (diag_row, diag_col) in opp_pieces:
                score += 50  # Threat bonus

    return score

def is_game_over(my_pieces, opp_pieces, direction, opponent_home_row):
    """Check if the game is over (win or loss)."""
    # Check for promotions
    for (row, col) in my_pieces:
        if row == opponent_home_row:
            return True
    for (row, col) in opp_pieces:
        if row == opponent_home_row:
            return True

    # Check if opponent has no pieces left
    if not opp_pieces:
        return True

    return False
