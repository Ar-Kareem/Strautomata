
def policy(state: list[list[object]], role: str) -> str:
    # Parse the board state
    board = {}
    my_pieces = {}
    opp_pieces = {}
    
    for fact in state:
        if fact[0] == "location":
            cell = tuple(fact[1][1:])  # (file, rank)
            piece = fact[2]
            piece_color = piece[1]
            piece_type = piece[2]
            piece_id = piece[3]
            
            board[cell] = (piece_color, piece_type, piece_id)
            
            if piece_color == role:
                if piece_type not in my_pieces:
                    my_pieces[piece_type] = []
                my_pieces[piece_type].append((cell, piece_id))
            else:
                if piece_type not in opp_pieces:
                    opp_pieces[piece_type] = []
                opp_pieces[piece_type].append((cell, piece_id))
    
    def cell_to_coords(cell):
        return (ord(cell[0]) - ord('a'), int(cell[1]) - 1)
    
    def coords_to_cell(x, y):
        return (chr(ord('a') + x), str(y + 1))
    
    def is_valid(x, y):
        return 0 <= x < 8 and 0 <= y < 8
    
    def get_pawn_moves(x, y, color):
        moves = []
        direction = 1 if color == "white" else -1
        start_rank = 1 if color == "white" else 6
        
        # Forward move
        nx, ny = x, y + direction
        if is_valid(nx, ny) and coords_to_cell(nx, ny) not in board:
            moves.append((nx, ny))
            
            # Double move from start
            if y == start_rank:
                nx2, ny2 = x, y + 2 * direction
                if coords_to_cell(nx2, ny2) not in board:
                    moves.append((nx2, ny2))
        
        # Captures
        for dx in [-1, 1]:
            nx, ny = x + dx, y + direction
            if is_valid(nx, ny):
                target_cell = coords_to_cell(nx, ny)
                if target_cell in board and board[target_cell][0] != color:
                    moves.append((nx, ny))
        
        return moves
    
    def get_knight_moves(x, y):
        moves = []
        for dx, dy in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
            nx, ny = x + dx, y + dy
            if is_valid(nx, ny):
                moves.append((nx, ny))
        return moves
    
    def get_bishop_moves(x, y, color):
        moves = []
        for dx, dy in [(-1,-1),(-1,1),(1,-1),(1,1)]:
            nx, ny = x + dx, y + dy
            while is_valid(nx, ny):
                target_cell = coords_to_cell(nx, ny)
                if target_cell in board:
                    if board[target_cell][0] != color:
                        moves.append((nx, ny))
                    break
                moves.append((nx, ny))
                nx += dx
                ny += dy
        return moves
    
    def get_rook_moves(x, y, color):
        moves = []
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nx, ny = x + dx, y + dy
            while is_valid(nx, ny):
                target_cell = coords_to_cell(nx, ny)
                if target_cell in board:
                    if board[target_cell][0] != color:
                        moves.append((nx, ny))
                    break
                moves.append((nx, ny))
                nx += dx
                ny += dy
        return moves
    
    def get_queen_moves(x, y, color):
        return get_rook_moves(x, y, color) + get_bishop_moves(x, y, color)
    
    def get_king_moves(x, y, color):
        moves = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if is_valid(nx, ny):
                    moves.append((nx, ny))
        return moves
    
    def get_legal_moves(piece_type, x, y, color):
        if piece_type == "pawn":
            return get_pawn_moves(x, y, color)
        elif piece_type == "knight":
            return get_knight_moves(x, y)
        elif piece_type == "bishop":
            return get_bishop_moves(x, y, color)
        elif piece_type == "rook":
            return get_rook_moves(x, y, color)
        elif piece_type == "queen":
            return get_queen_moves(x, y, color)
        elif piece_type == "king":
            return get_king_moves(x, y, color)
        return []
    
    piece_values = {"pawn": 1, "knight": 3, "bishop": 3, "rook": 5, "queen": 9, "king": 11}
    
    best_move = None
    best_score = -float('inf')
    
    for piece_type in my_pieces:
        for piece_cell, piece_id in my_pieces[piece_type]:
            x, y = cell_to_coords(piece_cell)
            legal_moves = get_legal_moves(piece_type, x, y, role)
            
            for nx, ny in legal_moves:
                target_cell = coords_to_cell(nx, ny)
                
                # Evaluate move
                score = 0
                
                # Capture value
                if target_cell in board:
                    target_type = board[target_cell][1]
                    score += piece_values[target_type] * 10
                
                # Piece advancement bonus
                if piece_type == "pawn":
                    score += ny if role == "white" else (7 - ny)
                
                # Centralization bonus
                center_bonus = 3 - abs(nx - 3.5) + 3 - abs(ny - 3.5)
                score += center_bonus * 0.5
                
                if score > best_score:
                    best_score = score
                    best_move = (piece_type, piece_id, target_cell)
    
    # Format move string
    piece_type, piece_id, target_cell = best_move
    return f"move(piece({role},{piece_type},{piece_id}),cell({target_cell[0]},{target_cell[1]}))"
