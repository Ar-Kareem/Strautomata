
import random
from typing import List, Tuple, Optional

def policy(my_men: List[Tuple[int, int]], my_kings: List[Tuple[int, int]],
           opp_men: List[Tuple[int, int]], opp_kings: List[Tuple[int, int]],
           color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """
    Checkers AI policy that returns the best move based on the current board state.
    Always returns a legal move, prioritizing captures when available.
    """

    # Combine all pieces for easier access
    my_pieces = my_men + my_kings
    opp_pieces = opp_men + opp_kings
    all_pieces = my_pieces + opp_pieces

    # Determine direction based on color
    direction = 1 if color == 'w' else -1

    # First check for mandatory captures
    capture_moves = get_all_capture_moves(my_men, my_kings, opp_men, opp_kings, color, all_pieces)
    if capture_moves:
        # Evaluate and return the best capture move
        best_move = evaluate_capture_moves(capture_moves, my_men, my_kings, opp_men, opp_kings, color)
        return best_move

    # If no captures, find all possible moves
    all_moves = get_all_possible_moves(my_men, my_kings, opp_pieces, color, all_pieces)

    if not all_moves:
        # This shouldn't happen as the game would be over, but return a random move if needed
        return random.choice([((p[0], p[1]), (p[0]+direction, p[1]+1)) for p in my_men if is_valid_move(p, (p[0]+direction, p[1]+1), my_pieces, opp_pieces, color)])

    # Evaluate and return the best non-capture move
    best_move = evaluate_regular_moves(all_moves, my_men, my_kings, opp_men, opp_kings, color)
    return best_move

def get_all_capture_moves(my_men: List[Tuple[int, int]], my_kings: List[Tuple[int, int]],
                         opp_men: List[Tuple[int, int]], opp_kings: List[Tuple[int, int]],
                         color: str, all_pieces: List[Tuple[int, int]]) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
    """
    Get all possible capture moves for the current player.
    Returns a list of (from, to) tuples representing capture moves.
    """
    captures = []
    direction = 1 if color == 'w' else -1

    # Check captures for regular pieces
    for piece in my_men:
        row, col = piece
        # Check all four diagonal directions for potential captures
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            # Calculate the square to jump over and the landing square
            jump_row, jump_col = row + dr, col + dc
            land_row, land_col = row + 2*dr, col + 2*dc

            # Check if the jump is valid
            if (0 <= land_row < 8 and 0 <= land_col < 8 and
                (jump_row, jump_col) in opp_pieces and
                (land_row, land_col) not in all_pieces and
                is_dark_square(land_row, land_col)):

                # For regular pieces, they can only move forward (unless capturing)
                if (color == 'w' and dr == -1) or (color == 'b' and dr == 1):
                    continue

                captures.append(((row, col), (land_row, land_col)))

    # Check captures for kings (can move in any direction)
    for piece in my_kings:
        row, col = piece
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            jump_row, jump_col = row + dr, col + dc
            land_row, land_col = row + 2*dr, col + 2*dc

            if (0 <= land_row < 8 and 0 <= land_col < 8 and
                (jump_row, jump_col) in opp_pieces and
                (land_row, land_col) not in all_pieces and
                is_dark_square(land_row, land_col)):

                captures.append(((row, col), (land_row, land_col)))

    return captures

def get_all_possible_moves(my_men: List[Tuple[int, int]], my_kings: List[Tuple[int, int]],
                          opp_pieces: List[Tuple[int, int]], color: str,
                          all_pieces: List[Tuple[int, int]]) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
    """
    Get all possible non-capture moves for the current player.
    """
    moves = []
    direction = 1 if color == 'w' else -1

    # Regular pieces can only move forward
    for piece in my_men:
        row, col = piece
        for dc in [-1, 1]:
            new_row = row + direction
            new_col = col + dc
            if (0 <= new_row < 8 and 0 <= new_col < 8 and
                (new_row, new_col) not in all_pieces and
                is_dark_square(new_row, new_col)):
                moves.append(((row, col), (new_row, new_col)))

    # Kings can move in any direction
    for piece in my_kings:
        row, col = piece
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            new_row = row + dr
            new_col = col + dc
            if (0 <= new_row < 8 and 0 <= new_col < 8 and
                (new_row, new_col) not in all_pieces and
                is_dark_square(new_row, new_col)):
                moves.append(((row, col), (new_row, new_col)))

    return moves

def evaluate_capture_moves(captures: List[Tuple[Tuple[int, int], Tuple[int, int]]],
                          my_men: List[Tuple[int, int]], my_kings: List[Tuple[int, int]],
                          opp_men: List[Tuple[int, int]], opp_kings: List[Tuple[int, int]],
                          color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """
    Evaluate capture moves and return the best one.
    """
    if not captures:
        return None

    # Simple evaluation: prefer moves that capture more pieces or promote to king
    best_move = None
    best_score = -float('inf')

    for move in captures:
        from_pos, to_pos = move
        score = 0

        # Check if this move promotes to king
        if (color == 'w' and to_pos[0] == 7) or (color == 'b' and to_pos[0] == 0):
            score += 10  # High value for promotion

        # Check if the captured piece is a king (more valuable)
        jump_row = (from_pos[0] + to_pos[0]) // 2
        jump_col = (from_pos[1] + to_pos[1]) // 2
        if (jump_row, jump_col) in opp_kings:
            score += 5
        else:
            score += 3

        # Prefer moves that move toward center
        center_dist = abs(to_pos[0] - 3.5) + abs(to_pos[1] - 3.5)
        score += (7 - center_dist)  # Max 7 when at center

        if score > best_score:
            best_score = score
            best_move = move

    return best_move if best_move else random.choice(captures)

def evaluate_regular_moves(moves: List[Tuple[Tuple[int, int], Tuple[int, int]]],
                          my_men: List[Tuple[int, int]], my_kings: List[Tuple[int, int]],
                          opp_men: List[Tuple[int, int]], opp_kings: List[Tuple[int, int]],
                          color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """
    Evaluate non-capture moves and return the best one.
    """
    if not moves:
        return None

    best_move = None
    best_score = -float('inf')

    for move in moves:
        from_pos, to_pos = move
        score = 0

        # Check if this move promotes to king
        if (color == 'w' and to_pos[0] == 7) or (color == 'b' and to_pos[0] == 0):
            score += 20  # Very high priority for promotion

        # Prefer moving kings over regular pieces
        if from_pos in my_kings:
            score += 2

        # Prefer moves that advance toward opponent's side
        direction = 1 if color == 'w' else -1
        if color == 'w':
            score += (to_pos[0] - from_pos[0]) * 2
        else:
            score += (from_pos[0] - to_pos[0]) * 2

        # Prefer moves toward center
        center_dist = abs(to_pos[0] - 3.5) + abs(to_pos[1] - 3.5)
        score += (7 - center_dist)

        # Avoid moving to squares that might be vulnerable
        # (simple check: don't move next to opponent's pieces if they can capture next turn)
        vulnerable = False
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            adj_row, adj_col = to_pos[0] + dr, to_pos[1] + dc
            if (0 <= adj_row < 8 and 0 <= adj_col < 8 and
                (adj_row, adj_col) in opp_pieces):
                # Check if opponent could capture from this adjacent square
                behind_row, behind_col = to_pos[0] + 2*dr, to_pos[1] + 2*dc
                if (0 <= behind_row < 8 and 0 <= behind_col < 8 and
                    (behind_row, behind_col) not in my_men and
                    (behind_row, behind_col) not in my_kings):
                    vulnerable = True
                    break

        if not vulnerable:
            score += 3

        if score > best_score:
            best_score = score
            best_move = move

    return best_move if best_move else random.choice(moves)

def is_dark_square(row: int, col: int) -> bool:
    """Check if a square is dark (playable) in checkers."""
    return (row + col) % 2 == 1

def is_valid_move(from_pos: Tuple[int, int], to_pos: Tuple[int, int],
                 my_pieces: List[Tuple[int, int]], opp_pieces: List[Tuple[int, int]],
                 color: str) -> bool:
    """Check if a move is valid (basic validation)."""
    from_row, from_col = from_pos
    to_row, to_col = to_pos

    # Check if moving to an adjacent diagonal square
    row_diff = abs(to_row - from_row)
    col_diff = abs(to_col - from_col)

    if row_diff != 1 or col_diff != 1:
        return False

    # Check if destination is empty
    if to_pos in my_pieces or to_pos in opp_pieces:
        return False

    # Check if moving in the correct direction for regular pieces
    if from_pos not in my_kings:
        if color == 'w' and to_row < from_row:
            return False
        if color == 'b' and to_row > from_row:
            return False

    return True
