
import numpy as np

def policy(pieces: dict[str, str], to_play: str) -> str:
    color = 'w' if to_play == 'white' else 'b'
    enemy_color = 'b' if color == 'w' else 'w'
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 100}
    
    own_pieces = [(sq, pc) for sq, pc in pieces.items() if pc[0] == color]
    max_score = -np.inf
    best_move = None
    
    # Check for captures and promotions
    for sq, pc in own_pieces:
        piece_type = pc[1]
        current_file, current_rank = sq[0], int(sq[1])
        
        # Knight moves
        if piece_type == 'N':
            deltas = [(2, 1), (1, 2), (-1, 2), (-2, 1), (-2, -1), (-1, -2), (1, -2), (2, -1)]
            for df, dr in deltas:
                new_file = chr(ord(current_file) + df)
                new_rank = current_rank + dr
                if 'a' <= new_file <= 'h' and 1 <= new_rank <= 8:
                    dest = f"{new_file}{new_rank}"
                    move = f"{sq}{dest}"
                    score = 0
                    if dest in pieces:
                        target_piece = pieces[dest]
                        if target_piece[0] == enemy_color:
                            score = piece_values.get(target_piece[1], 0)
                    if score > max_score:
                        max_score = score
                        best_move = move
        
        # Pawn moves and captures
        elif piece_type == 'P':
            direction = 1 if color == 'w' else -1
            start_rank = 2 if color == 'w' else 7
            # Captures
            for df in (-1, 1):
                new_file = chr(ord(current_file) + df)
                new_rank = current_rank + direction
                if 'a' <= new_file <= 'h' and 1 <= new_rank <= 8:
                    dest = f"{new_file}{new_rank}"
                    move = f"{sq}{dest}"
                    score = 0
                    if dest in pieces and pieces[dest][0] == enemy_color:
                        score = piece_values.get(pieces[dest][1], 0)
                    # Promotion
                    if new_rank in (1, 8):
                        move += 'q'
                        score += 9  # Queen promotion bonus
                    if score > max_score:
                        max_score = score
                        best_move = move
            # Forward moves
            for dr in [1, 2]:
                if dr == 2 and current_rank != start_rank:
                    continue
                new_rank = current_rank + direction * dr
                if 1 <= new_rank <= 8:
                    dest = f"{current_file}{new_rank}"
                    if dest not in pieces:
                        move = f"{sq}{dest}"
                        score = 0
                        if new_rank in (1, 8):
                            move += 'q'
                            score += 9
                        if score > max_score:
                            max_score = score
                            best_move = move
    
    if best_move:
        return best_move
    
    # Fallback: find any valid move
    for sq, pc in own_pieces:
        piece_type = pc[1]
        current_file, current_rank = sq[0], int(sq[1])
        # Try moving forward for pawns
        if piece_type == 'P':
            direction = 1 if color == 'w' else -1
            new_rank = current_rank + direction
            if 1 <= new_rank <= 8:
                dest = f"{current_file}{new_rank}"
                if dest not in pieces:
                    move = f"{sq}{dest}"
                    if new_rank in (1, 8):
                        move += 'q'
                    return move
        # Try any knight move
        if piece_type == 'N':
            deltas = [(2, 1), (1, 2), (-1, 2), (-2, 1)]
            for df, dr in deltas:
                new_file = chr(ord(current_file) + df)
                new_rank = current_rank + dr
                if 'a' <= new_file <= 'h' and 1 <= new_rank <= 8:
                    dest = f"{new_file}{new_rank}"
                    if dest not in pieces or pieces[dest][0] == enemy_color:
                        return f"{sq}{dest}"
    
    # Fallback: first available move (shouldn't reach here)
    for sq in pieces:
        if pieces[sq][0] == color:
            return sq + sq  # Default invalid, but ensures legal move
    return 'a1a1'  # Absolute fallback
