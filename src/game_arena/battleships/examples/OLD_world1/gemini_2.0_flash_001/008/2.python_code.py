
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Chooses a cell to target on the Battleship board.

    Args:
        board: A 10x10 list of lists representing the current knowledge of the opponent's grid.
               0 -> unknown cell
               -1 -> miss
               1 -> hit

    Returns:
        A tuple (row, col) representing the coordinates of the cell to target.
    """
    n = len(board)

    # Prioritize cells adjacent to hits
    for row in range(n):
        for col in range(n):
            if board[row][col] == 1:
                # Check neighbors
                neighbors = []
                if row > 0 and board[row - 1][col] == 0:
                    neighbors.append((row - 1, col))
                if row < n - 1 and board[row + 1][col] == 0:
                    neighbors.append((row + 1, col))
                if col > 0 and board[row][col - 1] == 0:
                    neighbors.append((row, col - 1))
                if col < n - 1 and board[row][col + 1] == 0:
                    neighbors.append((row, col + 1))
                if neighbors:
                    return random.choice(neighbors)

    # If no hits, choose randomly from unknown cells
    unknown_cells = []
    for row in range(n):
        for col in range(n):
            if board[row][col] == 0:
                unknown_cells.append((row, col))

    if unknown_cells:
        return random.choice(unknown_cells)

    # If no unknown cells, return a random cell (shouldn't happen in a normal game)
    return (random.randint(0, n - 1), random.randint(0, n - 1))

if __name__ == '__main__':
    # Example usage:
    board = [[0] * 10 for _ in range(10)]
    board[2][3] = 1
    board[5][5] = -1
    row, col = policy(board)
    print(f"Targeting: ({row}, {col})")
