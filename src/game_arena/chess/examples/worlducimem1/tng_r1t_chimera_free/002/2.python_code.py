
import random

def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    my_color = 'w' if to_play == 'white' else 'b'
    piece_values = {'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1, 'K': 0}
    
    current_eval = evaluate(pieces, my_color, piece_values)
    best_moves = []
    max_delta = -float('inf')
    
    # Generate all pseudo-legal moves (captures and promotions)
    legal_moves = generate_pseudo_legal_moves(pieces, my_color)
    
    for move in legal_moves:
        new_pieces = apply_move(pieces.copy(), move, my_color)
        new_eval = evaluate(new_pieces, my_color, piece_values)
        delta = new_eval - current_eval
        
        # Prioritize promotions to queen
        if len(move) == 5 and move[4] == 'q':
            delta += 8  # Promote pawn to queen
        
        if delta > max_delta:
            max_delta = delta
            best_moves = [move]
        elif delta == max_delta:
            best_moves.append(move)
    
    # Select randomly among best moves to avoid predictability
    selected_move = random.choice(best_moves) if best_moves else random.choice(legal_moves)
    return selected_move, memory

def evaluate(pieces: dict[str, str], my_color: str, piece_values: dict) -> int:
    my_material = 0
    opp_material = 0
    for code in pieces.values():
        color = code[0]
        p_type = code[1]
        val = piece_values.get(p_type, 0)
        if color == my_color:
            my_material += val
        else:
            opp_material += val
    return my_material - opp_material

def apply_move(pieces: dict, move: str, my_color: str) -> dict:
    new_pieces = pieces.copy()
    from_sq = move[:2]
    to_sq = move[2:4]
    if from_sq not in new_pieces:
        return new_pieces  # Invalid
    piece = new_pieces.pop(from_sq)
    if len(move) == 5:
        promote_to = move[4].upper()
        piece = piece[0] + promote_to
    new_pieces[to_sq] = piece
    return new_pieces

def generate_pseudo_legal_moves(pieces: dict, my_color: str) -> list:
    legal_moves = []
    for from_sq in pieces:
        piece = pieces[from_sq]
        if piece[0] != my_color:
            continue
        for to_sq in generate_target_squares(from_sq, piece[1], pieces, my_color):
            # Check if promotion is possible
            if piece[1] == 'P' and ((my_color == 'w' and to_sq[1] == '8') or (my_color == 'b' and to_sq[1] == '1')):
                for promo in ['q', 'r', 'b', 'n']:
                    legal_moves.append(f"{from_sq}{to_sq}{promo}")
            else:
                legal_moves.append(f"{from_sq}{to_sq}")
    return legal_moves

def generate_target_squares(from_sq: str, piece_type: str, pieces: dict, color: str) -> list:
    targets = []
    x, y = ord(from_sq[0]) - ord('a'), int(from_sq[1]) - 1
    
    def is_valid(x, y):
        return 0 <= x < 8 and 0 <= y < 8
    
    # Generate moves based on piece type
    if piece_type == 'P':
        # Pawn moves
        direction = 1 if color == 'w' else -1
        # Forward one
        new_y = y + direction
        if is_valid(x, new_y):
            forward_sq = f"{chr(x + ord('a'))}{new_y + 1}"
            if forward_sq not in pieces:
                targets.append(forward_sq)
                # Forward two if on starting rank
                if (color == 'w' and y == 1) or (color == 'b' and y == 6):
                    new_y2 = y + 2 * direction
                    forward_sq2 = f"{chr(x + ord('a'))}{new_y2 + 1}"
                    if forward_sq2 not in pieces:
                        targets.append(forward_sq2)
        # Captures
        for dx in [-1, 1]:
            new_x = x + dx
            new_y = y + direction
            if is_valid(new_x, new_y):
                capture_sq = f"{chr(new_x + ord('a'))}{new_y + 1}"
                if capture_sq in pieces and pieces[capture_sq][0] != color:
                    targets.append(capture_sq)
    elif piece_type == 'N':
        # Knight moves
        moves = [(2,1), (1,2), (-1,2), (-2,1),
                 (-2,-1), (-1,-2), (1,-2), (2,-1)]
        for dx, dy in moves:
            new_x, new_y = x + dx, y + dy
            if is_valid(new_x, new_y):
                sq = f"{chr(new_x + ord('a'))}{new_y + 1}"
                if sq not in pieces or pieces[sq][0] != color:
                    targets.append(sq)
    elif piece_type == 'K':
        # King moves (excluding castling)
        for dx in [-1,0,1]:
            for dy in [-1,0,1]:
                if dx == 0 and dy == 0:
                    continue
                new_x, new_y = x + dx, y + dy
                if is_valid(new_x, new_y):
                    sq = f"{chr(new_x + ord('a'))}{new_y + 1}"
                    if sq not in pieces or pieces[sq][0] != color:
                        targets.append(sq)
    else:
        # Simple sliding moves for R, B, Q (without obstruction checks)
        deltas = []
        if piece_type == 'R':
            deltas = [(1,0), (-1,0), (0,1), (0,-1)]
        elif piece_type == 'B':
            deltas = [(1,1), (1,-1), (-1,1), (-1,-1)]
        elif piece_type == 'Q':
            deltas = [(1,0), (-1,0), (0,1), (0,-1), (1,1), (1,-1), (-1,1), (-1,-1)]
        
        for dx, dy in deltas:
            steps = 1
            while True:
                new_x, new_y = x + dx * steps, y + dy * steps
                if not is_valid(new_x, new_y):
                    break
                sq = f"{chr(new_x + ord('a'))}{new_y + 1}"
                if sq in pieces:
                    if pieces[sq][0] != color:
                        targets.append(sq)
                    break
                targets.append(sq)
                steps += 1
    return targets
