
import numpy as np

def policy(you: list[int], opponent: list[int]) -> str:
    # Convert to numpy arrays for easier manipulation
    you_board = np.array(you, dtype=int)
    opp_board = np.array(opponent, dtype=int)
    
    # Dimensions
    rows, cols = 5, 6
    
    # Directions: Up, Right, Down, Left
    dirs = [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]
    
    # Find all your pieces
    your_pieces = np.where(you_board == 1)
    
    # List to store all legal moves
    moves = []
    
    # Check each of your pieces
    for i in range(len(your_pieces[0])):
        r = your_pieces[0][i]
        c = your_pieces[1][i]
        
        # Check each direction
        for dr, dc, d_str in dirs:
            nr, nc = r + dr, c + dc
            
            # Check bounds
            if 0 <= nr < rows and 0 <= nc < cols:
                # Check if opponent piece is there
                if opp_board[nr, nc] == 1:
                    # This is a legal move
                    moves.append((r, c, d_str))
    
    # Strategy: Prefer moves that maximize opponent's connectivity issues
    # or avoid immediate recapture if possible.
    # Here, we implement a simple greedy capture with slight preference for central control.
    
    if not moves:
        # This should not happen according to the prompt, but safety
        # Return a dummy move (should never occur)
        return "0,0,R"
    
    # Choose the first legal move (simple baseline)
    # For a more advanced policy, we could evaluate board states after each move
    # and choose the one that maximizes our advantage.
    # Given the time constraint, we return the first move.
    
    # Actually, let's prefer moves towards the center if possible
    # Center is roughly (2, 2.5) -> cells (2,2), (2,3)
    # We prefer moves that land closer to center
    
    best_move = moves[0]
    best_score = -1
    
    for r, c, d in moves:
        # Destination cell
        nr = r + (-1 if d == 'U' else 1 if d == 'D' else 0)
        nc = c + (1 if d == 'R' else -1 if d == 'L' else 0)
        
        # Distance to center (2.5, 2.5)
        # Score = - (distance squared)
        dist_sq = (nr - 2)**2 + (nc - 2.5)**2
        score = -dist_sq
        
        if score > best_score:
            best_score = score
            best_move = (r, c, d)
    
    r, c, d = best_move
    return f"{r},{c},{d}"
