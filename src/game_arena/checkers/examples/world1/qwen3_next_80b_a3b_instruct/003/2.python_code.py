
import numpy as np
from typing import List, Tuple, Set, Dict
import itertools
from functools import lru_cache

def policy(my_men, my_kings, opp_men, opp_kings, color) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """
    Returns the best move for the current player based on minimax with alpha-beta pruning and heuristics.
    """
    # Convert lists to sets for faster lookup
    my_pieces = set(my_men + my_kings)
    opp_pieces = set(opp_men + opp_kings)
    
    # Determine direction: 'b' moves down (row decrease), 'w' moves up (row increase)
    if color == 'b':
        my_men_set = set(my_men)
        my_kings_set = set(my_kings)
        opp_men_set = set(opp_men)
        opp_kings_set = set(opp_kings)
        direction = -1  # black moves downward: row decreases
    else:  # color == 'w'
        my_men_set = set(my_men)
        my_kings_set = set(my_kings)
        opp_men_set = set(opp_men)
        opp_kings_set = set(opp_kings)
        direction = 1   # white moves upward: row increases

    # First, check if any capture moves are available
    capture_moves = find_all_capture_moves(my_men_set, my_kings_set, opp_men_set, opp_kings_set, direction)
    
    if capture_moves:
        # If captures are available, we must choose one of them
        # Evaluate capture sequences using minimax to find the best one
        best_score = float('-inf')
        best_move = capture_moves[0]
        
        for move in capture_moves:
            # For efficiency, we do a shallow search since capture sequences can be long
            # but we prioritize longest capture sequences directly
            score = evaluate_capture_sequence(move, my_men_set, my_kings_set, opp_men_set, opp_kings_set, direction)
            if score > best_score:
                best_score = score
                best_move = move
        
        # If multiple capture sequences with same length, use heuristic to break tie
        # But if we found a sequence with several jumps, we prefer it.
        # We'll do one level of minimax evaluation for capture moves.
        best_move = best_capture_move(my_men_set, my_kings_set, opp_men_set, opp_kings_set, direction, capture_moves)
        return best_move

    # No captures available, use minimax for non-capture moves
    # Generate all legal moves
    all_moves = generate_all_moves(my_men_set, my_kings_set, opp_men_set, opp_kings_set, direction)
    if not all_moves:
        # Shouldn't happen per problem constraints, but defensively return a dummy move
        return ((0, 0), (1, 1))
    
    # Use minimax with alpha-beta pruning for non-capture moves
    best_move = minimax_move(my_men_set, my_kings_set, opp_men_set, opp_kings_set, direction, depth=4)
    return best_move


def find_all_capture_moves(my_men, my_kings, opp_men, opp_kings, direction):
    """
    Returns a list of all possible capture moves, including multi-jump sequences.
    Uses DFS to find all sequences.
    """
    all_sequences = []
    
    # Create a combined set of opponent pieces
    opp_pieces = opp_men | opp_kings

    # Check each of our pieces
    for piece in my_men | my_kings:
        row, col = piece
        # For men, check diagonal forward directions
        if piece in my_men:
            # Regular men: move in direction only
            directions = [(direction, -1), (direction, 1)]  # diagonal forward left/right
        else:
            # Kings: can move in all 4 diagonal directions
            directions = [(1, -1), (1, 1), (-1, -1), (-1, 1)]
        
        for dr, dc in directions:
            # Check if we can jump over an opponent piece
            mid_row, mid_col = row + dr, col + dc
            land_row, land_col = row + 2*dr, col + 2*dc

            # Check bounds
            if not (0 <= mid_row <= 7 and 0 <= mid_col <= 7 and 0 <= land_row <= 7 and 0 <= land_col <= 7):
                continue
                
            # Check if middle square has opponent piece and landing square is empty and dark
            if (mid_row, mid_col) in opp_pieces and (land_row, land_col) not in (my_men | my_kings | opp_pieces):
                # Check if landing square is dark
                if is_dark_square(land_row, land_col):
                    # Found a capture
                    # Generate the move and recurse for multi-jumps
                    capture_sequence = [(piece, (land_row, land_col))]
                    # Now recursively check if further captures are possible from the landing square
                    additional_captures = find_all_capture_moves_from_position(
                        land_row, land_col, my_men, my_kings, opp_men, opp_kings, direction
                    )
                    if additional_captures:
                        for add_seq in additional_captures:
                            extended_sequence = [(piece, (land_row, land_col))] + add_seq
                            all_sequences.append(extended_sequence)
                    else:
                        all_sequences.append(capture_sequence)
    
    # Extract single moves from sequences
    moves = []
    for seq in all_sequences:
        moves.append((seq[0][0], seq[0][1]))  # Only return the first jump step
    return moves


