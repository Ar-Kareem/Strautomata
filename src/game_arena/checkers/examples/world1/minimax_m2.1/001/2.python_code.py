
import random
import time
from functools import lru_cache

# Direction mappings for each color
DIRECTIONS = {
    'b': [(-1, -1), (-1, 1)],   # Black moves downwards (decreasing row)
    'w': [(1, -1), (1, 1)]      # White moves upwards (increasing row)
}

def policy(my_men, my_kings, opp_men, opp_kings, color):
    """
    Main policy function that returns the next move.
    """
    # Convert lists to sets for faster lookup
    my_men_set = set(my_men)
    my_kings_set = set(my_kings)
    opp_men_set = set(opp_men)
    opp_kings_set = set(opp_kings)
    
    # Board representation: (my_men, my_kings, opp_men, opp_kings)
    # We'll use bitboards for efficiency
    
    # Start timing
    start_time = time.time()
    max_time = 0.95  # Leave some margin
    
    # Generate all possible moves
    all_moves = generate_all_moves(my_men_set, my_kings_set, opp_men_set, opp_kings_set, color)
    
    # If no moves available, return None (shouldn't happen in valid game state)
    if not all_moves:
        return None
    
    # Separate capture moves from regular moves
    capture_moves = [m for m in all_moves if is_capture_move(m, my_men_set, my_kings_set, opp_men_set, opp_kings_set, color)]
    
    # If captures are available, must choose one (mandatory captures)
    if capture_moves:
        # Find multi-jumps (chains of captures)
        multi_jumps = find_multi_jumps(capture_moves, my_men_set, my_kings_set, opp_men_set, opp_kings_set, color)
        if multi_jumps:
            best_move = select_best_move(multi_jumps, my_men_set, my_kings_set, opp_men_set, opp_kings_set, color, start_time, max_time)
        else:
            best_move = select_best_move(capture_moves, my_men_set, my_kings_set, opp_men_set, opp_kings_set, color, start_time, max_time)
    else:
        best_move = select_best_move(all_moves, my_men_set, my_kings_set, opp_men_set, opp_kings_set, color, start_time, max_time)
    
    return best_move

def generate_all_moves(my_men, my_kings, opp_men, opp_kings, color):
    """Generate all possible moves for the current player."""
    moves = []
    
    # Get all my pieces
    all_my_pieces = my_men | my_kings
    
    for piece in all_my_pieces:
        if piece in my_kings:
            # King can move in all 4 diagonal directions
            for drow, dcol in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                moves.extend(generate_moves_from_square(piece, drow, dcol, my_men, my_kings, opp_men, opp_kings, color))
        else:
            # Regular piece moves in color-specific directions
            for drow, dcol in DIRECTIONS[color]:
                moves.extend(generate_moves_from_square(piece, drow, dcol, my_men, my_kings, opp_men, opp_kings, color))
    
    return moves

def generate_moves_from_square(piece, drow, dcol, my_men, my_kings, opp_men, opp_kings, color):
    """Generate moves from a specific square in a specific direction."""
    moves = []
    row, col = piece
    new_row, new_col = row + drow, col + dcol
    
    # Check if the immediate square is valid
    if not is_valid_square(new_row, new_col):
        return moves
    
    if (new_row, new_col) in my_men or (new_row, new_col) in my_kings:
        # Blocked by own piece
        return moves
    elif (new_row, new_col) in opp_men or (new_row, new_col) in opp_kings:
        # Potential capture
        capture_row, capture_col = new_row + drow, new_col + dcol
        if is_valid_square(capture_row, capture_col) and (capture_row, capture_col) not in my_men and (capture_row, capture_col) not in my_kings and (capture_row, capture_col) not in opp_men and (capture_row, capture_col) not in opp_kings:
            moves.append((piece, (capture_row, capture_col)))
    else:
        # Regular move
        moves.append((piece, (new_row, new_col)))
    
    return moves

def is_valid_square(row, col):
    """Check if a square is valid and playable (dark square only)."""
    return 0 <= row < 8 and 0 <= col < 8 and (row + col) % 2 == 1

def is_capture_move(move, my_men, my_kings, opp_men, opp_kings, color):
    """Check if a move is a capture."""
    from_pos, to_pos = move
    from_row, from_col = from_pos
    to_row, to_col = to_pos
    
    # Captures move 2 squares in one direction
    drow = to_row - from_row
    dcol = to_col - from_col
    
    return abs(drow) == 2 and abs(dcol) == 2

