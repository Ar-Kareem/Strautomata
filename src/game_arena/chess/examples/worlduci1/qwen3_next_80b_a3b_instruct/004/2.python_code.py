
import numpy as np
from typing import Dict, List, Tuple

def policy(pieces: Dict[str, str], to_play: str) -> str:
    # Define piece values for material evaluation
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    color = 'w' if to_play == 'white' else 'b'
    opponent_color = 'b' if color == 'w' else 'w'
    
    # Convert square to coordinate: 'e4' -> (4, 3) [file: a=0, h=7; rank: 1=0, 8=7]
    def square_to_coord(sq):
        file = ord(sq[0]) - ord('a')
        rank = int(sq[1]) - 1
        return file, rank
    
    # Convert coordinate to square
    def coord_to_square(file, rank):
        return chr(ord('a') + file) + str(rank + 1)
    
    # Get piece at square or None
    def get_piece(sq):
        return pieces.get(sq, None)
    
    # Check if square is on board
    def on_board(file, rank):
        return 0 <= file <= 7 and 0 <= rank <= 7
    
    # Get all legal moves for the given color
    def get_all_legal_moves():
        moves = []
        for sq, piece in pieces.items():
            if piece[0] != color:
                continue
            piece_type = piece[1]
            file, rank = square_to_coord(sq)
            if piece_type == 'P':
                # Pawn moves
                direction = 1 if color == 'w' else -1
                # Forward moves
                for fwd_step in [1, 2]:
                    new_rank = rank + direction * fwd_step
                    if not on_board(file, new_rank):
                        break
                    new_sq = coord_to_square(file, new_rank)
                    if new_sq in pieces:
                        break
                    moves.append(sq + new_sq)
                    if fwd_step == 1:  # Only allow double step from starting rank
                        if (color == 'w' and rank != 1) or (color == 'b' and rank != 6):
                            break
                # Captures
                for df in [-1, 1]:
                    new_file = file + df
                    new_rank = rank + direction
                    if on_board(new_file, new_rank):
                        new_sq = coord_to_square(new_file, new_rank)
                        if new_sq in pieces and pieces[new_sq][0] == opponent_color:
                            if new_rank == 7 or new_rank == 0:  # Promotion
                                for promo in ['q', 'r', 'b', 'n']:
                                    moves.append(sq + new_sq + promo)
                            else:
                                moves.append(sq + new_sq)
            elif piece_type == 'N':
                # Knight moves
                knight_moves = [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]
                for df, dr in knight_moves:
                    new_file = file + df
                    new_rank = rank + dr
                    if on_board(new_file, new_rank):
                        new_sq = coord_to_square(new_file, new_rank)
                        if new_sq not in pieces or pieces[new_sq][0] != color:
                            moves.append(sq + new_sq)
            elif piece_type in ['B', 'R', 'Q']:
                # Bishops, Rooks, Queens
                directions = []
                if piece_type in ['B', 'Q']:
                    # Diagonals
                    directions.extend([(-1,-1), (-1,1), (1,-1), (1,1)])
                if piece_type in ['R', 'Q']:
                    # Orthogonals
                    directions.extend([(-1,0), (1,0), (0,-1), (0,1)])
                for df, dr in directions:
                    for step in range(1, 8):
                        new_file = file + df * step
                        new_rank = rank + dr * step
                        if not on_board(new_file, new_rank):
                            break
                        new_sq = coord_to_square(new_file, new_rank)
                        if new_sq in pieces:
                            if pieces[new_sq][0] == opponent_color:
                                moves.append(sq + new_sq)
                            break  # Blocked by own or opponent piece
                        moves.append(sq + new_sq)
            elif piece_type == 'K':
                # King moves
                king_moves = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
                for df, dr in king_moves:
                    new_file = file + df
                    new_rank = rank + dr
                    if on_board(new_file, new_rank):
                        new_sq = coord_to_square(new_file, new_rank)
                        if new_sq not in pieces or pieces[new_sq][0] != color:
                            moves.append(sq + new_sq)
        return moves
    
    # Count material - returns material advantage for the current player
    def evaluate_material():
        material = 0
        for piece in pieces.values():
            if piece[0] == color:
                material += piece_values[piece[1]]
            else:
                material -= piece_values[piece[1]]
        return material
    
    # Check if a move creates a check
    def will_check_if_made(move):
        # Simulate the move
        from_sq, to_sq = move[:2], move[2:4]
        captured_piece = pieces.get(to_sq, None)
        
        # Temporarily update the board
        piece = pieces[from_sq]
        del pieces[from_sq]
        pieces[to_sq] = piece
        
        # Check if the opponent can capture the king
        king_sq = None
        for sq, p in pieces.items():
            if p[1] == 'K' and p[0] == color:
                king_sq = sq
                break
        
        if not king_sq:
            # This shouldn't happen
            result = False
        else:
            king_file, king_rank = square_to_coord(king_sq)
            # Check opponent's pieces for attacks on king
            opponent_moves = []
            for sq, p in pieces.items():
                if p[0] == opponent_color:
                    ptype = p[1]
                    of, ork = square_to_coord(sq)
                    
                    if ptype == 'P':
                        dir = -1 if opponent_color == 'w' else 1
                        for df in [-1, 1]:
                            if (king_file, king_rank) == (of + df, ork + dir):
                                result = True
                                break
                        else:
                            continue
                        break
                    elif ptype == 'N':
                        knight_moves = [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]
                        for df, dr in knight_moves:
                            if (king_file, king_rank) == (of + df, ork + dr):
                                result = True
                                break
                        else:
                            continue
                        break
                    elif ptype in ['B', 'R', 'Q']:
                        # Check if in line of attack
                        dir = (king_file - of, king_rank - ork)
                        distance = max(abs(dir[0]), abs(dir[1]))
                        if distance == 0:
                            continue
                        dir_norm = (dir[0] // max(1, abs(dir[0])), dir[1] // max(1, abs(dir[1])))
                        if ptype == 'B' and (dir[0] == 0 or dir[1] == 0):
                            continue
                        if ptype == 'R' and (dir[0] != 0 and dir[1] != 0):
                            continue
                        # Check if path is clear from opponent to king
                        clear_path = True
                        for step in range(1, distance):
                            check_file = of + dir_norm[0] * step
                            check_rank = ork + dir_norm[1] * step
                            check_sq = coord_to_square(check_file, check_rank)
                            if check_sq in pieces and check_sq != to_sq:
                                clear_path = False
                                break
                        if clear_path and ((ptype == 'Q') or 
                                           (ptype == 'B' and dir[0] != 0 and dir[1] != 0) or 
                                           (ptype == 'R' and (dir[0] == 0 or dir[1] == 0))):
                            result = True
                            break
                        else:
                            continue
                    else:  # King
                        for df in [-1,0,1]:
                            for dr in [-1,0,1]:
                                if (king_file, king_rank) == (of + df, ork + dr):
                                    result = True
                                    break
                            else:
                                continue
                            break
                        else:
                            continue
                        break
                else:
                    continue
                break
            else:
                result = False
        
        # Restore board
        pieces[from_sq] = piece
        if captured_piece:
            pieces[to_sq] = captured_piece
        else:
            del pieces[to_sq]
        
        return result
    
    # Check for checkmate or stalemate
    def is_mate():
        all_moves = get_all_legal_moves()
        if not all_moves:
            # Check if king is in check
            king_sq = None
            for sq, p in pieces.items():
                if p[1] == 'K' and p[0] == color:
                    king_sq = sq
                    break
            
            if king_sq:
                king_file, king_rank = square_to_coord(king_sq)
                for sq, p in pieces.items():
                    if p[0] == opponent_color:
                        ptype = p[1]
                        of, ork = square_to_coord(sq)
                        
                        if ptype == 'P':
                            dir = -1 if opponent_color == 'w' else 1
                            for df in [-1, 1]:
                                if (king_file, king_rank) == (of + df, ork + dir):
                                    return True
                        elif ptype == 'N':
                            knight_moves = [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]
                            for df, dr in knight_moves:
                                if (king_file, king_rank) == (of + df, ork + dr):
                                    return True
                        elif ptype in ['B', 'R', 'Q']:
                            dir = (king_file - of, king_rank - ork)
                            distance = max(abs(dir[0]), abs(dir[1]))
                            if distance == 0:
                                continue
                            dir_norm = (dir[0] // max(1, abs(dir[0])), dir[1] // max(1, abs(dir[1])))
                            if ptype == 'B' and (dir[0] == 0 or dir[1] == 0):
                                continue
                            if ptype == 'R' and (dir[0] != 0 and dir[1] != 0):
                                continue
                            # Check if path is clear
                            clear_path = True
                            for step in range(1, distance):
                                check_file = of + dir_norm[0] * step
                                check_rank = ork + dir_norm[1] * step
                                check_sq = coord_to_square(check_file, check_rank)
                                if check_sq in pieces:
                                    clear_path = False
                                    break
                            if clear_path and ((ptype == 'Q') or 
                                               (ptype == 'B' and dir[0] != 0 and dir[1] != 0) or 
                                               (ptype == 'R' and (dir[0] == 0 or dir[1] == 0))):
                                return True
                        else:  # King
                            for df in [-1,0,1]:
                                for dr in [-1,0,1]:
                                    if (king_file, king_rank) == (of + df, ork + dr):
                                        return True
            return False  # Stalemate
        return False
    
    # Simple static evaluation of board position
    def evaluate_position():
        material = evaluate_material()
        
        # Positional bonuses
        center_control = 0
        mobility = 0
        king_safety = 0
        pawn_structure = 0
        
        for sq, piece in pieces.items():
            if piece[0] != color:
                continue
            file, rank = square_to_coord(sq)
            piece_type = piece[1]
            
            # Central control bonus
            if piece_type == 'P':
                if file in [3, 4] and rank in [3, 4]:  # e4, d4, e5, d5
                    center_control += 0.3
                # Pawn structure: isolate factors
                left = coord_to_square(file-1, rank)
                right = coord_to_square(file+1, rank)
                if left not in pieces and right not in pieces:
                    pawn_structure -= 0.1
            elif piece_type == 'N':
                if file in [2, 5] and rank in [2, 5]:  # Knights on outposts
                    center_control += 0.4
                # Control central squares
                central_squares = ['d4', 'd5', 'e4', 'e5']
                for csq in central_squares:
                    if get_piece(csq) is None:
                        # Knight can reach center?
                        nf, nr = square_to_coord(csq)
                        if abs(nf - file) <= 2 and abs(nr - rank) <= 2:
                            center_control += 0.1
            elif piece_type == 'B':
                # Diagonal control
                if file in [3, 4] and rank in [3, 4]:
                    center_control += 0.3
            elif piece_type == 'R':
                # Open files
                open_file = True
                for r in range(8):
                    fsq = coord_to_square(file, r)
                    if fsq != sq and fsq in pieces:
                        if pieces[fsq][0] == color:
                            open_file = False
                            break
                if open_file:
                    center_control += 0.2
            elif piece_type == 'K':
                # King safety: better in corners
                if rank == 0 or rank == 7:
                    if file == 0 or file == 7 or file == 1 or file == 6:
                        king_safety += 0.5
                # If king has moved and hasn't castled, penalize
                if (color == 'w' and 'e1' == sq) or (color == 'b' and 'e8' == sq):
                    king_safety -= 0.7
        
        # Mobility bonus (number of legal moves)
        legal_moves = get_all_legal_moves()
        mobility = len(legal_moves) * 0.1
        
        # Threat detection: avoid placing pieces under attack
        threats = 0
        for sq, piece in pieces.items():
            if piece[0] == color:
                file, rank = square_to_coord(sq)
                # Is this piece attacked by opponent?
                for osq, opiece in pieces.items():
                    if opiece[0] == opponent_color:
                        of, ork = square_to_coord(osq)
                        opiece_type = opiece[1]
                        
                        # Simple attack check for this piece's position
                        if opiece_type == 'P':
                            dir = -1 if opponent_color == 'w' else 1
                            if (file, rank) == (of + 1, ork + dir) or (file, rank) == (of - 1, ork + dir):
                                threats += 0.3
                        elif opiece_type == 'N':
                            knight_moves = [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]
                            for df, dr in knight_moves:
                                if (file, rank) == (of + df, ork + dr):
                                    threats += 0.4
                        elif opiece_type in ['B', 'R', 'Q']:
                            dir = (file - of, rank - ork)
                            distance = max(abs(dir[0]), abs(dir[1]))
                            if distance == 0:
                                continue
                            dir_norm = (dir[0] // max(1, abs(dir[0])), dir[1] // max(1, abs(dir[1])))
                            if opiece_type == 'B' and (dir[0] == 0 or dir[1] == 0):
                                continue
                            if opiece_type == 'R' and (dir[0] != 0 and dir[1] != 0):
                                continue
                            # Check if path is clear
                            clear_path = True
                            for step in range(1, distance):
                                check_file = of + dir_norm[0] * step
                                check_rank = ork + dir_norm[1] * step
                                check_sq = coord_to_square(check_file, check_rank)
                                if check_sq in pieces:
                                    clear_path = False
                                    break
                            if clear_path and ((opiece_type == 'Q') or 
                                               (opiece_type == 'B' and dir[0] != 0 and dir[1] != 0) or 
                                               (opiece_type == 'R' and (dir[0] == 0 or dir[1] == 0))):
                                threats += 0.5
        
        evaluation = material + center_control + mobility + king_safety - threats + pawn_structure
        return evaluation
    
    # Minimax with alpha-beta pruning (depth-limited)
    def minimax(depth, alpha, beta, maximizing_player):
        legal_moves = get_all_legal_moves()
        
        if depth == 0 or len(legal_moves) == 0:
            return evaluate_position(), None
            
        best_move = None
        
        if maximizing_player:
            max_eval = float('-inf')
            # Order moves: captures first, then checks
            def move_priority(move):
                to_sq = move[2:4]
                if to_sq in pieces and pieces[to_sq][0] == opponent_color:
                    # Capture move
                    captured = pieces[to_sq]
                    return -piece_values[captured[1]]  # Higher priority for higher value captures
                else:
                    # Quiet moves
                    return 0
            
            # Sort by capture value
            ordered_moves = sorted(legal_moves, key=move_priority)
            
            for move in ordered_moves:
                # Simulate move
                from_sq, to_sq = move[:2], move[2:4]
                captured_piece = pieces.get(to_sq, None)
                piece = pieces[from_sq]
                del pieces[from_sq]
                pieces[to_sq] = piece
                
                eval_score, _ = minimax(depth - 1, alpha, beta, False)
                
                # Restore board
                pieces[from_sq] = piece
                if captured_piece:
                    pieces[to_sq] = captured_piece
                else:
                    del pieces[to_sq]
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Pruning
            
            return max_eval, best_move
        else:
            min_eval = float('inf')
            def move_priority(move):
                to_sq = move[2:4]
                if to_sq in pieces and pieces[to_sq][0] == color:
                    # Capture move
                    captured = pieces[to_sq]
                    return -piece_values[captured[1]]
                else:
                    return 0
            
            ordered_moves = sorted(legal_moves, key=move_priority)
            
            for move in ordered_moves:
                from_sq, to_sq = move[:2], move[2:4]
                captured_piece = pieces.get(to_sq, None)
                piece = pieces[from_sq]
                del pieces[from_sq]
                pieces[to_sq] = piece
                
                eval_score, _ = minimax(depth - 1, alpha, beta, True)
                
                # Restore board
                pieces[from_sq] = piece
                if captured_piece:
                    pieces[to_sq] = captured_piece
                else:
                    del pieces[to_sq]
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Pruning
            
            return min_eval, best_move
    
    # First check for immediate checkmate in one move
    legal_moves = get_all_legal_moves()
    
    for move in legal_moves:
        from_sq, to_sq = move[:2], move[2:4]
        captured_piece = pieces.get(to_sq, None)
        piece = pieces[from_sq]
        
        # Simulate move to check if it's checkmate
        del pieces[from_sq]
        pieces[to_sq] = piece
        
        # Check if opponent has any legal moves after this
        opponent_legal_moves = []
        for sq, p in pieces.items():
            if p[0] == opponent_color:
                ptype = p[1]
                of, ork = square_to_coord(sq)
                
                # Re-generate all opponent moves
                if ptype == 'P':
                    dir = 1 if opponent_color == 'b' else -1
                    for fwd_step in [1, 2]:
                        new_rank = ork + dir * fwd_step
                        if not on_board(of, new_rank):
                            break
                        new_sq = coord_to_square(of, new_rank)
                        if new_sq in pieces:
                            break
                        opponent_legal_moves.append(sq + new_sq)
                        if fwd_step == 1:
                            if (opponent_color == 'b' and ork != 1) or (opponent_color == 'w' and ork != 6):
                                break
                    for df in [-1, 1]:
                        new_file = of + df
                        new_rank = ork + dir
                        if on_board(new_file, new_rank):
                            new_sq = coord_to_square(new_file, new_rank)
                            if new_sq in pieces and pieces[new_sq][0] == color:
                                if new_rank == 7 or new_rank == 0:
                                    for promo in ['q', 'r', 'b', 'n']:
                                        opponent_legal_moves.append(sq + new_sq + promo)
                                else:
                                    opponent_legal_moves.append(sq + new_sq)
                elif ptype == 'N':
                    knight_moves = [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]
                    for df, dr in knight_moves:
                        new_file = of + df
                        new_rank = ork + dr
                        if on_board(new_file, new_rank):
                            new_sq = coord_to_square(new_file, new_rank)
                            if new_sq not in pieces or pieces[new_sq][0] != opponent_color:
                                opponent_legal_moves.append(sq + new_sq)
                elif ptype in ['B', 'R', 'Q']:
                    directions = []
                    if ptype in ['B', 'Q']:
                        directions.extend([(-1,-1), (-1,1), (1,-1), (1,1)])
                    if ptype in ['R', 'Q']:
                        directions.extend([(-1,0), (1,0), (0,-1), (0,1)])
                    for df, dr in directions:
                        for step in range(1, 8):
                            new_file = of + df * step
                            new_rank = ork + dr * step
                            if not on_board(new_file, new_rank):
                                break
                            new_sq = coord_to_square(new_file, new_rank)
                            if new_sq in pieces:
                                if pieces[new_sq][0] != opponent_color:
                                    opponent_legal_moves.append(sq + new_sq)
                                break
                            opponent_legal_moves.append(sq + new_sq)
                elif ptype == 'K':
                    king_moves = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
                    for df, dr in king_moves:
                        new_file = of + df
                        new_rank = ork + dr
                        if on_board(new_file, new_rank):
                            new_sq = coord_to_square(new_file, new_rank)
                            if new_sq not in pieces or pieces[new_sq][0] != opponent_color:
                                opponent_legal_moves.append(sq + new_sq)
        
        # Restore board
        pieces[from_sq] = piece
        if captured_piece:
            pieces[to_sq] = captured_piece
        else:
            del pieces[to_sq]
        
        # If opponent has no legal moves after this move, it's checkmate
        if not opponent_legal_moves:
            return move
    
    # Check for mate in 1 (opponent wins) - avoid this
    # Also check for material-winning moves first
    best_capture = None
    max_capture_value = 0
    move_priority = {}
    
    for move in legal_moves:
        to_sq = move[2:4]
        if to_sq in pieces and pieces[to_sq][0] == opponent_color:
            captured = pieces[to_sq]
            capture_value = piece_values[captured[1]]
            if capture_value > max_capture_value:
                max_capture_value = capture_value
                best_capture = move
        # Store move priority for later sorting
        move_priority[move] = 0
        if to_sq in pieces and pieces[to_sq][0] == opponent_color:
            move_priority[move] = 1000 + piece_values[pieces[to_sq][1]]
        elif move[2:4] in ['d4', 'e4', 'd5', 'e5']:
            move_priority[move] = 500
    
    # If we can capture a queen, do it
    if max_capture_value >= 9:
        return best_capture
    
    # Try iterative deepening - search depth 1, then 2, then 3
    depth = 2
    best_move = legal_moves[0]
    
    # Make sure we don't make moves that let opponent capture our queen
    # Filter out moves that expose king or queen to immediate capture
    filtered_moves = []
    for move in legal_moves:
        from_sq, to_sq = move[:2], move[2:4]
        piece = pieces[from_sq]
        captured = pieces.get(to_sq, None)
        
        # Simulate the move
        del pieces[from_sq]
        if to_sq in pieces:
            del pieces[to_sq]
        pieces[to_sq] = piece
        
        # Check if king is under threat after move
        king_sq = None
        for sq, p in pieces.items():
            if p[1] == 'K' and p[0] == color:
                king_sq = sq
                break
        
        if king_sq:
            king_file, king_rank = square_to_coord(king_sq)
            under_threat = False
            for osq, opiece in pieces.items():
                if opiece[0] == opponent_color:
                    of, ork = square_to_coord(osq)
                    opiece_type = opiece[1]
                    
                    if opiece_type == 'P':
                        dir = -1 if opponent_color == 'w' else 1
                        for df in [-1, 1]:
                            if (king_file, king_rank) == (of + df, ork + dir):
                                under_threat = True
                                break
                    elif opiece_type == 'N':
                        for df, dr in [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]:
                            if (king_file, king_rank) == (of + df, ork + dr):
                                under_threat = True
                                break
                    elif opiece_type in ['B', 'R', 'Q']:
                        dir = (king_file - of, king_rank - ork)
                        distance = max(abs(dir[0]), abs(dir[1]))
                        if distance == 0:
                            continue
                        dir_norm = (dir[0] // max(1, abs(dir[0])), dir[1] // max(1, abs(dir[1])))
                        if opiece_type == 'B' and (dir[0] == 0 or dir[1] == 0):
                            continue
                        if opiece_type == 'R' and (dir[0] != 0 and dir[1] != 0):
                            continue
                        clear_path = True
                        for step in range(1, distance):
                            check_file = of + dir_norm[0] * step
                            check_rank = ork + dir_norm[1] * step
                            check_sq = coord_to_square(check_file, check_rank)
                            if check_sq in pieces:
                                clear_path = False
                                break
                        if clear_path and ((opiece_type == 'Q') or 
                                           (opiece_type == 'B' and dir[0] != 0 and dir[1] != 0) or 
                                           (opiece_type == 'R' and (dir[0] == 0 or dir[1] == 0))):
                            under_threat = True
                            break
            if under_threat and piece[1] == 'Q' or piece[1] == 'K':
                pass  # Skip this move - too dangerous
            else:
                filtered_moves.append(move)
        else:
            filtered_moves.append(move)
        
        # Restore board
        pieces[from_sq] = piece
        if captured:
            pieces[to_sq] = captured
        else:
            del pieces[to_sq]
    
    legal_moves = filtered_moves if filtered_moves else legal_moves
    
    # Use minimax search if legal moves remain
    if legal_moves:
        if len(legal_moves) == 1:
            return legal_moves[0]
        
        _, selected_move = minimax(depth, float('-inf'), float('inf'), True)
        
        # Fallback: pick best capture or center move if minimax fails
        if selected_move is None:
            for move in legal_moves:
                if move in move_priority and move_priority[move] > 500:
                    selected_move = move
                    break
            if selected_move is None:
                selected_move = legal_moves[0]
        
        return selected_move

    # This shouldn't happen but handle edge case
    return legal_moves[0] if legal_moves else 'e1e2'
