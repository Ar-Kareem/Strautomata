
import copy

def get_capture_sequences(board, r, c, color):
    piece = board[r][c]
    sequences = []
    
    # Check if the piece belongs to the current player
    if color == 'b' and piece <= 0:
        return sequences
    if color == 'w' and piece >= 0:
        return sequences
    
    # Determine capture directions based on piece type and color
    if abs(piece) == 2:  # King
        directions = [(-2, -2), (-2, 2), (2, -2), (2, 2)]
    elif abs(piece) == 1:  # Man
        if color == 'b':
            directions = [(-2, -2), (-2, 2)]
        else:  # color 'w'
            directions = [(2, -2), (2, 2)]
    else:
        return sequences
    
    for dr, dc in directions:
        new_r = r + dr
        new_c = c + dc
        between_r = r + dr // 2
        between_c = c + dc // 2
        
        # Check bounds and if the destination is empty
        if new_r < 0 or new_r >= 8 or new_c < 0 or new_c >= 8:
            continue
        if board[new_r][new_c] != 0:
            continue
        
        # Check if the between square has an opponent piece
        if color == 'b':
            if board[between_r][between_c] <= 0:
                continue
        else:  # color 'w'
            if board[between_r][between_c] >= 0:
                continue
        
        # Create new board state after capture
        new_board = copy.deepcopy(board)
        new_board[r][c] = 0
        new_board[between_r][between_c] = 0
        new_board[new_r][new_c] = piece
        
        # Recursively get capture sequences from the new position
        recursive_seqs = get_capture_sequences(new_board, new_r, new_c, color)
        if recursive_seqs:
            for seq in recursive_seqs:
                sequences.append([(r, c)] + seq)
        else:
            sequences.append([(r, c), (new_r, new_c)])
    
    return sequences

def get_all_moves(board, color):
    moves = []
    
    # Generate capture moves first
    for r in range(8):
        for c in range(8):
            if board[r][c] != 0:
                piece = board[r][c]
                # Check if it's the current player's piece
                if color == 'b' and piece <= 0:
                    continue
                if color == 'w' and piece >= 0:
                    continue
                capture_seqs = get_capture_sequences(board, r, c, color)
                moves.extend(capture_seqs)
    
    # If capture moves are available, return only them
    if moves:
        return moves
    
    # Otherwise, generate simple moves
    for r in range(8):
        for c in range(8):
            if board[r][c] != 0:
                piece = board[r][c]
                # Check if it's the current player's piece
                if color == 'b' and piece <= 0:
                    continue
                if color == 'w' and piece >= 0:
                    continue
                
                # Determine simple move directions
                if abs(piece) == 2:  # King
                    directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
                elif abs(piece) == 1:  # Man
                    if color == 'b':
                        directions = [(-1, -1), (-1, 1)]
                    else:  # color 'w'
                        directions = [(1, -1), (1, 1)]
                else:
                    continue
                
                for dr, dc in directions:
                    new_r = r + dr
                    new_c = c + dc
                    if new_r < 0 or new_r >= 8 or new_c < 0 or new_c >= 8:
                        continue
                    if board[new_r][new_c] == 0:
                        moves.append([(r, c), (new_r, new_c)])
    
    return moves

def apply_move(board, move_sequence):
    new_board = copy.deepcopy(board)
    for i in range(len(move_sequence) - 1):
        from_sq = move_sequence[i]
        to_sq = move_sequence[i + 1]
        dr = to_sq[0] - from_sq[0]
        dc = to_sq[1] - from_sq[1]
        piece = new_board[from_sq[0]][from_sq[1]]
        new_board[from_sq[0]][from_sq[1]] = 0
        if abs(dr) == 2 and abs(dc) == 2:
            between_r = from_sq[0] + dr // 2
            between_c = from_sq[1] + dc // 2
            new_board[between_r][between_c] = 0
        new_board[to_sq[0]][to_sq[1]] = piece
    return new_board

def evaluate(board, current_color):
    # Count pieces
    my_men = my_kings = opp_men = opp_kings = 0
    my_pieces = opp_pieces = 0
    
    for r in range(8):
        for c in range(8):
            if board[r][c] != 0:
                if current_color == 'b':
                    if board[r][c] > 0:
                        my_pieces += 1
                        if board[r][c] == 1:
                            my_men += 1
                        else:
                            my_kings += 1
                    else:
                        opp_pieces += 1
                        if board[r][c] == -1:
                            opp_men += 1
                        else:
                            opp_kings += 1
                else:  # current_color 'w'
                    if board[r][c] < 0:
                        my_pieces += 1
                        if board[r][c] == -1:
                            my_men += 1
                        else:
                            my_kings += 1
                    else:
                        opp_pieces += 1
                        if board[r][c] == 1:
                            opp_men += 1
                        else:
                            opp_kings += 1
    
    # Check win/loss conditions
    if opp_pieces == 0:
        return 1000
    if my_pieces == 0:
        return -1000
    
    # Check for legal moves
    legal_moves = get_all_moves(board, current_color)
    if not legal_moves:
        return -1000
    
    # Piece count evaluation
    score = (my_kings * 3 + my_men * 1) - (opp_kings * 3 + opp_men * 1)
    return score

def policy(my_men, my_kings, opp_men, opp_kings, color):
    # Initialize board
    board = [[0] * 8 for _ in range(8)]
    # Place my pieces
    for r, c in my_men:
        board[r][c] = 1 if color == 'b' else -1
    for r, c in my_kings:
        board[r][c] = 2 if color == 'b' else -2
    # Place opponent pieces
    for r, c in opp_men:
        board[r][c] = -1 if color == 'b' else 1
    for r, c in opp_kings:
        board[r][c] = -2 if color == 'b' else 2
    
    # Generate all legal moves for my color
    my_moves = get_all_moves(board, color)
    if not my_moves:
        # Fallback if no moves (should not happen in practice)
        return ((0, 0), (0, 0))
    
    opponent_color = 'w' if color == 'b' else 'b'
    best_move = None
    best_score = -float('inf')
    
    # Evaluate each move using minimax with depth 2
    for move in my_moves:
        new_board = apply_move(board, move)
        opp_moves = get_all_moves(new_board, opponent_color)
        min_eval = float('inf')
        
        if not opp_moves:
            min_eval = 1000
        else:
            for opp_move in opp_moves:
                board_after_opp = apply_move(new_board, opp_move)
                score = evaluate(board_after_opp, color)
                if score < min_eval:
                    min_eval = score
        
        if min_eval > best_score:
            best_score = min_eval
            best_move = move
    
    # Return the move as from and to coordinates
    from_square = best_move[0]
    to_square = best_move[-1]
    return (from_square, to_square)