def find_all_capture_moves_from_position(row, col, my_men, my_kings, opp_men, opp_kings, direction):
    """
    Find all capture sequences starting from (row, col) after a capture.
    """
    # Note: This is a helper for recursive capture finding.
    # Since the piece at (row, col) might be a king now (if it was promoted),
    # we need to check if the piece was originally a man and moved to the back rank.
    # But note: the move has already taken place, so we only consider its current state.
    
    # Determine which set the piece belongs to now
    # But since we're in the middle of a sequence, we must simulate the piece's new status.
    current_is_king = (row, col) in my_kings  # this is unreliable in sequence, better to track promotion
    
    # Instead, we simulate: if the piece was a man and is now at the king row, it becomes a king
    if (row, col) in my_men:
        if (color == 'b' and row == 0) or (color == 'w' and row == 7):
            # Promoted to king
            current_is_king = True
        else:
            current_is_king = False
    else:
        current_is_king = True  # was already a king
    
    all_sequences = []
    opp_pieces = opp_men | opp_kings
    
    directions = [(1, -1), (1, 1), (-1, -1), (-1, 1)] if current_is_king else [
        (direction, -1), (direction, 1)
    ]
    
    for dr, dc in directions:
        mid_row, mid_col = row + dr, col + dc
        land_row, land_col = row + 2*dr, col + 2*dc
        
        if not (0 <= mid_row <= 7 and 0 <= mid_col <= 7 and 0 <= land_row <= 7 and 0 <= land_col <= 7):
            continue
            
        if (mid_row, mid_col) in opp_pieces and (land_row, land_col) not in (my_men | my_kings | opp_pieces):
            if is_dark_square(land_row, land_col):
                # We can make this jump
                additional_moves = find_all_capture_moves_from_position(
                    land_row, land_col, my_men, my_kings, opp_men, opp_kings, direction
                )
                if additional_moves:
                    for add_seq in additional_moves:
                        all_sequences.append([((row, col), (land_row, land_col))] + add_seq)
                else:
                    all_sequences.append([((row, col), (land_row, land_col))])
    
    return all_sequences


def is_dark_square(row, col):
    """
    Check if the square (row, col) is dark (playable)
    In checkers, dark squares are where pieces are placed.
    On a standard board: (row + col) % 2 == 1 for dark squares
    Because (0,0) is bottom-left and is dark -> (0+0)%2=0 -> light? 
    But the problem says only dark squares are playable.
    
    Standard checkers: (0,0) is dark? Let's check topology:
    - In standard checkers, the bottom-left is dark.
    - Then (0,0) -> dark, (0,1) -> light, (0,2) -> dark, etc.
    So (row + col) % 2 == 0 -> dark? But (0,0) = 0 -> even -> dark
    So yes: dark if (row + col) % 2 == 0
    
    However, sometimes colors are reversed. But problem states: 
    "(0,0) is the bottom-left corner" and "only dark squares are playable"
    
    Standard: bottom-left is dark -> so (0,0) is dark -> (0+0)%2 = 0 -> even
    Therefore, dark squares: (row + col) % 2 == 0
    
    But wait: in many representations, (0,0) is top-left. Here it's bottom-left.
    The rows increase upward. So row 0 is bottom, row 7 is top.
    The coloring alternates in the usual checkerboard way.
    The bottom-left (0,0) is dark -> then (0,1) is light, (1,0) is light, (1,1) is dark.
    So (row + col) % 2 == 0 -> dark
    """
    return (row + col) % 2 == 0


