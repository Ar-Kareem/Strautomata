
def get_piece_value(piece_str: str) -> int:
    if piece_str.startswith('K') or piece_str.startswith('k'):
        return 0  # Kings are not captured
    type_score = {
        'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9
    }.get(piece_str[1], 0)
    return type_score

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    # Check for check moves (highest priority)
    check_moves = [move for move in legal_moves if move.endswith('+')]
    if check_moves:
        best_check = None
        highest_score = -1
        for move in check_moves:
            # Calculate move score: captures add material value, +100 for check
            score = 100 + get_piece_value(pieces[target_square])  # 如果基本上是捕获棋子的值加上是否是一种检查性报给分
            if score > highest_score:
                best_check = move
                highest_score = score
        return best_check, memory

    # Evaluate all moves for material gain and promotions
    move_scores = []
    for move in legal_moves:
        capture_val = 0
        promotion_val = 0
        has_check = move.endswith('+')
        
        # Handle captures
        if 'x' in move:
            # Extract target square
            move_body = move.split('x')[1]
            target_square = move_body.split('=')[0] if '=' in move_body else move_body
            if target_square in pieces:
                captured_piece = pieces[target_square]
                capture_val = get_piece_value(captured_piece)
        
        # Handle promotions
        if '=' in move:
            promo_type = move.split('=')[1]
            promotion_val = get_piece_value(promotion_type + 'w') - 1  # Replace pawn
        
        # Compute total score
        total = capture_val + promotion_val
        if has_check:
            total += 100  # Additional bonus for check
        move_scores.append((move, total))
    
    # Select best move based on score
    if move_scores:
        move_scores.sort(key=lambda x: -x[1])
        best_move = move_scores[0][0]
    else:
        best_move = legal_moves[0]  # Fallback
    
    # Prioritize castling for king safety
    if 'O-O' in legal_moves:
        best_move = 'O-O'
    elif 'O-O-O' in legal_moves:
        best_move = 'O-O-O'
    
    return best_move, {}
