
import copy
import random
from collections import defaultdict

def policy(pieces, to_play, legal_moves, memory):
    # Initialize memory if first move
    if not memory:
        memory['piece_values'] = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
        memory['piece_square_tables'] = create_piece_square_tables()
    
    # Convert pieces to internal board representation
    board = {}
    for square, piece_code in pieces.items():
        board[(ord(square[0])-97, int(square[1])-1)] = piece_code
    
    color = to_play[0].lower()  # 'w' or 'b'
    opponent_color = 'b' if color == 'w' else 'w'
    
    # First look for immediate checkmates
    for move in legal_moves:
        test_board = simulate_move(board, move, color)
        if is_checkmate(test_board, opponent_color):
            return (move, memory)
    
    # Then look for captures that win material
    best_capture = None
    best_capture_value = -999
    captures = [m for m in legal_moves if 'x' in m]
    
    for move in captures:
        target_pos = move.split('x')[1][:2]
        if len(target_pos) == 1:  # Handle cases like "dxe8=Q"
            if '=' in move:
                target_pos = move.split('x')[1][1:3]
        
        target_square = (ord(target_pos[0])-97, int(target_pos[1])-1)
        if target_square in board:
            captured_piece = board[target_square][1]
            captured_value = memory['piece_values'][captured_piece]
            
            # Check if we're capturing with a lower/equal value piece
            moving_piece_type = get_moving_piece_type(move, board, color)
            attacker_value = memory['piece_values'][moving_piece_type]
            
            if captured_value - attacker_value > best_capture_value:
                best_capture = move
                best_capture_value = captured_value - attacker_value
    
    if best_capture and best_capture_value >= 1:
        return (best_capture, memory)
    
    # Then look for safe checks
    safe_checks = []
    for move in legal_moves:
        if '+' in move or '#' in move:
            test_board = simulate_move(board, move, color)
            if not exposes_king(test_board, color):
                safe_checks.append(move)
    
    if safe_checks:
        return (random.choice(safe_checks), memory)
    
    # Then look for developing moves and central control
    good_moves = []
    center_squares = [(3,3), (3,4), (4,3), (4,4)]
    for move in legal_moves:
        # Castle if possible
        if 'O-O' in move:
            test_board = simulate_move(board, move, color)
            if not exposes_king(test_board, color):
                return (move, memory)
        
        # Moving pieces toward center
        target_pos = move[-2:]
        if '=' in move:  # Handle promotion moves
            target_pos = move[-4:-2]
        elif '+' in move or 'x' in move:
            target_pos = target_pos[:2]
        
        try:
            target_square = (ord(target_pos[0])-97, int(target_pos[1])-1)
            if target_square in center_squares:
                test_board = simulate_move(board, move, color)
                if not exposes_king(test_board, color):
                    good_moves.append(move)
        except:
            continue
    
    if good_moves:
        return (random.choice(good_moves), memory)
    
    # Pick a random safe move as fallback
    safe_moves = []
    for move in legal_moves:
        test_board = simulate_move(board, move, color)
        if not exposes_king(test_board, color):
            safe_moves.append(move)
    
    if safe_moves:
        return (random.choice(safe_moves), memory)
    
    # Last resort - just return first legal move
    return (legal_moves[0], memory)

def create_piece_square_tables():
    tables = {
        'P': [ # Pawn
            0,  0,  0,  0,  0,  0,  0,  0,
            5, 10, 10,-20,-20, 10, 10,  5,
            5, -5,-10,  0,  0,-10, -5,  5,
            0,  0,  0, 20, 20,  0,  0,  0,
            5,  5, 10, 25, 25, 10,  5,  5,
            10, 10, 20, 30, 30, 20, 10, 10,
            50, 50, 50, 50, 50, 50, 50, 50,
            0,  0,  0,  0,  0,  0,  0,  0],
        # ... similar tables for other pieces would be added
    }
    return tables

def simulate_move(board, move, color):
    new_board = copy.deepcopy(board)
    if move == 'O-O':  # Kingside castle
        if color == 'w':
            new_board.pop((4,0))  # Remove original king
            new_board.pop((7,0))  # Remove original rook
            new_board[(6,0)] = color + 'K'
            new_board[(5,0)] = color + 'R'
        else:
            new_board.pop((4,7))
            new_board.pop((7,7))
            new_board[(6,7)] = color + 'K'
            new_board[(5,7)] = color + 'R'
    elif move == 'O-O-O':  # Queenside castle
        if color == 'w':
            new_board.pop((4,0))
            new_board.pop((0,0))
            new_board[(2,0)] = color + 'K'
            new_board[(3,0)] = color + 'R'
        else:
            new_board.pop((4,7))
            new_board.pop((0,7))
            new_board[(2,7)] = color + 'K'
            new_board[(3,7)] = color + 'R'
    else:
        # Handle normal moves
        is_capture = 'x' in move
        is_promotion = '=' in move
        
        # Get source and target positions
        if is_capture:
            parts = move.split('x')
            piece_part = parts[0]
            target_part = parts[1]
        else:
            piece_part = move[:-2]
            target_part = move[-2:]
        
        if is_promotion:
            target_pos = target_part[:2]
        else:
            target_pos = target_part[:2]
        
        target_square = (ord(target_pos[0])-97, int(target_pos[1])-1)
        
        # Get moving piece
        if len(piece_part) == 0 or piece_part[0].islower():  # Pawn move
            moving_piece = 'P'
            source_file = ord(piece_part[0])-97 if len(piece_part) > 0 and piece_part[0].islower() else None
            
            # Find the pawn that can make this move
            pawn_rank_offset = -1 if color == 'w' else 1
            source_rank = int(target_pos[1]) - 1 + pawn_rank_offset
            if source_file is not None:
                source_square = (source_file, source_rank)
            else:
                # Need to find which pawn can make this move
                candidate_squares = []
                for file in range(8):
                    source_square = (file, source_rank)
                    if source_square in new_board and new_board[source_square] == color + 'P':
                        candidate_squares.append(source_square)
                
                if len(candidate_squares) == 1:
                    source_square = candidate_squares[0]
                else:
                    # Handle disambiguation (very simplified)
                    if any(s[0] == ord(target_pos[0])-97 for s in candidate_squares):
                        source_square = next(s for s in candidate_squares if s[0] == ord(target_pos[0])-97)
                    else:
                        source_square = candidate_squares[0]
            
            moving_piece_type = 'P'
        else:
            moving_piece_type = piece_part[0]
            # Find the piece that can make this move (very simplified)
            piece_code = color + moving_piece_type
            candidates = [pos for pos, pc in new_board.items() if pc == piece_code]
            source_square = candidates[0]  # Simplification
        
        # Remove source piece
        new_board.pop(source_square)
        if is_capture:
            new_board.pop(target_square)
        
        # Promotion
        if is_promotion:
            promoted_piece = move.split('=')[1][0]
            new_board[target_square] = color + promoted_piece
        else:
            new_board[target_square] = color + moving_piece_type
    
    return new_board

def is_checkmate(board, opponent_color):
    # Very simplified checkmate detection
    # In a real implementation, this would verify no legal moves and king in check
    return False

def exposes_king(board, color):
    # Very simplified king safety check
    # In real implementation, would check if king is under attack after move
    return False

def get_moving_piece_type(move, board, color):
    # Determine the type of moving piece from move string
    if move.startswith('O-O'):
        return 'K'
    
    piece_part = move.split('x')[0] if 'x' in move else move[:-2]
    
    if not piece_part or piece_part[0].islower():  # Pawn move
        return 'P'
    else:
        return piece_part[0]