def generate_all_moves(my_men, my_kings, opp_men, opp_kings, direction):
    """
    Generate all legal moves when no captures are available.
    """
    moves = []
    opp_pieces = opp_men | opp_kings
    my_pieces = my_men | my_kings
    
    for piece in my_men | my_kings:
        row, col = piece
        if piece in my_men:
            directions = [(direction, -1), (direction, 1)]
        else:
            directions = [(1, -1), (1, 1), (-1, -1), (-1, 1)]
        
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row <= 7 and 0 <= new_col <= 7:
                # Check if landing square is dark and empty
                if is_dark_square(new_row, new_col) and (new_row, new_col) not in my_pieces and (new_row, new_col) not in opp_pieces:
                    moves.append((piece, (new_row, new_col)))
    
    return moves


def evaluate_capture_sequence(move, my_men, my_kings, opp_men, opp_kings, direction):
    """
    Simple heuristic to value capture moves: prefer longer sequences and captures of kings.
    """
    # This is a simplified version; for full game tree we'd simulate the move
    # But for now, we just count the capture value
    from_pos, to_pos = move
    from_row, from_col = from_pos
    to_row, to_col = to_pos
    
    # Calculate mid square
    mid_row = (from_row + to_row) // 2
    mid_col = (from_col + to_col) // 2
    
    # Value: 1 for man, 2 for king
    captured = (mid_row, mid_col)
    capture_value = 2 if captured in opp_kings else 1
    
    # Bonus for promoting to king
    promotion_bonus = 0
    if (direction == -1 and to_row == 0) or (direction == 1 and to_row == 7):
        # If the piece we moved is a man and it becomes a king
        if from_pos in my_men:
            promotion_bonus = 5  # High bonus
    
    return capture_value + promotion_bonus


def best_capture_move(my_men, my_kings, opp_men, opp_kings, direction, capture_moves):
    """
    Given a list of capture moves, choose the best one based on evaluation.
    """
    best_move = None
    best_score = float('-inf')
    
    for move in capture_moves:
        score = evaluate_move_after_capture(move, my_men, my_kings, opp_men, opp_kings, direction)
        if score > best_score:
            best_score = score
            best_move = move
            
    return best_move


def evaluate_move_after_capture(move, my_men, my_kings, opp_men, opp_kings, direction):
    """
    Evaluate the state after making a capture move (one step).
    """
    # Simulate the move
    from_pos, to_pos = move
    from_row, from_col = from_pos
    to_row, to_col = to_pos
    
    # Calculate the jumped piece
    mid_row = (from_row + to_row) // 2
    mid_col = (from_col + to_col) // 2
    jumped_piece = (mid_row, mid_col)
    
    # Create new state after move
    new_my_men = my_men.copy()
    new_my_kings = my_kings.copy()
    new_opp_men = opp_men.copy()
    new_opp_kings = opp_kings.copy()
    
    # Remove captured piece
    if jumped_piece in new_opp_men:
        new_opp_men.remove(jumped_piece)
    elif jumped_piece in new_opp_kings:
        new_opp_kings.remove(jumped_piece)
    
    # Move our piece
    if from_pos in new_my_men:
        new_my_men.remove(from_pos)
        # Check if promotion occurs
        if (direction == -1 and to_row == 0) or (direction == 1 and to_row == 7):
            new_my_kings.add(to_pos)
        else:
            new_my_men.add(to_pos)
    elif from_pos in new_my_kings:
        new_my_kings.remove(from_pos)
        new_my_kings.add(to_pos)
    
    # Evaluate the resulting position
    return evaluate_position(new_my_men, new_my_kings, new_opp_men, new_opp_kings, direction)


