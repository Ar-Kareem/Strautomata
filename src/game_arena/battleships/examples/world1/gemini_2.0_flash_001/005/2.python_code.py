
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    A Battleship policy that combines pattern-based targeting after a hit
    and random exploration for initial search.
    """
    n = 10

    def get_unexplored_cells(board):
        """Returns a list of (row, col) tuples representing unexplored cells."""
        unexplored = []
        for r in range(n):
            for c in range(n):
                if board[r][c] == 0:
                    unexplored.append((r, c))
        return unexplored

    def get_adjacent_cells(row, col):
        """Returns a list of valid adjacent (row, col) tuples."""
        adjacent = []
        if row > 0:
            adjacent.append((row - 1, col))
        if row < n - 1:
            adjacent.append((row + 1, col))
        if col > 0:
            adjacent.append((row, col - 1))
        if col < n - 1:
            adjacent.append((row, col + 1))
        return adjacent

    def get_promising_cells(board):
        """Returns a list of promising cells based on hits."""
        promising = []
        for r in range(n):
            for c in range(n):
                if board[r][c] == 1:  # Hit
                    adj = get_adjacent_cells(r, c)
                    for ar, ac in adj:
                        if board[ar][ac] == 0:
                            promising.append((ar, ac))
        return promising

    def get_extended_promising_cells(board):
        extended_promising = []
        for r in range(n):
            for c in range(n):
                if board[r][c] == 1:
                    # Check horizontally
                    left = c
                    while left > 0 and board[r][left-1] == 1:
                        left -= 1
                    right = c
                    while right < n - 1 and board[r][right+1] == 1:
                        right += 1

                    if left > 0 and board[r][left-1] == 0:
                        extended_promising.append((r, left-1))
                    if right < n - 1 and board[r][right+1] == 0 :
                        extended_promising.append((r, right+1))

                    # Check vertically
                    up = r
                    while up > 0 and board[up-1][c] == 1:
                        up -= 1
                    down = r
                    while down < n - 1 and board[down+1][c] == 1:
                        down += 1
                    
                    if up > 0 and board[up-1][c] == 0:
                        extended_promising.append((up-1, c))
                    if down < n - 1 and board[down+1][c] == 0:
                        extended_promising.append((down+1, c))
        return extended_promising


    # Prioritize promising cells adjacent to hits
    promising_cells = get_extended_promising_cells(board)
    if promising_cells:
        return random.choice(promising_cells)

    # Otherwise, explore randomly
    unexplored_cells = get_unexplored_cells(board)
    if unexplored_cells:
        return random.choice(unexplored_cells)

    # If all cells have been explored (unlikely, but handle it), return a random cell
    return (0, 0)
