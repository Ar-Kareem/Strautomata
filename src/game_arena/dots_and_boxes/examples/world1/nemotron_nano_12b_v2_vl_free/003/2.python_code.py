
import numpy as np

def policy(horizontal, vertical, capture):
    def get_captures(move_type, r, c):
        caps = 0
        if move_type == 'H':
            # Check upper box (r-1, c)
            if r > 0:
                top = horizontal[r-1, c] != 0
                left = vertical[r-1, c] != 0
                right = vertical[r-1, c+1] != 0
                if top and left and right:
                    caps += 1
            # Check lower box (r, c)
            if r < 4:
                left = vertical[r, c] != 0
                right = vertical[r, c+1] != 0
                bottom = horizontal[r+1, c] != 0
                if left and right and bottom:
                    caps += 1
        else:
            # Check left box (r, c-1)
            if c > 0:
                top = horizontal[r, c-1] != 0
                left = vertical[r, c-1] != 0
                bottom = horizontal[r+1, c-1] != 0
                if top and left and bottom:
                    caps += 1
            # Check right box (r, c)
            if c <= 3:
                top = horizontal[r, c] != 0
                bottom = horizontal[r+1, c] != 0
                right = vertical[r, c+1] != 0
                if top and bottom and right:
                    caps += 1
        return caps

    def get_three_sided_count(move_type, r, c):
        three_count = 0
        if move_type == 'H':
            # Check upper box (r-1, c)
            if r > 0:
                left = vertical[r-1, c] != 0
                right = vertical[r-1, c+1] != 0
                top = horizontal[r-1, c] != 0
                sum_edges = left + right + top
                if sum_edges == 2:
                    three_count += 1
            # Check lower box (r, c)
            if r < 4:
                left_mv = vertical[r, c] != 0
                right_mv = vertical[r, c+1] != 0
                bottom = horizontal[r+1, c] != 0
                sum_edges = left_mv + right_mv + bottom
                if sum_edges == 2:
                    three_count += 1
        else:
            # Check left box (r, c-1)
            if c > 0:
                top = horizontal[r, c-1] != 0
                bottom = horizontal[r+1, c-1] != 0
                left_edge = vertical[r, c-1] != 0
                sum_edges = top + bottom + left_edge
                if sum_edges == 2:
                    three_count += 1
            # Check right box (r, c)
            if c <= 3 and r <= 3:
                top = horizontal[r, c] != 0
                bottom = horizontal[r+1, c] != 0
                right = vertical[r, c+1] != 0
                sum_edges = top + bottom + right
                if sum_edges == 2:
                    three_count += 1
        return three_count

    # Collect all legal moves with capture counts and three-sided penalties
    moves = []
    # Check horizontal edges
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] == 0:
                cap = get_captures('H', r, c)
                three = get_three_sided_count('H', r, c)
                moves.append((-cap, three, r, c, 'H'))
    # Check vertical edges
    for r in range(4):
        for c in range(5):
            if vertical[r, c] == 0:
                cap = get_captures('V', r, c)
                three = get_three_sided_count('V', r, c)
                moves.append((-cap, three, r, c, 'V'))

    if not moves:
        return "0,0,H"  # Fallback, though should not occur in practice

    # Sort moves by priority: highest captures, then least three-sided boxes
    moves.sort(key=lambda x: (x[0], x[1]))

    # Find all candidates with maximum captures
    max_capture = -moves[0][0]
    candidates = [m for m in moves if -m[0] == max_capture]

    if candidates:
        # Prefer moves with least three-sided boxes
        candidates.sort(key=lambda x: (x[1], x[0]))
        best_move = candidates[0]
        return f"{best_move[2]},{best_move[3]},{best_move[4]}"
    else:
        # No capture possible; choose move that minimizes three-sided boxes
        moves_without_captures = [m for m in moves if m[0] == 0]
        if moves_without_captures:
            moves_without_captures.sort(key=lambda x: (x[1], x[0]))
            best_move = moves_without_captures[0]
            return f"{best_move[2]},{best_move[3]},{best_move[4]}"
        else:
            # Fallback to the first available move
            return f"{moves[0][2]},{moves[0][3]},{moves[0][4]}"
