
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    moves = []
    
    if color == 'w':
        direction = -1  # White moves up
    else:
        direction = 1   # Black moves down

    # Generate potential moves
    for (row, col) in me:
        forward = row + direction
        if 0 <= forward < 8:
            # Move straight forward
            if (forward, col) not in me and (forward, col) not in opp:
                moves.append(((row, col), (forward, col)))

            # Move diagonally left
            if col > 0 and (forward, col - 1) not in me:
                if (forward, col - 1) in opp:
                    moves.append(((row, col), (forward, col - 1)))  # Capture
                elif (forward, col - 1) not in opp:
                    moves.append(((row, col), (forward, col - 1)))

            # Move diagonally right
            if col < 7 and (forward, col + 1) not in me:
                if (forward, col + 1) in opp:
                    moves.append(((row, col), (forward, col + 1)))  # Capture
                elif (forward, col + 1) not in opp:
                    moves.append(((row, col), (forward, col + 1)))

    # Prioritize winning moves first
    for move in moves:
        (from_row, from_col), (to_row, to_col) = move
        if color == 'w' and to_row == 0:  # White moves into row 0 to win
            return move
        if color == 'b' and to_row == 7:  # Black moves into row 7 to win
            return move

    # If no winning move, take first valid move
    return moves[0] if moves else None
