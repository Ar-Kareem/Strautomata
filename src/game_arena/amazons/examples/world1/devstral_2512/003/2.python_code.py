
import numpy as np

def policy(board):
    # Directions for queen moves (8 directions: orthogonal + diagonal)
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1),
                  (-1, -1), (-1, 1), (1, -1), (1, 1)]

    def is_valid_move(from_pos, to_pos):
        """Check if moving from from_pos to to_pos is valid."""
        fr, fc = from_pos
        tr, tc = to_pos
        if board[fr, fc] != 1:
            return False
        if board[tr, tc] != 0:
            return False

        dr, dc = tr - fr, tc - fc
        if dr == 0 and dc == 0:
            return False

        # Check if move is in a straight line (queen move)
        if dr != 0 and dc != 0 and abs(dr) != abs(dc):
            return False

        # Determine step direction
        step_r = 1 if dr > 0 else (-1 if dr < 0 else 0)
        step_c = 1 if dc > 0 else (-1 if dc < 0 else 0)

        # Check path is clear
        r, c = fr + step_r, fc + step_c
        while (r, c) != (tr, tc):
            if board[r, c] != 0:
                return False
            r += step_r
            c += step_c

        return True

    def is_valid_arrow(from_pos, to_pos, arrow_pos):
        """Check if shooting an arrow from to_pos to arrow_pos is valid."""
        fr, fc = from_pos
        tr, tc = to_pos
        ar, ac = arrow_pos

        # Simulate the board after moving the amazon
        temp_board = board.copy()
        temp_board[fr, fc] = 0
        temp_board[tr, tc] = 1

        if temp_board[ar, ac] != 0:
            return False

        dr, dc = ar - tr, ac - tc
        if dr == 0 and dc == 0:
            return False

        # Check if arrow is in a straight line (queen move)
        if dr != 0 and dc != 0 and abs(dr) != abs(dc):
            return False

        # Determine step direction
        step_r = 1 if dr > 0 else (-1 if dr < 0 else 0)
        step_c = 1 if dc > 0 else (-1 if dc < 0 else 0)

        # Check path is clear
        r, c = tr + step_r, tc + step_c
        while (r, c) != (ar, ac):
            if temp_board[r, c] != 0:
                return False
            r += step_r
            c += step_c

        return True

    # Find all friendly amazons
    amazons = np.argwhere(board == 1)

    # Try to find a legal move
    for amazon in amazons:
        fr, fc = amazon
        # Generate all possible moves in 8 directions
        for dr, dc in directions:
            for step in range(1, 6):
                tr, tc = fr + dr * step, fc + dc * step
                if 0 <= tr < 6 and 0 <= tc < 6:
                    if is_valid_move((fr, fc), (tr, tc)):
                        # Now find a valid arrow shot from (tr, tc)
                        for adr, adc in directions:
                            for astep in range(1, 6):
                                ar, ac = tr + adr * astep, tc + adc * astep
                                if 0 <= ar < 6 and 0 <= ac < 6:
                                    if is_valid_arrow((fr, fc), (tr, tc), (ar, ac)):
                                        return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
                                else:
                                    break
                else:
                    break

    # Fallback: return any legal move (should not reach here if board is valid)
    # This is a safeguard to ensure we always return a legal move
    for fr in range(6):
        for fc in range(6):
            if board[fr, fc] == 1:
                for tr in range(6):
                    for tc in range(6):
                        if is_valid_move((fr, fc), (tr, tc)):
                            for ar in range(6):
                                for ac in range(6):
                                    if is_valid_arrow((fr, fc), (tr, tc), (ar, ac)):
                                        return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
    # If no move found (should not happen per problem statement)
    return "0,0:0,0:0,0"
