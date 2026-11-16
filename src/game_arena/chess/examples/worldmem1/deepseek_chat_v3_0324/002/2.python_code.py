
import time
from collections import defaultdict

def policy(pieces, to_play, legal_moves, memory):
    start_time = time.time()
    
    # Initialize memory if not present
    if not memory:
        memory = {
            'depth_limit': 3,  # Default depth
            'time_limit': 0.9,  # Max time to spend (0.9s)
        }
    
    # Piece values
    piece_values = {'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1, 'K': 0}
    
    # Convert position to board representation
    board = {}
    for square, piece_code in pieces.items():
        file, rank = square[0], int(square[1])
        col = ord(file) - ord('a')
        row = 8 - rank
        board[(row, col)] = piece_code
    
    # Determine our color
    our_color = 'w' if to_play == 'white' else 'b'
    opponent_color = 'b' if our_color == 'w' else 'w'
    
    # First look for immediate checkmates
    for move in legal_moves:
        if move.endswith('#'):
            return move, memory
    
    # Evaluate all legal moves with simple heuristic
    best_move = None
    best_score = -float('inf')
    
    # Try iterative deepening within time limit
    depth_limit = memory['depth_limit']
    best_move_found = legal_moves[0]  # Default if we run out of time
    
    for depth in range(1, depth_limit + 1):
        current_best = None
        current_score = -float('inf')
        
        # Shuffle moves to avoid always picking the first in case of equal scores
        evaluated_moves = []
        for move in legal_moves:
            if time.time() - start_time > memory['time_limit']:
                break
            
            # Simulate move
            new_board = simulate_move(board, move, our_color)
            
            # Check opponent responses
            min_score = float('inf')
            opponent_moves = generate_legal_moves(new_board, opponent_color)
            
            if depth > 1 and opponent_moves:
                min_score = float('inf')
                for opp_move in opponent_moves:
                    opp_board = simulate_move(new_board, opp_move, opponent_color)
                    
                    # Evaluate position after our move and opponent's response
                    score = evaluate_position(opp_board, our_color, opponent_color, piece_values)
                    
                    if score < min_score:
                        min_score = score
            
            if not opponent_moves:  # Checkmate or stalemate
                if is_check(new_board, opponent_color):
                    min_score = float('inf')  # Checkmate is best possible
                else:
                    min_score = 0  # Stalemate
            
            # If we have time for deeper search, continue
            if min_score > current_score:
                current_score = min_score
                current_best = move
            
            if time.time() - start_time > memory['time_limit']:
                break
        
        if current_best and time.time() - start_time <= memory['time_limit']:
            best_move_found = current_best
        else:
            break  # Out of time, return best from previous iteration
    
    # Update depth limit based on timing
    if time.time() - start_time < memory['time_limit'] * 0.5:
        memory['depth_limit'] = min(4, memory['depth_limit'] + 1)
    elif time.time() - start_time > memory['time_limit'] * 0.9:
        memory['depth_limit'] = max(2, memory['depth_limit'] - 1)
    
    return best_move_found, memory

def simulate_move(board, move, color):
    new_board = dict(board)
    
    # Handle special moves
    if move == 'O-O':
        # Kingside castling
        row = 0 if color == 'w' else 7
        new_board.pop((row, 4))
        new_board[(row, 6)] = color + 'K'
        new_board.pop((row, 7))
        new_board[(row, 5)] = color + 'R'
        return new_board
    elif move == 'O-O-O':
        # Queenside castling
        row = 0 if color == 'w' else 7
        new_board.pop((row, 4))
        new_board[(row, 2)] = color + 'K'
        new_board.pop((row, 0))
        new_board[(row, 3)] = color + 'R'
        return new_board
    
    # Handle promotion
    if '=' in move:
        move_part = move.split('=')[0]
        promo_piece = move.split('=')[1]
    else:
        move_part = move
        promo_piece = None
    
    # Handle capture
    if 'x' in move_part:
        # Remove captured piece
        capture_square = move_part.split('x')[1][-2:]
        file, rank = capture_square[0], int(capture_square[1])
        col = ord(file) - ord('a')
        row = 8 - rank
        new_board.pop((row, col), None)
    else:
        # Find target square
        if move_part[-1] in {'+', '#'}:
            target_square = move_part[:-1]
        else:
            target_square = move_part
    
    # Parse target square
    file, rank = target_square[-2], int(target_square[-1])
    target_col = ord(file) - ord('a')
    target_row = 8 - rank
    
    # Find source square
    if len(move_part) > 2 and move_part[0].isupper() and 'x' not in move_part:
        # Disambiguated piece move (e.g. Nbc3)
        piece_type = move_part[0]
        source_file = move_part[1]
        source_col = ord(source_file) - ord('a')
        for (row, col), piece in board.items():
            if piece[1] == piece_type and piece[0] == color and col == source_col:
                new_board.pop((row, col))
                break
    elif len(move_part) > 2 and move_part[0].isupper() and 'x' in move_part:
        # Disambiguated capture (e.g. Nxc3)
        piece_type = move_part[0]
        source_hint = move_part[1]  # file or rank
        if source_hint.isalpha():
            source_col = ord(source_hint) - ord('a')
            for (row, col), piece in board.items():
                if piece[1] == piece_type and piece[0] == color and col == source_col:
                    new_board.pop((row, col))
                    break
        else:
            source_row = 8 - int(source_hint)
            for (row, col), piece in board.items():
                if piece[1] == piece_type and piece[0] == color and row == source_row:
                    new_board.pop((row, col))
                    break
    elif move_part[0].isupper():
        # Piece move (e.g. Nc3)
        piece_type = move_part[0]
        for (row, col), piece in board.items():
            if piece[1] == piece_type and piece[0] == color:
                # Simple implementation - might be ambiguous
                new_board.pop((row, col))
                break
    else:
        # Pawn move (e.g. e4)
        pawn_file = move_part[0]
        pawn_col = ord(pawn_file) - ord('a')
        # Find the pawn that can move to target square
        pawn_row_diff = 1 if color == 'w' else -1
        if (target_row + pawn_row_diff, target_col) in board:
            piece = board.get((target_row + pawn_row_diff, target_col))
            if piece == color + 'P':
                new_board.pop((target_row + pawn_row_diff, target_col))
        elif (target_row + 2*pawn_row_diff, target_col) in board and abs(target_row - (target_row + 2*pawn_row_diff)) == 2:
            piece = board.get((target_row + 2*pawn_row_diff, target_col))
            if piece == color + 'P':
                new_board.pop((target_row + 2*pawn_row_diff, target_col))
    
    # Place the moved piece
    if promo_piece:
        new_board[(target_row, target_col)] = color + promo_piece
    else:
        if move_part[0].isupper():
            piece_type = move_part[0]
        else:
            piece_type = 'P'
        new_board[(target_row, target_col)] = color + piece_type
    
    return new_board

def generate_legal_moves(board, color):
    # Simplified move generation for opponent responses
    # In a full implementation, this would be more comprehensive
    moves = []
    for (row, col), piece in board.items():
        if piece[0] == color:
            piece_type = piece[1]
            if piece_type == 'P':
                # Simple pawn moves
                direction = -1 if color == 'w' else 1
                # Forward move
                if (row + direction, col) not in board:
                    moves.append(f"{chr(col + ord('a'))}{8 - (row + direction)}")
                    # Double move from starting position
                    if (row == 6 and color == 'w') or (row == 1 and color == 'b'):
                        if (row + 2*direction, col) not in board:
                            moves.append(f"{chr(col + ord('a'))}{8 - (row + 2*direction)}")
                # Captures
                for dc in [-1, 1]:
                    if 0 <= col + dc < 8 and (row + direction, col + dc) in board:
                        target_piece = board[(row + direction, col + dc)]
                        if target_piece[0] != color:
                            moves.append(f"{chr(col + ord('a'))}x{chr(col + dc + ord('a'))}{8 - (row + direction)}")
            elif piece_type == 'N':
                # Knight moves
                for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
                    new_row, new_col = row + dr, col + dc
                    if 0 <= new_row < 8 and 0 <= new_col < 8:
                        if (new_row, new_col) not in board or board[(new_row, new_col)][0] != color:
                            moves.append(f"N{chr(col + ord('a'))}{8 - row}{chr(new_col + ord('a'))}{8 - new_row}")
            elif piece_type == 'K':
                # King moves
                for dr in [-1,0,1]:
                    for dc in [-1,0,1]:
                        if dr == 0 and dc == 0:
                            continue
                        new_row, new_col = row + dr, col + dc
                        if 0 <= new_row < 8 and 0 <= new_col < 8:
                            if (new_row, new_col) not in board or board[(new_row, new_col)][0] != color:
                                moves.append(f"K{chr(col + ord('a'))}{8 - row}{chr(new_col + ord('a'))}{8 - new_row}")
    return moves

def is_check(board, color):
    # Simplified check detection - just looks if king can be captured
    king_pos = None
    for (row, col), piece in board.items():
        if piece == color + 'K':
            king_pos = (row, col)
            break
            
    if not king_pos:
        return False
        
    opponent_color = 'b' if color == 'w' else 'w'
    
    # Check for attacking pieces
    for (row, col), piece in board.items():
        if piece[0] == opponent_color:
            piece_type = piece[1]
            if piece_type == 'P':
                direction = 1 if opponent_color == 'w' else -1
                if (row - direction, col - 1) == king_pos or (row - direction, col + 1) == king_pos:
                    return True
            elif piece_type == 'N':
                for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
                    if (row + dr, col + dc) == king_pos:
                        return True
            elif piece_type == 'B' or piece_type == 'Q':
                # Diagonal moves
                for dr, dc in [(-1,-1),(-1,1),(1,-1),(1,1)]:
                    r, c = row + dr, col + dc
                    while 0 <= r < 8 and 0 <= c < 8:
                        if (r, c) == king_pos:
                            return True
                        if (r, c) in board:
                            break
                        r += dr
                        c += dc
            elif piece_type == 'R' or piece_type == 'Q':
                # Straight moves
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    r, c = row + dr, col + dc
                    while 0 <= r < 8 and 0 <= c < 8:
                        if (r, c) == king_pos:
                            return True
                        if (r, c) in board:
                            break
                        r += dr
                        c += dc
            elif piece_type == 'K':
                for dr in [-1,0,1]:
                    for dc in [-1,0,1]:
                        if dr == 0 and dc == 0:
                            continue
                        if (row + dr, col + dc) == king_pos:
                            return True
    return False

def evaluate_position(board, our_color, opponent_color, piece_values):
    score = 0
    
    # Material score
    for (row, col), piece in board.items():
        value = piece_values.get(piece[1], 0)
        if piece[0] == our_color:
            score += value
        else:
            score -= value
    
    # Center control
    center_squares = [(3,3), (3,4), (4,3), (4,4)]
    for square in center_squares:
        if square in board:
            piece = board[square]
            if piece[0] == our_color:
                score += 0.1
            else:
                score -= 0.1
    
    # King safety
    our_king_pos = None
    opponent_king_pos = None
    for (row, col), piece in board.items():
        if piece == our_color + 'K':
            our_king_pos = (row, col)
        elif piece == opponent_color + 'K':
            opponent_king_pos = (row, col)
    
    if our_king_pos:
        # Penalize king in center early
        if our_king_pos[0] in [3,4] and our_king_pos[1] in [3,4]:
            score -= 0.5
    
    if opponent_king_pos:
        # Reward opponent king in center early
        if opponent_king_pos[0] in [3,4] and opponent_king_pos[1] in [3,4]:
            score += 0.5
    
    # Doubled pawns
    pawn_counts = defaultdict(int)
    for (row, col), piece in board.items():
        if piece[1] == 'P':
            file = col
            pawn_counts[(piece[0], file)] += 1
    
    for (color_file, count) in pawn_counts.items():
        if count > 1 and color_file[0] == our_color:
            score -= 0.3 * (count - 1)
        elif count > 1 and color_file[0] == opponent_color:
            score += 0.3 * (count - 1)
    
    return score
