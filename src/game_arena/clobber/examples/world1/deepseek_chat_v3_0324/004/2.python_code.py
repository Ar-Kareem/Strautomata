
import numpy as np

def policy(you: list[int], opponent: list[int]) -> str:
    you = np.array(you)
    opponent = np.array(opponent)
    rows, cols = 5, 6
    
    # Find all legal moves
    legal_moves = []
    directions = [('U', -1, 0), ('D', 1, 0), ('L', 0, -1), ('R', 0, 1)]
    
    for row in range(rows):
        for col in range(cols):
            if you[row, col] == 1:  # our piece
                for dir_name, dr, dc in directions:
                    new_row, new_col = row + dr, col + dc
                    if (0 <= new_row < rows and 0 <= new_col < cols and 
                        opponent[new_row, new_col] == 1):
                        legal_moves.append((row, col, dir_name))
    
    if not legal_moves:
        raise ValueError("No legal moves available - should not happen on our turn")
    
    # First check for any immediate winning move
    for move in legal_moves:
        row, col, dir_name = move
        dr, dc = 0, 0
        for d in directions:
            if d[0] == dir_name:
                dr, dc = d[1], d[2]
                break
        
        new_you = you.copy()
        new_opponent = opponent.copy()
        new_you[row, col] = 0
        new_you[row + dr, col + dc] = 1
        new_opponent[row + dr, col + dc] = 0
        
        # Check if opponent has no moves left
        opponent_has_move = False
        for opp_row in range(rows):
            for opp_col in range(cols):
                if new_opponent[opp_row, opp_col] == 1:
                    for _, opp_dr, opp_dc in directions:
                        new_opp_row, new_opp_col = opp_row + opp_dr, opp_col + opp_dc
                        if (0 <= new_opp_row < rows and 0 <= new_opp_col < cols and 
                            new_you[new_opp_row, new_opp_col] == 1):
                            opponent_has_move = True
                            break
                    if opponent_has_move:
                        break
                if opponent_has_move:
                    break
        
        if not opponent_has_move:
            return f"{row},{col},{dir_name}"
    
    # Evaluate moves based on piece difference (ours - theirs) after move
    best_diff = -float('inf')
    best_moves = []
    
    for move in legal_moves:
        row, col, dir_name = move
        dr, dc = 0, 0
        for d in directions:
            if d[0] == dir_name:
                dr, dc = d[1], d[2]
                break
        
        new_you_count = np.sum(you)  # we lose 0, gain 0 (but capture theirs)
        new_opponent_count = np.sum(opponent) - 1
        
        # Heuristic: prefer moves that are more central
        center_score = abs(row - 2) + abs(col - 2.5)
        
        # Also consider mobility
        mobility_score = 0
        for r in range(rows):
            for c in range(cols):
                if you[r, c] == 1:
                    for _, dr_m, dc_m in directions:
                        nr, nc = r + dr_m, c + dc_m
                        if (0 <= nr < rows and 0 <= nc < cols and
                            opponent[nr, nc] == 1 and (r != row or c != col or nr != row + dr or nc != col + dc)):
                            mobility_score += 1
        
        # Combined score
        score = (new_you_count - new_opponent_count) - center_score/10 + mobility_score/100
        
        if score > best_diff:
            best_diff = score
            best_moves = [move]
        elif score == best_diff:
            best_moves.append(move)
    
    # Among best moves, prefer those with better centrality
    if best_moves:
        if len(best_moves) > 1:
            # Get the most central move
            min_center = float('inf')
            final_move = None
            for move in best_moves:
                row, col, _ = move
                center = abs(row - 2) + abs(col - 2.5)  # distance from center
                if center < min_center:
                    min_center = center
                    final_move = move
            best_moves = [final_move]
        
        row, col, dir_name = best_moves[0]
        return f"{row},{col},{dir_name}"
    
    # Fallback: just return the first legal move (shouldn't reach here)
    row, col, dir_name = legal_moves[0]
    return f"{row},{col},{dir_name}"
