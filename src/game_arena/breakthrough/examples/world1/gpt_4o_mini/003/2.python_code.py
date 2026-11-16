
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    directions = [(-1, 0), (-1, -1), (-1, 1)]  # Forward, Left Diagonal, Right Diagonal
    opponent_set = set(opp)
    target_row = 0 if color == 'b' else 7  # Target home row depending on player color
    
    # Check for immediate winning moves
    for (r, c) in me:
        if r == target_row - (1 if color == 'b' else -1):
            return ((r, c), (target_row, c))  # Move to home row
            
    # Prepare to capture an opponent's piece
    for (r, c) in me:
        for dr, dc in directions[1:]:  # Only diagonal captures
            new_r, new_c = r + dr, c + dc
            if (new_r, new_c) in opponent_set:
                return ((r, c), (new_r, new_c))  # Capture move
    
    # Advance pieces without immediate capture
    for (r, c) in me:
        for dr, dc in directions:
            new_r, new_c = r + dr, c + dc
            if 0 <= new_r < 8 and 0 <= new_c < 8 and (new_r, new_c) not in opponent_set and (new_r, new_c) not in me:
                return ((r, c), (new_r, new_c))  # Move forward
    
    # Fallback (should not happen in a normal game)
    return ((0, 0), (0, 0))  # Invalid move (should not reach here)
