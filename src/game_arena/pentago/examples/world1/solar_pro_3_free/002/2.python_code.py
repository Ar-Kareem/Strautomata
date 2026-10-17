
import numpy as np
import random
from collections import defaultdict

# Direction vectors for straight‑line checks
DIRS = [(0, 1), (1, 0), (1, 1), (1, -1)]

def _rotated_local(i, j, length, direction):
    """Rotate a local coordinate inside a 3×3 quadrant."""
    size = length
    if direction == 'L':
        # anticlockwise 90°
        return (j, size - 1 - i)
    else:  # 'R'
        # clockwise 90°
        return (size - 1 - j, i)

def rotate_combined(board, quad, direction):
    """
    Rotate the given 6×6 board (values: 1 = you, 2 = opponent) by a
    quadrant and a direction (L or R). After rotation, any cell that receives
    both a yours and an opponent marble is cleared.
    """
    rows, cols = board.shape
    # Quadrant offsets
    row_off = [0, 0, 3, 3][quad]
    col_off = [0, 3, 0, 3][quad]
    size = 3

    # Map new coordinates to owners (list of 1/2)
    owners = defaultdict(list)
    for i in range(rows):
        for j in range(cols):
            val = board[i, j]
            if val == 0:
                continue
            local_i = i - row_off
            local_j = j - col_off
            new_local = _rotated_local(local_i, local_j, size, direction)
            new_i = new_local[0] + row_off
            new_j = new_local[1] + col_off
            owners[(new_i, new_j)].append(val)

    # Apply the occupancy rule
    out = np.zeros_like(board)
    for (i, j), owners_list in owners.items():
        if len(owners_list) == 2:
            out[i, j] = 0
        elif len(owners_list) == 1:
            out[i, j] = owners_list[0]
        # (len == 0) stays 0 – nothing to do
    return out

def check_you_win(board):
    """Return True iff board contains 5 (or more) of your marbles in a straight line."""
    # Only need to look for 5‑in‑a‑row; longer lines are impossible on a 6×6 board
    for dr, dc in DIRS:
        if dr == 0:  # horizontal
            for r in range(6):
                for c in range(6 - 5 + 1):
                    line = board[r, c:c + 5]
                    if np.all(line == 1):
                        return True
        elif dc == 0:  # vertical
            for c in range(6):
                for r in range(6 - 5 + 1):
                    line = board[r:r + 5, c]
                    if np.all(line == 1):
                        return True
        else:  # diagonals
            # top‑left to bottom‑right
            for r in range(6 - 5 + 1):
                for c in range(6 - 5 + 1):
                    line = board[r:r + 5, c:c + 5].diagonal()
                    if np.all(line == 1):
                        return True
            # top‑right to bottom‑left
            for r in range(6 - 5 + 1):
                for c in range(6 - 5, 6):
                    line = [board[r + k, c - k] for k in range(5)]
                    if np.all([line[k] == 1 for k in range(5)]):
                        return True
    return False

def count_full_lines(board, marker, length):
    """Count straight lines of exactly `length` cells that are all `marker` (1 or 2)."""
    cnt = 0
    if length == 5:
        # horizontal
        for r in range(6):
            for c in range(6 - 5 + 1):
                line = board[r, c:c + 5]
                if np.all(line == marker):
                    cnt += 1
        # vertical
        for c in range(6):
            for r in range(6 - 5 + 1):
                line = board[r:r + 5, c]
                if np.all(line == marker):
                    cnt += 1
        # diagonal \
        for r in range(6 - 5 + 1):
            for c in range(6 - 5 + 1):
                line = board[r:r + 5, c:c + 5].diagonal()
                if np.all(line == marker):
                    cnt += 1
        # diagonal /
        for r in range(6 - 5 + 1):
            for c in range(6 - 5, 6):
                line = [board[r + k, c - k] for k in range(5)]
                if np.all(line == marker):
                    cnt += 1
    else:
        # length 4 or 3 – same pattern, just different start ranges
        horiz_start = range(6 - length + 1)
        vert_start = range(6 - length + 1)
        # horizontal
        for r in range(6):
            for c in horiz_start:
                line = board[r, c:c + length]
                if np.all(line == marker):
                    cnt += 1
        # vertical
        for c in range(6):
            for r in vert_start:
                line = board[r:r + length, c]
                if np.all(line == marker):
                    cnt += 1
        # diagonal \
        for r in range(6 - length + 1):
            for c in range(6 - length + 1):
                line = board[r:r + length, c:c + length].diagonal()
                if np.all(line == marker):
                    cnt += 1
        # diagonal /
        for r in range(6 - length + 1):
            for c in range(6 - length, 6):
                line = [board[r + k, c - k] for k in range(length)]
                if np.all(line == marker):
                    cnt += 1
    return cnt

