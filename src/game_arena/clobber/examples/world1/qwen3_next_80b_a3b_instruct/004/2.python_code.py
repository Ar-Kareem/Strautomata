
import numpy as np

def policy(you: list[int], opponent: list[int]) -> str:
    # Convert to numpy arrays for easier manipulation
    you = np.array(you)
    opponent = np.array(opponent)
    
    # Define the four possible directions: up, right, down, left
    directions = [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]
    
    # Find all legal moves
    legal_moves = []
    
    for row in range(5):
        for col in range(6):
            if you[row, col] == 1:  # This is our piece
                for dr, dc, dir_char in directions:
                    new_row, new_col = row + dr, col + dc
                    # Check if the destination is within bounds
                    if 0 <= new_row < 5 and 0 <= new_col < 6:
                        # Check if destination has opponent piece
                        if opponent[new_row, new_col] == 1:
                            legal_moves.append((row, col, dir_char))
    
    # If no legal moves (shouldn't happen in valid game state, but safety)
    if not legal_moves:
        # Fallback: return a dummy move (this should never be reached)
        return "0,0,U"
    
    # Score each legal move to select the best one
    best_move = legal_moves[0]
    best_score = -float('inf')
    
    for row, col, dir_char in legal_moves:
        dr, dc, _ = {'U': (-1, 0), 'R': (0, 1), 'D': (1, 0), 'L': (0, -1)}[dir_char]
        new_row, new_col = row + dr, col + dc
        
        # Score based on:
        # 1. Immediate capture (all are equal here)
        # 2. Future mobility potential: count how many opponent pieces are adjacent to the destination
        score = 0
        
        # Count adjacent opponent pieces at the destination (potential for follow-up captures)
        for ddr, ddc in [(-1, 0), (0, 1), (1, 0), (0, -1)]:
            adj_row, adj_col = new_row + ddr, new_col + ddc
            if 0 <= adj_row < 5 and 0 <= adj_col < 6:
                if opponent[adj_row, adj_col] == 1:
                    # This opponent piece is adjacent to where we'll be after capture
                    score += 1
        
        # Bonus: if the destination is not on the edge, prefer it (center control)
        if 0 < new_row < 4 and 0 < new_col < 5:
            score += 2  # Center bonus
        
        # Prefer moves that capture pieces with low connectivity (isolated)
        # Count how many opponent pieces are adjacent to the captured piece
        opponent_adjacent_count = 0
        for ddr, ddc in [(-1, 0), (0, 1), (1, 0), (0, -1)]:
            adj_row, adj_col = new_row + ddr, new_col + ddc
            if 0 <= adj_row < 5 and 0 <= adj_col < 6:
                if opponent[adj_row, adj_col] == 1:
                    opponent_adjacent_count += 1
        
        # Penalty for capturing a piece that is well-connected (opponent might have good response)
        # We want to capture isolated pieces to reduce opponent's mobility
        if opponent_adjacent_count == 0:
            score += 3  # High bonus for capturing isolated piece
        
        # Avoid moves that leave our piece vulnerable to immediate recapture
        # Check if the opponent can recapture from adjacent squares after our move
        vulnerable = False
        for ddr, ddc in [(-1, 0), (0, 1), (1, 0), (0, -1)]:
            adj_row, adj_col = row + ddr, col + ddc
            if 0 <= adj_row < 5 and 0 <= adj_col < 6:
                # If opponent has a piece adjacent to our starting position
                if opponent[adj_row, adj_col] == 1:
                    # And that opponent piece can move to our new position (new_row, new_col)
                    for ddr2, ddc2 in [(-1, 0), (0, 1), (1, 0), (0, -1)]:
                        recapture_row, recapture_col = adj_row + ddr2, adj_col + ddc2
                        if (recapture_row, recapture_col) == (new_row, new_col):
                            # This opponent piece can recapture us
                            # This is risky, so deduct score
                            vulnerable = True
                            break
                    if vulnerable:
                        break
        
        if vulnerable:
            score -= 2  # Penalize vulnerable moves
        
        # Prefer moves that don't place us on the edge (edge pieces are more vulnerable)
        if new_row == 0 or new_row == 4 or new_col == 0 or new_col == 5:
            score -= 1  # Slight penalty for edge positioning
        
        # Higher score is better
        if score > best_score:
            best_score = score
            best_move = (row, col, dir_char)
    
    # Return the best move in required format
    return f"{best_move[0]},{best_move[1]},{best_move[2]}"
