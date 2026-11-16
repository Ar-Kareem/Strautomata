
def policy(you, opponent):
    directions = [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]
    best_move = None
    best_score = -1

    for row in range(5):
        for col in range(6):
            if you[row][col] == 1:
                for dr, dc, dir in directions:
                    dest_row, dest_col = row + dr, col + dc
                    if 0 <= dest_row < 5 and 0 <= dest_col < 6 and opponent[dest_row][dest_col] == 1:
                        # Score is the number of opponent pieces adjacent to the captured piece
                        score = 0
                        for orow in [dest_row - 1, dest_row, dest_row + 1]:
                            for ocol in [dest_col - 1, dest_col, dest_col + 1]:
                                if 0 <= orow < 5 and 0 <= ocol < 6 and opponent[orow][ocol] == 1 and (orow != dest_row or ocol != dest_col):
                                    score += 1
                        # Also add the number of your pieces adjacent to the captured piece
                        for your_row in [dest_row - 1, dest_row, dest_row + 1]:
                            for your_col in [dest_col - 1, dest_col, dest_col + 1]:
                                if 0 <= your_row < 5 and 0 <= your_col < 6 and you[your_row][your_col] == 1 and (your_row != dest_row or your_col != dest_col):
                                    score += 1
                        if score > best_score:
                            best_score = score
                            best_move = (row, col, dir)
                            # Early exit if we find a move with score > 0
                            if best_score > 0:
                                return f"{row},{col},{dir}"
    # Fallback (shouldn't be needed per problem statement)
    for row in range(5):
        for col in range(6):
            if you[row][col] == 1:
                for dr, dc, dir in directions:
                    dest_row, dest_col = row + dr, col + dc
                    if 0 <= dest_row < 5 and 0 <= dest_col < 6 and opponent[dest_row][dest_col] == 1:
                        return f"{row},{col},{dir}"
    return ""  # Should never reach here