def find_multi_jumps(initial_moves, my_men, my_kings, opp_men, opp_kings, color):
    """Find sequences of multi-jumps (chain captures)."""
    multi_jumps = []
    
    for move in initial_moves:
        from_pos, to_pos = move
        captures = find_all_captures_from_move(move, my_men, my_kings, opp_men, opp_kings, color)
        if captures:
            # This move can be extended
            path = [move]
            current_moves = [(move, captures)]
            
            while current_moves:
                current_move, current_captures = current_moves.pop(0)
                
                for capture in current_captures:
                    from_pos, to_pos = current_move[-1] if isinstance(current_move[-1], tuple) and isinstance(current_move[-1][0], tuple) else current_move[-1]
                    path.append(capture)
                    
                    # Check for more captures
                    more_captures = find_all_captures_from_move(capture, my_men, my_kings, opp_men, opp_kings, color)
                    
                    if more_captures:
                        current_moves.append((capture, more_captures))
                    else:
                        # Complete chain found
                        multi_jumps.append(tuple(path))
                        path = path[:-1]  # Backtrack
    
    return multi_jumps

def find_all_captures_from_move(move, my_men, my_kings, opp_men, opp_kings, color):
    """Find all possible captures from a given move position."""
    from_pos, to_pos = move
    captures = []
    
    # Determine the piece type and directions
    if to_pos in my_kings:
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    else:
        directions = DIRECTIONS[color]
    
    for drow, dcol in directions:
        # Check diagonal squares for opponent pieces
        check_row, check_col = to_pos[0] + drow, to_pos[1] + dcol
        land_row, land_col = to_pos[0] + 2*drow, to_pos[1] + 2*dcol
        
        if not is_valid_square(check_row, check_col) or not is_valid_square(land_row, land_col):
            continue
            
        # Check if there's an opponent piece to capture
        check_pos = (check_row, check_col)
        land_pos = (land_row, land_col)
        
        if check_pos in opp_men or check_pos in opp_kings:
            if land_pos not in my_men and land_pos not in my_kings and land_pos not in opp_men and land_pos not in opp_kings:
                captures.append((to_pos, land_pos))
    
    return captures

def select_best_move(moves, my_men, my_kings, opp_men, opp_kings, color, start_time, max_time):
    """Select the best move using minimax with alpha-beta pruning."""
    
    # Simple case: few moves, use shallow search
    if len(moves) <= 3:
        return max(moves, key=lambda m: evaluate_move(m, my_men, my_kings, opp_men, opp_kings, color))
    
    # Use iterative deepening
    depth = 1
    best_move = moves[0]
    alpha = float('-inf')
    beta = float('inf')
    
    while time.time() - start_time < max_time:
        try:
            depth += 1
            # Convert moves to proper format for search
            move_values = {}
            
            for move in moves:
                # Simulate the move
                new_state = simulate_move(move, my_men, my_kings, opp_men, opp_kings, color)
                value = minimax(new_state, depth - 1, alpha, beta, False, color, start_time, max_time)
                move_values[move] = value
                
                if value > alpha:
                    alpha = value
                    best_move = move
        except TimeoutError:
            break
    
    # Return best move found
    if move_values:
        best_move = max(move_values, key=move_values.get)
    
    return best_move

def simulate_move(move, my_men, my_kings, opp_men, opp_kings, color):
    """Simulate a move and return the new board state."""
    from_pos, to_pos = move
    new_my_men = set(my_men)
    new_my_kings = set(my_kings)
    new_opp_men = set(opp_men)
    new_opp_kings = set(opp_kings)
    
    # Remove captured pieces
    drow = to_pos[0] - from_pos[0]
    dcol = to_pos[1] - from_pos[1]
    
    if abs(drow) == 2:  # Capture move
        mid_row = from_pos[0] + drow // 2
        mid_col = from_pos[1] + dcol // 2
        mid_pos = (mid_row, mid_col)
        
        if mid_pos in new_opp_men:
            new_opp_men.remove(mid_pos)
        elif mid_pos in new_opp_kings:
            new_opp_kings.remove(mid_pos)
    
    # Move the piece
    if from_pos in new_my_men:
        new_my_men.remove(from_pos)
        new_my_men.add(to_pos)
        
        # Check for promotion
        if color == 'b' and to_pos[0] == 0:
            new_my_men.remove(to_pos)
            new_my_kings.add(to_pos)
        elif color == 'w' and to_pos[0] == 7:
            new_my_men.remove(to_pos)
            new_my_kings.add(to_pos)
    elif from_pos in new_my_kings:
        new_my_kings.remove(from_pos)
        new_my_kings.add(to_pos)
    
    return (new_my_men, new_my_kings, new_opp_men, new_opp_kings)