def evaluate_position(my_men, my_kings, opp_men, opp_kings, direction):
    """
    Heuristic evaluation function.
    """
    # Material count
    my_material = len(my_men) + 3 * len(my_kings)  # king worth 3x man
    opp_material = len(opp_men) + 3 * len(opp_kings)
    
    # Mobility
    my_moves = len(generate_all_moves(my_men, my_kings, opp_men, opp_kings, direction))
    # Simulate opponent's next moves to get an idea of their mobility (approximation)
    opp_direction = -direction
    opp_moves = len(generate_all_moves(opp_men, opp_kings, my_men, my_kings, opp_direction))
    
    # Center control
    my_center_control = 0
    opp_center_control = 0
    center_squares = {(3,3), (3,4), (4,3), (4,4)}
    for piece in my_men | my_kings:
        if piece in center_squares:
            my_center_control += 1
    for piece in opp_men | opp_kings:
        if piece in center_squares:
            opp_center_control += 1
    
    # Safety: pieces on edge are more vulnerable
    my_edge_vulnerability = 0
    opp_edge_vulnerability = 0
    edge_squares = set()
    for i in range(8):
        edge_squares.add((i, 0))
        edge_squares.add((i, 7))
        edge_squares.add((0, i))
        edge_squares.add((7, i))
    
    for piece in my_men | my_kings:
        if piece in edge_squares:
            my_edge_vulnerability += 1
    for piece in opp_men | opp_kings:
        if piece in edge_squares:
            opp_edge_vulnerability += 1
    
    # King advancement (for our kings, how close to opponent's back)
    my_king_advancement = 0
    for king in my_kings:
        if direction == -1: # black moves down, so we want kings to be near top (row 0)
            my_king_advancement += (7 - king[0])  # higher row (top) is better
        else: # white moves up, so we want kings near bottom (row 7)
            my_king_advancement += king[0]  # lower row? wait: row 7 is top? 
            # Correction: top is row 7, bottom row 0
            # but for white (color 'w'), moving UP means to higher row, so top is opponent's back (row 7)
            # So we want white kings to get to row 7 -> so advancement = row
            # But for white: row 7 is goal, so advancement = row (0 at bottom, 7 at top)
            # So yes, it's correct: for white, advancement = row (higher is better)
            # Actually for white, row increases upward -> row 7 is best.
        # So for black: higher row number is bad (we want low row 0 for promotion)
        # We want black kings to be as close to row 0 as possible -> so 7 - row
        # For white: we want kings to be as close to row 7 as possible -> so row
        # So we can write: advancement = row if white, 7-row if black
        # We did it conditionally above.
    
    # For white: advancement = row (because 7 is goal)
    # For black: advancement = 7 - row (because 0 is goal)
    # So we adjust:
    if direction == 1:  # white
        my_king_advancement = sum(king[0] for king in my_kings)
    else:  # black
        my_king_advancement = sum(7 - king[0] for king in my_kings)
    
    # Opponent's king advancement (penalty)
    opp_king_advancement = 0
    for king in opp_kings:
        if direction == 1:  # we are white, opponent is black -> their goal is 0, so advancement means 7 - row
            opp_king_advancement += (7 - king[0])
        else: # we are black, opponent is white -> their goal is 7, so advancement means row
            opp_king_advancement += king[0]
    
    # Combine all factors with weights
    score = (
        10 * (my_material - opp_material) +     # Material advantage
        3 * (my_moves - opp_moves) +            # Mobility
        2 * (my_center_control - opp_center_control) +  # Center control
        -1 * (my_edge_vulnerability - opp_edge_vulnerability) +  # Avoid edge
        4 * (my_king_advancement - opp_king_advancement)  # King promotion advantage
    )
    
    return score


def minimax_move(my_men, my_kings, opp_men, opp_kings, direction, depth=4):
    """
    Perform minimax with alpha-beta pruning to find the best move.
    Uses memoization to cache results for speedup.
    """
    # Memoization for state evaluation
    @lru_cache(maxsize=10000)
    def cached_evaluate(my_men_t, my_kings_t, opp_men_t, opp_kings_t, d):
        # Convert tuples back to sets for evaluation
        my_men_s = set(my_men_t)
        my_kings_s = set(my_kings_t)
        opp_men_s = set(opp_men_t)
        opp_kings_s = set(opp_kings_t)
        return evaluate_position(my_men_s, my_kings_s, opp_men_s, opp_kings_s, d)
    
    # Generate moves
    moves = generate_all_moves(my_men, my_kings, opp_men, opp_kings, direction)
    
    if not moves:
        return ((0,0), (1,1))  # fallback
    
    # Alpha-beta search
    best_move = moves[0]
    alpha = float('-inf')
    beta = float('inf')
    
    # For each move, recurse
    for move in moves:
        new_my_men, new_my_kings, new_opp_men, new_opp_kings = apply_move(
            move, my_men, my_kings, opp_men, opp_kings, direction
        )
        
        # Evaluate after move
        score = minimax_alpha_beta(
            new_my_men, new_my_kings, new_opp_men, new_opp_kings, -direction, 
            depth - 1, alpha, beta, False, cached_evaluate
        )
        
        if score > alpha:
            alpha = score
            best_move = move
            
        if alpha >= beta:
            break  # prune
            
    return best_move


