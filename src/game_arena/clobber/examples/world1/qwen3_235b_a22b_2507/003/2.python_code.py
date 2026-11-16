
import numpy as np

def policy(you: list[int], opponent: list[int]) -> str:
    # Convert to numpy arrays for easier indexing
    you = np.array(you).reshape(5, 6)
    opp = np.array(opponent).reshape(5, 6)
    
    directions = {
        'U': (-1, 0),
        'R': (0, 1),
        'D': (1, 0),
        'L': (0, -1)
    }
    
    # List to store legal moves with score
    legal_moves = []
    
    # Precompute center weights (higher in center)
    center_weights = np.array([
        [1, 2, 3, 3, 2, 1],
        [2, 4, 5, 5, 4, 2],
        [3, 5, 6, 6, 5, 3],
        [2, 4, 5, 5, 4, 2],
        [1, 2, 3, 3, 2, 1]
    ])
    
    for r in range(5):
        for c in range(6):
            if you[r, c] == 1:  # Our piece
                for d, (dr, dc) in directions.items():
                    nr, nc = r + dr, c + dc
                    # Check bounds
                    if 0 <= nr < 5 and 0 <= nc < 6:
                        # Check if opponent piece is there
                        if opp[nr, nc] == 1:
                            # Legal capture move
                            # Score based on destination weight and local pressure
                            score = center_weights[nr, nc]
                            
                            # Bonus: count how many opponent pieces are around destination (mobility next turn)
                            followup = 0
                            for dr2, dc2 in directions.values():
                                nr2, nc2 = nr + dr2, nc + dc2
                                if 0 <= nr2 < 5 and 0 <= nc2 < 6:
                                    # If we moved here, we'd have a piece at (nr, nc), so check captures from there
                                    if opp[nr2, nc2] == 1:
                                        followup += 1
                            score += followup * 0.5  # bonus for future mobility
                            
                            legal_moves.append((score, r, c, d))
    
    # If no legal move found (shouldn't happen per problem statement), return dummy
    if not legal_moves:
        # Fallback: scan again and pick first possible move
        for r in range(5):
            for c in range(6):
                if you[r, c] == 1:
                    for d, (dr, dc) in directions.items():
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < 5 and 0 <= nc < 6 and opp[nr, nc] == 1:
                            return f"{r},{c},{d}"
        # Should not reach here
        return "0,0,R"
    
    # Sort by score descending and pick best move
    legal_moves.sort(key=lambda x: -x[0])
    _, best_r, best_c, best_d = legal_moves[0]
    
    return f"{best_r},{best_c},{best_d}"
