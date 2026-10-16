
from typing import List, Tuple

def _generate_lines(n: int) -> List[List[Tuple[int,int,int]]]:
    """
    Generate all winning lines for an n x n x n tic-tac-toe board.
    Coordinates are tuples (z, y, x) matching board[z][y][x].
    """
    lines = []

    # Layers (z fixed): rows, columns, diagonals
    for z in range(n):
        for y in range(n):
            # row along x
            lines.append([(z, y, x) for x in range(n)])
        for x in range(n):
            # column along y
            lines.append([(z, y, x) for y in range(n)])
        # two diagonals in this layer
        lines.append([(z, i, i) for i in range(n)])
        lines.append([(z, i, n - 1 - i) for i in range(n)])

    # Columns through layers (z varies) for each (y,x)
    for y in range(n):
        for x in range(n):
            lines.append([(z, y, x) for z in range(n)])

    # Diagonals in xz planes for each fixed y (x vs z)
    for y in range(n):
        lines.append([(i, y, i) for i in range(n)])           # main diag of xz plane
        lines.append([(i, y, n - 1 - i) for i in range(n)])   # anti-diag of xz plane

    # Diagonals in yz planes for each fixed x (y vs z)
    for x in range(n):
        lines.append([(i, i, x) for i in range(n)])           # main diag of yz plane
        lines.append([(i, n - 1 - i, x) for i in range(n)])   # anti-diag of yz plane

    # 4 space diagonals
    lines.append([(i, i, i) for i in range(n)])
    lines.append([(i, i, n - 1 - i) for i in range(n)])
    lines.append([(i, n - 1 - i, i) for i in range(n)])
    lines.append([(i, n - 1 - i, n - 1 - i) for i in range(n)])

    # Deduplicate (some lines may be added multiple times for n>3 structures); keep unique preserving order
    seen = set()
    unique_lines = []
    for line in lines:
        key = tuple(line)
        if key not in seen:
            seen.add(key)
            unique_lines.append(line)
    return unique_lines

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    """
    Choose next move for 3x3x3 tic-tac-toe.
    board is indexed as board[z][y][x], values: 0 empty, 1 = us, -1 = opponent.
    Returns (z, y, x) tuple of integers in 0..n-1.
    Strategy:
      1. If we can win immediately, play the winning cell.
      2. If opponent can win next, block.
      3. Try to create a fork (maximize number of immediate threats next turn).
      4. Play center if free.
      5. Choose cell maximizing a heuristic score (favor lines without opponent and with more of our pieces).
      6. Fallback: first empty cell.
    """
    n = len(board)
    lines = _generate_lines(n)

    # Helper to access board and check empties
    def value_at(coord):
        z,y,x = coord
        return board[z][y][x]

    # Collect empty cells
    empties = [(z,y,x) for z in range(n) for y in range(n) for x in range(n) if board[z][y][x] == 0]
    if not empties:
        # No moves available; arbitrary return
        return (0,0,0)

    # Quick helpers to evaluate a line
    def line_counts(line):
        cnt_us = cnt_op = cnt_empty = 0
        empt_coord = None
        for c in line:
            v = value_at(c)
            if v == 1:
                cnt_us += 1
            elif v == -1:
                cnt_op += 1
            else:
                cnt_empty += 1
                empt_coord = c
        return cnt_us, cnt_op, cnt_empty, empt_coord

    # 1. Immediate win
    for line in lines:
        cnt_us, cnt_op, cnt_empty, empt_coord = line_counts(line)
        if cnt_us == n - 1 and cnt_empty == 1:
            return empt_coord

    # 2. Block opponent immediate win
    for line in lines:
        cnt_us, cnt_op, cnt_empty, empt_coord = line_counts(line)
        if cnt_op == n - 1 and cnt_empty == 1:
            return empt_coord

    # 3. Try to create a fork: for each empty, simulate move and count how many lines become (n-1 us and 1 empty)
    best_fork_cell = None
    best_fork_count = -1
    for cell in empties:
        z0,y0,x0 = cell
        # simulate
        # count potential immediate wins after playing here
        fork_count = 0
        for line in lines:
            if cell not in line:
                continue
            # compute counts if we play here
            cnt_us = cnt_op = cnt_empty = 0
            for c in line:
                if c == cell:
                    v = 1
                else:
                    v = value_at(c)
                if v == 1:
                    cnt_us += 1
                elif v == -1:
                    cnt_op += 1
                else:
                    cnt_empty += 1
            if cnt_us == n - 1 and cnt_empty == 1:
                fork_count += 1
        if fork_count > best_fork_count:
            best_fork_count = fork_count
            best_fork_cell = cell
    if best_fork_count > 0 and best_fork_cell is not None:
        return best_fork_cell

    # 4. Center
    center = (n//2, n//2, n//2)
    if board[center[0]][center[1]][center[2]] == 0:
        return center

    # 5. Heuristic: score empties by sum over lines passing through cell.
    # Lines that contain opponent get 0 contribution. Otherwise contribution grows with our pieces in that line.
    # We'll use weight = 10 ** (count_of_our_pieces_in_line_after_move)
    best_cell = None
    best_score = -1
    for cell in empties:
        score = 0
        for line in lines:
            if cell not in line:
                continue
            cnt_us = cnt_op = cnt_empty = 0
            for c in line:
                if c == cell:
                    v = 1
                else:
                    v = value_at(c)
                if v == 1:
                    cnt_us += 1
                elif v == -1:
                    cnt_op += 1
                else:
                    cnt_empty += 1
            if cnt_op > 0:
                # if opponent already in this line, it's contested; give small value if we still have many.
                # But largely avoid
                continue
            # reward lines with more of our pieces after playing here
            score += 10 ** cnt_us
        if score > best_score:
            best_score = score
            best_cell = cell

    if best_cell is not None:
        return best_cell

    # 6. Fallback: return first empty
    return empties[0]
