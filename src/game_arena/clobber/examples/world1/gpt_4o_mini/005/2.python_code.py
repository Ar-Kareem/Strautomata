
def policy(you: list[int], opponent: list[int]) -> str:
    directions = {
        'U': (-1, 0),
        'R': (0, 1),
        'D': (1, 0),
        'L': (0, -1)
    }
    
    best_move = None

    for row in range(5):
        for col in range(6):
            if you[row][col] == 1:
                for direction, (dr, dc) in directions.items():
                    new_row, new_col = row + dr, col + dc
                    if 0 <= new_row < 5 and 0 <= new_col < 6 and opponent[new_row][new_col] == 1:
                        # We found a valid move, prioritizing this move if possible
                        if not best_move:  # Initial best move
                            best_move = f"{row},{col},{direction}"
                        else:
                            # Logic could be added here to choose which move is better 
                            pass  # For now, we pick the first valid capture we find

    if best_move:
        return best_move

    # If no captures are possible, we have to make a legal move
    # This is an additional fallback and would require more complex handling
    for row in range(5):
        for col in range(6):
            if you[row][col] == 1:
                for direction, (dr, dc) in directions.items():
                    new_row, new_col = row + dr, col + dc
                    if 0 <= new_row < 5 and 0 <= new_col < 6 and opponent[new_row][new_col] == 0:
                        return f"{row},{col},{direction}"

    # In case no moves are found, return a default legal move
    return '0,0,R'  # Fallback move, just as a placeholder
