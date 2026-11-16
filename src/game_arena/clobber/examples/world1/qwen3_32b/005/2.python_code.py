
def policy(you: list[list[int]], opponent: list[list[int]]) -> str:
    # Generate all possible legal moves
    moves = []
    for row in range(5):
        for col in range(6):
            if you[row][col] == 1:
                if row - 1 >= 0 and opponent[row - 1][col] == 1:
                    moves.append((row, col, 'U'))
                if row + 1 < 5 and opponent[row + 1][col] == 1:
                    moves.append((row, col, 'D'))
                if col - 1 >= 0 and opponent[row][col - 1] == 1:
                    moves.append((row, col, 'L'))
                if col + 1 < 6 and opponent[row][col + 1] == 1:
                    moves.append((row, col, 'R'))

    def get_mobility(you_peek, opp_peek):
        """Calculate number of legal moves for the current player"""
        count = 0
        for r in range(5):
            for c in range(6):
                if you_peek[r][c] == 1:
                    if r - 1 >= 0 and opp_peek[r - 1][c] == 1:
                        count += 1
                    if r + 1 < 5 and opp_peek[r + 1][c] == 1:
                        count += 1
                    if c - 1 >= 0 and opp_peek[r][c - 1] == 1:
                        count += 1
                    if c + 1 < 6 and opp_peek[r][c + 1] == 1:
                        count += 1
        return count

    evaluated_moves = []
    for s_row, s_col, direction in moves:
        # Determine destination coordinates
        new_row, new_col = s_row, s_col
        if direction == 'U': new_row = s_row - 1
        elif direction == 'D': new_row = s_row + 1
        elif direction == 'L': new_col = s_col - 1
        elif direction == 'R': new_col = s_col + 1

        # Create copies of the board
        new_you = [row[:] for row in you]
        new_opponent = [row[:] for row in opponent]

        # Update the simulated board state
        new_you[s_row][s_col] = 0
        new_you[new_row][new_col] = 1
        new_opponent[new_row][new_col] = 0

        # Evaluate the move
        opponent_mob = get_mobility(new_opponent, new_you)
        my_mob = get_mobility(new_you, new_opponent)
        evaluated_moves.append((opponent_mob, -my_mob, s_row, s_col, direction))

    # Sort by opponent mobility (lowest first) then by our mobility (highest first)
    evaluated_moves.sort()
    best_move = evaluated_moves[0]

    return f"{best_move[2]},{best_move[3]},{best_move[4]}"
