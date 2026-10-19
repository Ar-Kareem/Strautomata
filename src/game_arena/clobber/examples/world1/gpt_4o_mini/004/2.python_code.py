
def policy(you: list[int], opponent: list[int]) -> str:
    rows, cols = 5, 6
    directions = {
        'U': (-1, 0),
        'R': (0, 1),
        'D': (1, 0),
        'L': (0, -1)
    }
    
    def is_within_bounds(x, y):
        return 0 <= x < rows and 0 <= y < cols

    best_move = None

    # Iterate through the board to find potential moves
    for row in range(rows):
        for col in range(cols):
            if you[row][col] == 1:  # If there's a piece of yours
                for dir, (d_row, d_col) in directions.items():
                    new_row, new_col = row + d_row, col + d_col
                    # Check if we can capture an opponent's piece
                    if is_within_bounds(new_row, new_col) and opponent[new_row][new_col] == 1:
                        current_move = f"{row},{col},{dir}"
                        # Store the first found move
                        if best_move is None:
                            best_move = current_move

                        # Here we can implement additional logic such as prioritizing larger captures 
                        # or preventing future opponent moves, but for this implementation
                        # we return the first valid move found.
    
    if best_move:
        return best_move
    
    # Fallback, if no moves found (though this shouldn't happen per the guarantees of the game)
    return "0,0,D"  # A default move (non-capturing) just to conform to the API requirements
