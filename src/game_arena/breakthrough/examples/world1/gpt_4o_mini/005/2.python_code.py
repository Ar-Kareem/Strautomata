
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    def is_empty(row, col, pieces):
        return (row, col) not in pieces

    def can_capture(from_row, from_col, to_row, to_col, opponent):
        return (to_row, to_col) in opponent

    # Directions based on color
    if color == 'w':
        move_direction = -1
        win_row = 0
    else:
        move_direction = 1
        win_row = 7

    best_move = None

    for (from_row, from_col) in me:
        forward_row = from_row + move_direction
        # Check straight move
        if is_empty(forward_row, from_col, me + opp):
            best_move = ((from_row, from_col), (forward_row, from_col))

        # Check diagonal captures
        for diagonal_col in [from_col - 1, from_col + 1]:
            if 0 <= diagonal_col < 8:
                if can_capture(from_row, from_col, forward_row, diagonal_col, opp):
                    return ((from_row, from_col), (forward_row, diagonal_col))

        # Winning move
        if forward_row == win_row:
            return ((from_row, from_col), (forward_row, from_col))

    return best_move
