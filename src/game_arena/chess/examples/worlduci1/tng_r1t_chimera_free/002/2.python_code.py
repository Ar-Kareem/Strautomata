
import random

def policy(pieces: dict[str, str], to_play: str) -> str:
    current_color = 'w' if to_play == 'white' else 'b'
    opponent_color = 'b' if current_color == 'w' else 'w'
    
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    
    def get_legal_moves():
        legal_moves = []
        for from_sq, piece in pieces.items():
            if piece[0] != current_color:
                continue
            piece_type = piece[1]
            from_file, from_rank = from_sq[0], int(from_sq[1])
            directions = []
            if piece_type == 'P':
                if current_color == 'w':
                    directions = [(0, 1), (0, 2), (1, 1), (-1, 1)]
                else:
                    directions = [(0, -1), (0, -2), (1, -1), (-1, -1)]
            elif piece_type == 'N':
                directions = [(1, 2), (2, 1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-1, -2), (-2, -1)]
            elif piece_type == 'B':
                directions = [(i, i) for i in range(-7, 8) if i != 0] + [(i, -i) for i in range(-7, 8) if i != 0]
            elif piece_type == 'R':
                directions = [(i, 0) for i in range(-7, 8) if i != 0] + [(0, i) for i in range(-7, 8) if i != 0]
            elif piece_type == 'Q':
                directions = [(i, 0) for i in range(-7, 8) if i != 0] + [(0, i) for i in range(-7, 8) if i != 0] + \
                             [(i, i) for i in range(-7, 8) if i != 0] + [(i, -i) for i in range(-7, 8) if i != 0]
            elif piece_type == 'K':
                directions = [(i, j) for i in [-1, 0, 1] for j in [-1, 0, 1] if not (i == 0 and j == 0)]
            
            for d in directions:
                dx, dy = d
                new_file = ord(from_file) + dx
                if new_file < ord('a') or new_file > ord('h'):
                    continue
                new_file = chr(new_file)
                new_rank = from_rank + dy
                if new_rank < 1 or new_rank > 8:
                    continue
                to_sq = f"{new_file}{new_rank}"
                if to_sq == from_sq:
                    continue
                if to_sq in pieces and pieces[to_sq][0] == current_color:
                    continue
                move = f"{from_sq}{to_sq}"
                
                if piece_type == 'P':
                    if abs(dx) + abs(dy) == 1:
                        if (current_color == 'w' and dy == 1) or (current_color == 'b' and dy == -1):
                            if to_sq not in pieces:
                                if new_rank == 8 or new_rank == 1:
                                    for promo in ['q', 'r', 'b', 'n']:
                                        legal_moves.append(f"{move}{promo}")
                                else:
                                    legal_moves.append(move)
                    elif abs(dx) == 0 and dy in (2, -2):
                        if (current_color == 'w' and from_rank == 2 and new_rank == 4) or (current_color == 'b' and from_rank == 7 and new_rank == 5):
                            mid_rank = (from_rank + new_rank) // 2
                            mid_sq = f"{from_file}{mid_rank}"
                            if mid_sq not in pieces and to_sq not in pieces:
                                legal_moves.append(move)
                    elif abs(dx) == 1 and dy in (1, -1):
                        if to_sq in pieces and pieces[to_sq][0] == opponent_color:
                            if new_rank == 8 or new_rank == 1:
                                for promo in ['q', 'r', 'b', 'n']:
                                    legal_moves.append(f"{move}{promo}")
                            else:
                                legal_moves.append(move)
                else:
                    legal_moves.append(move)
        return legal_moves
    
    def is_check(move_pieces, color):
        king_sq = None
        for sq, pc in move_pieces.items():
            if pc == color + 'K':
                king_sq = sq
                break
        if not king_sq:
            return False
        attacker_color = 'w' if color == 'b' else 'b'
        for sq, pc in move_pieces.items():
            if pc[0] == attacker_color:
                piece_type = pc[1]
                if piece_type == 'P':
                    dx = abs(ord(sq[0]) - ord(king_sq[0]))
                    dy = int(king_sq[1]) - int(sq[1])
                    if attacker_color == 'w' and dy == 1 and dx == 1:
                        return True
                    elif attacker_color == 'b' and dy == -1 and dx == 1:
                        return True
                else:
                    f, r = sq[0], int(sq[1])
                    kf, kr = king_sq[0], int(king_sq[1])
                    df = abs(ord(f) - ord(kf))
                    dr = abs(r - kr)
                    if piece_type == 'Q':
                        if (df == 0 or dr == 0) or (df == dr):
                            return True
                    elif piece_type == 'R':
                        if df == 0 or dr == 0:
                            return True
                    elif piece_type == 'B':
                        if df == dr:
                            return True
                    elif piece_type == 'N':
                        if (df == 1 and dr == 2) or (df == 2 and dr == 1):
                            return True
                    elif piece_type == 'K':
                        if df <= 1 and dr <= 1:
                            return True
        return False
    
    legal_moves = get_legal_moves()
    if not legal_moves:
        return ''
    
    best_move = None
    max_score = -float('inf')
    for move in legal_moves:
        score = 0
        from_sq = move[:2]
        to_sq = move[2:4]
        promotion = move[4] if len(move) > 4 else None
        
        moving_piece = pieces[from_sq]
        captured_piece = pieces.get(to_sq, None)
        
        if captured_piece and captured_piece[0] == opponent_color:
            score += piece_values[captured_piece[1]] - piece_values[moving_piece[1]]
        
        tmp_pieces = pieces.copy()
        tmp_pieces.pop(from_sq)
        tmp_pieces[to_sq] = moving_piece
        if captured_piece:
            tmp_pieces.pop(to_sq, None)
        if promotion:
            tmp_pieces[to_sq] = moving_piece[0] + promotion.upper()
        
        if is_check(tmp_pieces, opponent_color):
            score += 2
        
        if promotion:
            score += piece_values[promotion.upper()]
        
        if score > max_score or (score == max_score and best_move is None):
            max_score = score
            best_move = move
    
    return best_move if best_move else random.choice(legal_moves)
