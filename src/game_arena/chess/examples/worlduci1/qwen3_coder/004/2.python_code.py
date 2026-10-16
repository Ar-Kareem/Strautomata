
import collections

def policy(pieces: dict[str, str], to_play: str) -> str:
    # Map pieces to values
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    
    # Generate all legal moves (placeholder - in real implementation, this is provided)
    # But per problem, we need to select from external legal_moves list which isn't passed
    # So this policy assumes it can generate moves or has access to them
    # Actually the problem says the moves are provided, but the API doesn't show them
    # We'll need to make a move generator - since we can't see legal_moves, we'll 
    # create a simplified move generator to get candidate moves
    
    # Since we do not have access to the legal_moves list, we'll improvise a policy that
    # estimates good moves
    
    def square_to_coords(sq):
        return (ord(sq[0]) - ord('a'), int(sq[1]) - 1)
    
    def coords_to_square(x, y):
        return chr(ord('a') + x) + str(y + 1)
    
    def is_on_board(x, y):
        return 0 <= x < 8 and 0 <= y < 8
    
    def get_color(piece):
        return piece[0]
    
    def get_type(piece):
        return piece[1]
    
    player_color = 'w' if to_play == 'white' else 'b'
    opponent_color = 'b' if player_color == 'w' else 'w'
    
    # Find king position
    player_king_pos = None
    for sq, piece in pieces.items():
        if piece == player_color + 'K':
            player_king_pos = sq
            break
    
    # Simple move generator (very basic - just enough for making decisions)
    def generate_pseudo_legal_moves():
        moves = []
        for sq, piece in pieces.items():
            if get_color(piece) != player_color:
                continue
            x, y = square_to_coords(sq)
            ptype = get_type(piece)
            
            if ptype == 'P':
                # Pawn moves
                dy = 1 if player_color == 'w' else -1
                # Forward move
                nx, ny = x, y + dy
                if is_on_board(nx, ny) and (coords_to_square(nx, ny) not in pieces):
                    # Promotion
                    if ny == 7 or ny == 0:
                        for prom in ['q', 'r', 'b', 'n']:
                            moves.append(sq + coords_to_square(nx, ny) + prom)
                    else:
                        moves.append(sq + coords_to_square(nx, ny))
                    # Double move from start
                    if (player_color == 'w' and y == 1) or (player_color == 'b' and y == 6):
                        n2x, n2y = x, y + 2 * dy
                        if is_on_board(n2x, n2y) and (coords_to_square(n2x, n2y) not in pieces):
                            moves.append(sq + coords_to_square(n2x, n2y))
                # Captures
                for dx in [-1, 1]:
                    nx, ny = x + dx, y + dy
                    if is_on_board(nx, ny):
                        tgt_sq = coords_to_square(nx, ny)
                        if tgt_sq in pieces and get_color(pieces[tgt_sq]) == opponent_color:
                            if ny == 7 or ny == 0:
                                for prom in ['q', 'r', 'b', 'n']:
                                    moves.append(sq + tgt_sq + prom)
                            else:
                                moves.append(sq + tgt_sq)
                                
            elif ptype == 'N':
                for dx, dy in [(2,1),(2,-1),(-2,1),(-2,-1),(1,2),(1,-2),(-1,2),(-1,-2)]:
                    nx, ny = x + dx, y + dy
                    if is_on_board(nx, ny):
                        tgt_sq = coords_to_square(nx, ny)
                        if tgt_sq not in pieces or get_color(pieces[tgt_sq]) != player_color:
                            moves.append(sq + tgt_sq)
                            
            elif ptype == 'B':
                for dx, dy in [(1,1),(1,-1),(-1,1),(-1,-1)]:
                    nx, ny = x, y
                    while True:
                        nx, ny = nx + dx, ny + dy
                        if not is_on_board(nx, ny):
                            break
                        tgt_sq = coords_to_square(nx, ny)
                        if tgt_sq not in pieces:
                            moves.append(sq + tgt_sq)
                        else:
                            if get_color(pieces[tgt_sq]) != player_color:
                                moves.append(sq + tgt_sq)
                            break
                            
            elif ptype == 'R':
                for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                    nx, ny = x, y
                    while True:
                        nx, ny = nx + dx, ny + dy
                        if not is_on_board(nx, ny):
                            break
                        tgt_sq = coords_to_square(nx, ny)
                        if tgt_sq not in pieces:
                            moves.append(sq + tgt_sq)
                        else:
                            if get_color(pieces[tgt_sq]) != player_color:
                                moves.append(sq + tgt_sq)
                            break
                            
            elif ptype == 'Q':
                for dx, dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
                    nx, ny = x, y
                    while True:
                        nx, ny = nx + dx, ny + dy
                        if not is_on_board(nx, ny):
                            break
                        tgt_sq = coords_to_square(nx, ny)
                        if tgt_sq not in pieces:
                            moves.append(sq + tgt_sq)
                        else:
                            if get_color(pieces[tgt_sq]) != player_color:
                                moves.append(sq + tgt_sq)
                            break
                            
            elif ptype == 'K':
                for dx in [-1,0,1]:
                    for dy in [-1,0,1]:
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = x + dx, y + dy
                        if is_on_board(nx, ny):
                            tgt_sq = coords_to_square(nx, ny)
                            if tgt_sq not in pieces or get_color(pieces[tgt_sq]) != player_color:
                                moves.append(sq + tgt_sq)
                # Castling (simplified)
                if sq == ('e1' if player_color == 'w' else 'e8'):
                    # Kingside
                    if all(coords_to_square(x, y) not in pieces for x in range(5, 7)):
                        moves.append(sq + coords_to_square(6, y))
                    # Queenside
                    if all(coords_to_square(x, y) not in pieces for x in range(1, 4)):
                        moves.append(sq + coords_to_square(2, y))
                        
        return moves
    
    def make_move(board, move):
        new_board = board.copy()
        if len(move) == 4:
            from_sq, to_sq = move[:2], move[2:]
        else:
            from_sq, to_sq = move[:2], move[2:4]
            prom_piece = move[4].upper()
            # For simplicity in eval, we'll treat it as a queen
        piece = new_board[from_sq]
        del new_board[from_sq]
        new_board[to_sq] = piece
        return new_board
    
    def is_in_check(board, color):
        # Find king
        king_sq = None
        for sq, piece in board.items():
            if piece == color + 'K':
                king_sq = sq
                break
        if not king_sq:
            return False
        kx, ky = square_to_coords(king_sq)
        opp_color = 'b' if color == 'w' else 'w'
        
        # Check for pawn attacks
        dy = 1 if color == 'w' else -1
        for dx in [-1, 1]:
            nx, ny = kx + dx, ky + dy
            if is_on_board(nx, ny):
                sq = coords_to_square(nx, ny)
                if sq in board and board[sq] == opp_color + 'P':
                    return True
                    
        # Check for knight attacks
        for dx, dy in [(2,1),(2,-1),(-2,1),(-2,-1),(1,2),(1,-2),(-1,2),(-1,-2)]:
            nx, ny = kx + dx, ky + dy
            if is_on_board(nx, ny):
                sq = coords_to_square(nx, ny)
                if sq in board and board[sq] == opp_color + 'N':
                    return True
                    
        # Check for sliding pieces
        for dx, dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
            nx, ny = kx, ky
            steps = 0
            while True:
                nx, ny = nx + dx, ny + dy
                steps += 1
                if not is_on_board(nx, ny):
                    break
                sq = coords_to_square(nx, ny)
                if sq in board:
                    piece = board[sq]
                    if get_color(piece) == opp_color:
                        ptype = get_type(piece)
                        if (ptype == 'Q' or 
                           (ptype == 'R' and abs(dx) + abs(dy) == 1) or
                           (ptype == 'B' and abs(dx) == abs(dy)) or
                           (ptype == 'K' and steps == 1)):
                            return True
                    break
                    
        return False
    
    # Since we can't get the legal moves list, we'll use our generated moves
    # and filter for legality (no self-check)
    candidate_moves = generate_pseudo_legal_moves()
    legal_moves = []
    for move in candidate_moves:
        new_board = make_move(pieces, move)
        if not is_in_check(new_board, player_color):
            legal_moves.append(move)
    
    if not legal_moves:
        # Should not happen in this arena but just in case
        return "0000"
    
    # Evaluate moves
    best_move = legal_moves[0]
    best_score = -10000
    
    for move in legal_moves:
        # Simulate move
        new_board = make_move(pieces, move)
        
        # Check for checkmate
        if is_in_check(new_board, opponent_color):
            # Check if all opponent moves lead to check
            opp_legal = []
            for sq, piece in new_board.items():
                if get_color(piece) != opponent_color:
                    continue
                # Very simplified opponent move gen for detection only
                x, y = square_to_coords(sq)
                ptype = get_type(piece)
                if ptype in 'PNBRQK':
                    # Generate just some moves to check
                    moves_local = []
                    if ptype == 'N':
                        for dx, dy in [(2,1),(2,-1),(-2,1),(-2,-1),(1,2),(1,-2),(-1,2),(-1,-2)]:
                            nx, ny = x + dx, y + dy
                            if is_on_board(nx, ny):
                                tgt_sq = coords_to_square(nx, ny)
                                if tgt_sq not in new_board or get_color(new_board[tgt_sq]) != opponent_color:
                                    moves_local.append(sq + tgt_sq)
                    # We'll assume if in check and can't easily escape, it's checkmate
                    # This is a simplification
                    if not moves_local:
                        # Likely checkmate
                        return move
        
        # Material gain scoring
        score = 0
        if len(move) == 4:
            from_sq, to_sq = move[:2], move[2:]
        else:
            from_sq, to_sq = move[:2], move[2:4]
        
        # Capture value
        if to_sq in pieces:
            captured = pieces[to_sq]
            score += piece_values[get_type(captured)]
            
        # Promotion bonus
        if len(move) > 4:
            score += piece_values[move[4].upper()]
            
        # Positional bonus for moving toward center
        tx, ty = square_to_coords(to_sq)
        center_bonus = 3 - (abs(tx - 3.5) + abs(ty - 3.5)) * 0.1
        score += center_bonus
        
        # King safety
        if get_type(pieces[from_sq]) == 'K':
            # Moving king away from center in endgame can be good
            pass
        else:
            # Keep king safe by not moving pieces in front of it unnecessarily
            pass
            
        # Mobility bonus for piece
        # We don't compute full mobility here for speed
        
        # Prefer development
        fx, fy = square_to_coords(from_sq)
        if get_type(pieces[from_sq]) in 'NBR' and ((player_color == 'w' and fy < 2) or (player_color == 'b' and fy > 5)):
            score += 0.5
            
        # Avoid moving same piece multiple times
        # Not tracked here
        
        if score > best_score:
            best_score = score
            best_move = move
            
    return best_move
