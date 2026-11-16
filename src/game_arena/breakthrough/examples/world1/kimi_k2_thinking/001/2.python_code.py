
import time

def policy(me, opp, color):
    """Main policy function: returns the best move using iterative deepening minimax."""
    my_pieces = set(me)
    opp_pieces = set(opp)
    
    # Check for immediate winning moves first
    moves = generate_moves(my_pieces, opp_pieces, color)
    for move in moves:
        if is_winning_move(move, my_pieces, opp_pieces, color):
            return move
    
    # Iterative deepening with time management
    best_move = None
    if moves:
        best_move = moves[0]  # Default fallback
    
    start_time = time.time()
    depth = 1
    
    # Search deeper until time runs out
    while time.time() - start_time < 0.95:  # Leave 50ms safety margin
        try:
            move = minimax_root(my_pieces, opp_pieces, color, depth, start_time)
            if move is not None:
                best_move = move
            depth += 1
        except TimeoutError:
            break
    
    return best_move

def minimax_root(my_pieces, opp_pieces, color, depth, start_time):
    """Root of minimax search: finds best move at given depth."""
    best_move = None
    best_value = -float('inf')
    alpha = -float('inf')
    beta = float('inf')
    
    moves = generate_moves(my_pieces, opp_pieces, color)
    if not moves:
        return None
    
    for move in moves:
        # Time check
        if time.time() - start_time > 0.95:
            raise TimeoutError()
        
        # Apply move and search
        new_my, new_opp = apply_move(move, my_pieces, opp_pieces)
        value = -minimax(new_opp, new_my, opposite_color(color), depth - 1, -beta, -alpha, start_time)
        
        if value > best_value:
            best_value = value
            best_move = move
        
        alpha = max(alpha, best_value)
        if alpha >= beta:
            break  # Beta cutoff
    
    return best_move

def minimax(my_pieces, opp_pieces, color, depth, alpha, beta, start_time):
    """Recursive minimax with alpha-beta pruning."""
    # Time check
    if time.time() - start_time > 0.95:
        raise TimeoutError()
    
    # Terminal condition: opponent reached my home row
    my_home_row = 0 if color == 'w' else 7
    for r, c in opp_pieces:
        if r == my_home_row:
            return -float('inf')  # Opponent already won
    
    # Terminal condition: all opponent pieces captured
    if not opp_pieces:
        return float('inf')  # I won
    
    # Depth limit reached: use evaluation
    if depth == 0:
        return evaluate(my_pieces, opp_pieces, color)
    
    # No legal moves: loss
    moves = generate_moves(my_pieces, opp_pieces, color)
    if not moves:
        return -float('inf')
    
    # Search all moves
    value = -float('inf')
    for move in moves:
        new_my, new_opp = apply_move(move, my_pieces, opp_pieces)
        child_value = -minimax(new_opp, new_my, opposite_color(color), depth - 1, -beta, -alpha, start_time)
        value = max(value, child_value)
        alpha = max(alpha, value)
        if alpha >= beta:
            break  # Beta cutoff
    
    return value

def generate_moves(my_pieces, opp_pieces, color):
    """Generate all legal moves for the given position."""
    moves = []
    direction = 1 if color == 'w' else -1
    
    for r, c in my_pieces:
        # Forward move (must be empty)
        nr, nc = r + direction, c
        if 0 <= nr < 8 and 0 <= nc < 8 and (nr, nc) not in my_pieces and (nr, nc) not in opp_pieces:
            moves.append(((r, c), (nr, nc)))
        
        # Diagonal moves (capture or non-capture)
        for dc in (-1, 1):
            nr, nc = r + direction, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                if (nr, nc) in opp_pieces:
                    moves.append(((r, c), (nr, nc)))  # Capture
                elif (nr, nc) not in my_pieces:
                    moves.append(((r, c), (nr, nc)))  # Non-capturing diagonal
    
    return moves

def is_winning_move(move, my_pieces, opp_pieces, color):
    """Check if a move wins immediately."""
    (fr, fc), (tr, tc) = move
    opp_home_row = 7 if color == 'w' else 0
    
    # Win by reaching opponent's home row
    if tr == opp_home_row:
        return True
    
    # Win by capturing last opponent piece
    if (tr, tc) in opp_pieces and len(opp_pieces) == 1:
        return True
    
    return False

def apply_move(move, my_pieces, opp_pieces):
    """Apply a move to the board and return new piece sets."""
    (fr, fc), (tr, tc) = move
    new_my = set(my_pieces)
    new_opp = set(opp_pieces)
    
    # Move piece
    new_my.remove((fr, fc))
    new_my.add((tr, tc))
    
    # Capture if landing on opponent piece
    if (tr, tc) in new_opp:
        new_opp.remove((tr, tc))
    
    return new_my, new_opp

def opposite_color(color):
    """Return the opposite color."""
    return 'b' if color == 'w' else 'w'

def evaluate(my_pieces, opp_pieces, color):
    """
    Evaluate position from perspective of player to move.
    Score is based on piece advancement toward opponent's home row.
    """
    if color == 'w':
        # White: higher rows are better (0 to 7)
        my_score = sum(r for r, c in my_pieces)
        opp_score = sum((7 - r) for r, c in opp_pieces)
    else:
        # Black: lower rows are better (7 to 0)
        my_score = sum((7 - r) for r, c in my_pieces)
        opp_score = sum(r for r, c in opp_pieces)
    
    # Return difference in advancement
    return my_score - opp_score
