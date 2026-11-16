
from typing import List, Tuple

# Cache the list of winning lines so we don't rebuild it every call
_LINES = None

def _generate_lines() -> List[List[Tuple[int,int,int]]]:
    lines = []
    # Straight lines along axes
    # x varies (i), y fixed (j), z fixed (k)
    for j in range(3):
        for k in range(3):
            lines.append([(i, j, k) for i in range(3)])
    # y varies, x and z fixed
    for i in range(3):
        for k in range(3):
            lines.append([(i, j, k) for j in range(3)])
    # z varies, x and y fixed
    for i in range(3):
        for j in range(3):
            lines.append([(i, j, k) for k in range(3)])

    # Face diagonals on planes x fixed (y-z planes)
    for i in range(3):
        lines.append([(i, d, d) for d in range(3)])
        lines.append([(i, d, 2-d) for d in range(3)])

    # Face diagonals on planes y fixed (x-z planes)
    for j in range(3):
        lines.append([(d, j, d) for d in range(3)])
        lines.append([(d, j, 2-d) for d in range(3)])

    # Face diagonals on planes z fixed (x-y planes)
    for k in range(3):
        lines.append([(d, d, k) for d in range(3)])
        lines.append([(d, 2-d, k) for d in range(3)])

    # Space diagonals (4)
    lines.append([(0,0,0),(1,1,1),(2,2,2)])
    lines.append([(0,0,2),(1,1,1),(2,2,0)])
    lines.append([(0,2,0),(1,1,1),(2,0,2)])
    lines.append([(2,0,0),(1,1,1),(0,2,2)])

    # Remove duplicates if any (just in case)
    uniq = []
    seen = set()
    for ln in lines:
        key = tuple(ln)
        if key not in seen:
            seen.add(key)
            uniq.append(ln)
    return uniq

def _get_lines():
    global _LINES
    if _LINES is None:
        _LINES = _generate_lines()
    return _LINES

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    """
    Choose next move for 3x3x3 Tic Tac Toe.
    board is a 3x3x3 list where board[i][j][k] in {0, 1, -1}.
    Returns (i, j, k) of an empty cell.
    """
    lines = _get_lines()

    # Helper to find empty coordinate in a line
    def empty_in_line(ln):
        for (i,j,k) in ln:
            if board[i][j][k] == 0:
                return (i,j,k)
        return None

    # 1) Immediate winning move (two 1s and one 0)
    for ln in lines:
        s = sum(board[i][j][k] for (i,j,k) in ln)
        if s == 2:  # two of mine (1) and one empty
            e = empty_in_line(ln)
            if e is not None:
                return e

    # 2) Block opponent immediate win (two -1s and one 0)
    for ln in lines:
        s = sum(board[i][j][k] for (i,j,k) in ln)
        if s == -2:
            e = empty_in_line(ln)
            if e is not None:
                return e

    # 3) Take center if available
    if board[1][1][1] == 0:
        return (1,1,1)

    # 4) Heuristic: score empty cells by potential
    # For lines containing the cell: if no opponent marks in line, give weight depending on how many of my marks
    weights = {0: 1, 1: 10, 2: 100}
    best_score = None
    best_move = None
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] != 0:
                    continue
                score = 0
                for ln in lines:
                    if (i,j,k) not in ln:
                        continue
                    my_count = 0
                    opp_count = 0
                    for (a,b,c) in ln:
                        v = board[a][b][c]
                        if v == 1:
                            my_count += 1
                        elif v == -1:
                            opp_count += 1
                    if opp_count == 0:
                        # This line is free of opponent; value increases with my_count
                        score += weights.get(my_count, 0)
                    # If opponent occupies but I have none, it's not useful for me (we already blocked immediate threats)
                if best_score is None or score > best_score:
                    best_score = score
                    best_move = (i,j,k)
    # 5) If for some reason best_move is None (shouldn't happen), pick first empty
    if best_move is not None:
        return best_move

    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    return (i,j,k)

    # Board full (no valid moves) - return a default valid tuple (should not happen in normal play)
    return (0,0,0)
