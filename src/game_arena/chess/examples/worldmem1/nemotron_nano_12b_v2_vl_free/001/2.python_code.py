
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    import re
    piece_values = {'K': 0, 'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1}
    best_move = None
    max_value = -float('inf')
    
    for move in legal_moves:
        # Determine the piece type making the move
        piece_type = None
        if move[0].islower():
            piece_type = 'P'
        else:
            if move[0].isalpha():
                piece_type = move[0]
            else:
                piece_type = 'K'  # Handle special cases like castling
        
        # Check for captures and calculate net value
        capture_sq = re.search(r'x([a-h][1-8])', move)
        captured_value = 0
        net_gain = 0
        if capture_sq:
            captured_sq_str = capture_sq.group(1)
            captured_piece = pieces.get(captured_sq_str)
            if captured_piece:
                captured_type = captured_piece[1]
                captured_value = piece_values.get(captured_type, 0)
            net_gain = captured_value - piece_values.get(piece_type, 0)
        else:
            net_gain = 0
        
        # Update best move based on net value
        if net_gain > max_value or (net_gain == max_value and best_move is None):
            max_value = net_gain
            best_move = move
    
    # Fallback to check promotions if no captures
    if best_move is None:
        for move in legal_moves:
            if '=' in move:
                best_move = move
                break
        else:
            best_move = legal_moves[0]
    
    return (best_move, memory)