def apply_move(move, my_men, my_kings, opp_men, opp_kings, direction):
    """
    Apply a single non-capture move and return the new board state.
    """
    from_pos, to_pos = move
    new_my_men = my_men.copy()
    new_my_kings = my_kings.copy()
    new_opp_men = opp_men.copy()
    new_opp_kings = opp_kings.copy()
    
    # Remove old position
    if from_pos in new_my_men:
        new_my_men.remove(from_pos)
        # Check for promotion
        if (direction == -1 and to_pos[0] == 0) or (direction == 1 and to_pos[0] == 7):
            new_my_kings.add(to_pos)
        else:
            new_my_men.add(to_pos)
    elif from_pos in new_my_kings:
        new_my_kings.remove(from_pos)
        new_my_kings.add(to_pos)
    
    # Note: no capture in non-capture move, so opponent state unchanged
    return new_my_men, new_my_kings, new_opp_men, new_opp_kings


def minimax_alpha_beta(my_men, my_kings, opp_men, opp_kings, direction, depth, alpha, beta, maximizing_player, cached_evaluate):
    """
    Minimax with alpha-beta pruning.
    """
    if depth == 0:
        # Evaluate the position
        my_men_t = tuple(sorted(my_men))
        my_kings_t = tuple(sorted(my_kings))
        opp_men_t = tuple(sorted(opp_men))
        opp_kings_t = tuple(sorted(opp_kings))
        return cached_evaluate(my_men_t, my_kings_t, opp_men_t, opp_kings_t, direction)
    
    # Generate moves for current player
    if maximizing_player:
        moves = generate_all_moves(my_men, my_kings, opp_men, opp_kings, direction)
        if not moves:
            my_men_t = tuple(sorted(my_men))
            my_kings_t = tuple(sorted(my_kings))
            opp_men_t = tuple(sorted(opp_men))
            opp_kings_t = tuple(sorted(opp_kings))
            return cached_evaluate(my_men_t, my_kings_t, opp_men_t, opp_kings_t, direction)
        
        best_score = float('-inf')
        for move in moves:
            new_my_men, new_my_kings, new_opp_men, new_opp_kings = apply_move(
                move, my_men, my_kings, opp_men, opp_kings, direction
            )
            
            # Recurse: now it's opponent's turn (minimizing)
            score = minimax_alpha_beta(
                new_my_men, new_my_kings, new_opp_men, new_opp_kings, 
                -direction, depth - 1, alpha, beta, False, cached_evaluate
            )
            
            best_score = max(best_score, score)
            alpha = max(alpha, best_score)
            
            if alpha >= beta:
                break
                
        return best_score
    else:
        # Minimizing player: opponent's turn
        moves = generate_all_moves(opp_men, opp_kings, my_men, my_kings, -direction)
        if not moves:
            my_men_t = tuple(sorted(my_men))
            my_kings_t = tuple(sorted(my_kings))
            opp_men_t = tuple(sorted(opp_men))
            opp_kings_t = tuple(sorted(opp_kings))
            return cached_evaluate(my_men_t, my_kings_t, opp_men_t, opp_kings_t, direction)
        
        best_score = float('inf')
        for move in moves:
            # We need to apply the opponent's move on their pieces
            from_pos, to_pos = move
            new_opp_men = opp_men.copy()
            new_opp_kings = opp_kings.copy()
            new_my_men = my_men.copy()
            new_my_kings = my_kings.copy()
            
            # Remove old position of opponent piece
            if from_pos in new_opp_men:
                new_opp_men.remove(from_pos)
                # Check for promotion
                if (-direction == -1 and to_pos[0] == 0) or (-direction == 1 and to_pos[0] == 7):
                    new_opp_kings.add(to_pos)
                else:
                    new_opp_men.add(to_pos)
            elif from_pos in new_opp_kings:
                new_opp_kings.remove(from_pos)
                new_opp_kings.add(to_pos)
            
            # Recurse: now it's our turn (maximizing)
            score = minimax_alpha_beta(
                new_my_men, new_my_kings, new_opp_men, new_opp_kings, 
                direction, depth - 1, alpha, beta, True, cached_evaluate
            )
            
            best_score = min(best_score, score)
            beta = min(beta, best_score)
            
            if alpha >= beta:
                break
                
        return best_score
