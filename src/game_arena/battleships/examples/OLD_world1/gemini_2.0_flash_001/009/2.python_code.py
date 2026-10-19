
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    A targeting policy for a Battleship-like game on a 10x10 grid.

    Args:
        board: A list of lists representing the current knowledge of the opponent's grid.
            0: unknown cell
            -1: miss
            1: hit

    Returns:
        A tuple (row, col) representing the coordinates of the next cell to target.
    """

    n = len(board)

    # Prioritize cells adjacent to hits
    potential_targets = []
    for row in range(n):
        for col in range(n):
            if board[row][col] == 1:
                # Check adjacent cells
                for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    new_row, new_col = row + dr, col + dc
                    if 0 <= new_row < n and 0 <= new_col < n and board[new_row][new_col] == 0:
                        potential_targets.append((new_row, new_col))

    if potential_targets:
        return random.choice(potential_targets)

    # If no hits, target randomly
    unknown_cells = []
    for row in range(n):
        for col in range(n):
            if board[row][col] == 0:
                unknown_cells.append((row, col))

    if unknown_cells:
        return random.choice(unknown_cells)

    # If all cells have been targeted (should not happen), return a random cell
    return (random.randint(0, n - 1), random.randint(0, n - 1))

if __name__ == '__main__':
    # Example usage:
    board = [[0] * 10 for _ in range(10)]
    board[2][3] = 1
    board[2][4] = -1
    board[5][5] = 0

    row, col = policy(board)
    print(f"Targeting: ({row}, {col})")
