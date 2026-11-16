
import random
from typing import List, Tuple

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    # Determine direction of movement (1 for white, -1 for black)
    direction = 1 if color == 'w' else -1
    my_home_row = 0 if color == 'w' else 7
    opp_home_row = 7 if color == 'w' else 0

    # Check if I already won (should not happen per problem statement)
    if any(row == opp_home_row for (row, col) in me):
        return ((0, 0), (0, 0))  # Dummy move (game already won)

    # Precompute all possible moves for my pieces
    my_moves = []
    for (row, col) in me:
        # Possible forward moves (straight or diagonal)
        forward_straight = (row + direction, col)
        forward_diag_left = (row + direction, col - 1)
        forward_diag_right = (row + direction, col + 1)

        # Check if moves are within bounds
        moves = []
        if 0 <= forward_straight[0] <= 7 and 0 <= forward_straight[1] <= 7:
            moves.append(forward_straight)
        if 0 <= forward_diag_left[0] <= 7 and 0 <= forward_diag_left[1] <= 7:
            moves.append(forward_diag_left)
        if 0 <= forward_diag_right[0] <= 7 and 0 <= forward_diag_right[1] <= 7:
            moves.append(forward_diag_right)

        # Check for captures (diagonal moves onto opponent pieces)
        captures = []
        for (opp_row, opp_col) in opp:
            if (row + direction, opp_col) == (opp_row, opp_col):
                captures.append(((row, col), (opp_row, opp_col)))
            if (row + direction, col - 1) == (opp_row, opp_col):
                captures.append(((row, col), (opp_row, opp_col)))
            if (row + direction, col + 1) == (opp_row, opp_col):
                captures.append(((row, col), (opp_row, opp_col)))

        my_moves.append((moves, captures))

    # --- Phase 1: Check for opponent's immediate threats ---
    # Opponent piece is one move away from promotion (row 6 for white, row 1 for black)
    opp_imminent_promotion_row = 6 if color == 'w' else 1
    opp_pieces_one_away = [(row, col) for (row, col) in opp if row == opp_imminent_promotion_row]

    # Opponent piece is in my home row (must capture)
    opp_pieces_in_my_home = [(row, col) for (row, col) in opp if row == my_home_row]

    # If opponent can promote next turn, capture the piece blocking promotion
    if opp_pieces_one_away:
        for (i, (moves, captures)) in enumerate(my_moves):
            for (from_row, from_col), (to_row, to_col) in captures:
                if (to_row, to_col) in opp_pieces_one_away:
                    return ((from_row, from_col), (to_row, to_col))
    # If opponent has pieces in my home row, capture them
    elif opp_pieces_in_my_home:
        for (i, (moves, captures)) in enumerate(my_moves):
            for (from_row, from_col), (to_row, to_col) in captures:
                if (to_row, to_col) in opp_pieces_in_my_home:
                    return ((from_row, from_col), (to_row, to_col))

    # --- Phase 2: Evaluate captures ---
    # Score captures based on:
    # 1. Does the capture unblock a path to promotion?
    # 2. Is the captured piece near the opponent's home row?
    # 3. Is the capture near the center?
    def capture_score(from_row, from_col, to_row, to_col):
        # Check if the captured piece is in the opponent's home row (unlikely, but possible)
        if to_row == opp_home_row:
            return 100  # Highest priority

        # Check if the captured piece is blocking a path to promotion
        # For white: if captured piece is in row 6, and my piece can now move to row 7
        if color == 'w':
            if to_row == 6 and (from_row + 1, from_col) not in opp and (from_row + 1, from_col) in [(r, c) for (r, c) in me if r == from_row + 2]:
                return 50  # Unblocking promotion
        else:  # For black
            if to_row == 1 and (from_row - 1, from_col) not in opp and (from_row - 1, from_col) in [(r, c) for (r, c) in me if r == from_row - 2]:
                return 50  # Unblocking promotion

        # Central control bonus (columns 3-4)
        center_bonus = 10 if 3 <= to_col <= 4 else 5
        return center_bonus

    # Find the best capture
    best_capture = None
    best_score = -1
    for (i, (moves, captures)) in enumerate(my_moves):
        for (from_row, from_col), (to_row, to_col) in captures:
            score = capture_score(from_row, from_col, to_row, to_col)
            if score > best_score:
                best_score = score
                best_capture = ((from_row, from_col), (to_row, to_col))

    if best_capture:
        return best_capture

    # --- Phase 3: Evaluate forward moves ---
    # Score moves based on:
    # 1. Does the move lead to promotion?
    # 2. Is the move near the center?
    def move_score(from_row, from_col, to_row, to_col):
        # Promotion score (highest priority)
        if to_row == opp_home_row:
            return 100

        # Central control bonus (columns 3-4)
        center_bonus = 10 if 3 <= to_col <= 4 else 5
        return center_bonus

    # Find the best forward move
    best_move = None
    best_score = -1
    for (i, (moves, captures)) in enumerate(my_moves):
        for move in moves:
            from_row, from_col = me[i]
            to_row, to_col = move
            score = move_score(from_row, from_col, to_row, to_col)
            if score > best_score:
                best_score = score
                best_move = ((from_row, from_col), (to_row, to_col))

    if best_move:
        return best_move

    # --- Phase 4: Defensive and positional play ---
    # If no captures or promotions, try to move pieces to unblock others or improve position
    for (i, (moves, captures)) in enumerate(my_moves):
        if moves:  # If there are possible moves
            from_row, from_col = me[i]
            # Prefer diagonal moves to create paths or avoid being blocked
            for move in moves:
                if move[0] != from_row:  # Diagonal move
                    return ((from_row, from_col), move)

    # --- Phase 5: Fallback to random legal move ---
    # If all else fails, pick a random legal move
    all_legal_moves = []
    for (i, (moves, captures)) in enumerate(my_moves):
        from_row, from_col = me[i]
        for move in moves:
            all_legal_moves.append(((from_row, from_col), move))
        for (from_row, from_col), (to_row, to_col) in captures:
            all_legal_moves.append(((from_row, from_col), (to_row, to_col)))

    if all_legal_moves:
        return random.choice(all_legal_moves)
    else:
        return ((0, 0), (0, 0))  # Dummy move (should not happen)