def evaluate(you_board, opponent_board):
    """Heuristic score = your lines (5/4/3) – opponent lines + central bonus."""
    # Own line counts
    you_counts = {
        5: count_full_lines(you_board, 1, 5),
        4: count_full_lines(you_board, 1, 4),
        3: count_full_lines(you_board, 1, 3),
    }
    # Opponent line counts (same lengths)
    opp_counts = {
        5: count_full_lines(opponent_board, 2, 5),
        4: count_full_lines(opponent_board, 2, 4),
        3: count_full_lines(opponent_board, 2, 3),
    }
    # Weights
    score_you = (you_counts[5] * 10) + (you_counts[4] * 5) + (you_counts[3] * 3)
    score_opp = (opp_counts[5] * 10) + (opp_counts[4] * 5) + (opp_counts[3] * 3)

    # Central bonus (rows 3‑4 and cols 3‑4 in 1‑indexed)
    central_you = (
        you_board[2, 2] + you_board[2, 3] +
        you_board[3, 2] + you_board[3, 3]
    )
    central_opp = (
        opponent_board[2, 2] + opponent_board[2, 3] +
        opponent_board[3, 2] + opponent_board[3, 3]
    )

    net = score_you - score_opp + central_you
    return net, central_you

def opponent_threats(you, opponent):
    """Return a list of empty cells that would complete a 5‑in‑a‑row for the opponent."""
    combined = np.where(you == 1, 1, np.where(opponent == 1, 2, 0))
    threats = []
    # Only need to examine length‑5 lines (four opponent stones + one empty)
    for dr, dc in DIRS:
        if dr == 0:        # horizontal
            start_r = range(6)
            start_c = range(6 - 5 + 1)   # 0 or 1
        elif dc == 0:      # vertical
            start_r = range(6 - 5 + 1)   # 0 or 1
            start_c = range(6)
        else:              # diagonals
            start_r = range(6 - 5 + 1)   # 0 or 1
            if dc == 1:     # top‑left → bottom‑right
                start_c = range(6 - 5 + 1)
            else:           # top‑right → bottom‑left
                start_c = range(6 - 5, 6)  # 4 or 5
        for r in start_r:
            for c in start_c:
                line_vals = []
                ok = True
                for k in range(5):
                    rr = r + k * dr
                    cc = c + k * dc
                    if not (0 <= rr < 6 and 0 <= cc < 6):
                        ok = False
                        break
                    line_vals.append(combined[rr, cc])
                if not ok:
                    continue
                opp = sum(v == 2 for v in line_vals)
                empty = sum(v == 0 for v in line_vals)
                yours = sum(v == 1 for v in line_vals)
                if opp == 4 and empty == 1 and yours == 0:
                    # locate the empty cell
                    empty_idx = line_vals.index(0)
                    threat = (r + empty_idx * dr, c + empty_idx * dc)
                    threats.append(threat)
    return threats

def policy(you, opponent):
    # Accept both list‑of‑lists and NumPy arrays
    you = np.asarray(you)
    opponent = np.asarray(opponent)

    if you.shape != (6, 6) or opponent.shape != (6, 6):
        raise ValueError("Both boards must be 6×6")

    # ------------------------------------------------------------------
    # 1. Immediate win scan
    # ------------------------------------------------------------------
    empties = [(r, c)
               for r in range(6) for c in range(6)
               if you[r, c] == 0 and opponent[r, c] == 0]

    # Try every candidate – if any gives you an immediate win, return it.
    for (r, c) in empties:
        for quad in range(4):
            for dir in ('L', 'R'):
                # Simulate move
                combined = np.where(you == 1, 1, np.where(opponent == 1, 2, 0))
                combined[r, c] = 1               # place
                rotated = rotate_combined(combined, quad, dir)

                # Split back
                new_you = (rotated == 1).astype(int)
                new_opp = (rotated == 2).astype(int)

                if check_you_win(new_you):
                    return f"{r+1},{c+1},{quad},{dir}"

    # ------------------------------------------------------------------
    # 2. Block opponent's 4‑in‑a‑row threats
    # ------------------------------------------------------------------
    threats = opponent_threats(you, opponent)
    if threats:
        best_score = -float('inf')
        best_move = None
        for (r, c) in threats:
            for quad in range(4):
                for dir in ('L', 'R'):
                    combined = np.where(you == 1, 1, np.where(opponent == 1, 2, 0))
                    combined[r, c] = 1
                    rotated = rotate_combined(combined, quad, dir)
                    new_you = (rotated == 1).astype(int)
                    new_opp = (rotated == 2).astype(int)
                    net, central_you = evaluate(new_you, new_opp)
                    if net > best_score:
                        best_score = net
                        best_move = (r, c, quad, dir)
                    # deterministic tie‑break: keep the first best
        r, c, quad, dir = best_move
        return f"{r+1},{c+1},{quad},{dir}"

    # ------------------------------------------------------------------
    # 3. Full board evaluation – choose move with highest heuristic value
    # ------------------------------------------------------------------
    best_score = -float('inf')
    best_move = None
    central = []
    for (r, c) in empties:
        for quad in range(4):
            for dir in ('L', 'R'):
                combined = np.where(you == 1, 1, np.where(opponent == 1, 2, 0))
                combined[r, c] = 1
                rotated = rotate_combined(combined, quad, dir)
                new_you = (rotated == 1).astype(int)
                new_opp = (rotated == 2).astype(int)

                # Heuristic evaluation
                net, central_you = evaluate(new_you, new_opp)
                # deterministic tie‑break: prefer lower quadrant, then L
                tie_better = False
                if net > best_score:
                    tie_better = True
                elif net == best_score:
                    # compare (quad, dir) lexicographically
                    if (quad < best_move[2] or
                        (quad == best_move[2] and dir < best_move[3])):
                        tie_better = True
                if tie_better:
                    best_score = net
                    best_move = (r, c, quad, dir)

    r, c, quad, dir = best_move
    return f"{r+1},{c+1},{quad},{dir}"
