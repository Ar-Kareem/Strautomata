
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    # Determine the direction of movement based on color
    direction = -1 if color == 'b' else 1
    home_row = 0 if color == 'b' else 7

    # Convert opponent positions to a set for faster lookup
    opp_positions = set(opp)
    me_positions = set(me)

    # Check for winning moves first
    for piece in me:
        row, col = piece
        # Check straight forward move to home row
        new_row = row + direction
        if new_row == home_row:
            if (new_row, col) not in me_positions and (new_row, col) not in opp_positions:
                return ((row, col), (new_row, col))
        # Check diagonal forward moves to home row
        for dc in [-1, 1]:
            new_col = col + dc
            if 0 <= new_col < 8:
                new_row = row + direction
                if new_row == home_row:
                    if (new_row, new_col) not in me_positions:
                        return ((row, col), (new_row, new_col))

    # Check for captures
    for piece in me:
        row, col = piece
        for dc in [-1, 1]:
            new_col = col + dc
            new_row = row + direction
            if 0 <= new_col < 8 and 0 <= new_row < 8:
                if (new_row, new_col) in opp_positions:
                    return ((row, col), (new_row, new_col))

    # Check for forward moves (straight or diagonal)
    for piece in me:
        row, col = piece
        # Straight forward
        new_row = row + direction
        if 0 <= new_row < 8:
            if (new_row, col) not in me_positions and (new_row, col) not in opp_positions:
                return ((row, col), (new_row, col))
        # Diagonal forward
        for dc in [-1, 1]:
            new_col = col + dc
            new_row = row + direction
            if 0 <= new_col < 8 and 0 <= new_row < 8:
                if (new_row, new_col) not in me_positions and (new_row, new_col) not in opp_positions:
                    return ((row, col), (new_row, new_col))

    # If no moves found (should not happen as per game rules), return the first piece's straight move (fallback)
    # This is a safeguard to ensure a legal move is always returned
    if me:
        row, col = me[0]
        new_row = row + direction
        if 0 <= new_row < 8 and (new_row, col) not in me_positions:
            return ((row, col), (new_row, col))
        # If straight is blocked, try diagonal
        for dc in [-1, 1]:
            new_col = col + dc
            new_row = row + direction
            if 0 <= new_col < 8 and 0 <= new_row < 8:
                if (new_row, new_col) not in me_positions:
                    return ((row, col), (new_row, new_col))

    # Final fallback: return the first legal move found (should not reach here)
    for piece in me:
        row, col = piece
        for dr, dc in [(direction, 0), (direction, -1), (direction, 1)]:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                if (new_row, new_col) not in me_positions:
                    return ((row, col), (new_row, new_col))

    # If all else fails, return a dummy move (should not happen)
    return ((0, 0), (1, 0))
