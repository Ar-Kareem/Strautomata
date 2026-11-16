
import random
import numpy as np

def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    # Directions for movement (down for black, up for white)
    directions = {
        'b': [(1, 1), (1, -1)],  # Black moves downward
        'w': [(-1, 1), (-1, -1)]  # White moves upward
    }
    king_directions = {
        'b': [(1, 1), (1, -1), (-1, 1), (-1, -1)],  # Black kings can move in all 4 diagonal directions
        'w': [(-1, 1), (-1, -1), (1, 1), (1, -1)]   # White kings can move in all 4 diagonal directions
    }

    # Check if a square is on the board
    def is_valid_square(row, col):
        return 0 <= row < 8 and 0 <= col < 8 and (row + col) % 2 == 1  # Only dark squares

    # Check if a move is legal (non-capture)
    def is_legal_move(from_row, from_col, to_row, to_col, is_king):
        dr = to_row - from_row
        dc = to_col - from_col
        if is_king:
            return abs(dr) == 1 and abs(dc) == 1
        else:
            return (dr, dc) in directions[color]

    # Check if a capture is legal
    def is_legal_capture(from_row, from_col, to_row, to_col, is_king):
        dr = to_row - from_row
        dc = to_col - from_col
        if is_king:
            return abs(dr) == 2 and abs(dc) == 2
        else:
            return abs(dr) == 2 and abs(dc) == 2 and (dr, dc) in [(2*d[0], 2*d[1]) for d in directions[color]]

    # Get all opponent pieces (men and kings)
    opp_pieces = opp_men + opp_kings

    # Generate all possible captures
    captures = []
    for piece in my_men + my_kings:
        from_row, from_col = piece
        is_king = piece in my_kings
        for dr, dc in king_directions[color] if is_king else directions[color]:
            to_row, to_col = from_row + dr, from_col + dc
            if not is_valid_square(to_row, to_col):
                continue
            # Check if the jump lands on an opponent's piece
            jump_row, jump_col = (from_row + dr // 2, from_col + dc // 2)
            if (jump_row, jump_col) in opp_pieces and is_legal_capture(from_row, from_col, to_row, to_col, is_king):
                captures.append(((from_row, from_col), (to_row, to_col)))

    # If captures are available, evaluate and choose the best one
    if captures:
        best_capture = None
        best_score = -float('inf')
        for move in captures:
            from_row, from_col = move[0]
            to_row, to_col = move[1]
            score = evaluate_capture(from_row, from_col, to_row, to_col, is_king=(from_row, from_col) in my_kings)
            if score > best_score:
                best_score = score
                best_capture = move
        return best_capture

    # If no captures, generate all possible regular moves
    moves = []
    for piece in my_men + my_kings:
        from_row, from_col = piece
        is_king = piece in my_kings
        for dr, dc in king_directions[color] if is_king else directions[color]:
            to_row, to_col = from_row + dr, from_col + dc
            if is_valid_square(to_row, to_col) and is_legal_move(from_row, from_col, to_row, to_col, is_king):
                moves.append(((from_row, from_col), (to_row, to_col)))

    # Evaluate and choose the best regular move
    best_move = None
    best_score = -float('inf')
    for move in moves:
        from_row, from_col = move[0]
        to_row, to_col = move[1]
        score = evaluate_move(from_row, from_col, to_row, to_col, is_king=(from_row, from_col) in my_kings)
        if score > best_score:
            best_score = score
            best_move = move
        elif score == best_score:
            # Randomly choose among equally good moves
            if random.random() < 0.5:
                best_move = move
    return best_move

def evaluate_capture(from_row, from_col, to_row, to_col, is_king):
    # Material advantage: capturing an opponent's piece is good
    score = 10  # Base score for a capture

    # Positional value: prefer captures that threaten opponent's kings or control center
    center_control = abs(4 - from_row) + abs(4 - from_col) + abs(4 - to_row) + abs(4 - to_col)
    score += 5 - center_control / 10  # Prefer center control

    # King safety: avoid leaving kings exposed
    if is_king:
        score += 2  # Kings are more valuable

    # Promote if reaching opponent's back row
    if (color == 'b' and to_row == 7) or (color == 'w' and to_row == 0):
        score += 10  # Promote to king

    return score

def evaluate_move(from_row, from_col, to_row, to_col, is_king):
    score = 0

    # Positional value: prefer moving towards center or opponent's back row
    center_distance = abs(4 - from_row) + abs(4 - from_col)
    back_row_distance = (7 - to_row) if color == 'b' else (to_row)
    score += (8 - center_distance) / 10  # Prefer center
    score += back_row_distance / 10  # Prefer moving towards opponent's back row

    # King development: promote men to kings early
    if not is_king and ((color == 'b' and to_row == 7) or (color == 'w' and to_row == 0)):
        score += 20  # High priority for promotion

    # King safety: avoid moving kings into danger
    if is_king:
        # Check if the move leaves the king vulnerable to captures
        # (Simplified: avoid moving kings to squares where they can be captured next turn)
        pass  # More complex logic can be added here

    return score
