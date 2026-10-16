
import numpy as np

def policy(you: list[int], opponent: list[int]) -> str:
    # Convert to numpy arrays for easier manipulation
    you = np.array(you, dtype=int)
    opponent = np.array(opponent, dtype=int)
    
    # Define directions: up, right, down, left
    directions = [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]
    
    # Find all legal moves
    legal_moves = []
    
    for row in range(5):
        for col in range(6):
            if you[row, col] == 1:  # Only consider positions with your pieces
                for dr, dc, dir_char in directions:
                    new_row, new_col = row + dr, col + dc
                    # Check bounds
                    if 0 <= new_row < 5 and 0 <= new_col < 6:
                        # Check if opponent piece is at destination
                        if opponent[new_row, new_col] == 1:
                            legal_moves.append((row, col, dir_char))
    
    # If no legal moves, return any move (though game should have ended)
    if not legal_moves:
        # This should not happen in a real game, but required by spec
        for row in range(5):
            for col in range(6):
                if you[row, col] == 1:
                    for dr, dc, dir_char in directions:
                        new_row, new_col = row + dr, col + dc
                        if 0 <= new_row < 5 and 0 <= new_col < 6:
                            if opponent[new_row, new_col] == 1:
                                return f"{row},{col},{dir_char}"
        # Fallback: return first possible position (shouldn't reach here)
        for row in range(5):
            for col in range(6):
                if you[row, col] == 1:
                    return f"{row},{col},R"  # Default direction
    
    # Score each legal move
    move_scores = []
    
    for row, col, dir_char in legal_moves:
        dr, dc = {'U': (-1, 0), 'R': (0, 1), 'D': (1, 0), 'L': (0, -1)}[dir_char]
        new_row, new_col = row + dr, col + dc
        
        # Base score: capture
        score = 1.0
        
        # Estimate opponent's mobility reduction
        # Check how many moves the captured piece enabled for opponent
        opponent_mobility = 0
        for ddr, ddc, _ in directions:
            opp_row, opp_col = new_row + ddr, new_col + ddc
            if 0 <= opp_row < 5 and 0 <= opp_col < 6:
                if you[opp_row, opp_col] == 1:  # This opponent piece could capture your piece
                    opponent_mobility += 1
        score -= 0.5 * opponent_mobility
        
        # Check connectivity after move
        # After moving, your piece will be at (new_row, new_col)
        # Check how many neighbors you have there
        after_connectivity = 0
        for ddr, ddc, _ in directions:
            nr, nc = new_row + ddr, new_col + ddc
            if 0 <= nr < 5 and 0 <= nc < 6 and you[nr, nc] == 1:
                after_connectivity += 1
        score += 0.3 * after_connectivity
        
        # Penalty for isolating on edge (if new position is edge and has no neighbors)
        if (new_row == 0 or new_row == 4 or new_col == 0 or new_col == 5) and after_connectivity == 0:
            score -= 0.4
        
        move_scores.append((score, row, col, dir_char))
    
    # Sort by score descending and pick best
    move_scores.sort(key=lambda x: x[0], reverse=True)
    
    # Return the highest-scoring move
    best_score, best_row, best_col, best_dir = move_scores[0]
    
    return f"{best_row},{best_col},{best_dir}"
