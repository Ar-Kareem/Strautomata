
import copy
import random

# Constants
ROWS = 8
COLS = 8

# Positional weights for white (rows increasing upward) and black (rows decreasing downward)
# We'll compute dynamically based on color

def get_advancement_score(piece, color):
    """Score based on how advanced the piece is."""
    r, c = piece
    if color == 'w':
        return r  # row 0 is bottom, 7 is top (goal)
    else:
        return 7 - r  # row 7 is top, 0 is bottom (goal)

def get_center_score(piece):
    """Prefer center columns."""
    r, c = piece
    return 3.5 - abs(c - 3.5)

def piece_value(piece, color):
    """Combined positional value for a single piece."""
    advancement = get_advancement_score(piece, color)
    center = get_center_score(piece)
    return 10 + advancement * 2.0 + center * 0.5

def is_empty(square, me, opp):
    """Check if square is empty."""
    return square not in me and square not in opp

def is_opponent(square, opp):
    """Check if square is occupied by opponent."""
    return square in opp

def in_bounds(r, c):
    return 0 <= r < ROWS and 0 <= c < COLS

def get_moves(me, opp, color):
    """Generate all legal moves for current player."""
    moves = []
    direction = 1 if color == 'w' else -1
    
    for (r, c) in me:
        # Straight forward
        nr = r + direction
        if 0 <= nr < ROWS and (nr, c) not in me and (nr, c) not in opp:
            moves.append(((r, c), (nr, c)))
        
        # Diagonal captures
        for dc in [-1, 1]:
            nc = c + dc
            nr = r + direction
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                if (nr, nc) in opp:
                    moves.append(((r, c), (nr, nc)))
                elif (nr, nc) not in me:
                    moves.append(((r, c), (nr, nc)))
    
    return moves

def apply_move(me, opp, move, color):
    """Apply a move, return (new_me, new_opp, is_win)."""
    (fr, fc), (tr, tc) = move
    new_me = set(me)
    new_opp = set(opp)
    
    new_me.remove((fr, fc))
    new_me.add((tr, tc))
    
    if (tr, tc) in new_opp:
        new_opp.remove((tr, tc))
    
    # Check win by reaching opponent's home row
    if color == 'w' and tr == ROWS - 1:
        return list(new_me), list(new_opp), True
    if color == 'b' and tr == 0:
        return list(new_me), list(new_opp), True
    
    # Check win by capturing all opponent pieces
    if len(new_opp) == 0:
        return list(new_me), list(new_opp), True
    
    return list(new_me), list(new_opp), False

def evaluate(me, opp, color):
    """Evaluate board from perspective of 'color'."""
    my_score = sum(piece_value(p, color) for p in me)
    opp_color = 'w' if color == 'b' else 'b'
    opp_score = sum(piece_value(p, opp_color) for p in opp)
    
    # Bonus for winning
    if any((color == 'w' and r == 7) or (color == 'b' and r == 0) for r, c in me):
        return 10000
    if len(opp) == 0:
        return 10000
    if any((opp_color == 'w' and r == 7) or (opp_color == 'b' and r == 0) for r, c in opp):
        return -10000
    
    # Threats: pieces that can be captured next turn
    my_threats = count_threats(me, opp, color)
    opp_threats = count_threats(opp, me, opp_color)
    
    # Defense: discourage leaving pieces vulnerable
    defense_score = -sum(2.0 for p in me if is_threatened(p, opp, me, opp_color))
    
    return my_score - opp_score + defense_score

def count_threats(attacker_pieces, defender_pieces, attack_color):
    """Count how many defender pieces are threatened."""
    direction = 1 if attack_color == 'w' else -1
    count = 0
    for (r, c) in defender_pieces:
        for dc in [-1, 1]:
            nr, nc = r - direction, c + dc  # attacker would be at r-direction
            if in_bounds(nr, nc) and (nr, nc) in attacker_pieces:
                count += 1
                break
    return count

def is_threatened(piece, opp_pieces, my_pieces, opponent_color):
    """Check if a specific piece is threatened."""
    r, c = piece
    direction = 1 if opponent_color == 'w' else -1
    for dc in [-1, 1]:
        nr, nc = r - direction, c + dc
        if (nr, nc) in opp_pieces:
            return True
    return False

def minimax(me, opp, color, depth, alpha, beta, maximizing):
    """Minimax with alpha-beta pruning."""
    if depth == 0:
        return evaluate(me, opp, color if maximizing else ('w' if color == 'b' else 'b')), None
    
    current_color = color if maximizing else ('w' if color == 'b' else 'b')
    current_me = me if maximizing else opp
    current_opp = opp if maximizing else me
    
    moves = get_moves(current_me, current_opp, current_color)
    
    # Move ordering: prioritize captures and advancing
    def move_priority(m):
        (fr, fc), (tr, tc) = m
        is_capture = (tr, tc) in current_opp
        advance = get_advancement_score((tr, tc), current_color) - get_advancement_score((fr, fc), current_color)
        return (is_capture, advance)
    
    moves.sort(key=move_priority, reverse=True)
    
    # If no moves (shouldn't happen if game is ongoing, but safety)
    if not moves:
        return evaluate(me, opp, color), None
    
    best_move = moves[0]
    
    if maximizing:
        max_eval = float('-inf')
        for move in moves:
            new_me, new_opp, win = apply_move(current_me, current_opp, move, current_color)
            if win:
                return 10000, move
            
            eval_score, _ = minimax(new_me, new_opp, color, depth - 1, alpha, beta, False)
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for move in moves:
            new_me, new_opp, win = apply_move(current_me, current_opp, move, current_color)
            if win:
                return -10000, move
            
            eval_score, _ = minimax(new_me, new_opp, color, depth - 1, alpha, beta, True)
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval, best_move

def policy(me, opp, color):
    """
    Policy function for Breakthrough game.
    Returns ((from_row, from_col), (to_row, to_col))
    """
    # First check if any move can win immediately
    moves = get_moves(me, opp, color)
    for move in moves:
        _, _, win = apply_move(set(me), set(opp), move, color)
        if win:
            return move
    
    # Search to depth 3 (adjust based on performance, 3 is good for 1 second)
    depth = 3
    _, best_move = minimax(me, opp, color, depth, float('-inf'), float('inf'), True)
    
    if best_move is None:
        # Fallback to random move
        return random.choice(moves)
    
    return best_move
