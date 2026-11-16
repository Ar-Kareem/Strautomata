
import random

def policy(my_men, my_kings, opp_men, opp_kings, color):
    # Combine all our pieces
    all_my_pieces = my_men + my_kings
    
    # Define movement directions based on color
    if color == 'b':
        # Black moves upwards (to smaller row indices)
        directions = [(-1, -1), (-1, 1)]  # Regular moves
        jump_directions = [(-2, -2), (-2, 2)]  # Jump moves
    else:
        # White moves downwards (to larger row indices)
        directions = [(1, -1), (1, 1)]  # Regular moves
        jump_directions = [(2, -2), (2, 2)]  # Jump moves

    # Convert lists to sets for faster operations
    my_men_set = set(my_men)
    my_kings_set = set(my_kings)
    opp_men_set = set(opp_men)
    opp_kings_set = set(opp_kings)
    all_opponents = opp_men_set | opp_kings_set

    # Check for captures first
    for piece in all_my_pieces:
        row, col = piece
        is_king = piece in my_kings_set
        
        # For kings, we can move in all four diagonal directions
        if is_king:
            dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            j_dirs = [(-2, -2), (-2, 2), (2, -2), (2, 2)]
        else:
            dirs = directions
            j_dirs = jump_directions

        for d, jd in zip(dirs, j_dirs):
            r, c = d
            jr, jc = jd
            target_row = row + r
            target_col = col + c
            jump_row = row + jr
            jump_col = col + jc
            
            # Check if the adjacent square has an opponent piece
            if (target_row, target_col) in all_opponents:
                # Check if the jump square is empty and within bounds
                if 0 <= jump_row < 8 and 0 <= jump_col < 8:
                    if (jump_row, jump_col) not in (my_men_set | my_kings_set | all_opponents):
                        return ((row, col), (jump_row, jump_col))

    # If no captures, make a regular move
    # Prioritize moving pieces that are closer to promotion
    # For simplicity, we'll just pick a random legal move
    legal_moves = []
    
    for piece in all_my_pieces:
        row, col = piece
        is_king = piece in my_kings_set
        
        # For kings, we can move in all four diagonal directions
        if is_king:
            dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        else:
            dirs = directions

        for r, c in dirs:
            target_row = row + r
            target_col = col + c
            
            # Check if the target square is empty and within bounds
            if 0 <= target_row < 8 and 0 <= target_col < 8:
                if (target_row, target_col) not in (my_men_set | my_kings_set | all_opponents):
                    legal_moves.append(((row, col), (target_row, target_col)))

    if legal_moves:
        return random.choice(legal_moves)
    else:
        # This shouldn't happen if the game is valid, but return a dummy move
        return ((0, 0), (0, 0))
