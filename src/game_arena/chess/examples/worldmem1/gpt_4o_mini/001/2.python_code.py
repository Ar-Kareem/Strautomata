
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    # A simple scoring system for evaluating the moves
    def evaluate_move(move):
        # This function can be expanded to include more checks and scoring
        score = 0
        if move.endswith('+'):
            score += 10  # Checks are positive
        if '=' in move:
            score += 5  # Promotions are valuable
        if 'x' in move:
            score += 3  # Captures are valuable
        return score

    # List to hold moves and their corresponding scores
    scored_moves = [(move, evaluate_move(move)) for move in legal_moves]
    
    # Sort the moves based on their scores
    scored_moves.sort(key=lambda x: x[1], reverse=True)
    
    # Choose the best move based on the scoring
    best_move = scored_moves[0][0]
    
    return best_move, memory
