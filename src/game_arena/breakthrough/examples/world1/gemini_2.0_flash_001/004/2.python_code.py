
import random

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    A Breakthrough policy that prioritizes winning, capturing, and advancing.
    """

    board_size = 8
    opponent_home_row = 0 if color == 'b' else 7
    direction = -1 if color == 'b' else 1

    def is_valid_move(start_row, start_col, end_row, end_col):
        return 0 <= end_row < board_size and 0 <= end_col < board_size

    def is_opponent(row, col):
        return (row, col) in opp

    def is_empty(row, col):
        return (row, col) not in me and (row, col) not in opp

    # 1. Check for immediate winning move
    for piece_row, piece_col in me:
        forward_row = piece_row + direction
        if forward_row == opponent_home_row:
            if is_empty(forward_row, piece_col):
                return ((piece_row, piece_col), (forward_row, piece_col))
        
        diag_left_col = piece_col - 1
        diag_right_col = piece_col + 1
        
        if is_valid_move(piece_row, piece_col, forward_row, diag_left_col) and is_opponent(forward_row, diag_left_col):
           return ((piece_row, piece_col), (forward_row, diag_left_col))
            
        if is_valid_move(piece_row, piece_col, forward_row, diag_right_col) and is_opponent(forward_row, diag_right_col):
            return ((piece_row, piece_col), (forward_row, diag_right_col))

    # 2. Check for captures that lead to winning
    for piece_row, piece_col in me:
        forward_row = piece_row + direction
        diag_left_col = piece_col - 1
        diag_right_col = piece_col + 1

        if is_valid_move(piece_row, piece_col, forward_row, diag_left_col) and is_opponent(forward_row, diag_left_col) and forward_row == opponent_home_row:
            return ((piece_row, piece_col), (forward_row, diag_left_col))
        if is_valid_move(piece_row, piece_col, forward_row, diag_right_col) and is_opponent(forward_row, diag_right_col) and forward_row == opponent_home_row:
            return ((piece_row, piece_col), (forward_row, diag_right_col))

    # 3. Capture Prioritization
    for piece_row, piece_col in me:
        forward_row = piece_row + direction
        diag_left_col = piece_col - 1
        diag_right_col = piece_col + 1

        if is_valid_move(piece_row, piece_col, forward_row, diag_left_col) and is_opponent(forward_row, diag_left_col):
            #Prioritize the ones closer to the middle.
            if diag_left_col in (3,4):
                return ((piece_row, piece_col), (forward_row, diag_left_col))
        if is_valid_move(piece_row, piece_col, forward_row, diag_right_col) and is_opponent(forward_row, diag_right_col):
            if diag_right_col in (3,4):
                return ((piece_row, piece_col), (forward_row, diag_right_col))  
        if is_valid_move(piece_row, piece_col, forward_row, diag_left_col) and is_opponent(forward_row, diag_left_col):
            return ((piece_row, piece_col), (forward_row, diag_left_col))
        if is_valid_move(piece_row, piece_col, forward_row, diag_right_col) and is_opponent(forward_row, diag_right_col):
            return ((piece_row, piece_col), (forward_row, diag_right_col))  

    # 4. Defensive Move
    for piece_row, piece_col in me:
        forward_row = piece_row + direction
        if color == 'b':
            threat_rows = [piece_row + 1]
        else:
            threat_rows = [piece_row - 1]
        
        for threat_row in threat_rows:
            if not (0 <= threat_row < board_size):
                continue #Out of bound row.
            
            threat_cols = []
            
            threat_cols = []
            if color == 'b':
                threat_cols = [ piece_col -1 , piece_col +1]
            else:
                threat_cols = [piece_col -1, piece_col + 1]

            

            for threat_col in threat_cols:
                if not (0 <= threat_col < board_size):
                    continue #Out of bound col

                if (threat_row, threat_col) in opp:
                    if is_empty(forward_row, piece_col) and is_valid_move(piece_row, piece_col, forward_row, piece_col):
                        return ((piece_row, piece_col), (forward_row, piece_col))
                        
    # 5. Advance Piece Position
    for piece_row, piece_col in me:
        forward_row = piece_row + direction
        if is_valid_move(piece_row, piece_col, forward_row, piece_col) and is_empty(forward_row, piece_col):
            return ((piece_row, piece_col), (forward_row, piece_col))

    # 6. Fallback: Random legal move
    possible_moves = []
    for piece_row, piece_col in me:
        forward_row = piece_row + direction
        
        if is_valid_move(piece_row, piece_col, forward_row, piece_col) and is_empty(forward_row, piece_col):
            possible_moves.append(((piece_row, piece_col), (forward_row, piece_col)))
        
        diag_left_col = piece_col - 1
        diag_right_col = piece_col + 1
        
        if is_valid_move(piece_row, piece_col, forward_row, diag_left_col):
            if is_opponent(forward_row, diag_left_col) or is_empty(forward_row, diag_left_col):
                 possible_moves.append(((piece_row, piece_col), (forward_row, diag_left_col)))
            
        if is_valid_move(piece_row, piece_col, forward_row, diag_right_col):
            if is_opponent(forward_row, diag_right_col) or is_empty(forward_row, diag_right_col):
                possible_moves.append(((piece_row, piece_col), (forward_row, diag_right_col)))
    

    if possible_moves:
        return random.choice(possible_moves)

    # If no move is possible (shouldn't happen in Breakthrough), return an arbitrary legal move to avoid disqualification
    print("No move possible. Returning a stub move.")
    return ((0,0), (1,0)) #Stub for when no moves are possible, avoiding disqualification
