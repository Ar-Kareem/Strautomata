
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    import random
    
    # Utility functions
    def is_capture(move: str) -> bool:
        return 'x' in move
    
    def is_checkmate(move: str) -> bool:
        return '#' in move
    
    def is_check(move: str) -> bool:
        return '+' in move
    
    def piece_value(piece: str) -> int:
        if piece == 'P' or piece == 'p': return 1
        if piece == 'N' or piece == 'n': return 3
        if piece == 'B' or piece == 'b': return 3
        if piece == 'R' or piece == 'r': return 5
        if piece == 'Q' or piece == 'q': return 9
        return 0
    
    def get_captured_piece(move: str) -> str:
        # Extract target square from move
        # Example: Rxc3 -> c3
        # Example: b8=Q+ -> b8
        # Example: O-O -> None
        if move.startswith('O-O'):
            return None
        # Remove checkmate/check markers and promotion markers
        move_clean = move.replace('+', '').replace('#', '')
        if '=' in move_clean:
            # Promotion: b8=Q -> b8
            move_clean = move_clean.split('=')[0]
        if 'x' in move_clean:
            # Capture: Rxc3 -> c3
            target = move_clean.split('x')[1]
        else:
            # Simple move: Ra1 -> a1
            # Find last square
            import re
            squares = re.findall(r'[a-h][1-8]', move_clean)
            if squares:
                target = squares[-1]
            else:
                return None
        return pieces.get(target, None)
    
    # Strategy
    # 1. Checkmate move
    for move in legal_moves:
        if is_checkmate(move):
            return move
    
    # 2. Capture highest value piece
    best_capture = None
    best_capture_value = -1
    for move in legal_moves:
        if is_capture(move):
            captured = get_captured_piece(move)
            if captured:
                value = piece_value(captured[1])
                if value > best_capture_value:
                    best_capture_value = value
                    best_capture = move
    if best_capture:
        return best_capture
    
    # 3. Check moves
    check_moves = [m for m in legal_moves if is_check(m)]
    if check_moves:
        return random.choice(check_moves)
    
    # 4. Random move
    return random.choice(legal_moves)
