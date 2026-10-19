
import numpy as np

def policy(pieces: dict[str, str], to_play: str) -> str:
    # Determine color prefix for our pieces
    color_prefix = 'w' if to_play == 'white' else 'b'
    opponent_prefix = 'b' if to_play == 'white' else 'w'
    
    # Generate all possible moves (legal_moves would be provided in real scenario)
    # Since we don't have the actual legal_moves parameter, we'll simulate a way to generate them
    # In the real implementation, legal_moves would be passed to the function
    
    # For this implementation, we need to generate legal moves from the pieces dict
    def generate_legal_moves():
        legal_moves = []
        
        # Piece values
        piece_values = {'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1, 'K': 0}
        
        # Generate moves for each piece
        for square, piece in pieces.items():
            if piece[0] == color_prefix:
                piece_type = piece[1]
                x, y = ord(square[0]) - ord('a'), int(square[1]) - 1
                
                if piece_type == 'P':
                    # Pawn moves
                    direction = 1 if color_prefix == 'w' else -1
                    # Forward moves
                    new_y = y + direction
                    if 0 <= new_y < 8:
                        forward_sq = f"{square[0]}{new_y + 1}"
                        if forward_sq not in pieces:
                            legal_moves.append(f"{square}{forward_sq}")
                            # Double move from starting position
                            if (y == 1 and color_prefix == 'w') or (y == 6 and color_prefix == 'b'):
                                double_y = y + 2 * direction
                                double_sq = f"{square[0]}{double_y + 1}"
                                if double_sq not in pieces:
                                    legal_moves.append(f"{square}{double_sq}")
                        # Captures
                        for dx in [-1, 1]:
                            new_x = x + dx
                            if 0 <= new_x < 8:
                                capture_sq = f"{chr(new_x + ord('a'))}{new_y + 1}"
                                if capture_sq in pieces and pieces[capture_sq][0] == opponent_prefix:
                                    legal_moves.append(f"{square}{capture_sq}")
                                    # Check for promotion
                                    if new_y == 0 or new_y == 7:
                                        for prom in ['q', 'r', 'b', 'n']:
                                            legal_moves.append(f"{square}{capture_sq}{prom}")
                
                elif piece_type == 'N':
                    # Knight moves
                    for dx, dy in [(1,2),(2,1),(-1,2),(-2,1),(1,-2),(2,-1),(-1,-2),(-2,-1)]:
                        new_x, new_y = x + dx, y + dy
                        if 0 <= new_x < 8 and 0 <= new_y < 8:
                            new_sq = f"{chr(new_x + ord('a'))}{new_y + 1}"
                            if new_sq not in pieces or pieces[new_sq][0] == opponent_prefix:
                                legal_moves.append(f"{square}{new_sq}")
                
                elif piece_type == 'K':
                    # King moves
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            if dx == 0 and dy == 0:
                                continue
                            new_x, new_y = x + dx, y + dy
                            if 0 <= new_x < 8 and 0 <= new_y < 8:
                                new_sq = f"{chr(new_x + ord('a'))}{new_y + 1}"
                                if new_sq not in pieces or pieces[new_sq][0] == opponent_prefix:
                                    legal_moves.append(f"{square}{new_sq}")
        
        return legal_moves
    
    legal_moves = generate_legal_moves()
    if not legal_moves:
        return ""  # should never happen in legal position
    
    # Simple evaluation function
    def evaluate_move(move):
        # Material gain
        material = 0
        # Check if capture
        if len(move) >= 4:
            target_sq = move[2:4]
            if target_sq in pieces:
                captured_piece = pieces[target_sq][1]
                material = {'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1}.get(captured_piece, 0)
        
        # Check promotion
        if len(move) > 4:
            promotion = move[-1]
            material += {'q': 9, 'r': 5, 'b': 3, 'n': 3}.get(promotion, 0)
        
        # Center control bonus
        center_bonus = 0
        if len(move) >= 4:
            target = move[2:4]
            x = ord(target[0]) - ord('a')
            y = int(target[1]) - 1
            # Center square control
            if (3 <= x <= 4) and (3 <= y <= 4):
                center_bonus = 0.5
        
        # King safety penalty
        king_safety = 0
        if len(move) >= 4 and move[0:2] in pieces and pieces[move[0:2]][1] == 'K':
            king_safety = -0.5  # discourage moving king unless necessary
        
        return material + center_bonus + king_safety
    
    # Find move with highest evaluation
    best_move = legal_moves[0]
    best_score = -999
    
    for move in legal_moves:
        score = evaluate_move(move)
        if score > best_score:
            best_score = score
            best_move = move
        elif score == best_score:
            # Randomize between equally good moves
            if np.random.rand() > 0.5:
                best_move = move
    
    return best_move
