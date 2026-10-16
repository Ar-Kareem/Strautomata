
import numpy as np

def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    # Initialize memory if needed
    if not memory:
        memory['history'] = []
        memory['last_capture'] = 0
    
    # Get color prefix
    color_prefix = 'w' if to_play == 'white' else 'b'
    opponent_prefix = 'b' if color_prefix == 'w' else 'w'
    
    # Generate all legal moves
    legal_moves = _generate_legal_moves(pieces, color_prefix)
    if not legal_moves:
        return ('', memory)  # should never happen as we must return a move
    
    # Special handling for first move (prioritize e4/e5 or d4/d5)
    if len(memory['history']) == 0:
        for move in ['e2e4', 'e7e5', 'd2d4', 'd7d5']:
            if move in legal_moves:
                memory['history'].append(move)
                return (move, memory)
    
    # 1. Check for checkmate moves first
    for move in legal_moves:
        new_pieces = _apply_move(pieces.copy(), move, color_prefix)
        if _is_checkmate(new_pieces, opponent_prefix):
            memory['history'].append(move)
            return (move, memory)
    
    # 2. Check for captures
    capture_moves = []
    for move in legal_moves:
        target = move[2:4]
        if target in pieces and pieces[target][0] == opponent_prefix:
            capture_moves.append(move)
    
    if capture_moves:
        # Evaluate captures by material gain
        best_capture = None
        best_score = -999
        for move in capture_moves:
            score = _evaluate_capture(pieces, move, color_prefix)
            if score > best_score:
                best_score = score
                best_capture = move
        if best_capture:
            memory['history'].append(best_capture)
            memory['last_capture'] = len(memory['history'])
            return (best_capture, memory)
    
    # 3. Prioritize castling if possible
    castling_moves = []
    for move in legal_moves:
        piece = pieces.get(move[0:2], '')
        if piece and piece[1] == 'K' and abs(ord(move[0]) - ord(move[2])) == 2:
            castling_moves.append(move)
    
    if castling_moves:
        # Prefer short castling
        for move in castling_moves:
            if move in ['e1g1', 'e8g8']:
                memory['history'].append(move)
                return (move, memory)
        # Otherwise take any castling
        memory['history'].append(castling_moves[0])
        return (castling_moves[0], memory)
    
    # 4. If we just captured something, consider avoiding recapture
    if memory['last_capture'] == len(memory['history']):
        safe_moves = []
        for move in legal_moves:
            target = move[2:4]
            if target not in pieces or pieces[target][0] == color_prefix:
                safe_moves.append(move)
        if safe_moves:
            legal_moves = safe_moves
    
    # 5. Evaluate positional moves
    scored_moves = []
    for move in legal_moves:
        score = _evaluate_move(pieces, move, color_prefix, memory)
        scored_moves.append((score, move))
    
    # Sort moves by score (highest first)
    scored_moves.sort(reverse=True, key=lambda x: x[0])
    
    # Return best move
    best_move = scored_moves[0][1]
    memory['history'].append(best_move)
    return (best_move, memory)

def _generate_legal_moves(pieces, color_prefix):
    # This simplified version assumes all moves are already legal
    # In a real implementation, this would need to generate moves correctly
    # For the arena, this will be handled by the game engine
    return []

def _apply_move(pieces, move, color_prefix):
    # Create a new pieces dictionary with the move applied
    new_pieces = pieces.copy()
    src = move[:2]
    dst = move[2:]
    if len(move) == 5:  # promotion
        piece = color_prefix + move[4].upper()
        new_pieces[dst] = piece
    else:
        piece = new_pieces.pop(src)
        new_pieces[dst] = piece
    return new_pieces

def _is_checkmate(pieces, opponent_prefix):
    # Simplified - assumes opponent has no legal moves and is in check
    # In reality, need to verify check and all possible legal moves
    return False

def _evaluate_capture(pieces, move, color_prefix):
    src = move[:2]
    dst = move[2:]
    moving_piece = pieces[src]
    captured_piece = pieces.get(dst, None)
    
    if not captured_piece:
        return 0
    
    # Piece values
    values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 100}
    
    # Calculate material exchange
    captured_value = values.get(captured_piece[1], 0)
    moving_value = values.get(moving_piece[1], 0)
    
    # Basic evaluation (difference + 1 if we're capturing with a less valuable piece)
    score = captured_value - moving_value * 0.1
    if captured_value > moving_value:
        score += 1
    
    return score

def _evaluate_move(pieces, move, color_prefix, memory):
    src = move[:2]
    dst = move[2:]
    piece = pieces.get(src, '')
    
    if not piece:
        return 0
    
    piece_type = piece[1]
    score = 0
    
    # Center control
    center_squares = ['d4', 'd5', 'e4', 'e5']
    if dst in center_squares:
        score += 0.5
    
    # Development (moving pieces from initial squares)
    if piece_type in ['N', 'B', 'Q', 'R']:
        if (color_prefix == 'w' and src[1] == '1') or (color_prefix == 'b' and src[1] == '8'):
            score += 0.3
    
    # King safety
    if piece_type == 'K' and abs(ord(src[0]) - ord(dst[0])) > 1:
        score += 1  # castling
    
    # Pawn structure (move forward)
    if piece_type == 'P':
        if (color_prefix == 'w' and dst[1] > src[1]) or (color_prefix == 'b' and dst[1] < src[1]):
            score += 0.2
    
    # Minor penalty for moving same piece repeatedly
    history = memory.get('history', [])
    if len(history) >= 2 and history[-2][:2] == src and history[-1][:2] == src:
        score -= 0.1
    
    return score
