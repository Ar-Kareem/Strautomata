
def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    def evaluate_move(move: str) -> int:
        # Simple evaluation function to prioritize moves
        from_piece = pieces[move[:2]]  # e.g., 'g3'
        to_piece = pieces.get(move[2:4], None)  # e.g., 'e4'

        # Determine base value of the piece being moved
        base_value = piece_value(from_piece[1])
        
        # If the move results in capturing an opponent's piece, add its value
        if to_piece:
            value_change = piece_value(to_piece[1])
            return base_value + value_change
        return base_value

    def piece_value(piece_type: str) -> int:
        if piece_type == 'K': return 0  # King is invaluable
        if piece_type == 'Q': return 9
        if piece_type == 'R': return 5
        if piece_type == 'B': return 3
        if piece_type == 'N': return 3
        if piece_type == 'P': return 1
        return 0

    # Assumed legal moves are passed in as argument
    legal_moves = list(memory.get('legal_moves', []))
    
    # Prioritize moves by their evaluation score
    best_move = None
    best_score = float('-inf')

    for move in legal_moves:
        score = evaluate_move(move)
        if score > best_score:  # Prefer higher scores
            best_score = score
            best_move = move

    # Store legal moves for future calls
    memory['legal_moves'] = legal_moves
    return best_move, memory
