
import random

def generate_winning_lines():
    """Return all 49 winning triples in a 3×3×3 board."""
    lines = []

    # Axis‑aligned lines (x, y, z)
    for j in range(3):
        for k in range(3):
            lines.append([(i, j, k) for i in range(3)])       # along X (vary i)
    for i in range(3):
        for k in range(3):
            lines.append([(i, j, k) for j in range(3)])       # along Y (vary j)
    for i in range(3):
        for j in range(3):
            lines.append([(i, j, k) for k in range(3)])       # along Z (vary k)

    # Face diagonals (three orthogonal 2‑D planes)
    for k in range(3):
        lines.append([(i, i, k)   for i in range(3)])        # main XY diagonal
        lines.append([(i, 2-i, k) for i in range(3)])        # anti‑XY diagonal
    for i in range(3):
        lines.append([(i, j, j)   for j in range(3)])        # main YZ diagonal
        lines.append([(i, j, 2-j) for j in range(3)])        # anti‑YZ diagonal
    for j in range(3):
        lines.append([(i, j, i)   for i in range(3)])        # main XZ diagonal
        lines.append([(i, j, 2-i) for i in range(3)])        # anti‑XZ diagonal

    # Space diagonals
    lines.append([(0, 0, 0),   (1, 1, 1), (2, 2, 2)])
    lines.append([(0, 0, 2),   (1, 1, 1), (2, 2, 0)])
    lines.append([(0, 2, 0),   (1, 1, 1), (2, 0, 2)])
    lines.append([(0, 2, 2),   (1, 1, 1), (2, 0, 0)])

    return lines


def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Choose a legal move for the player whose mark is 1.
    Returns a tuple (i, j, k) with 0 ≤ i,j,k ≤ 2.
    """
    # List of all empty cells
    empties = [(i, j, k)
               for i in range(3) for j in range(3) for k in range(3)
               if board[i][j][k] == 0]
    if not empties:
        raise ValueError("No empty cells on a full board – cannot make a move.")

    lines = generate_winning_lines()

    # How many winning lines contain each cell (centrality measure)
    line_counts = {}
    for line in lines:
        for cell in line:
            line_counts[cell] = line_counts.get(cell, 0) + 1

    # Helper dictionaries to count own/opponent one‑in‑a‑row threats for each empty cell
    own1_counts = {cell: 0 for cell in empties}
    opp1_counts = {cell: 0 for cell in empties}

    # Sets of cells that give us an instant win or the opponent an instant win
    own_two = set()
    opp_two = set()

    for line in lines:
        marks = [board[x][y][z] for x, y, z in line]
        one_cells = [line[i] for i, m in enumerate(marks) if m == 1]
        neg_one_cells = [line[i] for i, m in enumerate(marks) if m == -1]
        zero_cells = [line[i] for i, m in enumerate(marks) if m == 0]

        if len(one_cells) == 2:
            own_two.update(zero_cells)
        if len(neg_one_cells) == 2:
            opp_two.update(zero_cells)

        if len(one_cells) == 1:
            for cell in zero_cells:
                own1_counts[cell] += 1
        if len(neg_one_cells) == 1:
            for cell in zero_cells:
                opp1_counts[cell] += 1

    # 1️⃣ Immediate win
    if own_two:
        # Prefer central cells among winning moves
        moves = sorted(own_two,
                       key=lambda c: (-line_counts.get(c, 0), -own1_counts[c]))
        return moves[0]

    # 2️⃣ Block opponent's immediate win
    if opp_two:
        # Block centrally if possible
        moves = sorted(opp_two,
                       key=lambda c: (-line_counts.get(c, 0), -opp1_counts[c]))
        return moves[0]

    # 3️⃣ General best move
    # Primary: most central lines
    # Secondary: most own one‑in‑a‑row threats (potential double‑threat)
    # Tertiary: fewest opponent one‑in‑a‑row threats
    moves = sorted(empties,
                   key=lambda c: (-line_counts.get(c, 0),
                                 -own1_counts[c],
                                 opp1_counts[c]))
    return moves[0]
