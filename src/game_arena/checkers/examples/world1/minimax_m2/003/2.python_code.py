
def policy(my_men, my_kings, opp_men, opp_kings, color):
    # Create the board
    board = [[None for _ in range(8)] for _ in range(8)]
    
    # Place our pieces
    for (r, c) in my_men:
        board[r][c] = color + 'M'
    for (r, c) in my_kings:
        board[r][c] = color + 'K'
    
    opp_color = 'w' if color == 'b' else 'b'
    for (r, c) in opp_men:
        board[r][c] = opp_color + 'M'
    for (r, c) in opp_kings:
        board[r][c] = opp_color + 'K'
    
    # Generate all jumps
    jump_moves = []   # list of (move, new_board)
    
    # We'll iterate over all squares to find our pieces.
    for r in range(8):
        for c in range(8):
            piece = board[r][c]
            if piece is not None and piece[0] == color:
                # Check if it is a man or king? It can jump if it is a man or king? Both can jump.
                # We'll generate jumps for this piece.
                piece_type = piece
                # We'll call the DFS for jumps for this piece.
                # We'll define a helper function for the DFS.
                # We are going to use a recursive function that returns a list of (move, new_board)
                def dfs(current_r, current_c, current_board, path, visited):
                    # current_board is the board after the jumps so far (so the piece is at current_r, current_c)
                    piece_type = current_board[current_r][current_c]
                    # Determine the jump directions for this piece_type and color.
                    if piece_type[1] == 'M':
                        if color == 'b':
                            jump_dirs = [(-1,-1), (-1,1)]
                        else:
                            jump_dirs = [(1,-1), (1,1)]
                    else: # king
                        jump_dirs = [(-1,-1), (-1,1), (1,-1), (1,1)]
                    
                    moves = []
                    for (dr, dc) in jump_dirs:
                        adj_r = current_r + dr
                        adj_c = current_c + dc
                        landing_r = current_r + 2*dr
                        landing_c = current_c + 2*dc
                        
                        if 0 <= adj_r < 8 and 0 <= adj_c < 8 and 0 <= landing_r < 8 and 0 <= landing_c < 8:
                            # Check if the adjacent square has an opponent piece
                            if current_board[adj_r][adj_c] is not None and current_board[adj_r][adj_c][0] != color:
                                if current_board[landing_r][landing_c] is None:
                                    # We can jump: simulate on a new board
                                    new_board = [row[:] for row in current_board]
                                    # Remove the piece from current_r, current_c
                                    new_board[current_r][current_c] = None
                                    # Remove the opponent piece at adj_r, adj_c
                                    new_board[adj_r][adj_c] = None
                                    # Place the piece at landing_r, landing_c, and check if it becomes a king.
                                    new_piece_type = piece_type
                                    if piece_type[1]=='M':
                                        if color=='b' and landing_r==0:
                                            new_piece_type = color+'K'
                                        elif color=='w' and landing_r==7:
                                            new_piece_type = color+'K'
                                    new_board[landing_r][landing_c] = new_piece_type
                                    
                                    new_path = path + [(landing_r, landing_c)]
                                    new_visited = visited | {(current_r, current_c)}
                                    submoves = dfs(landing_r, landing_c, new_board, new_path, new_visited)
                                    moves.extend(submoves)
                    
                    if not moves: 
                        # No more jumps: record the move for this path
                        if len(path) > 1:   # at least one jump
                            move = (path[0], path[-1])
                            moves.append((move, current_board))
                    return moves
                
                # Start the DFS for this piece
                path = [(r, c)]
                visited = set()
                piece_jumps = dfs(r, c, board, path, visited)
                jump_moves.extend(piece_jumps)
    
    # If there is at least one jump, then we only consider jumps.
    if jump_moves:
        moves_to_evaluate = jump_moves
    else:
        # Generate simple moves
        moves_to_evaluate = []
        for r in range(8):
            for c in range(8):
                piece = board[r][c]
                if piece is not None and piece[0] == color:
                    piece_type = piece
                    # Determine simple move directions
                    if piece_type[1] == 'M':
                        if color == 'b':
                            simple_dirs = [(-1,-1), (-1,1)]
                        else:
                            simple_dirs = [(1,-1), (1,1)]
                    else:
                        simple_dirs = [(-1,-1), (-1,1), (1,-1), (1,1)]
                    
                    for (dr, dc) in simple_dirs:
                        new_r = r + dr
                        new_c = c + dc
                        if 0 <= new_r < 8 and 0 <= new_c < 8 and board[new_r][new_c] is None:
                            new_board = [row[:] for row in board]
                            new_board[r][c] = None
                            # Check if the piece becomes a king
                            new_piece_type = piece_type
                            if piece_type[1]=='M':
                                if color=='b' and new_r==0:
                                    new_piece_type = color+'K'
                                elif color=='w' and new_r==7:
                                    new_piece_type = color+'K'
                            new_board[new_r][new_c] = new_piece_type
                            move = ((r, c), (new_r, new_c))
                            moves_to_evaluate.append((move, new_board))
    
    # Now, evaluate each move in moves_to_evaluate.
    best_move = None
    best_value = -float('inf')
    
    for (move, new_board) in moves_to_evaluate:
        # Count our pieces and opponent pieces in new_board
        our_men = 0
        our_kings = 0
        opp_men = 0
        opp_kings = 0
        for r in range(8):
            for c in range(8):
                piece = new_board[r][c]
                if piece is not None:
                    if piece[0] == color:
                        if piece[1]=='M':
                            our_men += 1
                        else:
                            our_kings += 1
                    else:
                        if piece[1]=='M':
                            opp_men += 1
                        else:
                            opp_kings += 1
        value = (our_men * 1 + our_kings * 3) - (opp_men * 1 + opp_kings * 3)
        if value > best_value:
            best_value = value
            best_move = move
    
    # If there is no move (should not happen), return a default move? But we must return a legal move.
    # We'll assume there is at least one move.
    return best_move