def minimax(state, depth, alpha, beta, maximizing_player, color, start_time, max_time):
    """Minimax algorithm with alpha-beta pruning."""
    
    # Check for timeout
    if time.time() - start_time > max_time:
        raise TimeoutError("Search time exceeded")
    
    my_men, my_kings, opp_men, opp_kings = state
    
    # Check terminal conditions
    if not opp_men and not opp_kings:
        return float('inf') if maximizing_player else float('-inf')
    if not my_men and not my_kings:
        return float('-inf') if maximizing_player else float('inf')
    
    if depth == 0:
        return evaluate_board(state, color)
    
    # Generate moves for current player
    if maximizing_player:
        moves = generate_all_moves(my_men, my_kings, opp_men, opp_kings, color)
        if not moves:
            return float('-inf')
        
        # Prioritize captures
        capture_moves = [m for m in moves if is_capture_move(m, my_men, my_kings, opp_men, opp_kings, color)]
        if capture_moves:
            moves = capture_moves
        
        max_eval = float('-inf')
        for move in moves:
            new_state = simulate_move(move, my_men, my_kings, opp_men, opp_kings, color)
            eval_score = minimax(new_state, depth - 1, alpha, beta, False, color, start_time, max_time)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        moves = generate_all_moves(opp_men, opp_kings, my_men, my_kings, 'w' if color == 'b' else 'b')
        if not moves:
            return float('inf')
        
        # Prioritize captures
        capture_moves = [m for m in moves if is_capture_move(m, opp_men, opp_kings, my_men, my_kings, 'w' if color == 'b' else 'b')]
        if capture_moves:
            moves = capture_moves
        
        min_eval = float('inf')
        for move in moves:
            new_state = simulate_move(move, opp_men, opp_kings, my_men, my_kings, 'w' if color == 'b' else 'b')
            eval_score = minimax(new_state, depth - 1, alpha, beta, True, color, start_time, max_time)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval

def evaluate_board(state, color):
    """Evaluate the board position."""
    my_men, my_kings, opp_men, opp_kings = state
    
    # Material evaluation
    my_score = len(my_men) * 1 + len(my_kings) * 2
    opp_score = len(opp_men) * 1 + len(opp_kings) * 2
    
    # Position evaluation
    my_score += sum(position_bonus(pos, color) for pos in my_men)
    my_score += sum(position_bonus(pos, color) * 1.5 for pos in my_kings)
    opp_score += sum(position_bonus(pos, 'w' if color == 'b' else 'b') for pos in opp_men)
    opp_score += sum(position_bonus(pos, 'w' if color == 'b' else 'b') * 1.5 for pos in opp_kings)
    
    # Advancement evaluation
    my_score += advancement_bonus(my_men, my_kings, color)
    opp_score += advancement_bonus(opp_men, opp_kings, 'w' if color == 'b' else 'b')
    
    return my_score - opp_score

def position_bonus(pos, color):
    """Calculate position bonus for a piece."""
    row, col = pos
    
    # Center control bonus
    center_bonus = 0
    if 2 <= row <= 5 and 2 <= col <= 5:
        center_bonus = 0.3
    
    # Edge penalty (pieces on edges are more vulnerable)
    edge_penalty = 0
    if row in [0, 7] or col in [0, 7]:
        edge_penalty = -0.2
    
    # Safety bonus (back rank safety for regular pieces)
    safety_bonus = 0
    if color == 'b' and row <= 1:
        safety_bonus = 0.2
    elif color == 'w' and row >= 6:
        safety_bonus = 0.2
    
    return center_bonus + edge_penalty + safety_bonus

def advancement_bonus(men, kings, color):
    """Calculate advancement bonus for pieces closer to promotion."""
    bonus = 0
    
    for pos in men:
        row = pos[0]
        if color == 'b':
            bonus += (7 - row) / 7.0  # Higher for black pieces closer to row 0
        else:
            bonus += row / 7.0  # Higher for white pieces closer to row 7
    
    # Kings also get a bonus for being in advantageous positions
    for pos in kings:
        bonus += 0.5
    
    return bonus

def evaluate_move(move, my_men, my_kings, opp_men, opp_kings, color):
    """Evaluate a single move."""
    from_pos, to_pos = move
    
    score = 0
    
    # Capture bonus
    if is_capture_move(move, my_men, my_kings, opp_men, opp_kings, color):
        score += 10
    
    # Promotion bonus
    if color == 'b' and to_pos[0] == 0 and from_pos not in my_kings:
        score += 100
    elif color == 'w' and to_pos[0] == 7 and from_pos not in my_kings:
        score += 100
    
    # Advancement bonus
    if from_pos not in my_kings:
        if color == 'b':
            score += (from_pos[0] - to_pos[0]) * 0.5
        else:
            score += (to_pos[0] - from_pos[0]) * 0.5
    
    # Center control bonus
    if 2 <= to_pos[0] <= 5 and 2 <= to_pos[1] <= 5:
        score += 0.3
    
    # King safety
    if to_pos in my_kings:
        score += 0.2
    
    return score
