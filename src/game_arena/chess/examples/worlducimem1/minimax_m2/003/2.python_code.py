
def policy(pieces: dict, to_play: str, memory: dict) -> tuple:
    # Piece values: King=0 (not captured), Queen=9, Rook=5, Bishop=3, Knight=3, Pawn=1
    piece_values = {
        'K': 0, 'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1
    }
    
    def is_attacked(board, square, attacker_color):
        x = ord(square[0]) - ord('a')
        y = int(square[1]) - 1
        color_char = 'w' if attacker_color=='white' else 'b'
        
        # Check pawn attacks
        if attacker_color=='white':
            for dx in [1,-1]:
                nx, ny = x+dx, y+1
                if 0<=nx<=7 and 0<=ny<=7:
                    sq = chr(ord('a')+nx)+str(ny+1)
                    if sq in board and board[sq]=='wP':
                        return True
        else:
            for dx in [1,-1]:
                nx, ny = x+dx, y-1
                if 0<=nx<=7 and 0<=ny<=7:
                    sq = chr(ord('a')+nx)+str(ny+1)
                    if sq in board and board[sq]=='bP':
                        return True
        
        # Check knight attacks
        knight_moves = [(2,1),(2,-1),(1,2),(1,-2),(-1,2),(-1,-2),(-2,1),(-2,-1)]
        for dx,dy in knight_moves:
            nx, ny = x+dx, y+dy
            if 0<=nx<=7 and 0<=ny<=7:
                sq = chr(ord('a')+nx)+str(ny+1)
                piece = board.get(sq)
                if piece == color_char+'N':
                    return True
        
        # Check king attacks
        for dx in [-1,0,1]:
            for dy in [-1,0,1]:
                if dx==0 and dy==0:
                    continue
                nx, ny = x+dx, y+dy
                if 0<=nx<=7 and 0<=ny<=7:
                    sq = chr(ord('a')+nx)+str(ny+1)
                    piece = board.get(sq)
                    if piece == color_char+'K':
                        return True
        
        # Check sliding pieces (bishops, rooks, queens)
        directions = [(1,1),(1,-1),(-1,1),(-1,-1),(1,0),(-1,0),(0,1),(0,-1)]
        for dx,dy in directions:
            nx, ny = x+dx, y+dy
            while 0<=nx<=7 and 0<=ny<=7:
                sq = chr(ord('a')+nx)+str(ny+1)
                piece = board.get(sq)
                if piece is None:
                    nx += dx
                    ny += dy
                    continue
                if piece[0] == color_char:
                    if piece[1]=='B' and (dx,dy) in [(1,1),(1,-1),(-1,1),(-1,-1)]:
                        return True
                    if piece[1]=='R' and (dx,dy) in [(1,0),(-1,0),(0,1),(0,-1)]:
                        return True
                    if piece[1]=='Q':
                        return True
                break
        return False

    def is_in_check(board, color):
        king_piece = 'wK' if color=='white' else 'bK'
        king_square = None
        for sq, pc in board.items():
            if pc == king_piece:
                king_square = sq
                break
        if king_square is None:
            return False
        opponent = 'black' if color=='white' else 'white'
        return is_attacked(board, king_square, opponent)

    def simulate_move(board, move):
        new_board = board.copy()
        src = move[0:2]
        dst = move[2:4]
        if len(move)==5:
            promo = move[4]
            piece = new_board.pop(src)
            new_board[dst] = piece[0] + promo.upper()
        else:
            piece = new_board.pop(src)
            new_board[dst] = piece
        return new_board

    def generate_pseudo_legal_moves(board, square, color):
        piece = board[square]
        piece_type = piece[1]
        color_char = 'w' if color=='white' else 'b'
        moves = []
        x = ord(square[0]) - ord('a')
        y = int(square[1]) - 1
        
        if piece_type=='P':
            direction = 1 if color=='white' else -1
            # One step forward
            ny = y + direction
            if 0<=ny<=7:
                dst = chr(ord('a')+x)+str(ny+1)
                if dst not in board:
                    moves.append(square+dst)
                    # Two steps from initial rank
                    if (color=='white' and y==1) or (color=='black' and y==6):
                        ny2 = y + 2*direction
                        if 0<=ny2<=7:
                            dst2 = chr(ord('a')+x)+str(ny2+1)
                            if dst2 not in board:
                                moves.append(square+dst2)
            # Captures
            for dx in [1,-1]:
                nx = x+dx
                ny = y+direction
                if 0<=nx<=7 and 0<=ny<=7:
                    dst = chr(ord('a')+nx)+str(ny+1)
                    if dst in board and board[dst][0] != color_char:
                        moves.append(square+dst)
            
            # Handle promotions
            promotion_moves = []
            for m in moves:
                dst = m[2:4]
                if (color=='white' and dst[1]=='8') or (color=='black' and dst[1]=='1'):
                    for promo in ['q','r','b','n']:
                        promotion_moves.append(m+promo)
                else:
                    promotion_moves.append(m)
            moves = promotion_moves
            
        elif piece_type=='N':
            knight_moves = [(2,1),(2,-1),(1,2),(1,-2),(-1,2),(-1,-2),(-2,1),(-2,-1)]
            for dx,dy in knight_moves:
                nx, ny = x+dx, y+dy
                if 0<=nx<=7 and 0<=ny<=7:
                    dst = chr(ord('a')+nx)+str(ny+1)
                    if dst not in board or board[dst][0] != color_char:
                        moves.append(square+dst)
                        
        elif piece_type in ['B','R','Q']:
            directions = []
            if piece_type in ['B','Q']:
                directions += [(1,1),(1,-1),(-1,1),(-1,-1)]
            if piece_type in ['R','Q']:
                directions += [(1,0),(-1,0),(0,1),(0,-1)]
            for dx,dy in directions:
                nx, ny = x+dx, y+dy
                while 0<=nx<=7 and 0<=ny<=7:
                    dst = chr(ord('a')+nx)+str(ny+1)
                    if dst not in board:
                        moves.append(square+dst)
                    elif board[dst][0] != color_char:
                        moves.append(square+dst)
                        break
                    else:
                        break
                    nx += dx
                    ny += dy
                    
        elif piece_type=='K':
            for dx in [-1,0,1]:
                for dy in [-1,0,1]:
                    if dx==0 and dy==0:
                        continue
                    nx, ny = x+dx, y+dy
                    if 0<=nx<=7 and 0<=ny<=7:
                        dst = chr(ord('a')+nx)+str(ny+1)
                        if dst not in board or board[dst][0] != color_char:
                            moves.append(square+dst)
        return moves

    # Generate all legal moves
    legal_moves = []
    for square, piece in pieces.items():
        if piece[0] == ('w' if to_play=='white' else 'b'):
            pseudo_moves = generate_pseudo_legal_moves(pieces, square, to_play)
            for move in pseudo_moves:
                new_board = simulate_move(pieces, move)
                if not is_in_check(new_board, to_play):
                    legal_moves.append(move)
    
    if not legal_moves:
        return ('', memory)
    
    best_move = legal_moves[0]
    best_score = -float('inf')
    
    for move in legal_moves:
        # Evaluate this move
        score = 0
        src = move[0:2]
        dst = move[2:4]
        
        # Check if this move captures a piece
        captured_piece = pieces.get(dst)
        if captured_piece is not None:
            # We captured a piece
            # Get the attacking piece (after move simulation)
            new_board = simulate_move(pieces, move)
            attacking_piece = new_board[dst]
            attacker_value = piece_values[attacking_piece[1]]
            victim_value = piece_values[captured_piece[1]]
            net_gain = victim_value - attacker_value
            if net_gain > 0:
                score += 100 * net_gain
            else:
                score -= 50  # bad capture
        
        # Check for pawn double step (development)
        if pieces[src][1]=='P':
            y_src = int(src[1]) - 1
            y_dst = int(dst[1]) - 1
            if to_play=='white' and y_src==1 and y_dst==3:
                score += 10
            elif to_play=='black' and y_src==6 and y_dst==4:
                score += 10
        
        # Check for bringing a piece to the center
        if dst in ['d4','d5','e4','e5']:
            # Check if it's not a pawn
            new_board = simulate_move(pieces, move)
            piece_at_dst = new_board[dst]
            if piece_at_dst[1] != 'P':
                score += 10
        
        # Check if this move gives check
        new_board = simulate_move(pieces, move)
        opponent = 'black' if to_play=='white' else 'white'
        if is_in_check(new_board, opponent):
            score += 50
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return (best_move, memory)
