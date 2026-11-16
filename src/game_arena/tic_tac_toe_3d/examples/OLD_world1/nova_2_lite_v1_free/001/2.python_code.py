
"""
Policy for a 3x3x3 3D Tic Tac Toe game.
The function selects the first empty cell (value 0) it encounters when scanning
the board in layer, row, column order.
"""

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Returns the coordinates (layer, row, column) of the first empty cell (0)
    found while iterating through the board in layer-major order.
    
    Parameters
    ----------
    board : list[list[list[int]]]
        A 3x3x3 nested list representing the game board.
        Each element is 0 (empty), 1 (player), or -1 (opponent).

    Returns
    -------
    tuple[int, int, int]
        Coordinates (z, y, x) of the chosen empty cell.
    """
    n = len(board)  # board dimension (should be 3)
    for z in range(n):
        for y in range(n):
            for x in range(n):
                if board[z][y][x] == 0:
                    return (z, y, x)
    # If no empty cell is found (should not happen in legal game state),
    # return a fallback coordinate (0,0,0). In practice this will never be reached.
    return (0, 0, 0)
