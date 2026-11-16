
import random

def policy(my_men, my_kings, opp_men, opp_kings, color):
    """
    Smart checkers policy that chooses optimal moves.
    
    Args:
        my_men: List of squares containing your regular pieces
        my_kings: List of squares containing your kings  
        opp_men: List of squares containing opponent regular pieces
        opp_kings: List of squares containing opponent kings
        color: 'b' for black (moves downwards), 'w' for white (moves upwards)
    
    Returns:
        tuple[ tuple[int, int], tuple[int, int] ]: ((from_row, from_col), (to_row, to_col))
    """
    
    # Combine all pieces into dictionaries for easy lookup
    my_pieces = {}
    for pos in my_men:
        my_pieces[pos] = 'man'
    for pos in my_kings:
        my_pieces[pos] = 'king'
    
    opp_pieces = {}
    for pos in opp_men:
        opp_pieces[pos] = 'man'
    for pos in opp_kings:
        opp_pieces[pos] = 'king'
    
    # Generate all possible moves
    all_moves = generate_all_moves(my_pieces, opp_pieces, color)
    
    if not all_moves:
        # No moves available - return a placeholder (shouldn't happen in valid game states)
        return ((0, 0), (0, 0))
    
    # Filter to find capture moves (jumps)
    capture_moves = [move for move in all_moves if move.get('capture')]
    
    # If captures are available, they are mandatory
    if capture_moves:
        # Score capture moves: prioritize more captures, then king captures
        capture_moves = score_capture_moves(capture_moves, opp_pieces)
        best_move = capture_moves[0]
    else:
        # No captures available, evaluate regular moves
        all_moves = score_regular_moves(all_moves, my_pieces, color)
        best_move = all_moves[0]
    
    return (best_move['from'], best_move['to'])


def generate_all_moves(my_pieces, opp_pieces, color):
    """
    Generate all legal moves for the current player.
    
    Returns list of move dictionaries with keys:
        - 'from': (row, col) starting position
        - 'to': (row, col) destination position  
        - 'capture': (row, col) of captured piece (None if no capture)
        - 'path': list of intermediate positions for multi-jumps
    """
    moves = []
    
    for pos, piece_type in my_pieces.items():
        if piece_type == 'king':
            # Kings can move in all four diagonal directions
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        else:
            # Regular pieces can only move in their forward direction
            if color == 'b':
                directions = [(-1, -1), (-1, 1)]  # Black moves down (decreasing row)
            else:
                directions = [(1, -1), (1, 1)]   # White moves up (increasing row)
        
        # Generate simple moves (non-captures)
        for drow, dcol in directions:
            new_row = pos[0] + drow
            new_col = pos[1] + dcol
            new_pos = (new_row, new_col)
            
            if is_valid_position(new_pos) and new_pos not in opp_pieces and new_pos not in my_pieces:
                moves.append({
                    'from': pos,
                    'to': new_pos,
                    'capture': None,
                    'path': [pos]
                })
        
        # Generate capture moves (jumps)
        for drow, dcol in directions:
            mid_row = pos[0] + drow
            mid_col = pos[1] + dcol
            mid_pos = (mid_row, mid_col)
            
            new_row = pos[0] + 2 * drow
            new_col = pos[1] + 2 * dcol
            new_pos = (new_row, new_col)
            
            # Check if jump is valid
            if (is_valid_position(mid_pos) and mid_pos in opp_pieces and 
                is_valid_position(new_pos) and new_pos not in opp_pieces and new_pos not in my_pieces):
                moves.append({
                    'from': pos,
                    'to': new_pos,
                    'capture': mid_pos,
                    'path': [pos, new_pos]
                })
    
    return moves


def is_valid_position(pos):
    """Check if a position is on the board and is a dark square."""
    row, col = pos
    if not (0 <= row < 8 and 0 <= col < 8):
        return False
    # Only dark squares are playable (sum of row and col should be odd)
    return (row + col) % 2 == 1


def score_capture_moves(capture_moves, opp_pieces):
    """
    Score capture moves. Prioritize:
    1. Moves that capture more pieces (multi-jumps)
    2. Moves that capture kings
    """
    scored_moves = []
    
    for move in capture_moves:
        score = 0
        
        # Base score for having a capture
        score += 100
        
        # Count captures in the move path
        # For simple captures, we only have one capture
        num_captures = len([pos for pos in move['path'][1:] if pos != move['to']])
        
        # Score by number of captures (multi-jumps are highly valuable)
        score += num_captures * 50
        
        # Bonus for capturing kings
        if move['capture'] in opp_pieces and opp_pieces[move['capture']] == 'king':
            score += 25
        
        scored_moves.append((score, move))
    
    # Sort by score descending and return moves
    scored_moves.sort(key=lambda x: -x[0])
    return [move for _, move in scored_moves]


def score_regular_moves(moves, my_pieces, color):
    """
    Score regular (non-capture) moves using strategic evaluation.
    """
    scored_moves = []
    
    for move in moves:
        score = 0
        from_pos = move['from']
        to_pos = move['to']
        row, col = to_pos
        
        # 1. Advancement bonus (moving toward becoming a king)
        if color == 'b':
            # Black wants to move to lower rows (row 0)
            advancement_bonus = (7 - row) * 3
        else:
            # White wants to move to higher rows (row 7)
            advancement_bonus = row * 3
        
        score += advancement_bonus
        
        # 2. Center control bonus (center squares are more valuable)
        center_distance = abs(col - 3.5) + abs(row - 3.5)
        center_bonus = (7 - center_distance) * 2
        score += center_bonus
        
        # 3. Safety bonus (avoid moving to edge if not necessary)
        if col in [1, 6]:
            safety_bonus = 1
        elif col in [2, 5]:
            safety_bonus = 2
        else:  # col in [3, 4] (center)
            safety_bonus = 3
        score += safety_bonus
        
        # 4. King protection bonus
        if from_pos in my_pieces and my_pieces[from_pos] == 'king':
            # Prefer keeping kings in the back row when possible
            if (color == 'b' and row > 2) or (color == 'w' and row < 5):
                score += 5
        
        # 5. Progress toward king row
        if color == 'b' and row == 1:
            score += 10  # One move away from becoming king
        elif color == 'w' and row == 6:
            score += 10  # One move away from becoming king
        
        # 6. Small randomness to add variety
        score += random.uniform(0, 0.5)
        
        scored_moves.append((score, move))
    
    # Sort by score descending
    scored_moves.sort(key=lambda x: -x[0])
    return [move for _, move in scored_moves]
