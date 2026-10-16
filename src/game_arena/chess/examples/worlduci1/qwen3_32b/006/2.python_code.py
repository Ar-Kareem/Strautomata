
import copy
from itertools import product

def policy(pieces: dict[str, str], to_play: str) -> str:
    # Map the player color
    player_color = to_play[0]  # 'w' or 'b'
    enemy_color = 'w' if player_color == 'b' else 'b'
    
    # Locate enemy king for checkmate evaluation
    enemy_king_square = None
    for square, piece in pieces.items():
        if piece[0] == enemy_color and piece[1] == 'K':
            enemy_king_square = square
            break
    
    # Coordinates <-> Square conversion
    def coord_square(f, r): return chr(f + ord('a')), str(r + 1)
    def square_coord(square):
        return ord(square[0]) - ord('a'), int(square[1]) - 1
    
    # Heuristic to prioritize moves
    def evaluate_moves(moves):
        # First priority: checkmate
        for move in moves:
            if move[2:4] == enemy_king_square:
                return move
        
        # If no checkmate, prioritize pawn promotions to queen
        queen_promotions = []
        for move in moves:
            if len(move) > 4 and move[4] == 'q':
                queen_promotions.append(move)
        if queen_promotions:
            return queen_promotions[0]
        
        # Score each move
        def score(move_str):
            source = move_str[:2]
            dest = move_str[2:4]
            
            # Is this a capture?
            is_capture = dest in pieces and pieces[dest][0] == enemy_color
            
            if is_capture:
                captured_val = {'P':1, 'N':3, 'B':3, 'R':5, 'Q':9, 'K':0}.get(pieces[dest][1], 0)
                moving_val = {'P':1, 'N':3, 'B':3, 'R':5, 'Q':9, 'K':0}.get(pieces[source][1], 0)
                return captured_val - moving_val  # Material gain
            
            # Positional improvement - how far is destination from center for both players
            def center_proximity(square):
                f, r = square_coord(square)
                # Center files: d (3), e (4)
                file_score = 4 - abs(4 - f) if abs(3 - f) < 4 else max(0, 1)
                
                # Center rank depends on player's color
                center_ranks = [3, 4]
                if player_color == 'w':
                    # For white, we want to get closer to the opponent's side (rank >4)
                    rank_score = 4 - abs(4 - r) if r <= 7 else max(0, 1) - r + 3
                    
                else:
                    # For black, we want to get closer to the white side (rank <4)
                    rank_score = 4 - abs(4 - r) if r >= 0 else r - 3
                
                return file_score + rank_score
        
        source_val = {'P':1, 'N':3, 'B':3, 'R':5, 'Q':9, 'K':1000}.get(pieces[source][1])
        pos_diff = center_proximity(dest) - center_proximity(source)
        return pos_diff * source_val
        
        # Sort captured moves by captured piece value
        non_capture_moves = [m for m in moves if not any(m.startswith(s) for s in pieces if pieces[s][0] == player_color and s in pieces and pieces[s][1] == 'P')]
        
        non_capture_moves.sort(key=lambda m: score(m), reverse=True)
        return non_capture_moves[0]
    
    # Move generation
    def generate_moves(piece, square):
        f, r = square_coord(square)
        moves = []
        
        if piece[1] == 'N':  # Knight
            deltas = list(product([2, -2], [1, -1])) + list(product([1, -1], [2, -2]))
            for df, dr in deltas:
                nf, nr = f + df, r + dr
                if 0 <= nf < 8 and 0 <= nr < 8:
                    new_sq = ''.join(coord_square(nf, nr))
                    if new_sq in pieces and pieces[new_sq][0] != player_color:
                        moves.append(square + new_sq)
                    elif new_sq not in pieces:
                        moves.append(square + new_sq)
                        
        elif piece[1] == 'B':  # Bishop
            for dr, df in product([1, -1], [1, -1]):
                for step in range(1,8):
                    nf, nr = f + df * step, r + dr * step
                    if 0 <= nf < 8 and 0 <= nr < 8:
                        new_sq = ''.join(coord_square(nf, nr))
                        if new_sq in pieces:
                            if pieces[new_sq][0] != player_color:
                                moves.append(square + new_sq)
                            break
                        else:
                            moves.append(square + new_sq)
                    else:
                        break
                        
        elif piece[1] == 'R':  # Rook
            for dr, df in product([1, -1, 0], [0, 1, -1]):
                if dr == df == 0: continue  # Not moving
                for step in range(1,8):
                    nf, nr = f + df * step, r + dr * step
                    if 0 <= nf < 8 and 0 <= nr < 8:
                        new_sq = ''.join(coord_square(nf, nr))
                        if new_sq in pieces:
                            if pieces[new_sq][0] != player_color:
                                moves.append(square + new_sq)
                            break
                        else:
                            moves.append(square + new_sq)
                    else:
                        break
                        
        elif piece[1] == 'Q':  # Queen (combines Rook + Bishop)
            for dr, df in product([1, -1, 0], [1, -1, 0]):
                if dr == df == 0: continue
                for step in range(1,8):
                    nf, nr = f + df * step, r + dr * step
                    if 0 <= nf < 8 and 0 <= nr < 8:
                        new_sq = ''.join(coord_square(nf, nr))
                        if new_sq in pieces:
                            if pieces[new_sq][0] != player_color:
                                moves.append(square + new_sq)
                            break
                        else:
                            moves.append(square + new_sq)
                    else:
                        break
                        
        elif piece[1] == 'K':  # King
            for dr, df in product([-1,0,1], [-1,0,1]):
                if dr == df == 0: continue
                new_f, new_r = f + df, r + dr
                if 0 <= new_f < 8 and 0 <= new_r < 8:
                    new_sq = ''.join(coord_square(new_f, new_r))
                    if new_sq not in pieces or pieces[new_sq][0] != player_color:
                        moves.append(square + new_sq)
                        
        elif piece[1] == 'P':  # Pawn
            direction = 1 if player_color == 'w' else -1
            # Single step forward
            forward = r + direction
            if 0 <= forward < 8:
                new_sq1 = ''.join(coord_square(f, forward))
                if new_sq1 not in pieces:
                    moves.append(square + new_sq1)
                    
                    # Double step from rank 2/7
                    if (player_color == 'w' and r == 1) or (player_color == 'b' and r == 6):
                        new_sq2 = ''.join(coord_square(f, r + 2*direction))
                        if new_sq2 not in pieces and square + new_sq1 not in moves:
                            moves.append(square + new_sq2)
                            
            # Diagonal captures
            for side in [-1, 1]:
                new_f, new_r = f + side, r + direction
                if 0 <= new_f < 8 and 0 <= new_r < 8:
                    new_sq = ''.join(coord_square(new_f, new_r))
                    if new_sq in pieces and pieces[new_sq][0] != player_color:
                        moves.append(square + new_sq)
                        # Add promotion options if at end rank
                        if new_r == 7 or new_r == 0:
                            for promo in ['q', 'r', 'b', 'n']:
                                moves.append(square + new_sq + promo)
                                
        return moves

    # Collect all pseudo-legal moves
    pseudo_moves = []
    for square, piece in pieces.items():
        if piece[0] == player_color:
            piece_moves = generate_moves(piece, square)
            pseudo_moves.extend(piece_moves)
    
    # Filter for actual legal moves (not putting king in check)
    legal_moves = []
    
    for move in pseudo_moves:
        source = move[:2]
        dest = move[2:4]
        
        if source not in pieces or (dest in pieces and pieces[dest][0] == player_color):
            continue
            
        # Simulate move
        new_pieces = copy.copy(pieces)
        moving_piece = new_pieces[source]
        if dest in new_pieces:
            captured = new_pieces[dest]
            new_pieces[dest] = moving_piece
            if captured[0] == enemy_color:
                # Capture
                pass
            else:
                continue  # Can't capture own piece
                
        else:
            new_pieces[dest] = moving_piece
            
        if source in new_pieces:
            del new_pieces[source]
        
        # Check if this move causes check
        player_in_check = False
        for enemy_square, enemy_piece in new_pieces.items():
            if enemy_piece[0] != enemy_color or enemy_piece[1] == 'K':
                continue
                
            # Determine if enemy piece attacks player's king
            if enemy_square == source:
                # Moving piece was king? Not possible here
                continue
                
            for king_square, king_piece in new_pieces.items():
                if king_piece[0] == player_color and king_piece[1] == 'K':
                    player_king = king_square
                    
            # Pawn attack pattern
            if enemy_piece[1] == 'P':
                enemy_f, enemy_r = square_coord(enemy_square)
                if player_color == 'w':
                    if abs(enemy_f - square_coord(player_king)[0]) == 1 and square_coord(player_king)[1] == enemy_r+1:
                        player_in_check = True
                        break
                else:
                    if abs(enemy_f - square_coord(player_king)[0]) == 1 and square_coord(player_king)[1] == enemy_r-1:
                        player_in_check = True
                        break
                        
            # Knight attack pattern
            elif enemy_piece[1] == 'N':
                if sum(abs(x) for x in [square_coord(enemy_square)[0] - square_coord(player_king)[0], square_coord(enemy_square)[1] - square_coord(player_king)[1]]) == 3:
                    player_in_check = True
                    break
                    
            # Bishop attack pattern
            elif enemy_piece[1] == 'B':
                if abs(square_coord(enemy_square)[0] - square_coord(player_king)[0]) == abs(square_coord(enemy_square)[1] - square_coord(player_king)[1]):
                    path_clear = True
                    step = 1
                    while path_clear:
                        if step >= min(abs(square_coord(enemy_square)[0] - square_coord(player_king)[0]), abs(square_coord(enemy_square)[1] - square_coord(player_king)[1])):
                            player_in_check = True
                            break
                        nf = square_coord(enemy_square)[0] + (square_coord(player_king)[0] - square_coord(enemy_square)[0]) * step // abs(square_coord(player_king)[0] - square_coord(enemy_square)[0]) if abs(square_coord(player_king)[0] - square_coord(enemy_square)[0]) != 0 else 0
                        nr = square_coord(enemy_square)[1] + (square_coord(player_king)[1] - square_coord(enemy_square)[1]) * step // abs(square_coord(player_king)[1] - square_coord(enemy_square)[1]) if abs(square_coord(player_king)[1] - square_coord(enemy_square)[1]) != 0 else 0
                        check_square = coord_square(nf, nr)[0] + coord_square(nf, nr)[1]
                        
                        if check_square in new_pieces:
                            player_in_check = True
                            break
                        step += 1
                    
            # Rook and Queen attack pattern (combine with bishop)
            elif enemy_piece[1] in ['R', 'Q']:
                straight = abs(square_coord(enemy_square)[0] - square_coord(player_king)[0]) == 0 or abs(square_coord(enemy_square)[1] - square_coord(player_king)[1]) == 0
                diagonal = abs(square_coord(enemy_square)[0] - square_coord(player_king)[0]) == abs(square_coord(enemy_square)[1] - square_coord(player_king)[1])
                
                if not (straight and diagonal):
                    if not straight and not diagonal:
                        continue  # can't attack
                    
                path_clear = True
                for step in range(1, 8):
                    if straight:
                        axis = 0 if abs(square_coord(enemy_square)[0] - square_coord(player_king)[0]) > abs(square_coord(enemy_square)[1] - square_coord(player_king)[1]) else 1
                        
                        if axis == 0:
                            if step >= abs(square_coord(enemy_square)[0] - square_coord(player_king)[0]) or square_coord(enemy_square)[1] != square_coord(player_king)[1]:
                                break
                            nf = square_coord(enemy_square)[0] + (square_coord(player_king)[0] - square_coord(enemy_square)[0]) * step // abs(square_coord(player_king)[0] - square_coord(enemy_square)[0])
                            nr = square_coord(enemy_square)[1]
                        else:
                            if step >= abs(square_coord(enemy_square)[1] - square_coord(player_king)[1]) or square_coord(enemy_square)[0] != square_coord(player_king)[0]:
                                break
                            nf = square_coord(enemy_square)[0]
                            nr = square_coord(enemy_square)[1] + (square_coord(player_king)[1] - square_coord(enemy_square)[1]) * step // abs(square_coord(player_king)[1] - square_coord(enemy_square)[1])
                            
                        check_square = coord_square(nf, nr)
                        if check_square in new_pieces and check_square != player_king:
                            break
                        if check_square == player_king:
                            player_in_check = True
                            break
                            
            # King attack pattern (adjacent square)
            elif enemy_piece[1] == 'K':
                if abs(square_coord(enemy_square)[0] - square_coord(player_king)[0]) <=1 and abs(square_coord(enemy_square)[1] - square_coord(player_king)[1]) <=1:
                    player_in_check = True
                    break
                    
        if not player_in_check:
            legal_moves.append(move)
    
    if not legal_moves:
        return ''
        
    # Score and return best move
    best_move = None
    best_score = -1000
    
    for move in legal_moves:
        if not move:
            continue
            
        if move[2:4] == enemy_king_square:
            return move
            
        # Score based on piece value
        source = move[:2]
        dest = move[2:4]
        
        if dest in pieces and pieces[dest][0] == enemy_color:
            captured_value = {'P':1, 'N':3, 'B':3, 'R':5, 'Q':9, 'K':999}.get(pieces[dest][1], 0)
            moving_value = {'P':1, 'N':3, 'B':3, 'R':5, 'Q':9, 'K':999}.get(pieces[source][1], 0)
            score = captured_value - moving_value
            
            if len(move) > 4:  # Promotion
                promo = move[4]
                promo_value = {'q':9, 'r':5, 'n':3, 'b':3}.get(promo.lower(), 0)
                if promo_value:
                    score += (promo_value - 1)  # Add value of queen promotion for pawns
                    
        else:  # Non-capture, positional evaluation
            f1, r1 = square_coord(source)
            f2, r2 = square_coord(dest)
            
            # Center file: 3 (d), 4 (e)
            file_score = 4 - abs(3 - f2) + 4 - abs(4 - f2)
            rank_score = 4 - abs(3 - r2) + 4 - abs(4 - r2)
            
            # Score as distance from edge
            score = file_score + rank_score
            
            # Bonus for moving queen or rook to central rank
            if pieces[source][1] in ['Q', 'R', 'K']:
                score += 5
                
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move if best_move else legal_moves[0]
