
import itertools

# Precompute all winning lines in a 3x3x3 tic-tac-toe board.
def _generate_lines():
    lines = set()
    for x, y, z in itertools.product(range(3), repeat=3):
        for dx, dy, dz in itertools.product([-1, 0, 1], repeat=3):
            if dx == dy == dz == 0:
                continue
            # Only start lines at a cell that doesn't have a predecessor in this direction (avoid duplicates)
            prev = (x - dx, y - dy, z - dz)
            if 0 <= prev[0] < 3 and 0 <= prev[1] < 3 and 0 <= prev[2] < 3:
                continue
            # Build the 3-length line
            coords = []
            cx, cy, cz = x, y, z
            valid = True
            for _ in range(3):
                if 0 <= cx < 3 and 0 <= cy < 3 and 0 <= cz < 3:
                    coords.append((cx, cy, cz))
                    cx += dx; cy += dy; cz += dz
                else:
                    valid = False
                    break
            if valid and len(coords) == 3:
                lines.add(tuple(coords))
    return list(lines)

_LINES = _generate_lines()

def _board_value(board, coord):
    x, y, z = coord
    return board[x][y][z]

def _set_board_value(board, coord, val):
    x, y, z = coord
    board[x][y][z] = val

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Choose a move (x, y, z) in 0..2 for each dimension.
    Strategy:
    1. If we can win immediately, take that move.
    2. If opponent can win immediately, block that move.
    3. Choose a move that creates the largest number of immediate-winning threats (fork).
    4. Otherwise prefer center, then cells closest to center.
    """
    # Helper: list of empty cells
    empties = [(x, y, z)
               for x, y, z in itertools.product(range(3), repeat=3)
               if board[x][y][z] == 0]

    # Quick safety: if no empties (shouldn't happen), return (0,0,0)
    if not empties:
        return (0, 0, 0)

    # 1) Immediate win for us (player 1)
    for line in _LINES:
        vals = [ _board_value(board, c) for c in line ]
        if sum(vals) == 2 and vals.count(0) == 1:
            idx = vals.index(0)
            return line[idx]

    # 2) Immediate block (opponent is -1)
    for line in _LINES:
        vals = [ _board_value(board, c) for c in line ]
        if sum(vals) == -2 and vals.count(0) == 1:
            idx = vals.index(0)
            return line[idx]

    # 3) For each empty cell, simulate placing our mark and count how many lines become immediate wins next turn.
    def count_created_threats(cell):
        # simulate
        x, y, z = cell
        # create a shallow copy structure to modify
        board_copy = [[[board[i][j][k] for k in range(3)] for j in range(3)] for i in range(3)]
        board_copy[x][y][z] = 1
        threats = 0
        for line in _LINES:
            vals = [ board_copy[a][b][c] for (a,b,c) in line ]
            # If after our move the line is one move away from us winning, it's a threat.
            if sum(vals) == 2 and vals.count(0) == 1:
                threats += 1
        return threats

    best_cell = None
    best_threats = -1
    # Evaluate all empties
    # We'll gather candidates that maximize threats
    for cell in empties:
        t = count_created_threats(cell)
        if t > best_threats:
            best_threats = t
            best_cell = cell

    if best_threats > 0 and best_cell is not None:
        return best_cell

    # 4) Prefer center if available
    center = (1, 1, 1)
    if center in empties:
        return center

    # 5) Otherwise choose the empty cell closest to the center (tie-broken deterministically)
    def distance_to_center(cell):
        # Use squared Euclidean distance to center (1,1,1)
        return (cell[0]-1)**2 + (cell[1]-1)**2 + (cell[2]-1)**2

    empties_sorted = sorted(empties, key=lambda c: (distance_to_center(c), c))
    return empties_sorted[0]
