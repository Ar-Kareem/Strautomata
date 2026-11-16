
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    def evaluate_move(move: str, pieces: dict[str, str]) -> int:
        score = 0
        
        # Capture evaluation
        if 'x' in move:  # It's a capture move
            target_square = move.split('x')[1][:2]  # Assuming [Nx, Capture]
            if target_square in pieces:  # If the target square has a piece
                piece = pieces[target_square]
                value = 0
                if piece[1] == 'P':
                    value = 1
                elif piece[1] == 'N' or piece[1] == 'B':
                    value = 3
                elif piece[1] == 'R':
                    value = 5
                elif piece[1] == 'Q':
                    value = 9
                elif piece[1] == 'K':
                    value = 100  # Highly prioritize capturing the king (in illegal states)
                score += value
        
        # Check and Checkmate evaluation
        if '+' in move or '#' in move:
            score += 1000   # High value for check/checkmate moves
        
        return score

    best_move = ''
    best_score = -float('inf')
    
    for move in legal_moves:
        score = evaluate_move(move, pieces)    
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move, memory
