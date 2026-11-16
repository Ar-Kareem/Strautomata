
import random
from typing import List, Tuple

def _generate_lines() -> List[Tuple[Tuple[int,int,int], ...]]:
    """Generate all unique straight lines of length 3 in a 3x3x3 grid."""
    lines = []
    seen = set()
    for x in range(3):
        for y in range(3):
            for z in range(3):
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        for dz in (-1, 0, 1):
                            if dx == dy == dz == 0:
                                continue
                            coords = tuple((x + t*dx, y + t*dy, z + t*dz) for t in range(3))
                            # all must be in bounds
                            if all(0 <= a < 3 and 0 <= b < 3 and 0 <= c < 3 for (a,b,c) in coords):
                                # canonicalize so we keep each line once: require that the start is the lexicographically smallest
                                if min(coords) == (x,y,z):
                                    if coords not in seen:
                                        seen.add(coords)
                                        lines.append(coords)
    return lines

# Precompute lines once
_LINES = _generate_lines()

def policy(board: List[List[List[int]]]) -> Tuple[int,int,int]:
    """
    Choose a move for 3x3x3 Tic-Tac-Toe.
    board: 3x3x3 list of lists containing 0 (empty), 1 (us), -1 (opponent)
    returns: (x,y,z) each in 0..2
    """
    # Helper to read board values
    def val(cell):
        x,y,z = cell
        return board[x][y][z]

    # Find immediate winning move for us (sum == 2 -> two 1s + one 0)
    winning_moves = []
    blocking_moves = []
    for line in _LINES:
        s = sum(val(c) for c in line)
        # Winning condition for us: 2 (1+1+0)
        if s == 2:
            for c in line:
                if val(c) == 0:
                    winning_moves.append(c)
        # Block opponent: -2 (-1 + -1 + 0)
        if s == -2:
            for c in line:
                if val(c) == 0:
                    blocking_moves.append(c)

    if winning_moves:
        return random.choice(winning_moves)
    if blocking_moves:
        return random.choice(blocking_moves)

    # If center available, take it
    if board[1][1][1] == 0:
        return (1,1,1)

    # Prefer corners
    corners = [(x,y,z) for x in (0,2) for y in (0,2) for z in (0,2)]
    empty_corners = [c for c in corners if val(c) == 0]
    if empty_corners:
        return random.choice(empty_corners)

    # Otherwise score empty cells by how many "good" lines they are part of.
    # A line is "good" if it contains no opponent stones. Weight lines that already contain one of our marks higher.
    scores = {}
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] != 0:
                    continue
                cell = (x,y,z)
                score = 0
                for line in _LINES:
                    if cell in line:
                        line_vals = [val(c) for c in line]
                        if -1 in line_vals:
                            continue  # opponent blocks this line
                        # No opponent; prefer lines with our marks (closer to winning)
                        my_count = line_vals.count(1)
                        if my_count == 2:
                            score += 100  # high priority (should have been caught earlier)
                        elif my_count == 1:
                            score += 10
                        else:
                            score += 1
                scores[cell] = score

    if scores:
        # pick highest scoring cells, break ties randomly
        maxscore = max(scores.values())
        best = [c for c,s in scores.items() if s == maxscore]
        return random.choice(best)

    # Fallback: pick any empty cell (shouldn't reach here)
    empties = [(x,y,z) for x in range(3) for y in range(3) for z in range(3) if board[x][y][z] == 0]
    if empties:
        return random.choice(empties)

    # No moves (board full) -- return a default
    return (0,0,0)

# If this file is imported, policy is available. If run directly, provide a simple random-test example.
if __name__ == "__main__":
    # Example empty board
    b = [[[0 for _ in range(3)] for _ in range(3)] for _ in range(3)]
    print("Move chosen:", policy(b))
