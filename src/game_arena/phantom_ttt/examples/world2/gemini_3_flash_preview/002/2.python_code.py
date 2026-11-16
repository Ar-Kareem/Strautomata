
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Phantom Tic Tac Toe Policy.
    board[r][c] == 1: Confirmed mine.
    board[r][c] == 0: Unknown (Empty or Opponent's).
    """

    # 1. Check for immediate winning moves
    # We look for lines where we have 2 marks and 1 unknown.
    lines = []
    # Rows
    for r in range(3):
        lines.append([(r, 0), (r, 1), (r, 2)])
    # Cols
    for c in range(3):
        lines.append([(0, c), (1, c), (2, c)])
    # Diagonals
    lines.append([(0, 0), (1, 1), (2, 2)])
    lines.append([(0, 2), (1, 1), (2, 0)])

    for line in lines:
        marks = [board[r][c] for r, c in line]
        if sum(marks) == 2:
            # Find the index of the 0
            for r, c in line:
                if board[r][c] == 0:
                    return (r, c)

    # 2. Heuristic positioning
    # Priority: Center -> Corners -> Edges
    
    # Center
    if board[1][1] == 0:
        return (1, 1)

    # Corners
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    random.shuffle(corners)
    for r, c in corners:
        if board[r][c] == 0:
            return (r, c)

    # Edges
    edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
    random.shuffle(edges)
    for r, c in edges:
        if board[r][c] == 0:
            return (r, c)

    # Fallback (should not be reached if there are any 0s left)
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                return (r, c)

    return (0, 0) # Ultimate fallback
