
import random

def policy(my_men, my_kings, opp_men, opp_kings, color):
    # Define the board size
    BOARD_SIZE = 8

    # Convert lists to sets for faster lookup
    my_men_set = set(my_men)
    my_kings_set = set(my_kings)
    opp_men_set = set(opp_men)
    opp_kings_set = set(opp_kings)

    # Define player directions based on color
    if color == 'b':  # Black moves down (row decreases)
        directions = [(-1, -1), (-1, 1)]
        king_directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    else:  # White moves up (row increases)
        directions = [(1, -1), (1, 1)]
        king_directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

    def is_on_board(row, col):
        return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE

    def is_dark_square(row, col):
        return (row + col) % 2 == 1

    def generate_moves_for_piece(piece_pos, is_king):
        moves = []
        capture_moves = []
        start_row, start_col = piece_pos
        
        # Determine directions based on piece type and player color
        if is_king:
            dirs = king_directions
        else:
            dirs = directions

        # Check for captures
        for dr, dc in dirs:
            # Check the square to jump over
            jump_row = start_row + dr
            jump_col = start_col + dc
            if is_on_board(jump_row, jump_col):
                # Determine if there's an opponent piece to jump over
                opponent_here = (jump_row, jump_col) in opp_men_set or (jump_row, jump_col) in opp_kings_set
                if opponent_here:
                    # Check the landing square
                    land_row = start_row + 2 * dr
                    land_col = start_col + 2 * dc
                    if is_on_board(land_row, land_col) and is_dark_square(land_row, land_col):
                        # Landing square must be empty
                        is_empty = (land_row, land_col) not in my_men_set and \
                                   (land_row, land_col) not in my_kings_set and \
                                   (land_row, land_col) not in opp_men_set and \
                                   (land_row, land_col) not in opp_kings_set
                        if is_empty:
                            capture_moves.append(((start_row, start_col), (land_row, land_col)))

        if capture_moves:
            return capture_moves  # Mandatory capture rule

        # Regular moves (only if no captures are available)
        for dr, dc in dirs:
            new_row = start_row + dr
            new_col = start_col + dc
            if is_on_board(new_row, new_col) and is_dark_square(new_row, new_col):
                # Check if the square is empty
                is_empty = (new_row, new_col) not in my_men_set and \
                           (new_row, new_col) not in my_kings_set and \
                           (new_row, new_col) not in opp_men_set and \
                           (new_row, new_col) not in opp_kings_set
                if is_empty:
                    moves.append(((start_row, start_col), (new_row, new_col)))

        return moves

    def generate_all_moves():
        all_moves = []
        # Generate moves for men
        for man_pos in my_men:
            moves = generate_moves_for_piece(man_pos, False)
            all_moves.extend(moves)
        
        # Generate moves for kings
        for king_pos in my_kings:
            moves = generate_moves_for_piece(king_pos, True)
            all_moves.extend(moves)
        
        # If there are any capture moves, we must make one of them
        capture_moves = [move for move in all_moves if abs(move[0][0] - move[1][0]) == 2]
        if capture_moves:
            return capture_moves
        return all_moves

    def make_move_on_state(move, state_my_men, state_my_kings, state_opp_men, state_opp_kings):
        # Destructure the move
        from_pos, to_pos = move
        new_my_men = state_my_men[:]
        new_my_kings = state_my_kings[:]
        new_opp_men = state_opp_men[:]
        new_opp_kings = state_opp_kings[:]

        # Remove the piece from the old position
        if from_pos in new_my_men:
            new_my_men.remove(from_pos)
        elif from_pos in new_my_kings:
            new_my_kings.remove(from_pos)

        # Add the piece to the new position, promoting to king if necessary
        piece_was_man = from_pos in state_my_men
        if piece_was_man:
            # Check for promotion
            if (color == 'b' and to_pos[0] == 0) or (color == 'w' and to_pos[0] == BOARD_SIZE - 1):
                new_my_kings.append(to_pos)
            else:
                new_my_men.append(to_pos)
        else:
            new_my_kings.append(to_pos)

        # Handle capture
        if abs(from_pos[0] - to_pos[0]) == 2:
            capture_row = (from_pos[0] + to_pos[0]) // 2
            capture_col = (from_pos[1] + to_pos[1]) // 2
            capture_pos = (capture_row, capture_col)
            
            if capture_pos in new_opp_men:
                new_opp_men.remove(capture_pos)
            elif capture_pos in new_opp_kings:
                new_opp_kings.remove(capture_pos)

        return new_my_men, new_my_kings, new_opp_men, new_opp_kings

    def evaluate(state_my_men, state_my_kings, state_opp_men, state_opp_kings):
        # Piece count heuristic with king being worth more
        score = 0
        score += len(state_my_men) * 100
        score += len(state_my_kings) * 300
        score -= len(state_opp_men) * 100
        score -= len(state_opp_kings) * 300
        
        # Center control
        center_squares = [(3, 2), (3, 4), (4, 3), (4, 5)]
        for pos in state_my_men + state_my_kings:
            if pos in center_squares:
                score += 10
        
        # Advancement for men
        for (r, c) in state_my_men:
            if color == 'b':
                score += (7 - r) * 5 # The closer to row 0, the better for black
            else:
                score += r * 5 # The closer to row 7, the better for white
                
        for (r, c) in state_opp_men:
            if color == 'b': # We want opponent men to be far from row 0
                score -= (7 - r) * 5
            else: # We want opponent men to be far from row 7
                score -= r * 5

        return score

    def minimax(depth, is_maximizing, state_my_men, state_my_kings, state_opp_men, state_opp_kings, alpha, beta):
        if depth == 0:
            return evaluate(state_my_men, state_my_kings, state_opp_men, state_opp_kings), None

        all_moves = []
        if is_maximizing:
            temp_my_men, temp_my_kings = state_my_men, state_my_kings
            temp_opp_men, temp_opp_kings = state_opp_men, state_opp_kings
        else:
            temp_my_men, temp_my_kings = state_opp_men, state_opp_kings
            temp_opp_men, temp_opp_kings = state_my_men, state_my_kings

        # Generate moves for the current player in the simulation
        temp_moves = []
        for man_pos in temp_my_men:
            moves = generate_moves_for_piece(man_pos, False)
            temp_moves.extend(moves)
        for king_pos in temp_my_kings:
            moves = generate_moves_for_piece(king_pos, True)
            temp_moves.extend(moves)
            
        capture_moves = [move for move in temp_moves if abs(move[0][0] - move[1][0]) == 2]
        if capture_moves:
            all_moves = capture_moves
        else:
            all_moves = temp_moves

        if not all_moves:
            if is_maximizing:
                return -10000, None # Loss for maximizing player
            else:
                return 10000, None  # Loss for minimizing player (win for maximizing player)

        best_move = None
        if is_maximizing:
            max_eval = float('-inf')
            for move in all_moves:
                new_my_men, new_my_kings, new_opp_men, new_opp_kings = make_move_on_state(
                    move, state_my_men, state_my_kings, state_opp_men, state_opp_kings
                )
                eval_score, _ = minimax(depth - 1, False, new_my_men, new_my_kings, new_opp_men, new_opp_kings, alpha, beta)
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for move in all_moves:
                new_opp_men, new_opp_kings, new_my_men, new_my_kings = make_move_on_state(
                    move, state_opp_men, state_opp_kings, state_my_men, state_my_kings
                )
                eval_score, _ = minimax(depth - 1, True, new_my_men, new_my_kings, new_opp_men, new_opp_kings, alpha, beta)
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_move

    # Generate all possible moves for the current player
    possible_moves = generate_all_moves()
    
    if not possible_moves:
        # This should not happen if the game is still ongoing and it's our turn
        # But just in case, return a default move (should be handled by arena)
        return ((0, 0), (0, 0))

    # If there's only one move, make it
    if len(possible_moves) == 1:
        return possible_moves[0]

    # Use minimax to choose the best move
    _, best_move = minimax(4, True, my_men, my_kings, opp_men, opp_kings, float('-inf'), float('inf'))
    
    # If minimax didn't find a move (shouldn't happen), pick a random one
    if best_move is None:
        return random.choice(possible_moves)
        
    return best_move
