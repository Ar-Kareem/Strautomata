
import numpy as np
import random

def policy(you: list[int], opponent: list[int]) -> str:
    # Convert to numpy arrays for easier manipulation
    you_board = np.array(you).reshape(5, 6)
    opponent_board = np.array(opponent).reshape(5, 6)
    
    # Get all positions where we have pieces
    my_pieces = np.where(you_board == 1)
    my_positions = list(zip(my_pieces[0], my_pieces[1]))
    
    # Find all valid moves
    valid_moves = []
    
    # Directions: U, R, D, L
    directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
    dir_names = ['U', 'R', 'D', 'L']
    
    for row, col in my_positions:
        for i, (dr, dc) in enumerate(directions):
            new_row, new_col = row + dr, col + dc
            
            # Check if the destination is within bounds
            if 0 <= new_row < 5 and 0 <= new_col < 6:
                # Check if the destination contains opponent piece
                if opponent_board[new_row, new_col] == 1:
                    valid_moves.append((row, col, dir_names[i]))
    
    # If no moves available, return any legal move (should not happen with proper game logic)
    if not valid_moves:
        # Try all possible moves to find something
        for row in range(5):
            for col in range(6):
                if you_board[row, col] == 1:
                    for i, (dr, dc) in enumerate(directions):
                        new_row, new_col = row + dr, col + dc
                        if 0 <= new_row < 5 and 0 <= new_col < 6:
                            if opponent_board[new_row, new_col] == 1:
                                return f"{row},{col},{dir_names[i]}"
        # Fallback - just return a move of any piece
        for row, col in my_positions:
            for i, (dr, dc) in enumerate(directions):
                new_row, new_col = row + dr, col + dc
                if 0 <= new_row < 5 and 0 <= new_col < 6:
                    return f"{row},{col},{dir_names[i]}"
    
    # Prioritize capture moves
    capture_moves = []
    non_capture_moves = []
    
    for row, col, direction in valid_moves:
        capture_moves.append((row, col, direction))
    
    # Prefer capture moves or at least make moves that don't isolate pieces
    # In this case, we'll just pick a random good move
    # For a competitive policy, we'd do a more complex evaluation here
    
    # Select a move (this is a basic greedy approach - pick any capture move)
    if capture_moves:
        # Prefer moves toward center for better mobility
        center_priority = []
        for row, col, direction in capture_moves:
            # Check if the move brings the piece closer to center
            center_distance = abs(row - 2) + abs(col - 2.5)
            center_priority.append((row, col, direction, center_distance))
        
        # Sort by center proximity (smaller distance is better)
        center_priority.sort(key=lambda x: x[3])
        # Return the best one
        return f"{center_priority[0][0]},{center_priority[0][1]},{center_priority[0][2]}"
    else:
        # Just return the first move
        row, col, direction = valid_moves[0]
        return f"{row},{col},{direction}"
