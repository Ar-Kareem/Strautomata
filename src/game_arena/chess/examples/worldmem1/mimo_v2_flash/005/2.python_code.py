
import random
import re

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    """
    Selects the best move based on heuristic evaluation of captures, promotions, and checks.
    """
    
    # Piece values for heuristic evaluation
    piece_values = {
        'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0
    }

    def get_move_score(move: str) -> int:
        score = 0
        
        # Priority 1: Promotions to Queen (highest material gain)
        # Match pattern like 'e8=Q', 'b8=Q', etc.
        if re.search(r'=[QRB]', move):
            score += 100  # High priority for promotion
        
        # Priority 2: Captures (MVV-LVA approximation)
        if 'x' in move:
            # Identify captured piece from the destination square
            # Move format can be 'Nxe4', 'exd5', 'Qxh7'
            # The captured piece is at the destination square
            dest_sq = move[-2:]  # Last two characters are usually the square
            
            # Look up the piece at the destination
            # Note: In standard SAN, the destination is where the piece moves to.
            # We need to know what is currently on that square.
            if dest_sq in pieces:
                captured_piece = pieces[dest_sq]
                captured_type = captured_piece[1] # 'Q', 'R', etc.
                
                if captured_type in piece_values:
                    # Basic capture logic: Value of captured piece
                    # Could be refined by identifying the aggressor piece type
                    score += piece_values[captured_type] * 10
                    
                    # Penalize low-value pieces capturing high-value pieces (risky)
                    # We don't know the aggressor type easily from SAN without parsing,
                    # but basic capture value is a good start.
        
        # Priority 3: Checks
        if '+' in move or '#' in move:
            score += 5
        
        # Priority 4: Random factor for non-capturing moves to avoid stagnation
        # But we want to minimize reliance on randomness unless necessary.
        # We will sort by score, and if scores are tied, random choice happens later.
        
        return score

    # Evaluate all legal moves
    # We want to avoid O(1) complexity if legal_moves is large, but it's chess (max ~200 moves)
    scored_moves = []
    for move in legal_moves:
        score = get_move_score(move)
        scored_moves.append((score, move))

    # Sort moves by score descending
    scored_moves.sort(key=lambda x: x[0], reverse=True)
    
    # Determine the best score
    best_score = scored_moves[0][0]
    
    # If we have a winning move (checkmate or high value capture), prioritize it strictly
    # However, if the top moves have equal high scores (e.g., multiple winning captures),
    # we should select one at random among the best to vary play.
    best_moves = [m for s, m in scored_moves if s == best_score]
    
    # If there are multiple moves with the same top score, pick one randomly
    # If only one, pick that one.
    action = random.choice(best_moves)
    
    # Return the action and updated memory (empty for this simple strategy)
    return action, {}
