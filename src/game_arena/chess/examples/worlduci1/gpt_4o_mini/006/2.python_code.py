
def policy(pieces: dict[str, str], to_play: str) -> str:
    def evaluate_move(move: str, pieces: dict[str, str]) -> int:
        # This is a mock evaluation function for demonstration
        score = 0
        
        # Extract the start and end positions
        start = move[:2]
        end = move[2:4]

        # Check if the move results in a capture
        if end in pieces:
            # Assign arbitrary values for piece types
            piece_values = {
                'K': 0,  # King irrelevant for capture
                'Q': 9,  # Queen
                'R': 5,  # Rook
                'B': 3,  # Bishop
                'N': 3,  # Knight
                'P': 1,  # Pawn
            }
            captured_piece = pieces[end]
            score += piece_values[captured_piece[1]]  # Get piece value
            
        # Check if the move gives check (assuming it's legal)
        if causes_check(move, pieces, to_play):
            score += 5  # Higher value for moves that check opponent
            
        # Potentially add more evaluation heuristics here
        
        return score

    def causes_check(move: str, pieces: dict[str, str], to_play: str) -> bool:
        # Very simplified check logic: assume it only checks if current player puts the opponent's king in check
        return False  # For simplicity in this mock example

    # Main logic
    best_move = None
    best_score = -float('inf')
    
    for move in legal_moves:
        score = evaluate_move(move, pieces)
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
