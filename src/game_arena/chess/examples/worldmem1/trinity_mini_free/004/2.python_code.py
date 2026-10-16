
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    # Initialize evaluation scores for each move
    move_scores = {}
    
    # Helper function to evaluate material balance
    def evaluate_material():
        material = 0
        for square, piece in pieces.items():
            if piece[0] == 'w':
                material += PIECE_VALUES[piece[1]]
            else:
                material -= PIECE_VALUES[piece[1]]
        return material
    
    # Helper function to check if king is in check
    def is_king_in_check(color):
        king_square = None
        for square, piece in pieces.items():
            if piece == f"{color}K":
                king_square = square
                break
        if not king_square:
            return False
        
        # Check for checks from opponent's pieces
        for square, piece in pieces.items():
            if piece[0] != color:
                # Generate all possible moves for opponent's piece
                # (Simplified: check if any piece can attack king_square)
                # This is a placeholder; actual implementation would require move generation
                pass
        return False
    
    # Piece values for material evaluation
    PIECE_VALUES = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9}
    
    # Evaluate each legal move
    for move in legal_moves:
        # Simulate move on current board
        # (Actual simulation would require parsing move string and updating pieces)
        # Placeholder: assume move doesn't change material or king safety
        material_diff = evaluate_material()
        check_status = is_king_in_check(to_play)
        
        # Score based on material and king safety
        score = material_diff
        if check_status:
            score -= 100  # Severe penalty for exposing king to check
        
        move_scores[move] = score
    
    # Select move with highest score
    best_move = max(legal_moves, key=lambda move: move_scores[move])
    return best_move, {}
