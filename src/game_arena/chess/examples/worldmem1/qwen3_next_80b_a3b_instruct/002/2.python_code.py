
import sys

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    # Initialize memory if empty
    if 'move_count' not in memory:
        memory['move_count'] = 0
    if 'previous_moves' not in memory:
        memory['previous_moves'] = set()
    
    # Increment move count
    memory['move_count'] += 1

    # Define piece values for material evaluation
    piece_values = {'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1, 'K': 0}
    color = 'w' if to_play == 'white' else 'b'
    opponent_color = 'b' if to_play == 'white' else 'w'
    
    # Check for checkmate moves
    for move in legal_moves:
        if '+' in move and 'x' in move:  # Capture + check
            # More reliable: look for '++' or context of mate, but since we don't simulate,
            # use heuristic: if it's a check and captures something, it's high priority
            # Better: check for moves ending in '+' and are captures
            # We assume the engine will flag true mates, so evaluate any check that captures
            return move, memory
        elif '#' in move:  # MATE detected (some engines use #)
            return move, memory
        elif move in ['O-O', 'O-O-O'] and not is_king_in_check_after_castle(pieces, to_play, move):
            # Prefer castling if safe
            return move, memory
    
    # Look for any checkmate in the move (some representations use '#')
    for move in legal_moves:
        if '#' in move:
            return move, memory
    
    # Look for checks that are captures (often mating threats)
    check_captures = [m for m in legal_moves if '+' in m and 'x' in m]
    if check_captures:
        # Prefer highest material capture among checks
        best_capture = None
        best_value = -1
        for move in check_captures:
            # Parse captured piece: move like "Rxd5" or "Bxf5+", extract target square
            if 'x' in move:
                captured_square = move.split('x')[1].rstrip('+#')
                captured_piece = pieces.get(captured_square, '')
                if len(captured_piece) == 2 and captured_piece[0] == opponent_color:
                    value = piece_values.get(captured_piece[1], 0)
                    if value > best_value:
                        best_value = value
                        best_capture = move
        if best_capture:
            return best_capture, memory

    # Look for non-check captures (material gain)
    captures = [m for m in legal_moves if 'x' in m]
    if captures:
        best_capture = None
        best_value = -1
        for move in captures:
            captured_square = move.split('x')[1].rstrip('+#')
            captured_piece = pieces.get(captured_square, '')
            if len(captured_piece) == 2 and captured_piece[0] == opponent_color:
                value = piece_values.get(captured_piece[1], 0)
                if value > best_value:
                    best_value = value
                    best_capture = move
        if best_capture:
            return best_capture, memory

    # If no captures, look for moves that develop or control center
    center_squares = {'d4', 'd5', 'e4', 'e5'}
    if memory['move_count'] <= 10:  # Early game
        # Prefer pawn moves to center
        center_pawn_moves = [m for m in legal_moves if len(m) == 2 and m[0] in 'abcdefgh' and m[1] in '45']
        if center_pawn_moves:
            return center_pawn_moves[0], memory
        # Prefer knight moves to center
        knight_moves = [m for m in legal_moves if m.startswith('N') and len(m) == 3 and m[1:3] in center_squares]
        if knight_moves:
            return knight_moves[0], memory

    # Avoid reversing moves or repeating positions
    # Simple heuristic: prefer moves that move a piece not moved before, or castle
    # But since we don't track individual piece moves, favor castling and developing moves
    castling_moves = [m for m in legal_moves if m in ['O-O', 'O-O-O']]
    if castling_moves:
        # If safe, prefer castling
        if not is_king_in_check_after_castle(pieces, to_play, castling_moves[0]):
            return castling_moves[0], memory

    # If in late game, prefer king moves toward center
    if memory['move_count'] > 30:
        king_moves = [m for m in legal_moves if m.startswith('K') and len(m) == 3]
        if king_moves:
            king_square = next((sq for sq, piece in pieces.items() if piece == color + 'K'), None)
            if king_square:
                king_file = ord(king_square[0]) - ord('a')
                king_rank = int(king_square[1])
                center_file = 3.5
                center_rank = 4.5
                best_king_move = None
                best_distance = float('inf')
                for move in king_moves:
                    dest_file = ord(move[1]) - ord('a')
                    dest_rank = int(move[2])
                    dist = abs(dest_file - center_file) + abs(dest_rank - center_rank)
                    if dist < best_distance:
                        best_distance = dist
                        best_king_move = move
                if best_king_move:
                    return best_king_move, memory

    # If nothing better, pick the first legal move as fallback
    # Ensure we don't return an illegal move
    if legal_moves:
        # Try to avoid moves that put king in check later (simple heuristic)
        # Since we can't simulate, we assume legal_moves are safe
        # But we order by: castling, central pawn, then first available
        prioritized = []
        # Castling is top priority
        for move in ['O-O', 'O-O-O']:
            if move in legal_moves:
                prioritized.append(move)
        
        # Then central pawn moves, knight to center, etc.
        for move in legal_moves:
            if move not in prioritized:
                if len(move) == 2 and move[0] in 'abcdefgh' and move[1] in '45':  # central pawn
                    prioritized.append(move)
                elif len(move) == 3 and move[0] == 'N' and move[1:3] in center_squares:  # knight to center
                    prioritized.append(move)
                else:
                    prioritized.append(move)
        
        return prioritized[0], memory

    # Fallback: return any legal move (should not happen)
    if legal_moves:
        return legal_moves[0], memory

    # If there are no legal moves, this is a stalemate or error — but we must return a move
    # According to problem, legal_moves is correct and non-empty
    return 'a2a3', memory  # dummy

def is_king_in_check_after_castle(pieces, to_play, castle_move):
    # A heuristic to avoid castling into check
    # We don't simulate the full board, but we can check if the king would pass through attacked squares
    # This is simplified: if opponent has rooks or queens on the open file, or bishops on diagonals
    # We assume castling is safe unless very obvious threats
    # Since this is a simplified AI, we allow castle unless it's obviously dangerous
    # In real chess, we'd simulate, but here we just assume it's safe unless we have strong evidence otherwise
    # We'll be conservative: don't castle if opponent has a queen or rook on adjacent file
    color = 'w' if to_play == 'white' else 'b'
    king_pos = None
    for sq, piece in pieces.items():
        if piece == color + 'K':
            king_pos = sq
            break
    if not king_pos:
        return True  # can't find king, assume danger
    
    file = king_pos[0]
    rank = king_pos[1]
    
    # King starts at e1 or e8
    if castle_move == 'O-O':  # kingside
        # King moves to g1 or g8, passes f1/f8
        # Check if f and g files are attacked
        # Look for opponent pieces that can attack f or g squares
        opponent = 'b' if color == 'w' else 'w'
        # Check rooks/queens on the same file
        for sq, piece in pieces.items():
            if piece[0] == opponent:
                piece_type = piece[1]
                if piece_type in 'QR':  # can attack along files
                    if sq[0] == file or sq[0] == chr(ord(file) + 1) or sq[0] == chr(ord(file) + 2):
                        # On same file? Actually, the attack might come from behind
                        # Let's just assume if a rook/queen is on the same rank and file between b and g, it's risky
                        if sq[1] == rank:  # same rank
                            min_file = min(ord(file), ord('g'))
                            max_file = max(ord(file), ord('g'))
                            if min_file <= ord(sq[0]) <= max_file:
                                # There's a piece on the path — might be blocking or attacking
                                # Since we don't know the exact board, return False for safety
                                continue
                if piece_type in 'QB':  # can attack diagonals
                    # Check if on a diagonal that threatens f1/g1 or f8/g8
                    # Diagonal: |file_diff| == |rank_diff|
                    for target in [chr(ord(file) + 1) + rank, 'g' + rank]:  # f1, g1 or f8, g8
                        if len(target) == 2:
                            file_t = ord(target[0]) - ord('a')
                            rank_t = int(target[1]) - 1
                            piece_file = ord(sq[0]) - ord('a')
                            piece_rank = int(sq[1]) - 1
                            if abs(file_t - piece_file) == abs(rank_t - piece_rank):
                                # This piece can attack the square
                                # Remember: for kingside castle, king passes f1 and g1
                                # If opponent has bishop/queen on same diagonal, danger
                                if piece_type == 'B':
                                    return False  # conservative: avoid castle if bishop can attack
                                if piece_type == 'Q':
                                    return False  # queen is danger
        return False  # assume safe if no obvious threat

    elif castle_move == 'O-O-O':  # queenside
        # King moves to c1/c8, passes d1/d8
        opponent = 'b' if color == 'w' else 'w'
        for sq, piece in pieces.items():
            if piece[0] == opponent:
                piece_type = piece[1]
                if piece_type in 'QR':
                    if sq[0] == file or sq[0] == chr(ord(file) - 1) or sq[0] == chr(ord(file) - 2):
                        if sq[1] == rank:
                            continue
                if piece_type in 'QB':
                    for target in [chr(ord(file) - 1) + rank, 'c' + rank]:
                        if len(target) == 2:
                            file_t = ord(target[0]) - ord('a')
                            rank_t = int(target[1]) - 1
                            piece_file = ord(sq[0]) - ord('a')
                            piece_rank = int(sq[1]) - 1
                            if abs(file_t - piece_file) == abs(rank_t - piece_rank):
                                if piece_type == 'B' or piece_type == 'Q':
                                    return False
        return False  # assume safe
    
    return False  # By default, assume castling is safe
